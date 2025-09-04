import io, os, re
import json
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import BadRequest
from django.shortcuts import redirect, render
from django.views import View
from .models import Tool
from django.contrib.auth.decorators import login_required
from tools.scripts.AnalysisSequence import convert_gene_table_to_RepeatsFinder_Format, process_gene_table_results
from tools.scripts.split_enzyme_site import find_enzyme_sites
import pandas as pd
from Bio import SeqIO
import zipfile
from io import BytesIO
import requests
from typing import Dict, List, Tuple, Optional
import time

# ==============================================================================
# MiniGeneExtractor Logic - Adapted from extract_mini_genes.py
# ==============================================================================

class MiniGeneExtractorLogic:
    def __init__(self, genome_version='hg38'):
        if genome_version == 'hg19':
            self.ensembl_server = "https://grch37.rest.ensembl.org"
        else:
            self.ensembl_server = "https://rest.ensembl.org"
        self.session = requests.Session()
        
        self.aa_three_to_one = {
            'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
            'Gln': 'Q', 'Glu': 'E', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
            'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
            'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V',
            'Ter': '*', 'Stop': '*'
        }

    def three_to_one_aa(self, three_letter: str) -> str:
        if not three_letter:
            return ''
        return self.aa_three_to_one.get(three_letter, three_letter)

    def parse_hgvs_protein(self, hgvs_p: str) -> Optional[Dict]:
        if pd.isna(hgvs_p) or not hgvs_p:
            return None
        
        try:
            if ':' in hgvs_p:
                protein_id, variant_part = hgvs_p.split(':', 1)
            else:
                protein_id, variant_part = None, hgvs_p
                
            if variant_part.startswith('p.'):
                variant_part = variant_part[2:]
            
            patterns = {
                'range_deletion': r'^([A-Za-z]{3})(\d+)_([A-Za-z]{3})(\d+)del$',
                'single_deletion': r'^([A-Za-z]{3})(\d+)del$',
                'frameshift': r'^([A-Za-z]{3})(\d+)([A-Za-z]{3})fs(?:Ter|\*)(\d+)$',
                'insertion': r'^([A-Za-z]{3})(\d+)_([A-Za-z]{3})(\d+)ins([A-Za-z]+)$',
                'substitution': r'^([A-Za-z]{3})(\d+)([A-Za-z]{3})$'
            }

            match = re.match(patterns['range_deletion'], variant_part)
            if match:
                start_aa, start_pos, end_aa, end_pos = match.groups()
                return {'protein_id': protein_id, 'ref_aa': start_aa, 'position': int(start_pos), 'end_position': int(end_pos), 'end_aa': end_aa, 'alt_aa': '', 'type': 'deletion'}

            match = re.match(patterns['single_deletion'], variant_part)
            if match:
                ref_aa, position = match.groups()
                return {'protein_id': protein_id, 'ref_aa': ref_aa, 'position': int(position), 'alt_aa': '', 'type': 'deletion'}

            match = re.match(patterns['frameshift'], variant_part)
            if match:
                ref_aa, position, alt_aa, ter_position = match.groups()
                return {'protein_id': protein_id, 'ref_aa': ref_aa, 'position': int(position), 'alt_aa': alt_aa, 'ter_position': int(ter_position), 'type': 'frameshift'}

            match = re.match(patterns['insertion'], variant_part)
            if match:
                left_aa, left_pos, right_aa, right_pos, inserted_three = match.groups()
                return {'protein_id': protein_id, 'ref_aa': left_aa, 'position': int(left_pos), 'end_position': int(right_pos), 'end_aa': right_aa, 'alt_aa': inserted_three, 'type': 'insertion'}

            match = re.match(patterns['substitution'], variant_part)
            if match:
                ref_aa, position, alt_aa = match.groups()
                return {'protein_id': protein_id, 'ref_aa': ref_aa, 'position': int(position), 'alt_aa': alt_aa, 'type': 'substitution'}
            
            return None
        except Exception:
            return None

    def parse_hgvs_coding(self, hgvs_c: str) -> Optional[Dict]:
        if pd.isna(hgvs_c) or not hgvs_c:
            return None
        try:
            transcript_id = None
            c_part = hgvs_c
            if ':' in hgvs_c:
                tid, c_part = hgvs_c.split(':', 1)
                if tid.startswith('ENST') or tid.startswith('NM_'):
                    transcript_id = tid
            if c_part.startswith('c.'):
                c_part = c_part[2:]
            
            # Simplified patterns for view context
            m = re.match(r'^(\d+)([ATCG])>([ATCG])$', c_part, flags=re.IGNORECASE)
            if m:
                pos, ref_nt, alt_nt = m.groups()
                return {'type': 'substitution', 'position': int(pos), 'ref_nucleotide': ref_nt.upper(), 'alt_nucleotide': alt_nt.upper(), 'transcript_id': transcript_id}
            
            return {'transcript_id': transcript_id, 'raw': hgvs_c} # Return at least transcript_id
        except Exception:
            return None

    def get_protein_sequence_from_ensembl(self, transcript_id: str) -> Optional[str]:
        try:
            url = f"{self.ensembl_server}/sequence/id/{transcript_id}?type=protein"
            response = self.session.get(url, headers={"Content-Type": "application/json"}, timeout=10)
            if response.status_code == 200:
                return response.json().get('seq')
            return None
        except requests.RequestException:
            return None

    def extract_mini_gene_sequence(self, protein_seq: str, mutation_pos: int, ref_aa: str, alt_aa: str, mutation_type: str = 'substitution', window_size: int = 14) -> Dict:
        pos_0based = mutation_pos - 1
        
        # WT sequence - 突变位置前后各延长window_size个氨基酸
        start_pos_wt = max(0, pos_0based - window_size)
        end_pos_wt = min(len(protein_seq), pos_0based + window_size + 1)
        wt_seq = protein_seq[start_pos_wt:end_pos_wt]

        # MT sequence
        alt_aa_single = self.three_to_one_aa(alt_aa)
        mut_seq_list = list(protein_seq)
        
        if mutation_type == 'substitution':
            if 0 <= pos_0based < len(mut_seq_list):
                mut_seq_list[pos_0based] = alt_aa_single
            mutated_protein = "".join(mut_seq_list)
            start_pos_mt = max(0, pos_0based - window_size)
            end_pos_mt = min(len(mutated_protein), pos_0based + window_size + 1)
            mt_seq = mutated_protein[start_pos_mt:end_pos_mt]

        elif mutation_type == 'deletion':
            # Simplified for now
            mutated_protein = protein_seq[:pos_0based] + protein_seq[pos_0based + 1:]
            start_pos_mt = max(0, pos_0based - window_size)
            end_pos_mt = min(len(mutated_protein), pos_0based + window_size)
            mt_seq = mutated_protein[start_pos_mt:end_pos_mt]
        
        elif mutation_type == 'insertion':
            inserted_one_list = []
            if alt_aa:
                for i in range(0, len(alt_aa), 3):
                    inserted_one_list.append(self.three_to_one_aa(alt_aa[i:i+3]))
            inserted_one = ''.join(inserted_one_list)
            mutated_protein = protein_seq[:pos_0based + 1] + inserted_one + protein_seq[pos_0based + 1:]
            
            # 插入后重新计算位置
            start_pos_mt = max(0, pos_0based - window_size)
            end_pos_mt = min(len(mutated_protein), pos_0based + len(inserted_one) + window_size + 1)
            mt_seq = mutated_protein[start_pos_mt:end_pos_mt]

        else: # frameshift or other complex types
            # Fallback for complex types: show substitution at mutation point
            if 0 <= pos_0based < len(mut_seq_list):
                mut_seq_list[pos_0based] = alt_aa_single
            mutated_protein = "".join(mut_seq_list)
            start_pos_mt = max(0, pos_0based - window_size)
            end_pos_mt = min(len(mutated_protein), pos_0based + window_size + 1)
            mt_seq = mutated_protein[start_pos_mt:end_pos_mt]

        return {
            'WT_Minigene': wt_seq,
            'MUT_Minigene': mt_seq,
        }

    def segment_sequence(self, sequence: str, window_size: int, pad_with_gs: bool) -> List[str]:
        """
        将序列切割为若干段：
        - 每段长度为 (2*window_size + 1)
        - 步长为 window_size（即两段之间重叠 window_size）
        - 最后一段不足长度时：
            - 如果 pad_with_gs 为 True，则在末尾用 'GS' 重复补齐至目标长度；
            - 否则保持原样（不强制补齐）。
        """
        if window_size <= 0:
            return [sequence] if sequence else []
        target_len = 2 * window_size + 1
        step = window_size
        segments: List[str] = []
        n = len(sequence)
        if n == 0:
            return []

        i = 0
        while i < n:
            seg = sequence[i:i + target_len]
            if len(seg) < target_len:
                if pad_with_gs and len(seg) < target_len - 1:  # 如果只差1个位置，保持不补齐至28aa
                    # 末尾用GS重复补齐，直到达到或超过目标长度
                    while len(seg) + 2 <= target_len:
                        seg += 'GS'
                    # 如果现在正好差1个字符，仍然不补，因为只差1个位置的规则
                # 不需要 else，保持原样
            segments.append(seg)
            if i + step >= n:
                break
            i += step
        return segments

    def process_single_mutation(self, hgvs_c: str, hgvs_p: str, options: dict) -> Dict:
        protein_variant = self.parse_hgvs_protein(hgvs_p)
        coding_variant = self.parse_hgvs_coding(hgvs_c)

        if not protein_variant or not coding_variant:
            return {"error": "Invalid HGVSc or HGVSp format."}

        transcript_id = coding_variant.get('transcript_id')
        if not transcript_id:
            return {"error": "Could not extract Transcript ID from HGVSc."}

        protein_seq = self.get_protein_sequence_from_ensembl(transcript_id)
        if not protein_seq:
            return {"error": f"Could not fetch protein sequence for {transcript_id}."}

        result = self.extract_mini_gene_sequence(
            protein_seq,
            protein_variant['position'],
            protein_variant['ref_aa'],
            protein_variant['alt_aa'],
            protein_variant['type'],
            window_size=options.get('window_size', 14)
        )
        
        mut_minigene = result['MUT_Minigene']

        # 1) GS padding：按需求只在末尾补齐到 target_len
        target_len = 2 * options.get('window_size', 14) + 1
        if options.get('gs_padding'):
            # 如果长度不足目标长度
            if len(mut_minigene) < target_len:
                # 如果只差1个位置，就不补，保持为 target_len-1
                if len(mut_minigene) == target_len - 1:
                    pass
                else:
                    # 在末尾用 'GS' 重复补齐到目标长度或尽可能接近且不超过
                    while len(mut_minigene) + 2 <= target_len:
                        mut_minigene += 'GS'
                    # 如果现在刚好差1个字符，按规则不再补
        
        output = {
            'HGVSc': hgvs_c,
            'HGVSp': hgvs_p,
            'Mutation_Type': protein_variant['type'],
            'WT_Minigene': result['WT_Minigene'],
            'MUT_Minigene': mut_minigene,
        }

        # 3) Segment mutated mini-gene：开启时，额外输出分段结果
        if options.get('segment_minigene'):
            segments = self.segment_sequence(mut_minigene, options.get('window_size', 14), options.get('gs_padding'))
            output['MUT_Minigene_Segments'] = " | ".join(segments)
        
        return output

