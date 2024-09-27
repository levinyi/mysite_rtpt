import itertools
import json, re, os
import tempfile
import zipfile
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from product.models import GeneSynEnzymeCutSite, Species, Vector
from tools.scripts.AnalysisSequence import DNARepeatsFinder
from tools.scripts.ParsingGenBank import addFeaturesToGeneBank
from .models import Cart, GeneInfo, GeneOptimization, OrderInfo
from .utils.render_to_pdf import render_to_pdf
from urllib.parse import quote

# Create your views here.
@login_required(login_url='/account/login/')
def dashboard(request):
    # 如果没有shopping cart，创建一个
    production_order = OrderInfo.objects.filter(user=request.user, status='Created')
    shipping_order = OrderInfo.objects.filter(user=request.user, status='Shipping')
    shopping_cart = Cart.genes.through.objects.filter(cart__user=request.user)
    return render(request, 'user_center/dashboard.html', {
            'order_number_in_production': len(production_order),
            'order_number_in_shipment': len(shipping_order),
            'gene_number_in_cart': len(shopping_cart),
            })

# Step 1 create an order.
@login_required
def order_create(request):
    '''创建订单页'''
    if request.method == 'POST':
        # Parse JSON data from request
        data = json.loads(request.body.decode('utf-8'))
        vector_id = data.get("vectorId")
        gene_table = data.get("genetable")

        # 将 gene_table 转换为 DataFrame，并删除空行，重置索引，如果为空则返回错误信息
        df = pd.DataFrame(gene_table)
        df = df.dropna().reset_index(drop=True)
        if df.empty:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})
        
        # validate Vector ID
        try:
            vector = Vector.objects.get(id=vector_id)
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid vector ID'})
        
        # check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Please login first.'})
        
        # Get or create a shopping cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)

        response_message = ""
        new_gene_ids_for_session = []  # 用于存储新创建的基因的id, 用于session

        # 处理基因表格，根据列数判断是AA序列还是NT序列，NT序列只有两列，AA序列有6列
        if len(df.columns) == 2:
            print("Processing NT sequence")

            df.columns = ['GeneName', 'OriginalSeq']  # 重命名列名，方便后续处理
            # 去掉换行符和空格
            df['OriginalSeq'] = df['OriginalSeq'].str.replace("\n","").str.replace("\r","").str.replace(" ","").str.replace("\t", '')  # 去掉换行符和空格

            df['CombinedSeq'] = df.apply(lambda row: f'{vector.iu20.lower()}{row["OriginalSeq"]}{vector.id20.lower()}', axis=1)
            # 清理序列并检查是否包含非法碱基
            df['CombinedSeq'], df['warnings'] = zip(*df['CombinedSeq'].apply(clean_and_check_dna_sequence))

            # 计算GC含量, 将序列转换为大写后计算GC含量
            df['original_gc_content'] = df['OriginalSeq'].apply(lambda x: round((x.upper().count('G') + x.upper().count('C')) / len(x) * 100, 2))
            df['modified_gc_content'] = df['CombinedSeq'].apply(lambda x: round((x.upper().count('G') + x.upper().count('C')) / len(x) * 100, 2))

            # Repeats Finder. sequence 和 gene_id 是查找repeats时必须的字段, 给这两列重新赋值，不需要重命名。
            df['gene_id'] = df['GeneName']
            df['sequence'] = df['CombinedSeq']
            df = convert_gene_table_to_RepeatsFinder_Format(df)
            df['analysis_results'] = df.apply(lambda row: penalty_column_to_dict(row), axis=1)

            # Forbidden Check : 检测序列中是否包含禁止序列，有则记录其起始和终止位置和序列,
            # 从酶切位点数据库中获取禁止序列，每个禁止序列都有一个适用范围，即起始和终止位置
            # 然后应用到每个基因序列中，如果基因序列中包含禁止序列，则记录其起始和终止位置
            forbidden_list_objects = GeneSynEnzymeCutSite.objects.all()
            built_in_forbidden_list = [obj.enzyme_seq for obj in forbidden_list_objects]

            df['forbidden_info'] = df.apply(
                lambda row: check_forbidden_seq(row['CombinedSeq'], built_in_forbidden_list),
                axis=1
            )

            # 密码子检查，检查序列内部是否有终止密码子
            df['stop_codons'] = df['CombinedSeq'].apply(detect_stop_codons)

            # 检查forbidden 修改status
            df['status'] = df.apply(
                lambda row: 'forbidden' if row['forbidden_info'] or row['warnings'] or row['stop_codons'] else 'validated', 
                axis=1
            )

            # 整合,把forbidden seq，warnings，stop codons的content加到 FoundForbiddenSequence中，在header中展示。
            df['contained_forbidden_list'] = df.apply(process_contained_forbidden_list, axis=1)

            # 整合：把forbidden_seq, warnings, stop codons的位置信息加到highlights_positions中，用于前端展示
            df['highlights_positions'] = df.apply(
                lambda row: process_highlights_positions(row),
                axis=1
            )

            # 最后把CombinedSeq赋值给saved_seq
            df['saved_seq'] = df['CombinedSeq']  # 有必要写到这里吗？
            # 将 DataFrame 转换为 GeneInfo 对象
            gene_objects = [
                GeneInfo(
                    user=request.user,
                    gene_name=row['gene_id'],
                    original_seq=row['OriginalSeq'],
                    vector=vector,
                    species=row.get('species', None),
                    status=row.get('status', 'validated'),  # check if status is valid 
                    forbid_seq=row.get('forbidden_check_list', ''),
                    combined_seq=row['CombinedSeq'],
                    i5nc=row.get('i5nc', ''),
                    i3nc=row.get('i3nc', ''),
                    saved_seq=row.get('saved_seq', ''),
                    forbidden_check_list=row.get('forbidden_check_list', ''),
                    contained_forbidden_list=row.get('contained_forbidden_list', ''),
                    original_gc_content=row.get('original_gc_content', ''),
                    modified_gc_content=row.get('modified_gc_content', ''),
                    original_highlights=row.get('highlights_positions', []),
                    modified_highlights=row.get('highlights_positions', []),
                    penalty_score=row.get('total_penalty_score', None),
                    analysis_results=row['analysis_results'],
                )
                for _, row in df.iterrows()
            ]
            # Capture the current timestamp
            current_timestamp = timezone.now()

            with transaction.atomic():
                # Bulk create gene objects without immediately assigning them to a variable with IDs
                GeneInfo.objects.bulk_create(gene_objects)

                # Retrieve the gene objects from the database with their IDs
                gene_objects_with_ids = GeneInfo.objects.filter(
                    user=request.user, 
                    gene_name__in=df['gene_id'], 
                    create_date__gte=current_timestamp
                )

            # Add the gene objects to the cart's genes many-to-many relationship
            cart.genes.add(*gene_objects_with_ids)
            print("gene_objects_with_ids", gene_objects_with_ids)

            # Extend the new_gene_ids_for_session with the IDs of the retrieved objects
            new_gene_ids_for_session.extend([gene.id for gene in gene_objects_with_ids])
            print("new_gene_ids_for_session", new_gene_ids_for_session)
        else:
            print("Processing AA sequence")

            df.columns = ['GeneName', 'OriginalSeq', 'Species', 'ForbiddenSeqs', 'i5nc', 'i3nc']  # 重命名列名，方便后续处理
            # df['OriginalSeq'] = df['OriginalSeq'].str.replace("\n","").str.replace("\r","").str.replace(" ","")  # 去掉换行符和空格
            df['OriginalSeq'], df['warnings'] = zip(*df['protein_sequence'].apply(clean_and_check_protein_sequence))
    
            # 暂时不处理AA序列
            pass

        # Store the new gene IDs in the session for later use
        request.session['new_gene_ids'] = new_gene_ids_for_session

        if response_message:
            return JsonResponse({'status': 'info', 'message': response_message})
        else:
            return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
    else:
        company_vectors = Vector.objects.filter(user=None)
        species_list = Species.objects.all()
        # 假设 species_list 是您的物种模型列表
        species_names = [species.species_name for species in species_list]

        # 然后将这个列表转换为 JSON, 用于前端Handsontable中展示物种列表
        species_names_json = json.dumps(species_names)
        customer_vectors = Vector.objects.filter(user=request.user, status="ReadyToUse")
        return render(request, 'user_center/manage_order_create.html', {'customer_vectors': customer_vectors, 'company_vectors': company_vectors, 'species_names_json': species_names_json})

