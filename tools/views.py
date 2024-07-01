import base64
import io, os, re
import json
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import BadRequest
from django.shortcuts import redirect, render
from .models import Tool
from django.contrib.auth.decorators import login_required
from tools.scripts.AnalysisSequence import DNARepeatsFinder
import pandas as pd
from Bio import SeqIO

# Create your views here.

def tools_list(request):
    tools = Tool.objects.all()
    return render(request, 'tools/tools_list.html', {'tools': tools})

def safe_float_convert(x):
    try:
        return x.dropna().astype(float).sum()
    except ValueError:
        return 0  # 或其他适当的默认值，例如 np.nan 依情况而定
    
def expanded_rows_to_gene_table(df, gene_table):
    expanded_results = []

    for gene_id, row in df.iterrows():
        result_dict = {
            'gene_id': gene_id
        }
        
        for analysis_type, results_list in row.items():
            if results_list:
                # 假设每个结果都是一个字典，我们将使用扁平化处理
                for result in results_list:
                    for key, value in result.items():
                        column_name = f'{analysis_type}_{key}'
                        # 特殊处理 penalty_score 列，累加浮点数值
                        if 'penalty_score' in key:
                            if column_name in result_dict:
                                # 如果这是一个 penalty_score 列，我们将尝试将其转换为浮点数并将其添加到现有值上
                                try:
                                    result_dict[column_name] += float(value)
                                except ValueError:
                                    continue
                            else:
                                # 第一次遇到 penalty_score 列，我们将尝试将其转换为浮点数
                                try:
                                    result_dict[column_name] = float(value)
                                except ValueError:
                                    continue
                        # 特殊处理 seqType 列，只取第一个值
                        elif 'seqType' in key:
                            if column_name not in result_dict:
                                result_dict[column_name] = value
                        # 其他列使用字符串连接
                        else:
                            # 对于其他列，我们将使用字符串连接
                            if column_name in result_dict:
                                result_dict[column_name] += f';{value}'
                            else:
                                result_dict[column_name] = str(value)
            else:
                continue
            
        expanded_results.append(result_dict)

    expanded_df = pd.DataFrame(expanded_results)

    # merge gene_table and updated_df
    gene_table = gene_table.merge(expanded_df, on='gene_id', how='left')

    return gene_table


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
        if 'fastaFile' in request.FILES:
            fasta_file = request.FILES['fastaFile']
            gene_table = process_fasta_file(fasta_file)
        else:
            data = json.loads(request.body.decode('utf-8'))
            gene_table = data.get("genetable")
            if not gene_table:
                return JsonResponse({'status': 'error', 'message': 'No gene data provided'})
            gene_table = pd.DataFrame(gene_table, columns=['gene_id', 'sequence']).dropna().reset_index(drop=True)

        long_repeats_min_len = int(request.POST.get('longRepeatsMinLen', 16))
        homopolymers_min_len = int(request.POST.get('homopolymersMinLen', 7))
        min_w_length = int(request.POST.get('minWLength', 12))
        min_s_length = int(request.POST.get('minSLength', 12))
        window_size = int(request.POST.get('windowSize', 30))
        min_gc_content = int(request.POST.get('minGCContent', 20))
        max_gc_content = int(request.POST.get('maxGCContent', 80))

        finder_dataset = DNARepeatsFinder(data_set=gene_table)
        results = {}
        for index, row in gene_table.iterrows():
            gene_id = row['gene_id']
            results[gene_id] = {
                'long_repeats': finder_dataset.find_dispersed_repeats(index=index, min_len=long_repeats_min_len),
                'homopolymers': finder_dataset.find_homopolymers(index=index, min_len=homopolymers_min_len),
                'W8S8_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=min_w_length, min_S_length=min_s_length),
                'local_gc_content': finder_dataset.find_local_gc_content(index=index, window_size=window_size, min_GC_content=min_gc_content, max_GC_content=max_gc_content),
            }
        df = pd.DataFrame(results).T

        gene_table = expanded_rows_to_gene_table(df, gene_table)
        gene_table['total_penalty_score'] = gene_table.apply(lambda row: row.filter(like='penalty_score').sum(), axis=1)

        request.session['gene_table'] = gene_table.to_dict(orient='records')
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
    green_count = sum(1 for gene in gene_table if gene['total_penalty_score'] < 10)
    yellow_count = sum(1 for gene in gene_table if 10 <= gene['total_penalty_score'] < 30)
    red_count = sum(1 for gene in gene_table if gene['total_penalty_score'] >= 30)

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
            df['Subplate'] = 'R' + (df.groupby(['PRJIN_PLT_ID', 'PRJIN_WellPos']).cumcount() + 1).astype(str)
            df = df[['MWF5_Mfg_ID', 'PRJIN_PLT_ID', 'PRJIN_WellPos', 'FullSeqREAL_Credit', 
                     'GeneID', 'FullSeqREAL_Credit_Copy', 'Subplate']]
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
                'WellPos': 'WF3_WellPos'
            })
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
                     'Dialout_PrimerWellPos_For', 'Dialout_PrimerWellPos_Rev', 'WF3_PLT_ID', 'WF3_WellPos']]
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
    _columns = ["WF3_Mfg_ID", "WF3_gZip1_WellPos", "GeneID", "WF3_Synthon_GeneName", "MWF5_Mfg_ID", 
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


def test(request):
    return render(request, 'tools/test.html')