# ==============================================================================
# Django View
# ==============================================================================

class MiniGeneExtractorView(View):
    def get(self, request, *args, **kwargs):
        if 'download' in request.GET and 'results' in request.session:
            results_json = request.session.get('results', '[]')
            results_data = json.loads(results_json)
            df = pd.DataFrame(results_data)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='MiniGene_Results')
            output.seek(0)

            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="minigene_results.xlsx"'
            
            # Clean session
            del request.session['results']
            
            return response
            
        return render(request, 'tools/tools_MiniGeneExtractor.html')

    def post(self, request, *args, **kwargs):
        form_data = request.POST
        input_type = form_data.get('input_type')
        genome_version = form_data.get('genomeVersion', 'hg38')
        
        # Get new options from form
        options = {
            'window_size': int(form_data.get('window_size', 14)),
            'gs_padding': form_data.get('gs_padding') == 'on',
            'segment_minigene': form_data.get('segment_minigene') == 'on',
        }

        extractor = MiniGeneExtractorLogic(genome_version=genome_version)
        results = []
        
        try:
            if input_type == 'text':
                mutation_text = form_data.get('mutation_text', '')
                lines = [line.strip() for line in mutation_text.splitlines() if line.strip()]
                for line in lines:
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    if len(parts) == 2:
                        hgvs_c, hgvs_p = parts[0], parts[1]
                        result = extractor.process_single_mutation(hgvs_c, hgvs_p, options)
                        results.append(result)
                    else:
                        results.append({"error": f"Invalid line format: {line}"})

            elif input_type == 'file':
                mutation_file = request.FILES.get('mutation_file')
                if not mutation_file:
                    return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
                
                try:
                    if mutation_file.name.endswith('.xlsx'):
                        df = pd.read_excel(mutation_file)
                    elif mutation_file.name.endswith('.csv'):
                        df = pd.read_csv(mutation_file)
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Unsupported file type.'}, status=400)

                    # Expecting 'HGVSc' and 'HGVSp' columns
                    if 'HGVSc' not in df.columns or 'HGVSp' not in df.columns:
                         return JsonResponse({'status': 'error', 'message': "File must contain 'HGVSc' and 'HGVSp' columns."}, status=400)

                    for _, row in df.iterrows():
                        hgvs_c = row['HGVSc']
                        hgvs_p = row['HGVSp']
                        if pd.notna(hgvs_c) and pd.notna(hgvs_p):
                            result = extractor.process_single_mutation(hgvs_c, hgvs_p, options)
                            results.append(result)

                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'Error processing file: {str(e)}'}, status=500)

            # Store results in session for download
            request.session['results'] = json.dumps(results)

            return JsonResponse({'status': 'success', 'results_json': json.dumps(results)})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def tools_list(request):
    tools = Tool.objects.all()
    return render(request, 'tools/tools_list.html', {'tools': tools})