# 定义遗传密码表，将密码子翻译为氨基酸
codon_table = {
    'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M',
    'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
    'AAC':'N', 'AAT':'N', 'AAA':'K', 'AAG':'K',
    'AGC':'S', 'AGT':'S', 'AGA':'R', 'AGG':'R',                 
    'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L',
    'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
    'CAC':'H', 'CAT':'H', 'CAA':'Q', 'CAG':'Q',
    'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
    'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V',
    'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
    'GAC':'D', 'GAT':'D', 'GAA':'E', 'GAG':'E',
    'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
    'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S',
    'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
    'TAC':'Y', 'TAT':'Y', 'TAA':'*', 'TAG':'*',
    'TGC':'C', 'TGT':'C', 'TGA':'*', 'TGG':'W',
}

def detect_stop_codons(dna_sequence, offset=20):
    dna_sequence = dna_sequence[offset:-offset]  # 去掉前后20bp
    stop_codon_info = []
    # 将DNA序列按三个碱基分割为密码子
    codons = [dna_sequence[i:i+3] for i in range(0, len(dna_sequence), 3)]
    
    # 遍历除了最后一个密码子的所有密码子
    for idx, codon in enumerate(codons[:-1]):  # 最后一个密码子不包括
        amino_acid = codon_table.get(codon, '?')  # 翻译密码子为氨基酸
        if amino_acid == '*':  # 终止密码子
            start = idx * 3
            end = start + 3
            content = codon
            stop_codon_info.append({'start': start +offset, 'end': end + offset, 'content': content})
    
    return stop_codon_info

def clean_and_check_dna_sequence(sequence):
    # 1. 删除空格、换行符等无关字符
    cleaned_sequence = sequence.replace(' ', '').replace('\n', '').replace('\t', '')
    
    # 2. 查找所有连续的非ATCG片段，并记录它们的起始和结束位置及内容
    non_dna_bases_info = []
    
    # 使用正则表达式匹配连续的非ATCG字符
    for match in re.finditer(r'[^ATCGatcg]+', cleaned_sequence):
        start = match.start()
        end = match.end()
        content = match.group()
        non_dna_bases_info.append({'start': start, 'end': end, 'content': content})
    
    # 3. 返回处理后的序列以及非法碱基的提醒信息（包含位置信息）
    if non_dna_bases_info:
        # warnings = [f'start: {item['start']}, end: {item['end']}, content: {item['content']}' for item in non_dna_bases_info]
        warnings = [{'start': item['start'], 'end': item['end'], 'content': item['content']} for item in non_dna_bases_info]
        return cleaned_sequence, warnings
    
    return cleaned_sequence, None


def clean_and_check_protein_sequence(sequence):    
    # 1. 删除空格、换行符等无关字符
    cleaned_sequence = sequence.replace(' ', '').replace('\n', '').replace('\t', '')
    
    # 2. 检查最后一个字符是否为星号（终止密码子），如果是，保留它
    if cleaned_sequence.endswith('*'):
        sequence_to_check = cleaned_sequence[:-1]  # 处理除去最后一个星号的部分
        has_terminal_stop = True
    else:
        sequence_to_check = cleaned_sequence
        has_terminal_stop = False
    
    # 3. 查找所有连续的非标准氨基酸字符，并记录它们的起始和结束位置及内容
    non_standard_amino_acids_info = []
    
    # 使用正则表达式匹配连续的非标准氨基酸字符
    for match in re.finditer(r'[^ACDEFGHIKLMNPQRSTVWY]+', sequence_to_check):
        start = match.start()
        end = match.end() - 1  # 结束位置需要减1，因为是闭区间
        content = match.group()
        non_standard_amino_acids_info.append({'start': start, 'end': end, 'content': content})
    
    # 4. 返回处理后的序列以及非法氨基酸的提醒信息（包含位置信息）
    if non_standard_amino_acids_info:
        warnings = f"警告: 发现非法氨基酸片段 {', '.join([f'start: {item['start']}, end: {item['end']}, content: {item['content']}' for item in non_standard_amino_acids_info])}"
        return cleaned_sequence if has_terminal_stop else cleaned_sequence, warnings
    
    # 如果有终止密码子，添加它到处理后的序列
    return cleaned_sequence if has_terminal_stop else cleaned_sequence, None


def process_contained_forbidden_list(row):
    # 获取 forbidden_info 中的 forbidden_seq 列表
    forbidden_seqs = [info['forbidden_seq'] for info in row['forbidden_info']] if row['forbidden_info'] else []

    # 获取 warnings，如果存在的话
    warning_seqs = [each['content'] for each in row['warnings'] if 'content' in each] if row['warnings'] else []
    # warning_seqs = [each['content'] for each in (row['warnings'] or []) if 'content' in each]

    # 获取密码子检查中的终止密码子，如果存在的话
    stop_codons = [each['content'] for each in row['stop_codons']]

    # 合并 forbidden_seqs 和 warning_seqs
    contained_forbidden_list = forbidden_seqs + warning_seqs + stop_codons

    return contained_forbidden_list

def penalty_column_to_dict(row):
    '''将 row 中的所有列直接转换为字典'''
    row_dict = row.to_dict()
    # 确保字典中的所有值都是 JSON 兼容的
    row_dict_cleaned = {key: (value if pd.notna(value) else '') for key, value in row_dict.items()}
    return row_dict_cleaned


def process_highlights_positions(row):
    '''处理高亮位置'''
    highlights_positions = []

    # Define a regex pattern to extract all numeric values from a string
    pattern = r'\d+'

    # Iterate over all analysis types to process start and end positions
    for analysis_type in ['LongRepeats', 'Homopolymers', 'W12S12Motifs', 'highGC', 'lowGC', 'doubleNT']:
        if row[f'{analysis_type}_start'] and row[f'{analysis_type}_end']:
            # Use regex to find all numbers in the string and convert them to integers
            start_results = list(map(int, re.findall(pattern, str(row[f'{analysis_type}_start']))))
            end_results = list(map(int, re.findall(pattern, str(row[f'{analysis_type}_end']))))

            # Ensure start and end lists are of the same length
            if len(start_results) != len(end_results):
                continue  # Skip this row or handle the inconsistency as needed

            # Iterate over the extracted positions and add them to highlights_positions
            for index in range(len(start_results)):
                highlights_positions.append({
                    'start': start_results[index],
                    'end': end_results[index],
                    'type': 'text-warning',
                })

    # If there is forbidden information, process and add it to highlights_positions
    if row['forbidden_info']:
        for info in row['forbidden_info']:
            highlights_positions.append({
                'start': info['start'],
                'end': info['end'],
                'type': 'bg-danger',
            })
    
    if row['warnings']:
        for warning in row['warnings']:
            highlights_positions.append({
                'start': warning['start'],
                'end': warning['end'],
                'type': 'bg-danger',
            })

    if row['stop_codons']:
        for stop_codon in row['stop_codons']:
            highlights_positions.append({
                'start': stop_codon['start'],
                'end': stop_codon['end'],
                'type': 'bg-danger',
            })

    return highlights_positions


def process_forbidden_seq(row):
    '''处理禁止序列'''
    forbidden_seq = row['forbidden_check_list']
    if forbidden_seq:
        forbidden_seq = forbidden_seq.replace(" ", "").replace(",", ";")
        forbidden_seq = forbidden_seq.split(";")
        forbidden_seq_positions = []
        for seq in forbidden_seq:
            start = row['sequence'].find(seq)
            end = start + len(seq)
            if start != -1:
                forbidden_seq_positions.append({
                    'start': start,
                    'end': end,
                    'seq': seq,
                    'type': 'bg-danger',
                })
        if forbidden_seq_positions:
            row['forbidden_check_list_start'] = forbidden_seq_positions[0]['start']
            row['forbidden_check_list_end'] = forbidden_seq_positions[-1]['end']
        else:
            row['forbidden_check_list_start'] = None
            row['forbidden_check_list_end'] = None
    else:
        row['forbidden_check_list_start'] = None
        row['forbidden_check_list_end'] = None
    return row