def process_fasta_file(fasta_file):
    gene_table = pd.DataFrame(columns=['gene_id', 'sequence'])
    fasta_content = fasta_file.read().decode('utf-8')
    fasta_io = io.StringIO(fasta_content)
    for record in SeqIO.parse(fasta_io, 'fasta'):
        gene_table = gene_table._append({'gene_id': record.id, 'sequence': str(record.seq)}, ignore_index=True)
    return gene_table


@login_required
def SequenceAnalyzer(request):
    if request.method == 'POST':
        upload_type = request.POST.get('uploadType')
        if upload_type == 'file' and 'fastaFile' in request.FILES:
             # 如果有文件上传，通过 request.FILES 读取
            fasta_file = request.FILES['fastaFile']
            gene_table = process_fasta_file(fasta_file)
        elif upload_type == 'table':
            # 尝试从表单字段中读取 JSON 数据
            genetable_json = request.POST.get('genetable')
            if not genetable_json:
                return JsonResponse({'status': 'error', 'message': 'No gene data provided'})
            
            try:
                gene_table = json.loads(genetable_json)
                gene_table = pd.DataFrame(gene_table, columns=['gene_id', 'sequence']).dropna().reset_index(drop=True)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})      
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid upload type or missing data'})
        
        # 从前端获取参数
        long_repeats_min_len = int(request.POST.get('longRepeatsMinLen', 16))
        homopolymers_min_len = int(request.POST.get('homopolymersMinLen', 7))
        min_w_length = int(request.POST.get('minWLength', 12))
        min_s_length = int(request.POST.get('minSLength', 12))
        window_size = int(request.POST.get('windowSize', 30))
        min_gc_content = int(request.POST.get('minGCContent', 20))
        max_gc_content = int(request.POST.get('maxGCContent', 80))

        data = convert_gene_table_to_RepeatsFinder_Format(
            gene_table,
            long_repeats_min_len=long_repeats_min_len,
            homopolymers_min_len=homopolymers_min_len,
            min_w_length=min_w_length,
            min_s_length=min_s_length,
            window_size=window_size,
            min_gc_content=min_gc_content,
            max_gc_content=max_gc_content
        )
        # 处理数据并获取结果 DataFrame
        result_df = process_gene_table_results(data)
        result_df = gene_table.merge(result_df, left_on='gene_id', right_on='GeneName', how='left')
        
        # USE Model 11
        # model_path = 'tools/scripts/best_rf_model_11.pkl'
        # weights_path = 'tools/scripts/best_rf_weights_11.npy'
        # scale_path = 'tools/scripts/scaler_11.pkl'

        # 使用模型预测新数据
        # USE Model 12
        # model_path = 'tools/scripts/best_rf_model_12.pkl'
        # weights_path = 'tools/scripts/best_rf_weights_12.npy'
        # scale_path = None
        # result_df = predict_new_data_from_df(result_df, model_path, scaler=scale_path, weights_path=weights_path)
        # 不预测就没有 ‘total_penalty_score’ 这一列, 所以要单独添加
        feature_columns = [
            'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score','LongRepeats_penalty_score', 
            'Homopolymers_penalty_score', 'DoubleNT_penalty_score'
        ]
        result_df['total_penalty_score'] = sum(result_df[col] for col in feature_columns).round(2)
        
        request.session['gene_table'] = result_df.to_dict(orient='records')
        return JsonResponse({'status': 'success', 'redirect_url': '/tools/sequence_analysis_detail/'})    
    return render(request, 'tools/SequenceAnalyzer.html')

@login_required
def download_gene_table(request):
    # 假设你已经在某个地方存储了需要的数据或可以快速访问/生成它
    # 从会话中获取存储的gene_table
    gene_table_data = request.session.get('gene_table')
    if not gene_table_data:
        return HttpResponse('No gene table data found in the session.', status=404)
    
    # 将数据转换为DataFrame
    df = pd.DataFrame(gene_table_data)

    # 将DataFrame转换为CSV文件
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="gene_analysis_results.csv"'
    return response