def convert_gene_table_to_RepeatsFinder_Format(gene_table):
    def expanded_rows_to_gene_table(df, gene_table):
        expanded_results = []
        all_columns = set()
        gene_analysis_types = []

        # 首先收集所有可能的列名
        for _, row in df.iterrows():
            for analysis_type, results_list in row.items():
                if analysis_type not in gene_analysis_types:
                    gene_analysis_types.append(analysis_type)
                if results_list:
                    for result in results_list:
                        for key, value in result.items():
                            column_name = f'{analysis_type}_{key}'
                            all_columns.add(column_name)

        # 按照检测类型和键的字母顺序排序列名
        gene_analysis_types = list(set(gene_analysis_types))  # 去除重复项
        sorted_columns = ['gene_id'] + sorted(all_columns, key=lambda x: (gene_analysis_types.index(x.split('_')[0]), x.split('_')[1]))

        # 初始化每个 result_dict，并确保所有可能的列名都在字典中
        for gene_id, row in df.iterrows():
            result_dict = {col: '' for col in sorted_columns}
            result_dict['gene_id'] = gene_id
            
            for analysis_type, results_list in row.items():
                if results_list:
                    for result in results_list:
                        for key, value in result.items():
                            column_name = f'{analysis_type}_{key}'
                            if 'penalty_score' in key:
                                if value == '':
                                    continue  # 跳过空值
                                if result_dict[column_name] != '':
                                    try:
                                        result_dict[column_name] += float(value)
                                    except ValueError:
                                        print(f'Error: {value} is not a valid float')
                                else:
                                    try:
                                        result_dict[column_name] = float(value)
                                    except ValueError:
                                        print(f'Error: {value} is not a valid float')
                            elif 'seqType' in key:
                                if value == '':
                                    continue
                                result_dict[column_name] = value
                            else:
                                if result_dict[column_name] != '':
                                    result_dict[column_name] += f';{value}'
                                else:
                                    result_dict[column_name] = str(value)
                else:
                    continue
                
            expanded_results.append(result_dict)

        expanded_df = pd.DataFrame(expanded_results)
        # 将所有带有penalty_score的列，求和赋值给total_penalty_score列
        penalty_columns = [col for col in expanded_df.columns if 'penalty_score' in col]
        expanded_df[penalty_columns] = expanded_df[penalty_columns].apply(pd.to_numeric, errors='coerce')
        expanded_df['total_penalty_score'] = expanded_df[penalty_columns].fillna(0).sum(axis=1).round(0).astype(int)

        gene_table = gene_table.merge(expanded_df, on='gene_id', how='left')

        return gene_table
    # Remove rows with None
    finder_dataset = DNARepeatsFinder(data_set=gene_table)

    results = {}
    for index, row in gene_table.iterrows():
        gene_id = row['gene_id']
        results[gene_id] = {
            # 'tandem_repeats': finder_dataset.find_tandem_repeats(index=index, min_unit=3, min_copies=3),
            'LongRepeats': finder_dataset.find_dispersed_repeats(index=index, min_len=16),
            # 'palindromes': finder_dataset.find_palindrome_repeats(index=index, min_len=15),
            # # 'inverted_repeats': finder_dataset.find_inverted_repeats(index=index, min_len=10),
            'Homopolymers': finder_dataset.find_homopolymers(index=index, min_len=7),
            'W12S12Motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=12, min_S_length=12),
            'highGC': finder_dataset.find_high_gc_content(index=index, window_size=30, max_GC_content=80),
            'lowGC': finder_dataset.find_low_gc_content(index=index, window_size=30, min_GC_content=20),
            'LCC': finder_dataset.get_lcc(index=index),
            'doubleNT': finder_dataset.find_dinucleotide_repeats(index=index, threshold=10),
        }
    #将结果列表转换为DataFrame， 处理长度不一致问题
    df = pd.DataFrame(results).T
    
    gene_table = expanded_rows_to_gene_table(df, gene_table)

    return gene_table

# checked
def submit_notification(request):
    ''' when user submit AA sequence. this function will be called.'''
    if request.method == 'GET':
        return render(request, 'user_center/aa_sequence_submit_success.html')
    else:
        return render(request, 'user_center/aa_sequence_submit_success.html')


@login_required
def gene_detail(request):
    ''' when user click the "submit & analysis" button, this function will be called.'''
    # 从session中获取新创建的基因
    new_gene_ids = request.session.get('new_gene_ids', [])

    if not new_gene_ids:
        # 如果没有新创建的基因ID，从数据库中筛选符合条件的基因
        gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')
    else:
        # 如果有新创建的基因ID，从数据库中获取这些基因
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=new_gene_ids)

    # 获取所有物种的名称
    species_list = Species.objects.all()
    species_names = sorted([species.species_name for species in species_list])
    
    return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})

@login_required
def bulk_view_gene_detail(request):
    ''' 批量查看基因详情 '''
    try:
        gene_ids = request.POST.getlist('gene_ids')
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)
        
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)
        species_list = Species.objects.all()
        species_names = sorted([species.species_name for species in species_list])
        return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def gene_data_api(request):
    '''返回基因数据的json格式, 用于本地服务器的数据请求'''
    gene_ids = request.session.get('new_gene_ids', [])
    if not gene_ids:
        gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')
    else:
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)

    data = gene_list.values('id', 'gene_name', 'original_seq', 'status', 'forbid_seq', 'vector__vector_id','modified_gc_content')
    return JsonResponse({'data': list(data)}, safe=False)
        

@login_required
def save_species(request):
    data = json.loads(request.body.decode('utf-8'))
    species = data['species']
    gene_id = data['gene_id']
    this_gene = GeneInfo.objects.get(user=request.user, id=gene_id)
    this_gene.species = Species.objects.get(species_name=species)
    this_gene.save()
    return JsonResponse({'status': 'success', 'message': 'Species saved successfully'})

@login_required
def gene_edit(request, gene_id):
    ''' when user click the "Edit" button, this function will be called.'''
    if request.method == 'POST':
        gene_object = GeneInfo.objects.get(user=request.user, id=gene_id)
        gene_object.status = "validated"
        gene_object.save()
        return JsonResponse({'status': 'success', 'message': 'Gene saved successfully'})
    else:
        gene_object = GeneInfo.objects.get(user=request.user, id=gene_id)
        # 将单个对象封装成列表
        gene_list = [gene_object]
        species_list = Species.objects.all()
        species_names = sorted([species.species_name for species in species_list])
        return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})

@login_required
def protein_edit(request, gene_id):
    gene_list = GeneInfo.objects.filter(user=request.user, status__in=['optimizing', 'optimized', 'failed'])
    return render(request, 'user_center/protein_detail.html', {'gene_list': gene_list})


def handle_gene_saving(gene_object, edited_seq):
    """
    用于基因序列验证和保存的统一函数
    """
    original_seq = gene_object.original_seq
    if original_seq == edited_seq:
        if gene_object.status == 'validated':
            gene_object.status = 'saved'
            gene_object.save()
            return True
        else:
            return False

    tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, \
        modified_gc_content, modified_highlights = process_sequence_get_highlight_position(edited_seq, gene_object.forbid_seq)
    
    gene_object.saved_seq = tagged_seq
    gene_object.forbidden_check_list = forbidden_check_list
    gene_object.contained_forbidden_list = contained_forbidden_list
    gene_object.combined_seq = edited_seq
    gene_object.modified_highlights = modified_highlights
    gene_object.modified_gc_content = modified_gc_content

    if seq_status == 'validated':
        gene_object.status = 'saved'
        gene_object.save()
        return True
    else:
        gene_object.status = seq_status
        gene_object.save()
        return False
    
@login_required
def gene_validation(request):
    ''' when user click the "Re-analyze" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        edited_seq = data.get("sequence") # 换个变量名，好区分
        gene_id = data.get("gene_id")  # 应该换成gene_id，

        gene_object = GeneInfo.objects.get(user=user, id=gene_id)
        combined_seq = gene_object.combined_seq     # 不带格式有小写 {iu20}.lower() + seq + {id20}.lower(), 可以直接比较

        if combined_seq == edited_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})

        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, \
            modified_gc_content, modified_highlights = process_sequence_get_highlight_position(edited_seq, gene_object.forbid_seq)

        if seq_status in ['Protein', 'Invalid Protein']:
            return JsonResponse({'status': 'error', 'message': 'Squence is not allowed. Your sequence may has '+ seq_status + ' sequence.'})
        gene_object.status = seq_status
        gene_object.saved_seq = tagged_seq
        gene_object.forbidden_check_list = forbidden_check_list
        gene_object.contained_forbidden_list = contained_forbidden_list
        gene_object.combined_seq = edited_seq
        gene_object.modified_highlights = modified_highlights
        gene_object.modified_gc_content = modified_gc_content
        gene_object.save()
        return JsonResponse({'status': 'success', 'message': 'Validation process finished', 'new_seq': tagged_seq, 'seq_status': seq_status})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def validation_save(request, id):
    ''' when user click the "Save" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        edited_seq = data.get("sequence")
        gene_object = GeneInfo.objects.get(user=user, id=id)

        if handle_gene_saving(gene_object, edited_seq):
            return JsonResponse({'status': 'success', 'message': 'Gene saved successfully', 'new_seq': gene_object.saved_seq})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please check your sequence and analysis first.'})
    except GeneInfo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Gene not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def bulk_optimization_submit(request):
    '''批量优化基因页面'''
    if request.method == 'POST':
        # 从请求中获取基因ID列表和物种
        gene_ids = request.POST.get('selected_genes').split(',')
        print("gene_ids", gene_ids)
        species_selected = request.POST.get('species_select')
        print("species_selected", species_selected)

        # 遍历基因ID列表并创建GeneOptimization记录
        for gene_id in gene_ids:
            try:
                gene_info = GeneInfo.objects.get(id=gene_id)
                # 创建GeneOptimization实例
                GeneOptimization.objects.create(
                    gene=gene_info,
                    user=request.user,
                    vector=gene_info.vector,
                    species=Species.objects.get(species_name=species_selected),
                )
            except GeneInfo.DoesNotExist:
                print(f"GeneInfo with id {gene_id} does not exist.")
            except Species.DoesNotExist:
                print(f"Species with name {species_selected} does not exist.")
        
        # 提交后重定向到展示页面
        return redirect('user_center:bulk_optimization_display')  # 替换为你的展示页面的URL名称


@login_required
def bulk_optimization_display(request):
    # 从模型中获取数据
    gene_list = GeneOptimization.objects.filter(user=request.user)

    return render(request, 'user_center/bulk_optimization.html', {'gene_list': gene_list})


###################### 以下是shopping cart 管理的函数 ############################
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    shopping_cart = cart.genes.all()

    grouped_shopping_cart = []
    for key, group in itertools.groupby(
        shopping_cart, 
        key=lambda x: timezone.localtime(x.create_date).strftime('%Y-%m-%d %H:%M')
        ):
        grouped_shopping_cart.append({
            'date': key,
            'genes': list(group)
        })
    context = {
        'grouped_shopping_cart': grouped_shopping_cart,
    }
    return render(request, 'user_center/shoppingCart_view.html', context)

# checked
@login_required
def gene_delete(request):
    '''从shopping cart中删除gene'''
    if request.method == 'POST':
        gene_ids = request.POST.getlist('gene_ids[]')  # Use getlist to retrieve multiple values
        if gene_ids:
            # Batch deletion
            GeneInfo.objects.filter(user=request.user, id__in=gene_ids).delete()
            return JsonResponse({'status': 'success', 'message': 'Genes deleted successfully'})
        else:
            # Single deletion
            gene_id = request.POST.get('gene_id')
            gene = GeneInfo.objects.get(user=request.user, id=gene_id)
            gene.delete()
            return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_order_create.html')


@login_required
def cart_genbank_download(request, gene_id):
    '''下载购物车中的基因的genbank文件'''
    gene = GeneInfo.objects.get(user=request.user, id=gene_id)
    sequence = re.sub(r'<[^>]*>', '', gene.saved_seq)
    # 删除序列前后的小写字母
    sequence = re.sub(r'^[a-z]+|[a-z]+$', '', sequence)

    vector = gene.vector
    if vector.vector_gb:
        vector_genbank_file_path = vector.vector_gb.path  # Get the file path
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=False) as temp_file:
            # addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name)  # old
            addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name, 'iU20', 'iD20', gene)
            
            temp_file.seek(0)
            response = HttpResponse(temp_file.read(), content_type='application/genbank')
            response['Content-Disposition'] = f'attachment; filename="RootPath-{vector.vector_name}-{gene.gene_name}-{gene.status}.gb"'
            return response
    else:
        return HttpResponse("No vector genbank file found")