@login_required
def sequence_analysis_detail(request):
    gene_table = request.session.get('gene_table', [])

    # 计算每种颜色的数量
    green_count = sum(1 for gene in gene_table if gene['total_penalty_score'] == 0)
    yellow_count = sum(1 for gene in gene_table if 0 < gene['total_penalty_score'] <= 28)
    red_count = sum(1 for gene in gene_table if gene['total_penalty_score'] > 28)

    total_count = len(gene_table)
    green_percentage = (green_count / total_count) * 100 if total_count > 0 else 0
    yellow_percentage = (yellow_count / total_count) * 100 if total_count > 0 else 0
    red_percentage = (red_count / total_count) * 100 if total_count > 0 else 0

    context = {
        'gene_table': gene_table,
        'green_count': green_count,
        'yellow_count': yellow_count,
        'red_count': red_count,
        'green_percentage': green_percentage,
        'yellow_percentage': yellow_percentage,
        'red_percentage': red_percentage,
    }

    return render(request, 'tools/sequence_analysis_detail.html', context)


def upload_file(file_name, project_path):
    # 去掉文件名中的空格,[],()
    file_name_name = file_name.name.replace(" ", "").replace('[',"").replace(']',"")  
    file_name_name = file_name_name.replace("(","").replace(")","")
    file_path = os.path.join(project_path, file_name_name)  # result_path to project_path. Changed by dsy 20230612.
    os.makedirs(project_path, exist_ok=True)
    with open(file_path, 'wb+') as f:
        for chunk in file_name.chunks():
            f.write(chunk)
    return file_path


def GenePlateExplorer(request):
    if request.method == 'GET':
        return render(request, 'tools/tools_GenePlate_Explorer.html')
    elif request.method == 'POST':
        project_name = request.POST.get("project_name", "Default Project")

        temp_dir = 'media/temp/'

        # 检查用户上传的文件组合
        temp_file1 = request.FILES.get("file_name1")
        temp_file2 = request.FILES.get("file_name2")
        temp_file3 = request.FILES.get("file_name3")

        # 初始化文件路径变量
        file1_path, file2_path, file3_path = None, None, None

        # 处理选项1: 上传5p30和3p30文件
        if temp_file1 and temp_file2:
            file1_path = upload_file(temp_file1, temp_dir)
            file2_path = upload_file(temp_file2, temp_dir)
        # 处理选项2: 上传MTPIN文件
        elif temp_file3:
            file3_path = upload_file(temp_file3, temp_dir)
        else:
            # 如果未上传任何有效文件组合，返回错误消息
            return render(request, 'tools/tools_GenePlate_Explorer.html', {'error': '请上传所需的文件组合。'})

        context = {
            'project_name': project_name,
            'file1': file1_path,
            'file2': file2_path,
            'file3': file3_path,
        }
        return render(request, 'tools/tools_GenePlate_Explorer_detail.html', context)