@require_POST
@login_required
def bulk_download_genbank(request):
    '''批量下载购物车中的基因的genbank文件'''
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        temp_zip = tempfile.NamedTemporaryFile(delete=False)
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            for gene_id in gene_ids:
                try:
                    gene = GeneInfo.objects.get(user=request.user, id=gene_id)
                    sequence = re.sub(r'<[^>]*>', '', gene.saved_seq)
                    sequence = re.sub(r'^[a-z]+|[a-z]+$', '', sequence)
                    vector = gene.vector
                    if vector.vector_gb:
                        vector_genbank_file_path = vector.vector_gb.path
                        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=False) as temp_file:
                            # addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name)
                            addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name, 'iU20', 'iD20', gene)
                            temp_file.seek(0)
                            genbank_content = temp_file.read()
                            genbank_filename = f"RootPath-{vector.vector_name}-{gene.gene_name}-{gene.status}.gb"
                            zf.writestr(genbank_filename, genbank_content)
                    else:
                        zf.writestr(f"Error-{gene_id}.txt", "No vector GenBank file found")
                except GeneInfo.DoesNotExist:
                    zf.writestr(f"Error-{gene_id}.txt", "Gene not found")

        temp_zip.seek(0)
        response = HttpResponse(temp_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="RootPath-Online-Submission.zip"'
        temp_zip.close()
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def bulk_download_geneinfo_excel(request):
    '''批量下载购物车中的基因信息到Excel文件'''
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        gene_info_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)
        gene_info_list = gene_info_list.values(
            'gene_name', 'species__species_name', 'vector__vector_name', 'vector__vector_id', 
            'i5nc', 'i3nc', 'forbid_seq', 'original_seq','original_gc_content','saved_seq',
            'modified_gc_content','status'
        )

        df = pd.DataFrame(gene_info_list)
        # 重新修改一下列名
        df.columns = ['GeneName', 'Species', 'VectorName', 'VectorID', 'i5nc', 'i3nc', 'ForbiddenSeqs', 
                      'OriginalSeq', 'OriginalGCContent', 'ModifiedSeq', 'ModifiedGCContent', 'Status']

        # Prepare response with Excel content
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="RootPath-Online-Submission-Gene-Information-{request.user}.xlsx"'
        df.to_excel(excel_writer=response, index=False, engine='openpyxl')
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@require_POST
def checkout(request):
    # 获取所有选中的gene_ids, 提交订单。
    gene_ids = request.POST.getlist('gene_ids')
    if not gene_ids:
        return JsonResponse({'status': 'error', 'message': 'No gene selected'})

    # 为选中的gene创建一个订单
    order = OrderInfo.objects.create(user=request.user)
    # 获取所有选中的gene对象
    genes = get_list_or_404(GeneInfo, user=request.user, id__in=gene_ids)

    # 将gene添加到订单中
    order.gene_infos.add(*genes)
    order.status = 'Created'
    time_strf = order.order_time.strftime('%Y%m%d')[2:]
    order.inquiry_id = f'IQ{time_strf}{order.id:02d}'
    order.save()

    # 将选中的gene从购物车中删除
    cart = Cart.objects.get(user=request.user)
    cart.genes.remove(*genes)
    cart.save()

    # 不删除GeneInfo对象，改变status为submitted
    for gene_id in gene_ids:
        GeneInfo.objects.filter(user=request.user, id=gene_id).update(status='submitted')

    # 重定向到订单详情页面
    return JsonResponse({'status': 'success', 'message': 'Order created successfully', 'redirect_url': f'/user_center/manage_order/'})

@login_required
def view_order_detail(request, order_id):
    # retrieve the order
    order = OrderInfo.objects.get(id=order_id)
    return render(request, 'user_center/order_detail_view.html', {'order': order})

def get_seq_aa(combined_seq):
    start_index = 0
    while start_index < min(20, len(combined_seq)) and combined_seq[start_index].islower():
        start_index += 1

    end_index = -1
    while abs(end_index) <= min(20, len(combined_seq)) and combined_seq[end_index].islower():
        end_index -= 1

    # Check if any lowercase character was found in the first 20 characters
    if start_index <= min(20, len(combined_seq)):
        # Check if any lowercase character was found in the last 20 characters
        if abs(end_index) >= min(20, len(combined_seq)):
            return combined_seq[start_index:end_index + 1]

    # No lowercase characters found, return the original sequence
    return combined_seq

@login_required
def manage_order(request):
    order_list = OrderInfo.objects.filter(user=request.user)
    return render(request, 'user_center/order_view.html', {'order_list': order_list})

@login_required
def export_order_to_csv(request, order_id):
    # Retrieve the order with optimized query
    order = OrderInfo.objects.get(id=order_id)

    # Create a list of dictionaries containing gene information
    gene_info_list = [
        {
            'GeneName': gene_info.gene_name,
            'SeqAA': get_seq_aa(gene_info.combined_seq),
            'Species': gene_info.species.species_name if gene_info.species else None,
            'ForbiddenSeqs': gene_info.forbid_seq,
            'VectorID': gene_info.vector.vector_id if gene_info.vector else None,
            'VectorName': gene_info.vector.vector_name,
            'Seq5NC': gene_info.vector.NC5 + (gene_info.i5nc if gene_info.i5nc is not None else ''),
            'Seq3NC': (gene_info.i3nc if gene_info.i3nc is not None else '') + gene_info.vector.NC3,
            'i5nc': gene_info.i5nc,
            'i3nc': gene_info.i3nc,
            'InquiryID': order.inquiry_id,
        }
        for gene_info in order.gene_infos.all()
    ]

    # Create a DataFrame from the list
    df = pd.DataFrame(gene_info_list)

    # Prepare response with Excel content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{order.inquiry_id}-{order.user}-RootPath_Gene_Library_Order_Information.xlsx"'
    df.to_excel(excel_writer=response, index=False, engine='openpyxl')

    return response


@login_required
def order_delete(request):
    '''删除订单
        只有status为Cancelled的订单才能被删除!
    '''
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = OrderInfo.objects.get(id=order_id)
        if order.status == 'Cancelled':
            order.delete()
            return JsonResponse({'status': 'success', 'message': 'Order deleted successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Only cancelled order can be deleted'})
    else:
        return render(request, 'user_center/order_view.html')
         

def check_forbiden_seq(seq, seq_length, customer_forbidden_list=None):
    '''根据序列长度检查正义和反义链'''
    seq = seq.upper().replace(" ", "")

    forbidden_check_list = []
    forbidden_list_objects = GeneSynEnzymeCutSite.objects.all()
    for enzyme in forbidden_list_objects:
        enzyme_name = enzyme.enzyme_name
        enzyme_seq = enzyme.enzyme_seq
        enzyme_scope = enzyme.usescope
        start,end = enzyme_scope.split("-")
        start = int(start)
        end = int(end)

        if start <= seq_length <= end:
            forbidden_check_list.append(enzyme_seq)
    ###############################
    if customer_forbidden_list and isinstance(customer_forbidden_list, str):
        formated_list = re.split(r'[;,]', customer_forbidden_list)
        forbidden_check_list.extend(formated_list)

    contained_forbidden_list = [forbiden_seq for forbiden_seq in forbidden_check_list if forbiden_seq in seq]

    # find start and end positions of contained forbidden sequences
    positions = []
    for forbidden in contained_forbidden_list:
        start_positions = [match.start() for match in re.finditer(forbidden, seq)]
        end_poitions = [start + len(forbidden) for start in start_positions]
        positions.extend(list(zip(start_positions, end_poitions)))
    positions = merge_overlapping_positions(positions)
    return contained_forbidden_list, forbidden_check_list, positions