def plate_view(request):
    def well_position(domain_name):
        if pd.notna(domain_name) and '.' in domain_name:
            try:
                position = int(domain_name.split('.')[1])
                rows = 'ABCDEFGHIJKLMNOP'
                row = rows[(position - 1) % 16]
                col = (position - 1) // 16 + 1
                return f'{row}{col}'
            except ValueError:
                return None
        return None

    def extract_project_name(filename):
        basename = os.path.basename(filename)
        a = basename.split('_')
        prj_name = a[2]
        return prj_name

    try:
        data = json.loads(request.body)
        file1 = data.get('file1')
        file2 = data.get('file2')
        file3 = data.get('file3')  # Use get() to handle missing 'file3'
    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'status': 'error', 'message': f"Missing or invalid data: {str(e)}"}, status=400)

    def process_5p30_file(file):
        def split_memo(x):
            # 只找gzip2的值
            pattern = r"(gZip2.*)\|"
            match = re.search(pattern, x)
            if match:
                gzip = match.group(1)
            else:
                gzip = None
            return gzip
        
        project_name = extract_project_name(file)
        try:
            df = pd.read_csv(file, sep='\t')
            df['PRJIN_PLT_ID'] = df['Plate'].apply(lambda x: x.replace('Plate', 'MWF5p30_Plate'))
            df = df.rename(columns={
                'WellPos': 'PRJIN_WellPos',
            })
            df['GeneID'] = 'G' + df['IntraPRJSN'].astype(str).str.zfill(4)

            # for gene assembly.
            df['MWF5_Mfg_ID'] = '[' + df['PRJID'] + '][G' + df['IntraPRJSN'].astype(str).str.zfill(4) + ']'
            df['gZip2'] = df['Memo'].apply(split_memo)
            df['WF5_gzip2_WellPos'] = df['gZip2'].apply(well_position)
            df['len(PostGG2)'] = df['FullSeqREAL'].apply(len)
            gene_assembly_df = df[['MWF5_Mfg_ID', 'PRJIN_PLT_ID', 'PRJIN_WellPos', 'VectorID', 
                                   'gZip2', 'WF5_gzip2_WellPos', 'len(PostGG2)']]
            
            # for layout
            df['FullSeqREAL_Credit_Copy'] = df['FullSeqREAL_Credit']
            df = df.assign(FullSeqREAL_Credit=df['FullSeqREAL_Credit'].str.split(';')).explode('FullSeqREAL_Credit').reset_index(drop=True)
            # df['Subplate'] = 'R' + (df.groupby(['PRJIN_PLT_ID', 'PRJIN_WellPos']).cumcount() + 1).astype(str)
            df = df[['MWF5_Mfg_ID', 'PRJIN_PLT_ID', 'PRJIN_WellPos', 'FullSeqREAL_Credit', 
                     'GeneID', 'FullSeqREAL_Credit_Copy']]
            return df, gene_assembly_df, project_name
        except FileNotFoundError:
            raise BadRequest(f"File not found: {file}")
        except pd.errors.ParserError:
            raise BadRequest(f"Error parsing file: {file}")
        except KeyError as e:
            raise BadRequest(f"Missing expected column: {e.args[0]}")
        except Exception as e:
            raise BadRequest(f"Unexpected error processing file {file}: {str(e)}")
    
    def process_3p30_file(file):
        def split_memo(x):
            pattern = r"\|([A-Z0-9]+)\|([A-Z0-9]+)\.([A-Z0-9]+)\.([a-z0-9]+)\|"
            match = re.search(pattern, x)
            if match:
                var1, var2, var3, var4 = match.groups()
            else:
                var1, var2, var3, var4 = None, None, None, None
            return var1, var2, var3, var4
        
        def transform_spa(spa):
            if spa and len(spa) > 1:
                return f'SPA.{spa[1]}rc'
            return None

        def transform_spb(spb):
            if spb and spb.startswith('B'):
                number_part = spb[1:]
                number = int(number_part)  # 将三位数字转换为整数，去掉前导零
                return f'SPB.{number}'
            return None

        def transform_gzip(gzip):
            if gzip and gzip.startswith('g'):
                number_part = gzip[1:]
                number = int(number_part)
                return f'gZip.{number}'

        def process_gene_name(gene_name):
            if gene_name.startswith('[') and gene_name.endswith(']'):
                # 移除最后一个[]内的内容
                return re.sub(r'\[\d+\]$', '', gene_name)
            return gene_name

        def generate_well_ids(num_wells):
            rows = 'ABCDEFGHIJKLMNOP'
            cols = range(1, 25)
            well_ids = [f'{row}{col}' for col in cols for row in rows]
            return well_ids[:num_wells]

        def process_rank_file(file):
            rank_df = pd.read_csv(file, sep='\t')
            rank_dict = rank_df.set_index('Rank').T.to_dict('list')
            return rank_dict
        
        project_name = extract_project_name(file)
        try:
            df = pd.read_csv(file, sep='\t')
            df = df.rename(columns={
                'Plate': 'WF3_Plate',
                'GeneName': 'WF3_Synthon_GeneName',
                'WellPos': 'WF3_WellPos',
                'FullSeqREAL_Credit': 'WF3_FullSeqREAL_Credit',
            })
            df = df.sort_values(by=['WF3_Synthon_GeneName'])
            df['WF3_PLT_ID'] = df['WF3_Plate'].apply(lambda x: x.replace('Plate', 'WF3p30_Plate0'))
            df['WF3_Mfg_ID'] = '[' + df['PRJID'] + '][G' + df['IntraPRJSN'].astype(str).str.zfill(4) + ']'
            
            df[['ASP', 'SPA', 'SPB', 'gzip']] = df['Memo'].apply(split_memo).apply(pd.Series)
            df['Len'] = df['FullSeqREAL'].apply(len)
            df['SPA_Primer'] = df['SPA'].apply(transform_spa) # 转换SPA列
            df['SPB_DomainName'] = df['SPB'].apply(transform_spb) # 转换SPB列
            df['gZip_DomainName'] = df['gzip'].apply(transform_gzip) # 转换gzip列
            df['ProcessedGeneName'] = df['WF3_Synthon_GeneName'].apply(process_gene_name) # 处理GeneName列

            # 生成 Synthon Rank 列
            df['Rank'] = df.groupby('ProcessedGeneName').cumcount() + 1
            df['Rank'] = 'R' + df['Rank'].astype(str)
            df['Synthon_number'] = df.groupby('ProcessedGeneName')['ProcessedGeneName'].transform('size')
            df['Synthon_number'] = 'S' + df['Synthon_number'].astype(str)
            df['SynRank'] = df['Synthon_number'] + df['Rank']
            syn_rank_file = "tools/scripts/DO2a_PrimerName_Table_Single.txt"
            syn_rank_dict = process_rank_file(syn_rank_file)
            df['Dialout_PrimerWellPos_For']	= df['SynRank']
            df['Dialout_PrimerWellPos_Rev'] = df['SynRank']
            df['Dialout_PrimerName_For'] = df['Dialout_PrimerWellPos_For'].apply(lambda x: syn_rank_dict[x][0] if x in syn_rank_dict else None)
            df['Dialout_PrimerName_Rev'] = df['Dialout_PrimerWellPos_Rev'].apply(lambda x: syn_rank_dict[x][1] if x in syn_rank_dict else None)

            rank_dict = {
                'R1': ['ZY3061-gCF1_alt', 'ZY3072-gCF1alt-RE4'],
                'R2': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
                'R3': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
                'R4': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
                'R5': ['ZY3061-gCF1_alt', 'ZY3072-gCF1alt-RE4'],
                'R6': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
                'R7': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
                'R8': ['ZY2384-GG.gCF', 'ZY3071-gCF1-RE3'],
            }
            # 生成新的列
            df['PostGG1_Forward_Primer'] = df['Rank'].apply(lambda x: rank_dict[x][0] if x in rank_dict else None)
            df['RE_PCR_forMTP_Forward_Primer'] = df['Rank'].apply(lambda x: rank_dict[x][1] if x in rank_dict else None)
            
            # 生成新的列
            df['GG1_Plate_ID'] = df['ASP'].apply(lambda x: x.replace('ASP', 'GG1_PLT_'))
            
            # 生成 Assembly_Well_ID 列
            df['GG1_Well_ID'] = None
            df = df.sort_values(by=['WF3_Mfg_ID'])
            for plate, group in df.groupby('GG1_Plate_ID'):
                num_wells = len(group)
                well_ids = generate_well_ids(num_wells)
                df.loc[group.index, 'GG1_Well_ID'] = well_ids

            # 生成 SPB_Well_Pos 列
            df['SPB_Well_Pos(in PrimerPlate)'] = df['SPB_DomainName'].apply(well_position)

            # 生成 gZip_Well_Pstn 列
            df['WF3_gZip1_WellPos'] = df['gZip_DomainName'].apply(well_position)

            # 筛选列
            Gene_Assembly_df = df[["WF3_Mfg_ID", "WF3_Synthon_GeneName", "ASP", "SPA_Primer", "SPB", "SPB_DomainName", 
                    "SPB_Well_Pos(in PrimerPlate)", "PostGG1_Forward_Primer", "gzip", "gZip_DomainName",	
                    "WF3_gZip1_WellPos", "RE_PCR_forMTP_Forward_Primer", "GG1_Plate_ID", "GG1_Well_ID"]]
            
            df = df[['WF3_Mfg_ID', 'WF3_gZip1_WellPos', "WF3_Synthon_GeneName", 'Dialout_PrimerName_For', 'Dialout_PrimerName_Rev', 
                     'Dialout_PrimerWellPos_For', 'Dialout_PrimerWellPos_Rev', 'WF3_PLT_ID', 'WF3_WellPos','WF3_FullSeqREAL_Credit']]
            # 这个Gene_Assembly_df 要返回前端去下载
            return df, Gene_Assembly_df, project_name
        except FileNotFoundError:
            raise BadRequest(f"File not found: {file}")
        except pd.errors.ParserError:
            raise BadRequest(f"Error parsing file: {file}")
        except KeyError as e:
            raise BadRequest(f"Missing expected column: {e.args[0]}")
        except Exception as e:
            raise BadRequest(f"Unexpected error processing file {file}: {str(e)}")

    ##########################
    # 从这里开始处理文件
    if file1 and file2:
        df5, WF5_Gene_Assembly_df, WF5_PRJ_name = process_5p30_file(file1)
        df3, WF3_Gene_Assembly_df, WF3_PRJ_name = process_3p30_file(file2)
        df_merge = pd.merge(df3, df5, left_on='WF3_Mfg_ID', right_on="FullSeqREAL_Credit", how='outer')
        df_merge = df_merge.sort_values(by=['WF3_Synthon_GeneName'])
        df_merge['Subplate'] = 'R' + (df_merge.groupby(['PRJIN_PLT_ID', 'PRJIN_WellPos']).cumcount() + 1).astype(str)
    elif file3:
        df_merge = pd.read_csv(file3, sep='\t')

        if 'GeneID' not in df_merge.columns:
            df_merge['GeneID'] = df_merge['MWF5_Mfg_ID'].apply(lambda x: x.split('][')[1].replace(']', '') if pd.notna(x) else None)

        if 'FullSeqREAL_Credit_Copy' not in df_merge.columns:
            df_merge['FullSeqREAL_Credit_Copy'] = df_merge.groupby('GeneID')['WF3_Mfg_ID'].transform(lambda x: ';'.join(x))

        if 'WF3_PLT_ID' not in df_merge.columns:
            df_merge[['WF3_PLT_ID', 'Subplate']] = df_merge['Dialout_PLT_ID'].str.rsplit('_', n=1, expand=True)

        if 'WF3_WellPos' not in df_merge.columns:
            df_merge['WF3_WellPos'] = df_merge['Dialout_WellPos']

        WF5_Gene_Assembly_df = pd.DataFrame()
        WF3_Gene_Assembly_df = pd.DataFrame()
        WF5_PRJ_name = "NO_FILE"
        WF3_PRJ_name = "NO_FILE"

    all_data = {'plates': {}, 'subplates': {}, 'missing_data': {}, 'extra_data': {}, 'ab_data': {}}
    ab_gene_dict = {}  # {'X303': {'X303-IGH': 'G0034', 'X303-IGL': 'G0035'}}
    for _, row in df_merge.iterrows():
        PRJIN_PLT_ID = row['PRJIN_PLT_ID']
        PRJIN_WellPos = row['PRJIN_WellPos']
        subplate = row['Subplate']
        WF3_Mfg_ID = row['WF3_Mfg_ID']
        WF3_WellPos = row['WF3_WellPos']
        WF3_PLT_ID = row['WF3_PLT_ID']
        FullSeqREAL_Credit_Copy = row['FullSeqREAL_Credit_Copy']

        # plate data
        if pd.notna(PRJIN_PLT_ID) and pd.notna(PRJIN_WellPos) and pd.notna(row['GeneID']):
            all_data['plates'].setdefault(PRJIN_PLT_ID, {'well_positions': {}})['well_positions'][PRJIN_WellPos] = {
                'gene_id': row['GeneID'],
                'hover_info': FullSeqREAL_Credit_Copy,
            }

        # subplate data
        if 'Dialout_PLT_ID' not in row:  # 说明是5p30文件
            if pd.notna(WF3_PLT_ID) and pd.notna(subplate) and pd.notna(PRJIN_WellPos) and pd.notna(WF3_Mfg_ID):
                all_data['subplates'].setdefault(PRJIN_PLT_ID, {}).setdefault(subplate, {})[PRJIN_WellPos] = WF3_Mfg_ID
        else:  # 说明是MTP文件
            all_data['subplates'].setdefault(WF3_PLT_ID, {}).setdefault(subplate, {})[row['Dialout_WellPos']] = WF3_Mfg_ID

        # extra data and Antibody data
        if 'Dialout_PLT_ID' not in row:
            if pd.isna(PRJIN_PLT_ID) and pd.notna(WF3_Mfg_ID):
                if row['WF3_Synthon_GeneName'].endswith(('-IGL', '-IGH')):
                    # 说明是抗体基因, 先把基因名存起来，后面再处理
                    gene_name = row['WF3_Synthon_GeneName'].split('-')[0]
                    ab_gene_dict.setdefault(gene_name, {})[row['WF3_Synthon_GeneName']] = WF3_Mfg_ID
                else:
                    # 说明是普通的基因
                    # 根据WF3 的plate 和WellPos 生成一个新的字典 : WF3_Plate: {WF3_WellPos: WF3_Mfg_ID}
                    all_data['extra_data'].setdefault(WF3_PLT_ID, {})[row['WF3_WellPos']] = WF3_Mfg_ID
        else:
            # 说明是MTPIN文件
            if pd.isna(PRJIN_PLT_ID) and pd.notna(WF3_Mfg_ID):
                # 判断是否被移动过,移动过就不是extra data，没有移动过就是extra data
                if '3p30' in  WF3_PLT_ID:
                    all_data['extra_data'].setdefault(WF3_PLT_ID, {})[WF3_WellPos] = WF3_Mfg_ID
                    

        # missing data
        if 'Rank1.MTP1.Primer.Pstn' in row and pd.isna(row['Rank1.MTP1.Primer.Pstn']):
            all_data['missing_data'].setdefault(row['WF3_PLT_ID'], {}).setdefault(subplate, []).append(row['Dialout_WellPos'])
    
    # 重新处理antibody data的排版问题，按照顺序排版
    def generate_well_ids(num_wells):
        rows = 'ABCDEFGHIJKLMNOP'
        cols = range(1, 25)
        well_ids = [f'{row}{col}' for col in cols for row in rows]
        return well_ids[:num_wells]
    
    # 按照顺序排列到384孔板中，并写入到all_data中
    well_position = generate_well_ids(384)
    well_index = 0
    plate_number = 1

    for gene_name, gene_dict in ab_gene_dict.items():
        if len(gene_dict) == 2:
            IGL_gene_id = gene_dict.get(f'{gene_name}-IGL')
            IGH_gene_id = gene_dict.get(f'{gene_name}-IGH')
            plate_name = f'AB_Plate_{plate_number}'

            # # 检查是否有足够的孔位来存放两个基因
            if well_index >= len(well_position) - 1:
                # 切换到下一块板
                plate_number += 1
                well_index = 0
                plate_name = f'AB_Plate_{plate_number}'
            
            # 获取当前的两个相邻孔位
            well_pos_IGL = well_position[well_index]
            well_pos_IGH = well_position[well_index + 1]

            # 写入到all_data中
            all_data['ab_data'].setdefault(plate_name, {})[well_pos_IGL] = IGL_gene_id
            all_data['ab_data'].setdefault(plate_name, {})[well_pos_IGH] = IGH_gene_id

            # 更新well_index
            well_index += 2

    # 最后再重新处理一下df_merge，将不需要的列删除
    _columns = ["WF3_Mfg_ID", "WF3_gZip1_WellPos", "WF3_FullSeqREAL_Credit", "GeneID", "WF3_Synthon_GeneName", "MWF5_Mfg_ID", 
                "PRJIN_PLT_ID", "PRJIN_WellPos", "Dialout_PLT_ID", "Dialout_WellPos", 
                "Dialout_PrimerName_For", "Dialout_PrimerName_Rev", "Dialout_PrimerWellPos_For", 
                "Dialout_PrimerWellPos_Rev", "Complete_final_gene", "Rank1.reads.errFree", 
                "Rank1.MTP1.Primer.Pstn", "Rank1.MTP4.Primer.Pstn", "Rank1.MTP2.Primer.Pstn", 
                "Rank1.MTP3.Primer.Pstn", "Rank2.reads.errFree", "Rank2.MTP2.Primer.Pstn", 
                "Rank2.MTP4.Primer.Pstn", "Rank2.MTP2.Primer.Pstn", "Rank2.MTP3.Primer.Pstn", 
                "Rank3.reads.errFree", "Rank3.MTP3.Primer.Pstn", "Rank3.MTP4.Primer.Pstn", 
                "Rank3.MTP3.Primer.Pstn", "Rank3.MTP3.Primer.Pstn"]
    
    for col in df_merge.columns:
        if col not in _columns:
            df_merge.drop(columns=[col], inplace=True)
    df_merge_json = df_merge.to_json(orient='records')
    # 保存数据到文件
    with open('media/temp/all_data.json', 'w') as f:
        json.dump(all_data, f, indent=4)

    # with open('media/temp/WF3_Gene_Assembly.json', 'w') as f:
    #     json.dump(WF3_Gene_Assembly, f, indent=4)

    # with open('media/temp/WF5_Gene_Assembly.json', 'w') as f:
    #     json.dump(WF5_Gene_Assembly, f, indent=4)

    return JsonResponse({
        'status': 'success', 'all_data': all_data, 
        'df_merge': df_merge_json, 
        'WF3_gene_assembly': WF3_Gene_Assembly_df.to_json(orient='records'), 
        'WF5_gene_assembly': WF5_Gene_Assembly_df.to_json(orient='records'),
        'WF5_PRJ_name': WF5_PRJ_name,
        'WF3_PRJ_name': WF3_PRJ_name
    })