def check_forbidden_seq(seq, built_in_forbidden_list, customer_forbidden_list=None):
    # 初始化结果列表
    forbidden_positions = []

    # 将内置的和客户提供的 forbidden list 合并
    all_forbidden_list = built_in_forbidden_list
    if customer_forbidden_list:
        all_forbidden_list.extend(customer_forbidden_list)

    # 检查 seq 中的 forbidden 序列
    for forbidden_seq in all_forbidden_list:
        for match in re.finditer(forbidden_seq, seq):
            match_start = match.start()
            match_end = match.end()
            forbidden_positions.append({
                'forbidden_seq': forbidden_seq,
                'start': match_start,
                'end': match_end
            })
    return forbidden_positions


def find_sequence_positions(sequence, pattern):
    positions = []
    for match in re.finditer(pattern, sequence):
        start = match.start()
        end = match.end()
        positions.append((start, end))
    return positions

def merge_overlapping_positions(all_positions):
    '''合并所有重叠的区间'''
    if not all_positions:
        return []

    all_positions.sort(key=lambda x: x[0])
    merged_positions = [all_positions[0]]

    for current in all_positions[1:]:
        previous = merged_positions[-1]

        if current[0] <= previous[1]:
            merged = (previous[0], max(previous[1], current[1]))
            merged_positions[-1] = merged
        else:
            merged_positions.append(current)

    return merged_positions

def check_S8W8G6_sequence(sequence):
    '''consecutive NTs
    如果含有 S8 W8 G6结构的需要标注成Warning
    S8表示：含有8个连续的G或C e.g. GCGGCCGG,
    W8表示：含有8个连续的A或T e.g. ATATATAT,
    G6表示：含有6个连续的G，e.g. GGGGGG'''

    # Check for S8 (8 consecutive G or C) using regular expression
    s8_positions = find_sequence_positions(sequence, r'[GC]{8,}')

    # Check for W8 (8 consecutive A or T) using regular expression
    w8_positions = find_sequence_positions(sequence, r'[AT]{8,}')

    # Check for G6 (6 consecutive G) using regular expression
    g6_positions = find_sequence_positions(sequence, r'G{6,}')

    all_positions = s8_positions + w8_positions + g6_positions
    # 对所有的区间取并集
    all_positions = merge_overlapping_positions(all_positions)

    return all_positions

def calculate_gc_content(sequence):
    sequence = sequence.upper().replace(" ", "")
    gc_count = sequence.count('G') + sequence.count('C')
    gc_content = (gc_count / len(sequence)) * 100
    return gc_content

def check_regional_gc_content(sequence, window_size=20, threshold_low=20, threshold_high=80):
    positions = []
    for i in range(len(sequence) - window_size + 1):
        window = sequence[i:i + window_size]
        gc_content = calculate_gc_content(window)
        if gc_content <= threshold_low or gc_content >= threshold_high:
            start = i
            end = i + window_size
            positions.append((start, end))
    positions = merge_overlapping_positions(positions)

    return positions

def check_sequence(seq):
    '''检查序列GC含量
        overall GC content (only for NT submission)
            30% < Overall < 70% --> Pass 
            20% < Overall =< 30% OR 70% <= Overall < 80% --> Warning
            Overall <= 20% OR >= 80% --> Fail
        regional GC content (only for NT submission)
            20% < Regional < 80% --> Pass
            10% < Regional =< 20% OR 80% <= Regional < 90% --> Warning
            Regional <= 10% OR >= 90% --> Fail
        consecutive NTs
            S8W8G6 --> Warning
    '''
    seq = seq.upper().replace(" ", "")
    # check regional GC content
    regional_GC_positions = check_regional_gc_content(seq)
    # check consecutive NTs
    consecutive_NT_positions = check_S8W8G6_sequence(seq)

    all_positions = regional_GC_positions + consecutive_NT_positions
    return all_positions

def identify_sequence(seq):
    if not isinstance(seq, str):
        return "Invalid input, expected a string."

    seq = seq.upper().replace(" ", "")

    if not seq:
        return "Empty sequence"

    nucleotides_DNA = set("ATCG")
    nucleotides_RNA = set("AUCG")
    amino_acids = set("ACDEFGHIKLMNPQRSTVWY")

    # 允许"*"出现，但必须出现在最后
    if seq.endswith("*"):
        seq = seq[:-1]

    if all(base in nucleotides_DNA for base in seq):
        return "DNA sequence"
    elif all(base in nucleotides_RNA for base in seq):
        return "RNA sequence"
    elif all(aa in amino_acids for aa in seq):
        return "Protein sequence"
    else:
        invalid_bases = set(seq).difference(nucleotides_DNA.union(amino_acids))
        if invalid_bases:
            return f"Invalid sequence, containing: {', '.join(invalid_bases)}"
        else:
            return "Invalid or unknown sequence"


def process_sequence_get_highlight_position(seq, forbidden_seq):
    seq = seq.upper().replace(" ", "")
    seq = re.sub(r'[^a-zA-Z]', '', seq) # 删除所有非字母的字符
    seq = seq[:20].lower() + seq[20:-20]  + seq[-20:].lower() # Add lower case to the first and last 20 bases
    # 删除所有非字母的字符
    # 如果seq是氨基酸序列，则不需要检查forbid_seq，不需要计算gc_content，不需要检查consecutive NTs，直接返回
    if identify_sequence(seq) == "Protein sequence":
        return seq, "Protein", None, None, None
    elif identify_sequence(seq) == "Invalid sequence, containing: *":
        return seq, "Invalid Protein", None, None, None

    GC_content = calculate_gc_content(seq)
    gc_positions = check_sequence(seq)

    contained_forbidden_list, forbidden_check_list, forbidden_positions = check_forbiden_seq(seq, len(seq), forbidden_seq)

    # 把GC_positions和forbidden_positions 都写到json里面，这些都是需要highlight的位置
    highlights_positions = []
    for position in gc_positions:
        highlights_positions.append({
            'start': position[0],
            'end': position[1],
            'type': 'text-warning'
        })
    
    for position in forbidden_positions:
        highlights_positions.append({
            'start': position[0],
            'end': position[1],
            'type': 'bg-danger'
        })

    if len(forbidden_positions) > 0:
        return seq, "forbidden", forbidden_check_list, contained_forbidden_list, GC_content, highlights_positions
    
    return seq, "validated", forbidden_check_list, contained_forbidden_list, GC_content, highlights_positions


@login_required
def manage_vector(request):
    '''list vectors of the company and the user'''
    '''前端页面通过javascript从下面的customer_vector_data_api和rootpath_vector_data_api获取数据'''
    return render(request, 'user_center/manage_vector.html')

@login_required
def customer_vector_data_api(request):
    '''获取用户的vector数据'''
    vector_list = Vector.objects.filter(user=request.user).values(
        'id', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20', 
        'status', 'user__username', 'vector_file', 'vector_png', 'vector_gb'
    )
    return JsonResponse({'data': list(vector_list)}, safe=False)


@login_required
def rootpath_vector_data_api(request):
    '''获取公司的vector数据'''
    vector_list = Vector.objects.filter(user=None).values(
        'id', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20',
        'status', 'user__username', 'vector_file', 'vector_png', 'vector_gb'
    )
    return JsonResponse({'data': list(vector_list)}, safe=False)

# checked
@login_required
def vector_upload(request):
    '''当用户在manage_vector页面点击上传按钮时，调用此函数，上传自己的vector文件'''
    if request.method == 'POST':
        vector_file = request.FILES.get('vector_file')
        vector_name = request.POST.get('vector_name')
        this_vector, created = Vector.objects.update_or_create(
            user=request.user,
            vector_name=vector_name,
            vector_file=vector_file,
            defaults={
                'status': 'Submitted',
            }
        )
        return redirect('user_center:manage_vector')
    else:
        return redirect('user_center:manage_vector')

# checked
@login_required
def vector_delete(request):
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        vector = Vector.objects.get(user=request.user, id=vector_id)

        # 删除与之关联的文件
        if vector.vector_file:
            file_path = vector.vector_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        vector.delete()
        return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_vector.html')


@login_required
def vector_download(request, vector_id, file_type, is_admin=False):
    # user只能下载自己的vector和公司的vector，不能下载别人的vector，所以需要验证
    if not is_admin:
        try:
            # 获取当前用户的vector或公司的vector
            vector_object = Vector.objects.get(user=request.user, id=vector_id)
        except Vector.DoesNotExist:
            # 如果当前用户没有这个vector，检查是否为公司的vector
            vector_object = get_object_or_404(Vector, id=vector_id, user=None)
    else:
        vector_object = Vector.objects.get(id=vector_id)
    # 从vector_object中提取数据
    vector_name = vector_object.vector_name
    vector_id = vector_object.vector_id
    NC5 = vector_object.NC5
    NC3 = vector_object.NC3
    iu20 = vector_object.iu20
    id20 = vector_object.id20
    vector_map = vector_object.vector_map  # 
    vector_file = vector_object.vector_file # 这是用户上传的原始文件，通常是一个没有处理的序列文件，可以是多种格式。不是png的文件, 
    # pdf not used
    if file_type == 'pdf':
        '''Not used'''
        # 生成PDF文件
        data = {
            'vector_id': vector_id,
            'vector_name': vector_name,
            'NC5': NC5,
            'NC3': NC3,
            'iu20': iu20,
            'id20': id20,
            'vector_map': vector_map,
        }
        pdf_buffer = render_to_pdf(data)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{vector_name}.pdf"'
        return response
    elif file_type == 'txt':
        '''Not used'''
        # 使用 quote 可以确保浏览器正确解析文件名。特别是文件名包含空格或其他特殊字符时
        response = HttpResponse(content_type='text/plain')
        custom_filename = f'RootPath_{vector_id}_{vector_name}.txt'
        response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
        response.write(f"Vector Name: {vector_name}\n")
        response.write(f"iD20: {iu20}\n")
        response.write(f"iD20: {id20}\n")
        response.write(f"Vector Map: {NC3}{vector_map}{NC5}\n")
    
        return response
    elif file_type == 'dna':
        '''Not used'''
        response = HttpResponse(content_type='text/plain')
        custom_filename = f'RootPath_{vector_id}_{vector_name}.dna'
        response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
        response.write(f"{NC3}{vector_map}{NC5}")
        return response
    elif file_type == 'map':
        # 返回vector_png文件
        vector_png = vector_object.vector_png  # 这是改造后的Vector_png
        if vector_png:
            response = HttpResponse(vector_png, content_type='application/octet-stream')
            name = vector_png.name   # user/vector_file/pCVa001M1Kan_pET-28.png
            file_path = default_storage.path(name)  # /path/to/media/user/vector_file/pCVa001M1Kan_pET-28.png
            basename = os.path.basename(file_path)  # pCVa001M1Kan_pET-28.png
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='image/png')
                custom_filename = f'RootPath_{basename}'
                response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'

                return response
        else:
            return HttpResponse("No vector map found")
    elif file_type == 'gb':
        # 返回vector_genebank文件
        vector_gb = vector_object.vector_gb
        if vector_gb:
            response = HttpResponse(vector_gb, content_type='application/octet-stream')
            name = vector_gb.name
            file_path = default_storage.path(name)
            basename = os.path.basename(file_path)
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                custom_filename = f'RootPath_{basename}'
                response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
                return response
        else:
            return HttpResponse("No vector GeneBank file found", status=404)
    elif file_type == 'file':
        # 返回vector_file文件
        vector_file = vector_object.vector_file
        if vector_file:
            response = HttpResponse(vector_file, content_type='application/octet-stream')
            name = vector_file.name
            file_path = default_storage.path(name)
            basename = os.path.basename(file_path)
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                custom_filename = f'RootPath_{basename}'
                response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
                return response
        else:
            return HttpResponse("No vector file found", status=404)
    else:
        return HttpResponse("File type not supported", status=400)


def test(request):
    return render(request, 'user_center/test.html')