@login_required
def SplitEnzymeSite(request):
    if request.method == 'GET':
        return render(request, 'tools/tools_SplitEnzymeSite.html')
    elif request.method == 'POST':
        enzyme_site_table = request.POST.get('tableData')
        sequence_file = request.FILES.get('file_name1')
        sequence_type = request.POST.get('sequenceType')
        circular = sequence_type == 'circular'

        # 内置酶信息
        enzymes_info = [
            {'Enzyme': 'BamHI', 'Site_NT': 'GGATCC', 'Cutting_Site_Left(bp)': 1, 'Cutting_Site_Right(bp)': 5},
            {'Enzyme': 'EcoRV', 'Site_NT': 'GATATC', 'Cutting_Site_Left(bp)': 3, 'Cutting_Site_Right(bp)': 3},
            {'Enzyme': 'PstI', 'Site_NT': 'CTGCAG', 'Cutting_Site_Left(bp)': 5, 'Cutting_Site_Right(bp)': 1},
            {'Enzyme': 'PvuII', 'Site_NT': 'CAGCTG', 'Cutting_Site_Left(bp)': 3, 'Cutting_Site_Right(bp)': 3}
        ]

        # 自定义酶处理
        enzyme_site_list = json.loads(enzyme_site_table)
        if all(all(cell is None for cell in row) for row in enzyme_site_list):
            enzyme_site_list = []
        if enzyme_site_list:
            for row in enzyme_site_list:
                if any(row):
                    enzyme_info = {
                        'Enzyme': row[0],
                        'Site_NT': row[1],
                        'Cutting_Site_Left(bp)': row[2],
                        'Cutting_Site_Right(bp)': row[3]
                    }
                    enzymes_info.append(enzyme_info)

        if not sequence_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'})

        if not os.path.exists('media/temp/'):
            os.makedirs('media/temp/')

        # 上传文件
        file_path = upload_file(sequence_file, 'media/temp/')
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                return JsonResponse({'status': 'error', 'message': 'Unsupported file format'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to read file: {str(e)}'})

        # 检查必要字段是否存在
        required_cols = {'Name', 'Sequence', 'Enzyme'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'status': 'error', 'message': f'File must contain columns: {required_cols}'})

        # ✅ 提前检查重复组合 (Name, Enzyme)
        dup_check = df[['Name', 'Enzyme']].duplicated(keep=False)

        # 如果有重复组合，返回错误信息
        if dup_check.any():
            dup_examples = df.loc[dup_check, ['Name', 'Enzyme']].drop_duplicates().head(5).to_dict(orient='records')
            return JsonResponse({
                'status': 'error',
                'message': 'Input file contains duplicate (Name, Enzyme) combinations. Please remove duplicates and try again.',
                'duplicates': dup_examples
            })

        # ✅ 无重复才处理分析
        def process_row(row):
            name = row['Name']
            dna_sequence = row['Sequence']
            enzyme_input = row['Enzyme'].split(';')
            results = find_enzyme_sites(dna_sequence, enzymes_info, enzyme_input, circular=circular)
            length_list = []
            for enzyme, sites in results.items():
                for site in sites:
                    _, length = site
                    length_list.append(length)
            return pd.Series({
                'Name': name,
                'Sequence': dna_sequence,
                'Enzyme': ';'.join(enzyme_input),
                'Results': json.dumps(results),
                'Cutting_Size': sorted(length_list, reverse=True)
            })

        processed_df = df.apply(process_row, axis=1)
        pivot_input_df = processed_df.copy()

        pivot_df = processed_df.pivot(index='Name', columns='Enzyme', values='Cutting_Size').reset_index()
        pivot_df.insert(1, 'Sequence', processed_df.drop_duplicates('Name')['Sequence'].values)

        # 创建ZIP
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            pivot_excel_buffer = BytesIO()
            with pd.ExcelWriter(pivot_excel_buffer, engine='xlsxwriter') as writer:
                pivot_df.to_excel(writer, index=False)
            zf.writestr('pivot_results.xlsx', pivot_excel_buffer.getvalue())

            processed_excel_buffer = BytesIO()
            with pd.ExcelWriter(processed_excel_buffer, engine='xlsxwriter') as writer:
                pivot_input_df.to_excel(writer, index=False)
            zf.writestr('processed_results.xlsx', processed_excel_buffer.getvalue())

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="results.zip"'
        return response

def Seq2AA(request):
    return render(request, 'tools/tools_Seq2AA.html')


def MiniGeneExtractor(request):
    if request.method == 'GET':
        if request.GET.get('download') == 'true':
            results_data = request.session.get('mini_gene_results')
            if not results_data:
                return HttpResponse("No results to download.", status=404)

            df = pd.DataFrame(results_data)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='MiniGeneResults')
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="mini_gene_results.xlsx"'
            return response
        return render(request, 'tools/tools_MiniGeneExtractor.html')

    elif request.method == 'POST':
        try:
            genome_version = request.POST.get('genomeVersion', 'hg38')
            input_type = request.POST.get('input_type')
            mutations = []

            if input_type == 'text':
                mutation_text = request.POST.get('mutation_text', '')
                mutations = [line.strip() for line in mutation_text.splitlines() if line.strip()]
                if not mutations:
                    return JsonResponse({'status': 'error', 'message': '文本输入框中没有提供突变信息。'}, status=400)

            elif input_type == 'file':
                mutation_file = request.FILES.get('mutation_file')
                if not mutation_file:
                    return JsonResponse({'status': 'error', 'message': '没有上传文件。'}, status=400)

                try:
                    if mutation_file.name.endswith('.csv'):
                        df = pd.read_csv(mutation_file)
                    elif mutation_file.name.endswith(('.xls', '.xlsx')):
                        df = pd.read_excel(mutation_file)
                    else:
                        return JsonResponse({'status': 'error', 'message': '不支持的文件格式，请上传 CSV 或 Excel 文件。'}, status=400)

                    if 'Mutation' not in df.columns:
                        return JsonResponse({'status': 'error', 'message': "文件中缺少 'Mutation' 列。"}, status=400)
                    
                    mutations = df['Mutation'].dropna().astype(str).tolist()
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'处理文件时出错: {str(e)}'}, status=400)

            else:
                return JsonResponse({'status': 'error', 'message': '无效的输入类型。'}, status=400)

            if not mutations:
                return JsonResponse({'status': 'error', 'message': '未找到有效的突变信息进行分析。'}, status=400)

            # =================================================================
            # 在这里调用你的脚本
            # 这是一个示例处理函数，你需要用你的实际脚本替换它
            # 它接收突变列表和基因组版本，并返回一个字典列表
            # =================================================================
            results_df = process_mutations_for_minigene(mutations, genome_version)
            # =================================================================

            # 将结果存储在会话中以便下载
            request.session['mini_gene_results'] = results_df.to_dict(orient='records')

            return JsonResponse({
                'status': 'success',
                'results_json': results_df.to_json(orient='records')
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'发生意外错误: {str(e)}'}, status=500)


def process_mutations_for_minigene(mutations, genome_version):
    """
    (占位符函数)
    处理突变列表以生成 mini-gene 片段。
    你需要用你自己的脚本逻辑替换这里的内容。

    :param mutations: 突变信息的列表 (例如 ['NM_000546.6:c.818G>T', ...])
    :param genome_version: 基因组版本 ('hg38' 或 'hg19')
    :return: 一个包含结果的 pandas DataFrame
    """
    # 示例输出。你的脚本应该生成类似这样的数据结构。
    # 这里的列名只是示例，你可以根据你的脚本输出进行修改。
    results_data = []
    for i, mutation in enumerate(mutations):
        results_data.append({
            'Input_Mutation': mutation,
            'Genome_Version': genome_version,
            'Gene_Symbol': f'GENE{i+1}',
            'Status': 'Success',
            'Mini_Gene_Sequence_29AA': f'SEQUENCE_{"A"*20}_{i}',
            'Error_Message': ''
        })

    # 如果某个突变处理失败，你可以这样记录：
    if len(mutations) > 1:
        results_data[1]['Status'] = 'Failed'
        results_data[1]['Mini_Gene_Sequence_29AA'] = ''
        results_data[1]['Error_Message'] = 'Invalid mutation format'

    return pd.DataFrame(results_data)


def test(request):
    return render(request, 'tools/test.html')

def test_analyze_sequence(request):
    from tools.scripts.AnalysisSequence import DNARepeatsFinder
    if request.method == 'POST':
        sequence = request.POST.get('sequence')
        print("sequence: ", sequence)
        
        if sequence:
            repeats_finder = DNARepeatsFinder(sequence=sequence)
            results = repeats_finder.find_high_gc_content(window_size=30, max_GC_content=80)
            print("results: ", results)
            return JsonResponse({'status': 'success', 'message': 'Sequence analyzed successfully', 'penalty_score': results})
        else:
            return JsonResponse({'status': 'error', 'message': 'No sequence provided'})
    return render(request, 'tools/test.html')
