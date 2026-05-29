import itertools
import json, re, os
import copy
import tempfile
import zipfile
import uuid
import pandas as pd
import numpy as np
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from product.models import GeneSynEnzymeCutSite, Species, Vector
from tools.scripts.AnalysisSequence import convert_gene_table_to_RepeatsFinder_Format, process_gene_table_results
from tools.scripts.ParsingGenBank import addMultipleFeaturesToGeneBank, addAnalysisFeaturesAndFragments
# from tools.scripts.penalty_score_predict import predict_new_data_from_df
from .models import Cart, GeneInfo, GeneOptimization, OrderInfo
from .utils.render_to_pdf import render_to_pdf
from urllib.parse import quote
from django.core.mail import send_mail
from decouple import config
from Bio import SeqIO
from user_center.utils.vector_automation import VectorAutomationDesigner
from user_center.utils.sequence_fragmenter import fragment_sequence_by_penalty
from user_center.utils.sequence_processing import (
    clean_and_check_dna_sequence,
    check_forbidden_seq,
    process_contained_forbidden_list,
    process_highlights_positions,
    deal_repeats_warnings,
    process_status,
    make_restriction_site_decision
)

logger = logging.getLogger(__name__)

# Create your views here.
@login_required()
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
        start_time = time.time()  # 性能监控
        logger = logging.getLogger(__name__)

        # check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Please login first.'})

        # Parse JSON data from request
        data = json.loads(request.body.decode('utf-8'))
        vector_id = data.get("vectorId")
        gene_table = data.get("genetable")

        # validate Vector ID
        try:
            vector = Vector.objects.get(id=vector_id)
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid vector ID'})

        # 将 gene_table 转换为 DataFrame，并删除空行，重置索引，如果为空则返回错误信息
        df = pd.DataFrame(gene_table)
        df = df.dropna(how='all').reset_index(drop=True) # 删除空行,

        if df.empty:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})

        # Get or create a shopping cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)

        new_gene_ids_for_session = []  # 用于存储新创建的基因的id, 用于session

        # 处理基因表格，根据列数判断是AA序列还是NT序列，NT序列只有4列，AA序列有6列
        if len(df.columns) == 4:
            # print("Start processing NT sequence")
            df.columns = ['GeneName', 'OriginalSeq', 'i5nc', 'i3nc']  # 重命名列名，方便后续处理
            # 如果i5nc和i3nc为空，填充为''
            df['i5nc'] = df['i5nc'].fillna('')
            df['i3nc'] = df['i3nc'].fillna('')

            df['OriginalSeq'] = df['OriginalSeq'].str.replace("\n","").str.replace("\r","").str.replace(" ","").str.replace("\t", '')  # 去掉换行符和空格
            df['CombinedSeq'] = df.apply(lambda row: f'{vector.iu20.lower()}{row.get("i5nc","")}{row["OriginalSeq"]}{row.get("i3nc","")}{vector.id20.lower()}', axis=1)

            # 计算GC含量 - 使用向量化操作优化性能
            def calc_gc_content(seq):
                upper_seq = seq.upper()
                return round((upper_seq.count('G') + upper_seq.count('C')) / len(seq) * 100, 2) if len(seq) > 0 else 0

            df['original_gc_content'] = df['OriginalSeq'].apply(calc_gc_content)
            df['modified_gc_content'] = df['CombinedSeq'].apply(calc_gc_content)

            # 清理序列并检查是否包含非法碱基（在OriginalSeq上检查，位置相对于insert）
            _, df['Error'] = zip(*df['OriginalSeq'].apply(clean_and_check_dna_sequence))

            ##########################################################################################################################
            # Forbidden Check List - 优化：提前查询并缓存，只查询一次
            forbidden_list_objects = GeneSynEnzymeCutSite.objects.only('enzyme_seq').all()
            built_in_forbidden_list = [obj.enzyme_seq for obj in forbidden_list_objects]

            # 并行处理 forbidden sequence 检查以提升性能
            def check_forbidden_parallel(sequences, forbidden_list, max_workers=4):
                results = [None] * len(sequences)
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_idx = {
                        executor.submit(check_forbidden_seq, seq, forbidden_list): idx
                        for idx, seq in enumerate(sequences)
                    }
                    for future in as_completed(future_to_idx):
                        idx = future_to_idx[future]
                        results[idx] = future.result()
                return results

            # 根据数据量决定是否使用并行处理（在OriginalSeq上检查，位置相对于insert）
            if len(df) > 10:  # 超过10条序列时使用并行处理
                df['forbidden_info'] = check_forbidden_parallel(df['OriginalSeq'].tolist(), built_in_forbidden_list)
            else:
                df['forbidden_info'] = df['OriginalSeq'].apply(
                    lambda seq: check_forbidden_seq(seq, built_in_forbidden_list)
                )

            ###############################################################################################################################
            # Repeats Finder. sequence 和 gene_id 是查找repeats时必须的字段, 给这两列重新赋值，不需要重命名。
            # 在OriginalSeq上分析，使所有位置相对于insert，避免iU20/iD20导致的~20bp偏移
            repeats_start = time.time()
            df['gene_id'] = df['GeneName']
            df['sequence'] = df['OriginalSeq']
            data_json = convert_gene_table_to_RepeatsFinder_Format(df)
            result_df = process_gene_table_results(data_json)
            logger.info(f"Repeats analysis took {time.time() - repeats_start:.2f}s")

            # model_path = os.path.join(settings.BASE_DIR, 'tools', 'scripts', 'best_rf_model_12.pkl')
            # weights_path = os.path.join(settings.BASE_DIR, 'tools','scripts','best_rf_weights_12.npy')
            # predicted_data = predict_new_data_from_df(result_df, model_path=model_path, scaler=None, weights_path=weights_path)
            feature_columns = [
                'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score','LongRepeats_penalty_score',
                'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
                # ========== 新增三个特征的惩罚分 ==========
                'TandemRepeats_penalty_score', 'PalindromeRepeats_penalty_score', 'InvertedRepeats_penalty_score'
            ]
            result_df['total_penalty_score'] = sum(result_df[col] for col in feature_columns).round(2)
            # 将结果合并到原始数据中
            df = df.merge(result_df, left_on='GeneName', right_on='GeneName', how='left')
            ###############################################################################################################################
            # 限制性酶切位点自动决策
            # 获取克隆方法
            cloning_method = vector.cloning_method if vector.cloning_method else 'T4'

            # 对每个序列进行限制性酶切位点决策
            def apply_restriction_decision(row):
                decision_seq = build_restriction_scan_sequence(
                    vector,
                    i5nc=row.get('i5nc', ''),
                    insert_seq=row.get('OriginalSeq', ''),
                    i3nc=row.get('i3nc', '')
                )
                decision_result = make_restriction_site_decision(decision_seq, cloning_method)
                return pd.Series({
                    'restriction_decision': decision_result['decision'],
                    'restriction_process_route': decision_result['process_route'],
                    'restriction_message': decision_result['message'],
                    'restriction_requires_manual_review': decision_result['requires_manual_review'],
                    'bsai_count': decision_result['bsai_count'],
                    'bsmbi_count': decision_result['bsmbi_count'],
                    'bsai_positions': decision_result['bsai_positions'],
                    'bsmbi_positions': decision_result['bsmbi_positions']
                })

            restriction_results = df.apply(apply_restriction_decision, axis=1)
            df = pd.concat([df, restriction_results], axis=1)

            ###############################################################################################################################
            # 整合  把forbidden seq，warnings，stop codons的content加到 FoundForbiddenSequence中，在header中展示。
            df['contained_forbidden_list'] = df.apply(process_contained_forbidden_list, axis=1)

            # 整合：把forbidden_seq, warnings, stop codons 的位置信息加到 highlights_positions中，用于前端展示
            df['highlights_positions'] = df.apply(
                lambda row: process_highlights_positions(row),
                axis=1
            )

            # 最后把CombinedSeq赋值给saved_seq
            df['saved_seq'] = df['OriginalSeq']  # 有必要写到这里吗？
            df['warnings'] = df.apply(deal_repeats_warnings, axis=1)
            df['status'] = df.apply(process_status, axis=1)
            # print("df: \n", df[['warnings', 'contained_forbidden_list', 'status', 'forbidden_info', 'highlights_positions', 'Error']])
            
            gene_objects = []
            for _, row in df.iterrows():
                gene_id = row['gene_id']

                # 查找与当前行 gene_id 对应的分析结果
                analysis_results = data_json.get(gene_id, {})
                # 标记优化状态, 要根据序列状态来判断，如果是forbidden，就是NeedToOptimize，如果是validated，就是NotOptimized
                if row['status'] == 'forbidden':
                    optimization_status = 'NeedsOptimization'
                elif row['status'] == 'error':
                    optimization_status = 'Error'
                elif row['status'] == 'warning':
                    optimization_status = 'NotOptimized'
                else:
                    optimization_status = 'NotOptimized'

                # 创建 GeneInfo 对象
                # 注意：fragments_data 字段暂时为 None（切割功能已禁用）
                gene_objects.append(
                    GeneInfo(
                        user=request.user,
                        gene_name=gene_id,
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
                        seq_type='NT',  # 标记序列类型
                        optimization_status=optimization_status, # 标记优化状态

                        # 存储从 data_json 匹配到的分析结果
                        analysis_results=analysis_results,  # 假设你有一个 JSONField 或 TextField 存储分析结果

                        # 存储片段数据（暂时为None）
                        fragments_data=None,

                        # 限制性酶切位点决策结果
                        restriction_decision=row.get('restriction_decision', None),
                        restriction_process_route=row.get('restriction_process_route', None),
                        restriction_message=row.get('restriction_message', None),
                        restriction_requires_manual_review=row.get('restriction_requires_manual_review', False),
                        bsai_count=row.get('bsai_count', None),
                        bsmbi_count=row.get('bsmbi_count', None),
                        bsai_positions=row.get('bsai_positions', None),
                        bsmbi_positions=row.get('bsmbi_positions', None)
                    )
                )

            # Capture the current timestamp
            current_timestamp = timezone.now()

            with transaction.atomic():
                # Bulk create gene objects without immediately assigning them to a variable with IDs
                GeneInfo.objects.bulk_create(gene_objects)

                # Retrieve the gene objects from the database with their IDs
                # 优化：使用 select_related 减少数据库查询
                gene_objects_with_ids = GeneInfo.objects.select_related('vector', 'species').filter(
                    user=request.user,
                    gene_name__in=df['gene_id'],
                    create_date__gte=current_timestamp
                )

            # Add the gene objects to the cart's genes many-to-many relationship
            cart.genes.add(*gene_objects_with_ids)

            # Extend the new_gene_ids_for_session with the IDs of the retrieved objects
            new_gene_ids_for_session.extend([gene.id for gene in gene_objects_with_ids])

            # ========== 片段切割功能（暂时禁用，等待客户优化序列后再启用） ==========
            # TODO: 考虑在序列优化完成后再触发切割，而不是在初始提交时
            # 原因：序列可能需要先被客户优化，优化后的序列才需要切割
            # 触发异步片段切割任务（只对罚分>28的基因）
            # genes_need_fragmentation = [
            #     gene for gene in gene_objects_with_ids
            #     if gene.penalty_score and gene.penalty_score > 28
            # ]
            #
            # if genes_need_fragmentation:
            #     from user_center.tasks import async_fragment_genes
            #     gene_ids_to_fragment = [gene.id for gene in genes_need_fragmentation]
            #     task = async_fragment_genes.delay(gene_ids_to_fragment)
            #     logger.info(f"Triggered async fragmentation for {len(gene_ids_to_fragment)} genes (task: {task.id})")
            #
            #     # 将 task_id 存入 session，前端可以查询进度
            #     if 'fragmentation_tasks' not in request.session:
            #         request.session['fragmentation_tasks'] = []
            #     request.session['fragmentation_tasks'].append({
            #         'task_id': task.id,
            #         'gene_ids': gene_ids_to_fragment,
            #         'started_at': timezone.now().isoformat()
            #     })
            #     request.session.modified = True
        else:
            # print("Processing AA sequence")

            df.columns = ['GeneName', 'OriginalSeq', 'Species', 'ForbiddenSeqs', 'i5nc', 'i3nc']  # 重命名列名，方便后续处理
            df['protein_sequence'] = df['OriginalSeq']
            df['OriginalSeq'] = df['OriginalSeq'].str.replace("\n","").str.replace("\r","").str.replace(" ","")  # 去掉换行符和空格
            
            # 检测非氨基酸字符
            df['OriginalSeq'], df['Error'] = zip(*df['protein_sequence'].apply(clean_and_check_protein_sequence))
            df['warnings'] = ''
            # print("df: \n", df)
            df['contained_forbidden_list'] = df.apply(process_contained_forbidden_list, axis=1)
            df['highlights_positions'] = df.apply(process_highlights_positions, axis=1)

            df['status'] = df.apply(process_status, axis=1)

            gene_objects = []

            for _, row in df.iterrows():
                gene_id = row['GeneName']

                # 创建 Species 对象
                species = Species.objects.get(species_name=row.get('Species', None))
                optimization_status = 'Error' if row['status'] == 'error' else 'NeedsOptimization'
                # 创建 GeneInfo 对象，存储分析结
                gene_objects.append(
                    GeneInfo(
                        user=request.user,
                        gene_name=gene_id,
                        original_seq=row['OriginalSeq'],
                        vector=vector,
                        species=species,
                        status=row.get('status', 'validated'),  # check if status is valid 
                        forbid_seq=row.get('forbidden_check_list', ''),
                        combined_seq='',
                        i5nc=row.get('i5nc', ''),
                        i3nc=row.get('i3nc', ''),
                        saved_seq='',
                        forbidden_check_list=row.get('forbidden_check_list', ''),
                        contained_forbidden_list=row.get('contained_forbidden_list', ''),
                        original_highlights=row.get('highlights_positions', []),
                        modified_highlights='',
                        penalty_score=row.get('total_penalty_score', None),
                        optimization_status=optimization_status,
                        seq_type='AA',
                    )
                )

            current_timestamp = timezone.now()
            with transaction.atomic():
                # Bulk create gene objects without immediately assigning them to a variable with IDs
                GeneInfo.objects.bulk_create(gene_objects)

                # Retrieve the gene objects from the database with their IDs
                # 优化：使用 select_related 减少数据库查询
                gene_objects_with_ids = GeneInfo.objects.select_related('vector', 'species').filter(
                    user=request.user,
                    gene_name__in=df['GeneName'],
                    create_date__gte=current_timestamp
                )

            # Add the gene objects to the cart's genes many-to-many relationship
            cart.genes.add(*gene_objects_with_ids)
            new_gene_ids_for_session.extend([gene.id for gene in gene_objects_with_ids])

        # Store the new gene IDs in the session for later use
        request.session['new_gene_ids'] = new_gene_ids_for_session

        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time:.2f}s for {len(gene_table)} sequences ({total_time/len(gene_table):.3f}s per sequence)")

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
        end = match.end()
        content = match.group()
        non_standard_amino_acids_info.append({'start': start, 'end': end, 'content': content})
    
    # 检查终止密码子是否存在于序列中间
    if '*' in sequence_to_check:
        # 如果终止密码子出现在中间，记录其位置
        for match in re.finditer(r'\*', sequence_to_check):
            non_standard_amino_acids_info.append({
                'start': match.start(),
                'end': match.start(),  # 单个字符位置
                'content': '*'
            })

    # 4. 返回处理后的序列以及非法氨基酸的提醒信息（包含位置信息）
    if non_standard_amino_acids_info:
        warnings = [{'start': item['start'], 'end': item['end'], 'content': item['content']} for item in non_standard_amino_acids_info]
        return cleaned_sequence if has_terminal_stop else cleaned_sequence, warnings
    
    # 如果有终止密码子，添加它到处理后的序列
    return cleaned_sequence if has_terminal_stop else cleaned_sequence, None

def process_contained_forbidden_list(row):
    # 获取 forbidden_info 中的 forbidden_seq 列表
    forbidden_seqs = [info['forbidden_seq'] for info in row.get('forbidden_info', [])] if row.get('forbidden_info') else []

    contained_forbidden_list = forbidden_seqs

    return contained_forbidden_list

def process_highlights_positions(row):
    '''处理高亮位置'''
    highlights_positions = []

    # 定义一个正则表达式模式来提取所有数字
    pattern = r'\d+'

    def extract_field_numbers(item, field_name):
        match = re.search(rf'{field_name}\s*:\s*([^|]+)', item)
        if not match:
            return []
        return list(map(int, re.findall(pattern, match.group(1))))

    # 遍历每种分析类型以处理 start 和 end 位置
    # ========== 新增三个特征类型 ==========
    for analysis_type in ['LongRepeats', 'Homopolymers', 'W12S12Motifs', 'HighGC', 'LowGC', 'DoubleNT',
                          'TandemRepeats', 'PalindromeRepeats', 'InvertedRepeats']:
        if analysis_type not in row:
            continue
        analysis_value = row[analysis_type]
        if not isinstance(analysis_value, str) or not analysis_value.strip():
            continue

        items = [item.strip() for item in analysis_value.split(';') if item.strip()]

        # InvertedRepeats 有两组 start/end (stem1 和 stem2)，需要特殊处理
        if analysis_type == 'InvertedRepeats':
            for item in items:
                stem1_starts = extract_field_numbers(item, 'stem1_start')
                stem1_ends = extract_field_numbers(item, 'stem1_end')
                for i in range(min(len(stem1_starts), len(stem1_ends))):
                    highlights_positions.append({
                        'start': stem1_starts[i],
                        'end': stem1_ends[i],
                        'type': 'text-warning',
                    })

                stem2_starts = extract_field_numbers(item, 'stem2_start')
                stem2_ends = extract_field_numbers(item, 'stem2_end')
                for i in range(min(len(stem2_starts), len(stem2_ends))):
                    highlights_positions.append({
                        'start': stem2_starts[i],
                        'end': stem2_ends[i],
                        'type': 'text-warning',
                    })
        else:
            for item in items:
                start_results = extract_field_numbers(item, 'start')
                end_results = extract_field_numbers(item, 'end')
                for index in range(min(len(start_results), len(end_results))):
                    highlights_positions.append({
                        'start': start_results[index],
                        'end': end_results[index],
                        'type': 'text-warning',
                    })

    # 处理 forbidden_info 和 warnings 字段
    if 'forbidden_info' in row:
        for info in row['forbidden_info']:
            highlights_positions.append({
                'start': info['start'],
                'end': info['end'],
                'type': 'bg-info',
            })

    if 'Error' in row and row['Error']:  # 有Error列, qie有值的话，遍历Error列，添加到highlights_positions
        for error in row['Error']:
            highlights_positions.append({
                'start': error['start'],
                'end': error['end'],
                'type': 'bg-danger',
            })
    return highlights_positions

def deal_repeats_warnings(row):
    '''在LongRepeats，Homopolymers，W12S12Motifs，HighGC，LowGC，DoubleNT，TandemRepeats，PalindromeRepeats，InvertedRepeats中查询，
    只要任意一个有值，warnings就为True
    '''
    # ========== 新增三个特征类型 ==========
    for analysis_type in ['LongRepeats', 'Homopolymers', 'W12S12Motifs', 'HighGC', 'LowGC', 'DoubleNT',
                          'TandemRepeats', 'PalindromeRepeats', 'InvertedRepeats']:
        if analysis_type in row and row[analysis_type]:
            return True

# 定义安全判断是否有值的函数
def has_value(value):
    if isinstance(value, (list, dict, set, np.ndarray)):  # 判断列表、字典、集合、数组
        return len(value) > 0  # 长度大于0即为有效
    elif isinstance(value, pd.Series):  # 如果是Pandas Series，使用any判断是否有值
        return value.any()
    elif pd.isna(value):  # 如果是None或NaN，返回False
        return False
    elif isinstance(value, str):  # 对字符串去空格后判断
        return bool(value.strip())
    return True  # 其他情况默认视为有值


def normalize_sequence_text(value):
    """将序列相关字段标准化为字符串，避免None/NaN/'nan'参与拼接。"""
    if value is None:
        return ''

    try:
        if pd.isna(value):
            return ''
    except Exception:
        pass

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() in {'nan', 'none', 'null'}:
            return ''
        return cleaned

    return str(value)


def build_restriction_scan_sequence(vector, i5nc='', insert_seq='', i3nc=''):
    """
    统一Decision/BsaI/BsmBI统计序列：
    v5NC + i5nc + insert + i3nc + v3NC
    其中 iU20/iD20 仅作为标记，不参与任何计算。
    """
    i5nc = normalize_sequence_text(i5nc)
    insert_seq = normalize_sequence_text(insert_seq)
    i3nc = normalize_sequence_text(i3nc)
    core_seq = f'{i5nc}{insert_seq}{i3nc}' or insert_seq

    if not vector:
        return core_seq

    v5nc = normalize_sequence_text(getattr(vector, 'NC5', ''))
    v3nc = normalize_sequence_text(getattr(vector, 'NC3', ''))

    return f'{v5nc}{core_seq}{v3nc}'


def get_restriction_scan_sequence(gene, default_seq=''):
    """
    基于Gene对象构建统一Decision/BsaI/BsmBI统计序列。
    """
    insert_seq = normalize_sequence_text(default_seq or gene.original_seq)
    return build_restriction_scan_sequence(
        getattr(gene, 'vector', None),
        i5nc=getattr(gene, 'i5nc', ''),
        insert_seq=insert_seq,
        i3nc=getattr(gene, 'i3nc', '')
    )


def calculate_restriction_for_gene(gene, insert_seq_override=None):
    """
    按统一规则计算单条基因的Decision与BsaI/BsmBI位点信息。
    返回值与make_restriction_site_decision一致。
    """
    insert_seq = normalize_sequence_text(
        insert_seq_override if insert_seq_override is not None else (
            getattr(gene, 'saved_seq', '') or getattr(gene, 'original_seq', '')
        )
    )
    seq_to_analyze = build_restriction_scan_sequence(
        getattr(gene, 'vector', None),
        i5nc=getattr(gene, 'i5nc', ''),
        insert_seq=insert_seq,
        i3nc=getattr(gene, 'i3nc', '')
    )
    cloning_method = gene.vector.cloning_method if getattr(gene, 'vector', None) and gene.vector.cloning_method else 'T4'

    if not seq_to_analyze:
        return {
            'decision': '',
            'process_route': None,
            'message': '',
            'requires_manual_review': False,
            'bsai_count': 0,
            'bsmbi_count': 0,
            'bsai_positions': [],
            'bsmbi_positions': []
        }

    return make_restriction_site_decision(seq_to_analyze, cloning_method)


def apply_restriction_result_to_gene(gene, decision_result):
    """
    将Decision结果写回Gene对象（仅赋值，不save）。
    """
    gene.restriction_decision = decision_result.get('decision') or ''
    gene.restriction_process_route = decision_result.get('process_route')
    gene.restriction_message = decision_result.get('message') or ''
    gene.restriction_requires_manual_review = bool(decision_result.get('requires_manual_review', False))
    gene.bsai_count = int(decision_result.get('bsai_count') or 0)
    gene.bsmbi_count = int(decision_result.get('bsmbi_count') or 0)
    gene.bsai_positions = decision_result.get('bsai_positions') or []
    gene.bsmbi_positions = decision_result.get('bsmbi_positions') or []


def normalize_fragments_data_for_gene(gene, fragments_data):
    """
    将片段坐标标准化到基因区间（0-based, end-exclusive）。
    用于导出与图谱标注，避免片段位置超出真实基因长度。
    """
    if not isinstance(fragments_data, dict):
        return fragments_data

    fragments = fragments_data.get('fragments')
    if not isinstance(fragments, list):
        return fragments_data

    gene_seq = normalize_sequence_text(
        getattr(gene, 'saved_seq', '') or getattr(gene, 'original_seq', '')
    )
    gene_len = len(gene_seq)
    if gene_len <= 0:
        return fragments_data

    normalized = copy.deepcopy(fragments_data)
    normalized_fragments = []

    for frag in fragments:
        if not isinstance(frag, dict):
            continue

        try:
            start = int(frag.get('start', 0))
            end = int(frag.get('end', 0))
        except (TypeError, ValueError):
            continue

        start = max(0, min(start, gene_len))
        end = max(0, min(end, gene_len))
        if end <= start:
            continue

        frag_copy = copy.deepcopy(frag)
        frag_copy['start'] = start
        frag_copy['end'] = end
        frag_copy['length'] = end - start
        frag_copy['seq'] = gene_seq[start:end]
        normalized_fragments.append(frag_copy)

    normalized['fragments'] = normalized_fragments
    normalized['total_fragments'] = len(normalized_fragments)

    cut_positions = [frag['end'] for frag in normalized_fragments[:-1]]
    if cut_positions:
        try:
            from user_center.utils.sequence_fragmenter import get_grouping_strategy, format_mustcut_positions
            grouping = get_grouping_strategy(len(normalized_fragments))
            normalized['mustcut_positions'] = format_mustcut_positions(cut_positions, grouping)
        except Exception:
            normalized['mustcut_positions'] = '/'.join(str(pos) for pos in cut_positions) + '/'
    else:
        normalized['mustcut_positions'] = ''

    return normalized


# 定义状态处理函数
def process_status(row):
    forbidden = has_value(row.get('contained_forbidden_list'))
    error = has_value(row.get('Error'))
    warning = has_value(row.get('warnings'))
    # print("forbidden: ", forbidden, "error: ", error, "warning: ", warning)
    # 根据组合规则确定 status
    if forbidden and error and warning:
        return 'error'
    elif forbidden and error:
        return 'error'
    elif forbidden:
        return 'forbidden'
    elif error and warning:
        return 'error'
    elif error:
        return 'error'
    elif warning:
        return 'warning'
    else:
        return 'validated'

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
    decision_result = calculate_restriction_for_gene(gene_object)
    apply_restriction_result_to_gene(gene_object, decision_result)

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
        gene_id = data.get("gene_id")  # 应该换成 gene_id，

        gene_object = GeneInfo.objects.get(user=user, id=gene_id)
        combined_seq = gene_object.combined_seq     # 不带格式有小写 {iu20}.lower() + seq + {id20}.lower(), 可以直接比较

        if combined_seq == edited_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})

        # 这里需要重新处理
        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, \
            modified_gc_content, modified_highlights = process_sequence_get_highlight_position(edited_seq, gene_object.forbid_seq)

        if seq_status in ['Protein', 'Invalid Protein']:
            return JsonResponse({'status': 'error', 'message': 'Squence is not allowed. Your sequence may has '+ seq_status + ' sequence.'})
        
        if seq_status == 'forbidden':
            optimization_status = 'NeedsOptimization'
        elif seq_status == 'error':
            optimization_status = 'Error'
        elif seq_status == 'warning':
            optimization_status = 'NotOptimized'
        else:
            optimization_status = 'NotOptimized'
        
        gene_object.status = seq_status
        gene_object.saved_seq = tagged_seq
        gene_object.forbidden_check_list = forbidden_check_list
        gene_object.contained_forbidden_list = contained_forbidden_list
        gene_object.combined_seq = edited_seq
        gene_object.original_seq = edited_seq
        gene_object.modified_highlights = modified_highlights
        gene_object.modified_gc_content = modified_gc_content
        gene_object.optimization_status = optimization_status
        decision_result = calculate_restriction_for_gene(gene_object)
        apply_restriction_result_to_gene(gene_object, decision_result)
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
        from user_center.utils.email_notifications import send_optimization_started_email

        # 从请求中获取基因ID列表和物种
        gene_ids = request.POST.get('selected_genes')
        species_selected = request.POST.get('species_select_for_optimization')
        optimization_method = request.POST.get('optimization_method')

        optimization_method_dict = {
            '1': 'FbdSeqOnly',
            '2': 'NoFoldingCheck',
            '3': 'LongGene_Relaxed',
        }
        # print(f"Gene IDs: {gene_ids}")
        # print(f"Species: {species_selected}")
        # print(f"Optimization Method: {optimization_method_dict.get(optimization_method)}")

        # 转换基因ID为列表
        gene_ids = gene_ids.split(',')

        if species_selected == None:
            return JsonResponse({'status': 'error', 'message': 'Please select a species for optimization'})

        # 检查 species 是否存在
        species_obj = get_object_or_404(Species, species_name=species_selected)

        # Retrieve the genes and update their status, species, and optimization method
        gene_objects = GeneInfo.objects.filter(id__in=gene_ids)

        for gene in gene_objects:
            gene.optimization_status = 'Pending'
            gene.species = species_obj
            gene.optimization_method = optimization_method_dict.get(optimization_method)
            gene.optimization_id = uuid.uuid4()  # Generate a unique ID for optimization
            gene.save()

        # 发送优化开始的邮件通知
        try:
            send_optimization_started_email(
                user=request.user,
                gene_objects=gene_objects,
                species=species_obj,
                optimization_method=optimization_method_dict.get(optimization_method)
            )
        except Exception as e:
            # 邮件发送失败不影响主流程，只记录日志
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send optimization started email: {str(e)}")

        return redirect('user_center:bulk_optimization_display')

    return redirect('user_center:bulk_optimization')

@csrf_exempt
def condon_optimization_api(request):
    """
    设置一个 API，用于 GET 和 POST 请求，
    - 当 GET 请求时，根据 status 参数返回基因数据，默认返回所有 status 为 'pending' 的数据；
    - 当 POST 请求时，将 POST 回来的数据更新到数据库中。
    """
    if request.method == "GET":
        try:
            # 获取查询参数中的 status 值，默认为 'pending'
            status = request.GET.get('status', 'Pending')
            if status == 'pending':
                status = 'Pending'
            # 根据 optimization_status 为Pending来过滤基因数据
            gene_list = GeneInfo.objects.filter(optimization_status=status)
            data = list(
                gene_list.values(
                    'optimization_id', 'gene_name', 'original_seq', 'status', 'i5nc', 'i3nc',
                    'vector__vector_id', 'vector__NC5', 'vector__NC3',
                    'forbid_seq', 'modified_gc_content',
                    'species__species_name', 'saved_seq', 'optimization_method', 'seq_type'
                )
            )

            # 调整返回的 JSON 结构
            response_data = {'gene': data}

            return JsonResponse({'status': 'success', 'response': response_data}, safe=False)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to fetch genes: {str(e)}'}, status=500)
    elif request.method == "POST":
        try:
            import sys
            import pandas as pd

            # 添加项目路径以便导入 AnalysisSequence
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            tools_scripts_path = os.path.join(project_root, 'tools', 'scripts')
            sys.path.insert(0, tools_scripts_path)

            from AnalysisSequence import convert_gene_table_to_RepeatsFinder_Format, process_gene_table_results
            from user_center.utils.sequence_processing import (
                check_forbidden_seq,
                deal_repeats_warnings,
                process_status,
                process_contained_forbidden_list,
                process_highlights_positions,
                clean_and_check_dna_sequence
            )

            # Parse form-encoded data (request.POST)
            task_id = request.POST.get("gene_id")
            optimized_seq = request.POST.get("optimized_seq")
            status = request.POST.get("status")
            optimization_message = request.POST.get("optimization_message")

            status_mapping = {
                'completed': 'Optimized',
                'failed': 'failed',
                'processing': 'Optimizing',
            }

            # Update the gene information
            gene = GeneInfo.objects.get(optimization_id=task_id)  # assuming task_id maps to gene_id

            # 保存优化前的penalty score，用于邮件通知
            old_penalty_score = gene.penalty_score

            if status_mapping.get(status) == 'failed':
                gene.optimization_status = 'failed'
                gene.optimization_message = optimization_message
            else:
                # 更新优化状态和序列
                gene.optimization_status = status_mapping.get(status, 'Optimizing')
                gene.saved_seq = optimized_seq

                # 仅在优化完成时重新分析序列
                if status_mapping.get(status) == 'Optimized':
                    # 1. 计算GC含量
                    gene.modified_gc_content = round(
                        (optimized_seq.upper().count('G') + optimized_seq.upper().count('C')) / len(optimized_seq) * 100, 2
                    ) if len(optimized_seq) > 0 else 0

                    # 2. 清理序列并检查非法碱基
                    cleaned_seq, error_info = clean_and_check_dna_sequence(optimized_seq)

                    # 3. 检查禁用序列
                    built_in_forbidden_list = [
                        'GAAGAC', 'GGTCTC', 'CGTCTC', 'CACCTGC', 'GCAGGTG',
                        'CTGCAG', 'CTCGAG', 'AGATCT', 'ACTAGT', 'TCTAGA',
                        'GGATCC', 'GAATTC', 'GCGGCCGC', 'TTAATTAA'
                    ]
                    forbidden_info = check_forbidden_seq(optimized_seq, built_in_forbidden_list)

                    # 4. 计算penalty score
                    df = pd.DataFrame({
                        'gene_id': [gene.gene_name],
                        'sequence': [optimized_seq],
                        'forbidden_info': [forbidden_info],
                        'Error': [error_info] if error_info else [None]
                    })

                    # 使用AnalysisSequence进行分析
                    data_json = convert_gene_table_to_RepeatsFinder_Format(df)
                    result_df = process_gene_table_results(data_json)

                    # 计算总penalty score
                    feature_columns = [
                        'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score',
                        'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
                        'TandemRepeats_penalty_score', 'PalindromeRepeats_penalty_score', 'InvertedRepeats_penalty_score'
                    ]
                    total_penalty_score = sum(result_df[col].iloc[0] for col in feature_columns)
                    gene.penalty_score = round(total_penalty_score, 2)

                    # 5. 更新 contained_forbidden_list
                    forbidden_seqs = [info['forbidden_seq'] for info in forbidden_info] if forbidden_info else []
                    gene.contained_forbidden_list = forbidden_seqs

                    # 6. 处理 highlights_positions
                    row_dict = df.iloc[0].to_dict()
                    for col in result_df.columns:
                        if col != 'GeneName':
                            row_dict[col] = result_df.iloc[0][col]
                    highlights_positions = process_highlights_positions(row_dict)
                    gene.modified_highlights = highlights_positions

                    # 7. 更新 warnings
                    gene.warnings = deal_repeats_warnings(row_dict)

                    # 8. 更新 status (Sequence Status)
                    row_dict['contained_forbidden_list'] = forbidden_seqs
                    row_dict['warnings'] = gene.warnings
                    new_status = process_status(row_dict)
                    gene.status = new_status

                    # 9. 更新 analysis_results
                    if gene.gene_name in data_json:
                        gene.analysis_results = data_json[gene.gene_name]

            gene.save()

            # 发送优化完成的邮件通知（成功或失败都发送）
            if status_mapping.get(status) in ['Optimized', 'failed']:
                try:
                    from user_center.utils.email_notifications import send_optimization_completed_email
                    send_optimization_completed_email(
                        user=gene.user,
                        gene=gene,
                        optimization_status=status_mapping.get(status),
                        old_penalty_score=old_penalty_score
                    )
                except Exception as email_error:
                    # 邮件发送失败不影响主流程，只记录日志
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send optimization completed email: {str(email_error)}")

            return JsonResponse({'status': 'success', 'message': 'Gene status updated successfully'})
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return JsonResponse({'status': 'error', 'message': f'Failed to update gene status: {str(e)}', 'details': error_details}, status=500)

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def bulk_optimization_display(request):
    # 从模型中获取数据
    gene_list = GeneOptimization.objects.filter(user=request.user)

    return render(request, 'user_center/bulk_optimization.html', {'gene_list': gene_list})


###################### 以下是shopping cart 管理的函数 ############################
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    # 获取并按 `create_date` 正序排序（保持提交顺序）
    shopping_cart = list(cart.genes.all().select_related('vector').order_by('create_date'))

    # 统一按最新规则重算Decision与位点，修复历史数据导致的页面/导出不一致
    changed_genes = []
    restriction_fields = [
        'restriction_decision', 'restriction_process_route', 'restriction_message',
        'restriction_requires_manual_review', 'bsai_count', 'bsmbi_count',
        'bsai_positions', 'bsmbi_positions'
    ]
    for gene in shopping_cart:
        previous = (
            gene.restriction_decision,
            gene.restriction_process_route,
            gene.restriction_message,
            gene.restriction_requires_manual_review,
            gene.bsai_count,
            gene.bsmbi_count,
            gene.bsai_positions,
            gene.bsmbi_positions,
        )
        decision_result = calculate_restriction_for_gene(gene)
        apply_restriction_result_to_gene(gene, decision_result)
        current = (
            gene.restriction_decision,
            gene.restriction_process_route,
            gene.restriction_message,
            gene.restriction_requires_manual_review,
            gene.bsai_count,
            gene.bsmbi_count,
            gene.bsai_positions,
            gene.bsmbi_positions,
        )
        if current != previous:
            changed_genes.append(gene)

    if changed_genes:
        GeneInfo.objects.bulk_update(changed_genes, restriction_fields)

    # 分组
    grouped_shopping_cart = [
        {
            'date': key,
            'genes': list(group)
        }
        for key, group in itertools.groupby(
            shopping_cart, 
            key=lambda x: timezone.localtime(x.create_date).strftime('%Y-%m-%d %H:%M')
        )
    ]
    # 获取所有物种的名称
    species_list = Species.objects.all()
    species_names = sorted([species.species_name for species in species_list])

    # 获取正在进行的切割任务
    fragmentation_tasks = request.session.get('fragmentation_tasks', [])

    # 清理超过1小时的旧任务
    if fragmentation_tasks:
        from datetime import datetime, timedelta
        now = timezone.now()
        fragmentation_tasks = [
            task for task in fragmentation_tasks
            if (now - datetime.fromisoformat(task['started_at'].replace('Z', '+00:00'))).total_seconds() < 3600
        ]
        request.session['fragmentation_tasks'] = fragmentation_tasks
        request.session.modified = True

    context = {
        'grouped_shopping_cart': grouped_shopping_cart,
        'species_names': species_names,
        'fragmentation_tasks': json.dumps(fragmentation_tasks),  # 传递任务给前端
    }
    return render(request, 'user_center/shoppingCart_view.html', context)


@login_required
def get_fragmentation_status(request):
    """
    获取片段切割任务的状态
    """
    from django.core.cache import cache

    task_ids = request.GET.get('task_ids', '').split(',')
    if not task_ids or task_ids == ['']:
        return JsonResponse({'status': 'error', 'message': 'No task IDs provided'})

    results = {}
    for task_id in task_ids:
        task_id = task_id.strip()
        if not task_id:
            continue

        cache_key = f'fragment_task_{task_id}'
        task_data = cache.get(cache_key)

        if task_data:
            results[task_id] = task_data
        else:
            # 如果缓存中没有，可能任务已经很久之前完成了
            results[task_id] = {
                'status': 'unknown',
                'message': 'Task information not available'
            }

    return JsonResponse({'status': 'success', 'tasks': results})


@login_required
@require_POST
def trigger_gene_fragmentation(request):
    """
    手动触发基因序列片段切割
    用户可以选择特定的基因进行切割
    """
    try:
        gene_ids = request.POST.getlist('gene_ids[]')

        if not gene_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No genes selected for fragmentation'
            }, status=400)

        # 获取用户的基因
        genes = GeneInfo.objects.filter(
            user=request.user,
            id__in=gene_ids
        ).select_related('vector')

        if not genes.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No valid genes found'
            }, status=404)

        # 过滤出罚分 > 28 的基因
        genes_need_fragmentation = [
            gene for gene in genes
            if gene.penalty_score and gene.penalty_score > 28
        ]

        if not genes_need_fragmentation:
            return JsonResponse({
                'status': 'info',
                'message': 'None of the selected genes require fragmentation (all penalty scores ≤ 28)',
                'total_selected': len(gene_ids),
                'need_fragmentation': 0
            })

        # 触发异步切割任务
        from user_center.tasks import async_fragment_genes
        gene_ids_to_fragment = [gene.id for gene in genes_need_fragmentation]
        task = async_fragment_genes.delay(gene_ids_to_fragment)

        logger.info(f"User {request.user.username} manually triggered fragmentation for {len(gene_ids_to_fragment)} genes (task: {task.id})")

        # 将 task_id 存入 session，前端可以查询进度
        if 'fragmentation_tasks' not in request.session:
            request.session['fragmentation_tasks'] = []
        request.session['fragmentation_tasks'].append({
            'task_id': task.id,
            'gene_ids': gene_ids_to_fragment,
            'started_at': timezone.now().isoformat()
        })
        request.session.modified = True

        return JsonResponse({
            'status': 'success',
            'message': f'Fragmentation started for {len(gene_ids_to_fragment)} genes',
            'task_id': task.id,
            'total_selected': len(gene_ids),
            'need_fragmentation': len(gene_ids_to_fragment),
            'skipped': len(gene_ids) - len(genes_need_fragmentation)
        })

    except Exception as e:
        logger.error(f"Error triggering fragmentation: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to trigger fragmentation: {str(e)}'
        }, status=500)


@login_required
def get_fragment_details(request, gene_id):
    """
    获取基因的Fragment详细信息
    用于在购物车页面展示切割详情
    """
    try:
        # 获取基因
        gene = GeneInfo.objects.get(id=gene_id, user=request.user)

        # 检查是否有fragments_data
        if not gene.fragments_data or not gene.fragments_data.get('need_fragmentation'):
            return JsonResponse({
                'status': 'error',
                'message': 'This gene has not been fragmented or does not need fragmentation'
            }, status=404)

        normalized_fragments_data = normalize_fragments_data_for_gene(gene, gene.fragments_data)

        return JsonResponse({
            'status': 'success',
            'gene_id': gene.id,
            'gene_name': gene.gene_name,
            'fragments_data': normalized_fragments_data
        })

    except GeneInfo.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Gene not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting fragment details for gene {gene_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to load fragment details: {str(e)}'
        }, status=500)


@login_required
@require_POST
def trigger_order_fragmentation(request, order_id):
    """
    触发订单级别的基因序列片段切割
    处理订单中所有罚分 > 28 的基因
    """
    import time
    from user_center.utils.sequence_fragmenter import fragment_sequence_by_penalty

    try:
        # 获取订单
        order = OrderInfo.objects.get(id=order_id, user=request.user)

        # 获取订单中的所有基因
        genes = order.gene_infos.select_related('vector').all()

        if not genes:
            return JsonResponse({
                'status': 'error',
                'message': 'No genes found in this order'
            }, status=404)

        # 过滤出罚分 > 28 的基因
        genes_need_fragmentation = [
            gene for gene in genes
            if gene.penalty_score and gene.penalty_score > 28
        ]

        if not genes_need_fragmentation:
            return JsonResponse({
                'status': 'info',
                'message': 'None of the genes in this order require fragmentation (all penalty scores ≤ 28)',
                'total': len(genes),
                'need_fragmentation': 0
            })

        # 同步处理切割（订单级别，基因数量通常不多）
        success_count = 0
        fail_count = 0
        start_time = time.time()

        for gene in genes_need_fragmentation:
            try:
                # 获取载体的克隆方法和抗性
                cloning_method = gene.vector.cloning_method if gene.vector and gene.vector.cloning_method else "Gibson"
                vector_resistance = gene.vector.antibiotic_resistance if gene.vector and hasattr(gene.vector, 'antibiotic_resistance') else None
                fragment_source_seq = normalize_sequence_text(gene.saved_seq or gene.original_seq or gene.combined_seq)
                if not fragment_source_seq:
                    raise ValueError("No valid DNA sequence found for fragmentation")

                # 执行片段切割
                fragmentation_result = fragment_sequence_by_penalty(
                    sequence=fragment_source_seq,
                    cloning_method=cloning_method,
                    vector_resistance=vector_resistance,
                    max_penalty=28.0
                )

                if fragmentation_result and fragmentation_result.get('need_fragmentation'):
                    # 更新基因的 fragments_data
                    gene.fragments_data = fragmentation_result
                    gene.save(update_fields=['fragments_data'])
                    success_count += 1
                    logger.info(
                        f"Gene {gene.gene_name} (ID: {gene.id}) from Order {order_id} "
                        f"fragmented into {fragmentation_result.get('total_fragments', 0)} pieces"
                    )

            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to fragment gene {gene.gene_name} (ID: {gene.id}): {str(e)}", exc_info=True)

        elapsed_time = time.time() - start_time
        logger.info(
            f"User {request.user.username} fragmented Order {order_id}: "
            f"{success_count} success, {fail_count} failed out of {len(genes_need_fragmentation)} genes (took {elapsed_time:.2f}s)"
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Fragmentation completed',
            'total': len(genes),
            'success': success_count,
            'failed': fail_count,
            'skipped': len(genes) - len(genes_need_fragmentation),
            'time': round(elapsed_time, 2)
        })

    except OrderInfo.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error triggering order fragmentation: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to trigger fragmentation: {str(e)}'
        }, status=500)


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

def is_dna_or_protein(sequence):
    # 将序列转换成大写以统一处理
    sequence = sequence.upper()

    # 定义DNA和氨基酸的字符集
    dna_bases = set('ACGT')
    amino_acids = set('ACDEFGHIKLMNPQRSTVWY')

    # 检查是否所有字符都是DNA碱基
    if all(base in dna_bases for base in sequence):
        return "DNA"
    
    # 检查是否所有字符都是氨基酸
    elif all(aa in amino_acids for aa in sequence):
        return "Protein"

    else:
        # 如果有不匹配的字符，无法确定类型
        return "Unknown"

@login_required
def cart_genbank_download(request, gene_id):
    '''单个下载购物车中的基因的genbank文件， '''
    try:
        gene = GeneInfo.objects.get(user=request.user, id=gene_id)
    except GeneInfo.DoesNotExist:
        return HttpResponse("Gene not found", status=404)

    i5nc = gene.i5nc or ''
    i3nc = gene.i3nc or ''
    sequence = gene.saved_seq
    # 检查sequence是否为AA序列
    if is_dna_or_protein(sequence) != 'DNA':
        return HttpResponse("Your sequence is not a DNA sequence, or your amino acid sequence is not optimized. Please check.", status=400)

    # 与GenBank插入序列保持一致，先按统一规则重算并回写Restriction结果
    decision_result = calculate_restriction_for_gene(gene, insert_seq_override=sequence)
    apply_restriction_result_to_gene(gene, decision_result)
    gene.save(update_fields=[
        'restriction_decision', 'restriction_process_route', 'restriction_message',
        'restriction_requires_manual_review', 'bsai_count', 'bsmbi_count',
        'bsai_positions', 'bsmbi_positions'
    ])

    new_sequences = [i5nc, sequence, i3nc]
    new_feature_names = ['i5NC', gene.gene_name, 'i3NC']

    vector = gene.vector
    if vector and vector.vector_gb and os.path.exists(vector.vector_gb.path):
        vector_genbank_file_path = vector.vector_gb.path  # Get the file path
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=True) as temp_file: # 确保文件使用后自动删除，减少空间占用
            # 计算基因序列在插入序列中的起始位置（i5nc之后）
            gene_start_pos_in_insert = len(i5nc)

            # 使用新的函数，添加序列评估特征和fragments标注
            normalized_fragments_data = normalize_fragments_data_for_gene(gene, gene.fragments_data)
            try:
                addAnalysisFeaturesAndFragments(
                    genebank_file=vector_genbank_file_path,
                    output_file=temp_file.name,
                    new_sequences=new_sequences,
                    new_feature_names=new_feature_names,
                    start_feature_label='iU20',
                    end_feature_label='iD20',
                    analysis_results=gene.analysis_results,
                    fragments_data=normalized_fragments_data,
                    gene_start_pos_in_insert=gene_start_pos_in_insert
                )
            except ValueError as e:
                # 载体GenBank文件缺少iU20/iD20插入位点标记，无法定位插入区间
                return HttpResponse(
                    f"Cannot generate GenBank: vector '{vector.vector_name}' is missing iU20/iD20 insertion markers ({e}). Please contact the administrator to fix the vector file.",
                    status=422
                )
            temp_file.seek(0)
            response = HttpResponse(temp_file.read(), content_type='application/genbank')
            response['Content-Disposition'] = f'attachment; filename="RootPath-{vector.vector_name}-{gene.gene_name}.gb"'
            return response
    else:
        return HttpResponse("No vector genbank file found", status=404)

@csrf_exempt
@require_POST
def generate_genbank_delete_if_not_used(request):
    '''API :生成带有新特征的genbank文件'''
    ''' GenBank API JSON 数据格式如下:
    {
        "Plasmid_GZID": "plasmid_id",
        "features": [
            {
                "sequence": "ATGCGTAA",
                "name": "Feature_1"
            },
            {
                "sequence": "GGTACCTT",
                "name": "Feature_2"
            },
            {
                "sequence": "TACCGGTA",
                "name": "Feature_3"
            }
        ],
        "start_feature_label": "iU20",
        "end_feature_label": "iD20",
        "filename": "output.gb"
    }
    '''
    if request.method == 'POST':
        # 尝试解析JSON数据
        # print("Raw request body: ", request.body.decode('utf-8'))
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        # 获取请求中的参数
        plasmid_gzid = data.get('Plasmid_GZID')
        features = data.get('features', [])
        start_feature_label = data.get('start_feature_label', 'iU20')  # 默认值
        end_feature_label = data.get('end_feature_label', 'iD20')  # 默认值
        # print(f"Plasmid_GZID: {plasmid_gzid}, Features: {features}, Start Feature Label: {start_feature_label}, End Feature Label: {end_feature_label}")
        # 验证参数完整性
        if not plasmid_gzid or not features:
            return JsonResponse({"error": "Missing required parameters (Plasmid_GZID or features)"}, status=400)

        # 提取特征序列和名称
        new_sequences = []
        new_feature_names = []
        for f in features:
            seq = f.get('sequence', '').strip()
            fname = f.get('name', '').strip()
            seq = re.sub(r'<[^>]*>', '', seq)  # 去除HTML标签
            # 只添加非空序列的特征
            if seq:
                new_sequences.append(seq)
                new_feature_names.append(fname)
        
        # 检查是否有有效的特征序列, 如果没有，返回错误
        if not any(new_sequences):
            return JsonResponse({"error": "All provided feature sequences are empty"}, status=400)
        
        # 验证Plasmid GZID是否有对应的genbank文件
        try:
            vector = Vector.objects.get(vector_id=plasmid_gzid, )
        except Vector.DoesNotExist:
            return JsonResponse({"error": "No vector GenBank file found"}, status=404)

        if vector.vector_gb and os.path.exists(vector.vector_gb.path):
            vector_genbank_file_path = vector.vector_gb.path  # 获取文件路径
            # print(vector_genbank_file_path)

            # 对输入序列进行清理（如果有需要的话，这里主要看业务逻辑）
            # 不过此处new_sequences通常是用户直接传入的真实序列，所以可能不需要复杂的清理
            # 如果需要对序列进行简单清理，比如去除HTML标签和小写字符：
            new_sequences = [re.sub(r'<[^>]*>', '', seq) for seq in new_sequences]
            new_sequences = [re.sub(r'^[a-z]+|[a-z]+$', '', seq) for seq in new_sequences]

            # 生成带有新特征的GenBank文件
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=True) as temp_file:
                addMultipleFeaturesToGeneBank(
                    genebank_file=vector_genbank_file_path, 
                    output_file=temp_file.name, 
                    new_sequences=new_sequences, 
                    new_feature_names=new_feature_names, 
                    start_feature_label=start_feature_label, 
                    end_feature_label=end_feature_label
                )
                # 确保所有数据写入文件
                temp_file.flush()

                # 读取生成的GenBank文件并返回给用户
                temp_file.seek(0)
                record = SeqIO.read(temp_file, 'genbank')
                plasmid_sequence = str(record.seq)

                # 重置文件指针，并读取全部内容
                temp_file.seek(0)
                gb_content = temp_file.read()

                # 构建响应
                exclude_features=['Upstream of CDS', 'Downstream of CDS', 'i5NC', 'i3NC']
                filtered_features = [name for name in new_feature_names if name not in exclude_features]
                feature_count = len(filtered_features)
                
                # 文件名处理逻辑
                if feature_count == 1:
                    feature_part = filtered_features[0]
                elif feature_count == 2:
                    feature_part = f"{filtered_features[0]}_and_{filtered_features[1]}"
                elif feature_count >= 3:
                    feature_part = f"{filtered_features[0]}_plus_{feature_count - 1}_features"
                else:
                    feature_part = "unknown_features"  # 如果过滤后没有剩余的 feature，使用默认名称
                output_filename = f"{plasmid_gzid}-{feature_part}.gb"
                
                response = HttpResponse(gb_content, content_type='application/genbank')
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
                response['X-GenBank-Sequence'] = json.dumps(plasmid_sequence)
                return response
        else:
            return JsonResponse({"error": "No vector GenBank file found"}, status=404)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@require_POST
def generate_genbank(request):
    if request.method == 'POST':
        # print("Raw request body: ", request.body.decode('utf-8'))
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        plasmid_gzid = data.get('Plasmid_GZID')
        features = data.get('features', [])
        start_feature_label = data.get('start_feature_label', 'iU20')
        end_feature_label = data.get('end_feature_label', 'iD20')
        user_filename = data.get('filename', None)  # 用户提供的文件名
        
        if not plasmid_gzid or not features:
            return JsonResponse({"error": "Missing required parameters (Plasmid_GZID or features)"}, status=400)

        new_sequences = []
        new_feature_names = []
        for f in features:
            seq = f.get('sequence', '').strip()
            fname = f.get('name', '').strip()
            seq = re.sub(r'<[^>]*>', '', seq)
            if seq:
                new_sequences.append(seq)
                new_feature_names.append(fname)
        
        if not any(new_sequences):
            return JsonResponse({"error": "All provided feature sequences are empty"}, status=400)
        
        try:
            vector = Vector.objects.get(vector_id=plasmid_gzid)
        except Vector.DoesNotExist:
            return JsonResponse({"error": "No vector GenBank file found"}, status=404)

        if vector.vector_gb and os.path.exists(vector.vector_gb.path):
            vector_genbank_file_path = vector.vector_gb.path

            new_sequences = [re.sub(r'<[^>]*>', '', seq) for seq in new_sequences]

            with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=True) as temp_file:
                addMultipleFeaturesToGeneBank(
                    genebank_file=vector_genbank_file_path, 
                    output_file=temp_file.name, 
                    new_sequences=new_sequences, 
                    new_feature_names=new_feature_names, 
                    start_feature_label=start_feature_label, 
                    end_feature_label=end_feature_label
                )
                temp_file.flush()
                temp_file.seek(0)
                record = SeqIO.read(temp_file, 'genbank')
                plasmid_sequence = str(record.seq)
                temp_file.seek(0)
                gb_content = temp_file.read()
                
                if user_filename:
                    output_filename = user_filename
                else:
                    exclude_features = ['Upstream of CDS', 'Downstream of CDS', 'i5NC', 'i3NC']
                    filtered_features = [name for name in new_feature_names if name not in exclude_features]
                    feature_count = len(filtered_features)
                    if feature_count == 1:
                        feature_part = filtered_features[0]
                    elif feature_count == 2:
                        feature_part = f"{filtered_features[0]}_and_{filtered_features[1]}"
                    elif feature_count >= 3:
                        feature_part = f"{filtered_features[0]}_plus_{feature_count - 1}_features"
                    else:
                        feature_part = "unknown_features"
                    output_filename = f"{plasmid_gzid}-{feature_part}.gb"
                
                response = HttpResponse(gb_content, content_type='application/genbank')
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
                response['X-GenBank-Sequence'] = json.dumps(plasmid_sequence)
                return response
        else:
            return JsonResponse({"error": "No vector GenBank file found"}, status=404)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@require_POST
@login_required
def bulk_download_genbank(request):
    '''批量下载购物车中的基因的genbank文件'''
    # 注意：AA 序列是不能生成genbank文件的，要检查序列类型
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        temp_zip = tempfile.NamedTemporaryFile(delete=False)
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            changed_genes = []
            restriction_fields = [
                'restriction_decision', 'restriction_process_route', 'restriction_message',
                'restriction_requires_manual_review', 'bsai_count', 'bsmbi_count',
                'bsai_positions', 'bsmbi_positions'
            ]
            for gene_id in gene_ids:
                try:
                    gene = GeneInfo.objects.get(user=request.user, id=gene_id)
                    sequence = gene.saved_seq
                    if is_dna_or_protein(sequence) != 'DNA':
                        zf.writestr(f"Error-{gene_id}.{gene.gene_name}.txt", "Your sequence is not a DNA sequence, or your amino acid sequence is not optimized. Please check.")
                        continue
                    # 与GenBank插入序列保持一致，先按统一规则重算并回写Restriction结果
                    previous = (
                        gene.restriction_decision,
                        gene.restriction_process_route,
                        gene.restriction_message,
                        gene.restriction_requires_manual_review,
                        gene.bsai_count,
                        gene.bsmbi_count,
                        gene.bsai_positions,
                        gene.bsmbi_positions,
                    )
                    decision_result = calculate_restriction_for_gene(gene, insert_seq_override=sequence)
                    apply_restriction_result_to_gene(gene, decision_result)
                    current = (
                        gene.restriction_decision,
                        gene.restriction_process_route,
                        gene.restriction_message,
                        gene.restriction_requires_manual_review,
                        gene.bsai_count,
                        gene.bsmbi_count,
                        gene.bsai_positions,
                        gene.bsmbi_positions,
                    )
                    if current != previous:
                        changed_genes.append(gene)

                    i5nc = gene.i5nc or ''
                    i3nc = gene.i3nc or ''

                    vector = gene.vector
                    if vector and vector.vector_gb:
                        vector_genbank_file_path = vector.vector_gb.path
                        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=False) as temp_file:
                            # 计算基因序列在插入序列中的起始位置（i5nc之后）
                            gene_start_pos_in_insert = len(i5nc)

                            # 使用新的函数，添加序列评估特征和fragments标注
                            normalized_fragments_data = normalize_fragments_data_for_gene(gene, gene.fragments_data)
                            addAnalysisFeaturesAndFragments(
                                genebank_file=vector_genbank_file_path,
                                output_file=temp_file.name,
                                new_sequences=[i5nc, sequence, i3nc],
                                new_feature_names=['i5NC', gene.gene_name, 'i3NC'],
                                start_feature_label='iU20',
                                end_feature_label='iD20',
                                analysis_results=gene.analysis_results,
                                fragments_data=normalized_fragments_data,
                                gene_start_pos_in_insert=gene_start_pos_in_insert
                            )
                            temp_file.seek(0)
                            genbank_content = temp_file.read()
                            genbank_filename = f"RootPath-{vector.vector_name}-{gene.gene_name}.gb"
                            zf.writestr(genbank_filename, genbank_content)
                            temp_file.close()
                            os.remove(temp_file.name)
                    else:
                        zf.writestr(f"Error-{gene_id}.txt", "No vector GenBank file found")
                except GeneInfo.DoesNotExist:
                    zf.writestr(f"Error-{gene_id}.txt", "Gene not found")
                except ValueError as e:
                    # 载体GenBank文件缺少iU20/iD20标记等，跳过该基因，不影响其它基因
                    zf.writestr(f"Error-{gene_id}.txt", f"Cannot generate GenBank: {e}")

            if changed_genes:
                GeneInfo.objects.bulk_update(changed_genes, restriction_fields)

        temp_zip.seek(0)
        response = HttpResponse(temp_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="RootPath-Online-Submission.zip"'
        temp_zip.close()
        os.remove(temp_zip.name)
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def bulk_download_geneinfo_excel(request):
    '''批量下载购物车中的基因信息到Excel文件'''
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        # 获取完整的GeneInfo对象(需要fragments_data字段)
        gene_info_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids).select_related('species', 'vector')

        # 构建数据列表
        data_rows = []
        changed_genes = []
        restriction_fields = [
            'restriction_decision', 'restriction_process_route', 'restriction_message',
            'restriction_requires_manual_review', 'bsai_count', 'bsmbi_count',
            'bsai_positions', 'bsmbi_positions'
        ]
        for gene in gene_info_list:
            modified_seq = normalize_sequence_text(gene.combined_seq if gene.combined_seq else gene.original_seq)

            decision_info = calculate_restriction_for_gene(gene)
            previous = (
                gene.restriction_decision,
                gene.restriction_process_route,
                gene.restriction_message,
                gene.restriction_requires_manual_review,
                gene.bsai_count,
                gene.bsmbi_count,
                gene.bsai_positions,
                gene.bsmbi_positions,
            )
            apply_restriction_result_to_gene(gene, decision_info)
            current = (
                gene.restriction_decision,
                gene.restriction_process_route,
                gene.restriction_message,
                gene.restriction_requires_manual_review,
                gene.bsai_count,
                gene.bsmbi_count,
                gene.bsai_positions,
                gene.bsmbi_positions,
            )
            if current != previous:
                changed_genes.append(gene)

            bsai_info = {
                'count': int(decision_info.get('bsai_count') or 0),
                'positions': decision_info.get('bsai_positions') or []
            }
            bsmbi_info = {
                'count': int(decision_info.get('bsmbi_count') or 0),
                'positions': decision_info.get('bsmbi_positions') or []
            }

            if decision_info.get('decision') == 'accept' and decision_info.get('process_route'):
                decision_text = f"{decision_info['process_route']} route"
            elif decision_info.get('decision') == 'reject':
                decision_text = 'Reject'
            else:
                decision_text = ''

            # 格式化位置信息为字符串 (例如: "10-16, 50-56")
            bsai_positions_str = ', '.join([f"{p['start']}-{p['end']}" for p in bsai_info['positions']]) if bsai_info['positions'] else ''
            bsmbi_positions_str = ', '.join([f"{p['start']}-{p['end']}" for p in bsmbi_info['positions']]) if bsmbi_info['positions'] else ''

            used_modified_fallback = not bool(gene.combined_seq)
            row = {
                'GeneName': gene.gene_name,
                'Species': gene.species.species_name if gene.species else '',
                'VectorName': gene.vector.vector_name if gene.vector else '',
                'VectorID': gene.vector.vector_id if gene.vector else '',
                'v5NC': normalize_sequence_text(gene.vector.NC5 if gene.vector else ''),
                'v3NC': normalize_sequence_text(gene.vector.NC3 if gene.vector else ''),
                'i5nc': normalize_sequence_text(gene.i5nc),
                'i3nc': normalize_sequence_text(gene.i3nc),
                'ForbiddenSeqs': gene.forbid_seq or '',
                'OriginalSeq': gene.original_seq or '',
                'OriginalGCContent': gene.original_gc_content if gene.original_gc_content is not None else '',
                'ModifiedSeq': normalize_sequence_text(modified_seq),
                'ModifiedGCContent': gene.modified_gc_content if gene.modified_gc_content is not None else '',
                'Status': gene.status or '',
                'PenaltyScore': gene.penalty_score if gene.penalty_score is not None else '',
                'BsaI_Count': bsai_info['count'],
                'BsaI_Positions': bsai_positions_str,
                'BsmBI_Count': bsmbi_info['count'],
                'BsmBI_Positions': bsmbi_positions_str,
                'Decision': decision_text,
                'ModifiedSeqFallback': 'Yes' if used_modified_fallback else 'No',
            }

            # 添加详细的序列评估特征列
            if gene.analysis_results:
                analysis = gene.analysis_results
                # 添加9种评估特征的罚分
                row['HighGC_penalty'] = analysis.get('HighGC_penalty_score', '')
                row['LowGC_penalty'] = analysis.get('LowGC_penalty_score', '')
                row['W12S12Motifs_penalty'] = analysis.get('W12S12Motifs_penalty_score', '')
                row['LongRepeats_penalty'] = analysis.get('LongRepeats_penalty_score', '')
                row['Homopolymers_penalty'] = analysis.get('Homopolymers_penalty_score', '')
                row['DoubleNT_penalty'] = analysis.get('DoubleNT_penalty_score', '')
                row['TandemRepeats_penalty'] = analysis.get('TandemRepeats_penalty_score', '')
                row['PalindromeRepeats_penalty'] = analysis.get('PalindromeRepeats_penalty_score', '')
                row['InvertedRepeats_penalty'] = analysis.get('InvertedRepeats_penalty_score', '')

                # 添加位置信息（转换为 1-based 坐标）
                def _to_1based(features_data):
                    """将原始 0-based 位置数据转换为 1-based 用于 Excel 输出"""
                    if not features_data:
                        return ''
                    position_keys = {'start', 'end', 'stem1_start', 'stem1_end', 'stem2_start', 'stem2_end'}
                    items = features_data if isinstance(features_data, list) else [features_data]
                    converted = []
                    for item in items:
                        if not isinstance(item, dict):
                            converted.append(item)
                            continue
                        new_item = {}
                        for k, v in item.items():
                            if k in position_keys:
                                if isinstance(v, list):
                                    new_item[k] = [p + 1 if isinstance(p, (int, float)) else p for p in v]
                                elif isinstance(v, (int, float)):
                                    new_item[k] = int(v) + 1
                                else:
                                    new_item[k] = v
                            else:
                                new_item[k] = v
                        converted.append(new_item)
                    return converted

                row['HighGC_positions'] = _to_1based(analysis.get('HighGC', ''))
                row['LowGC_positions'] = _to_1based(analysis.get('LowGC', ''))
                row['W12S12Motifs_positions'] = _to_1based(analysis.get('W12S12Motifs', ''))
                row['LongRepeats_positions'] = _to_1based(analysis.get('LongRepeats', ''))
                row['Homopolymers_positions'] = _to_1based(analysis.get('Homopolymers', ''))
                row['DoubleNT_positions'] = _to_1based(analysis.get('DoubleNT', ''))
                row['TandemRepeats_positions'] = _to_1based(analysis.get('TandemRepeats', ''))
                row['PalindromeRepeats_positions'] = _to_1based(analysis.get('PalindromeRepeats', ''))
                row['InvertedRepeats_positions'] = _to_1based(analysis.get('InvertedRepeats', ''))
            else:
                # 如果没有analysis_results，填充空值
                for feature in ['HighGC', 'LowGC', 'W12S12Motifs', 'LongRepeats', 'Homopolymers',
                               'DoubleNT', 'TandemRepeats', 'PalindromeRepeats', 'InvertedRepeats']:
                    row[f'{feature}_penalty'] = ''
                    row[f'{feature}_positions'] = ''

            # 处理片段信息
            if gene.fragments_data:
                frag_data = normalize_fragments_data_for_gene(gene, gene.fragments_data)
                fragments = frag_data.get('fragments', [])
                row['IsFragmented'] = 'Yes' if frag_data.get('need_fragmentation') else 'No'
                row['VectorMethod'] = gene.vector.cloning_method if gene.vector and gene.vector.cloning_method else ''
                row['FragmentMethod'] = frag_data.get('cloning_method', '')
                row['TotalFragments'] = len(fragments) if fragments else frag_data.get('total_fragments', 1)
                row['MustCut'] = frag_data.get('mustcut_positions', '')

                # 片段详情(格式: "Frag1(0-1000,25.5);Frag2(1000-2000,27.8)")
                if fragments:
                    frag_details = []
                    for frag in fragments:
                        start_1based = int(frag.get('start', 0)) + 1
                        end_pos = int(frag.get('end', 0))
                        penalty = frag.get('penalty_score', 0)
                        frag_details.append(f"Frag{frag['index']}({start_1based}-{end_pos},{penalty})")
                    row['FragmentDetails'] = '; '.join(frag_details)
                else:
                    row['FragmentDetails'] = ''

                # 警告信息
                row['FragmentWarning'] = frag_data.get('warning', '')
            else:
                row['IsFragmented'] = 'No'
                row['VectorMethod'] = gene.vector.cloning_method if gene.vector and gene.vector.cloning_method else ''
                row['FragmentMethod'] = ''
                row['TotalFragments'] = 1
                row['MustCut'] = ''
                row['FragmentDetails'] = ''
                row['FragmentWarning'] = ''

            data_rows.append(row)

        if changed_genes:
            GeneInfo.objects.bulk_update(changed_genes, restriction_fields)

        df = pd.DataFrame(data_rows)

        # 统一清洗序列字段：None/NaN/'nan'/'none'/'null' -> ''
        seq_columns = ['v5NC', 'i5nc', 'ModifiedSeq', 'i3nc', 'v3NC']
        for col in seq_columns:
            df[col] = df[col].map(normalize_sequence_text)

        # 添加 fullSeq 列：v5NC + i5NC + OriginalSeq(insert) + i3NC + v3NC
        # 注意：不能用ModifiedSeq，因为ModifiedSeq是combined_seq = iU20+i5nc+insert+i3nc+iD20
        # 使用ModifiedSeq会导致iU20/iD20和i5nc/i3nc被重复拼接
        df['FullSeq'] = (
            df['v5NC'] +
            df['i5nc'] +
            df['OriginalSeq'] +
            df['i3nc'] +
            df['v3NC']
        )

        # 调整列顺序
        column_order = [
            'GeneName', 'Species', 'VectorName', 'VectorID', 'v5NC', 'v3NC', 'i5nc', 'i3nc',
            'ForbiddenSeqs', 'OriginalSeq', 'OriginalGCContent', 'ModifiedSeq',
            'ModifiedGCContent', 'Status', 'PenaltyScore',
            # 序列评估特征（罚分和位置）
            'HighGC_penalty', 'HighGC_positions',
            'LowGC_penalty', 'LowGC_positions',
            'W12S12Motifs_penalty', 'W12S12Motifs_positions',
            'LongRepeats_penalty', 'LongRepeats_positions',
            'Homopolymers_penalty', 'Homopolymers_positions',
            'DoubleNT_penalty', 'DoubleNT_positions',
            'TandemRepeats_penalty', 'TandemRepeats_positions',
            'PalindromeRepeats_penalty', 'PalindromeRepeats_positions',
            'InvertedRepeats_penalty', 'InvertedRepeats_positions',
            # 酶切位点
            'BsaI_Count', 'BsaI_Positions', 'BsmBI_Count', 'BsmBI_Positions', 'Decision',
            # 序列信息
            'FullSeq', 'ModifiedSeqFallback',
            # 片段信息
            'IsFragmented', 'VectorMethod', 'FragmentMethod', 'TotalFragments', 'MustCut', 'FragmentDetails', 'FragmentWarning'
        ]
        df = df[column_order]

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
@require_POST
def get_task_status(request):
    """
    API: 查询异步任务状态

    POST参数:
        process_task_id: ProcessTask对象的ID

    返回:
        {
            'status': 'pending' | 'processing' | 'completed' | 'failed',
            'progress': int,  # 已处理数量
            'total': int,  # 总数量
            'percentage': int,  # 进度百分比
            'error_message': str | null,
            'gene_ids': list | null  # 完成后的基因ID列表
        }
    """
    from user_center.models import ProcessTask

    try:
        process_task_id = request.POST.get('process_task_id')
        if not process_task_id:
            return JsonResponse({'error': 'process_task_id is required'}, status=400)

        # 获取ProcessTask对象
        process_task = ProcessTask.objects.get(pk=process_task_id, user=request.user)

        response_data = {
            'status': process_task.status,
            'progress': process_task.progress,
            'total': process_task.total,
            'percentage': process_task.get_progress_percentage(),
            'error_message': process_task.error_message,
            'gene_ids': process_task.gene_ids if process_task.status == 'completed' else None
        }

        return JsonResponse(response_data)

    except ProcessTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
    gene_info_list = []
    for gene_info in order.gene_infos.all():
        # 基础信息
        gene_data = {
            'GeneName': gene_info.gene_name,
            'SeqAA': get_seq_aa(gene_info.combined_seq),
            'Species': gene_info.species.species_name if gene_info.species else None,
            'ForbiddenSeqs': gene_info.forbid_seq,
            'VectorID': gene_info.vector.vector_id if gene_info.vector else None,
            'VectorName': gene_info.vector.vector_name,
            'Seq5NC': (
                normalize_sequence_text(gene_info.vector.NC5 if gene_info.vector else '') +
                normalize_sequence_text(gene_info.i5nc)
            ),
            'Seq3NC': (
                normalize_sequence_text(gene_info.i3nc) +
                normalize_sequence_text(gene_info.vector.NC3 if gene_info.vector else '')
            ),
            'i5nc': gene_info.i5nc,
            'i3nc': gene_info.i3nc,
            'InquiryID': order.inquiry_id,
        }

        # 添加切割信息（如果存在）
        if gene_info.fragments_data and gene_info.fragments_data.get('need_fragmentation'):
            frag_data = normalize_fragments_data_for_gene(gene_info, gene_info.fragments_data)
            gene_data.update({
                'Fragmented': 'Yes',
                'TotalFragments': frag_data.get('total_fragments', ''),
                'CloningMethod': frag_data.get('cloning_method', ''),
                'MustCutPositions': frag_data.get('mustcut_positions', ''),
                'PenaltyScore': gene_info.penalty_score if gene_info.penalty_score else '',
            })

            # 添加每个片段的详细信息
            fragments = frag_data.get('fragments', [])
            for idx, fragment in enumerate(fragments, 1):
                gene_data[f'Fragment{idx}_Length'] = fragment.get('length', '')
                gene_data[f'Fragment{idx}_Penalty'] = fragment.get('penalty_score', '')
                gene_data[f'Fragment{idx}_Position'] = f"{fragment.get('start', '')}-{fragment.get('end', '')}"
        else:
            gene_data.update({
                'Fragmented': 'No',
                'TotalFragments': '',
                'CloningMethod': gene_info.vector.cloning_method if gene_info.vector else '',
                'MustCutPositions': '',
                'PenaltyScore': gene_info.penalty_score if gene_info.penalty_score else '',
            })

        gene_info_list.append(gene_data)

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
    # 取两位小数
    gc_content = round(gc_content, 2)
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
        'status', 'user__username', 'vector_file', 'vector_png', 'vector_gb',
        'design_status', 'cloning_method', 'i5NC', 'i3NC'
    )
    data = list(vector_list)
    return JsonResponse({'data': data}, safe=False)


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
        try:
            vector_id = request.POST.get('vector_id')
            vector = Vector.objects.get(user=request.user, id=vector_id)

            # 删除与之关联的文件
            # 删除原始GenBank文件
            if vector.vector_file and vector.vector_file.name:
                try:
                    file_path = vector.vector_file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting vector_file: {e}")

            # 删除改造后的GenBank文件
            if vector.vector_gb and vector.vector_gb.name:
                try:
                    gb_path = vector.vector_gb.path
                    if os.path.exists(gb_path):
                        os.remove(gb_path)
                except Exception as e:
                    print(f"Error deleting vector_gb: {e}")

            # 删除PNG图片文件
            if vector.vector_png and vector.vector_png.name:
                try:
                    png_path = vector.vector_png.path
                    if os.path.exists(png_path):
                        os.remove(png_path)
                except Exception as e:
                    print(f"Error deleting vector_png: {e}")

            vector.delete()
            return JsonResponse({'status': 'success', 'message': 'Vector deleted successfully'})
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Vector not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return render(request, 'user_center/manage_vector.html')


@login_required
def vector_automation_design_trigger(request):
    """
    触发载体改造自动化设计
    """
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        forced_method = request.POST.get('forced_method') or None

        # 校验指定的克隆方法
        valid_methods = {'Gibson', 'GoldenGate', 'T4'}
        if forced_method and forced_method not in valid_methods:
            return JsonResponse({'status': 'error', 'message': f'不支持的克隆方法: {forced_method}'})

        try:
            vector = Vector.objects.get(user=request.user, id=vector_id)

            # 检查是否已上传文件
            if not vector.vector_file:
                return JsonResponse({
                    'status': 'error',
                    'message': '请先上传载体文件'
                })

            # 重置设计状态
            vector.design_status = 'Pending'
            vector.design_error = None
            vector.save()

            # 触发异步任务
            from user_center.tasks import async_vector_automation_design
            task = async_vector_automation_design.delay(vector_id, forced_method=forced_method)

            return JsonResponse({
                'status': 'success',
                'message': '载体改造设计任务已启动',
                'task_id': task.id
            })

        except Vector.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '载体不存在'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'启动设计任务失败: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


@login_required
def vector_automation_design_status(request):
    """
    查询载体改造自动化设计状态
    """
    if request.method == 'GET':
        vector_id = request.GET.get('vector_id')
        try:
            vector = Vector.objects.get(user=request.user, id=vector_id)

            def parse_primer(value):
                if value and '::' in value:
                    parts = value.split('::', 1)
                    return parts[0], parts[1]
                return None, value or ''

            response_data = {
                'status': 'success',
                'design_status': vector.design_status,
                'cloning_method': vector.cloning_method,
                'design_error': vector.design_error
            }

            # 如果设计完成，返回详细信息
            if vector.design_status == 'Completed':
                forward_name, forward_seq = parse_primer(vector.primer_forward)
                reverse_name, reverse_seq = parse_primer(vector.primer_reverse)
                forward_hairpin_tm = VectorAutomationDesigner.calculate_hairpin_tm(forward_seq) if forward_seq else None
                reverse_hairpin_tm = VectorAutomationDesigner.calculate_hairpin_tm(reverse_seq) if reverse_seq else None
                forward_dg = VectorAutomationDesigner.calculate_dimer_dg(forward_seq) if forward_seq else None
                reverse_dg = VectorAutomationDesigner.calculate_dimer_dg(reverse_seq) if reverse_seq else None
                hetero_dg = None
                if forward_seq and reverse_seq:
                    hetero_dg = VectorAutomationDesigner.calculate_dimer_dg(forward_seq, reverse_seq)
                response_data.update({
                    'v5nc': vector.NC5,
                    'v3nc': vector.NC3,
                    'i5nc': vector.i5NC,
                    'i3nc': vector.i3NC,
                    'iu20': vector.iu20,
                    'id20': vector.id20,
                    'primer_forward': forward_seq,
                    'primer_reverse': reverse_seq,
                    'primer_forward_name': forward_name,
                    'primer_reverse_name': reverse_name,
                    'primer_forward_tm': vector.primer_forward_tm,
                    'primer_reverse_tm': vector.primer_reverse_tm,
                    'primer_forward_hairpin_tm': forward_hairpin_tm,
                    'primer_reverse_hairpin_tm': reverse_hairpin_tm,
                    'primer_forward_homodimer_dg': forward_dg,
                    'primer_reverse_homodimer_dg': reverse_dg,
                    'primer_heterodimer_dg': hetero_dg,
                    'has_genbank': bool(vector.vector_gb)
                })

            return JsonResponse(response_data)

        except Vector.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '载体不存在'
            })

    return JsonResponse({'status': 'error', 'message': '仅支持GET请求'})


@login_required
def vector_automation_design_download(request, vector_id):
    """
    下载改造后的GenBank文件
    """
    try:
        vector = Vector.objects.get(user=request.user, id=vector_id)

        if not vector.vector_gb:
            return JsonResponse({
                'status': 'error',
                'message': '改造后的GenBank文件不存在'
            })

        # 返回文件
        response = HttpResponse(vector.vector_gb, content_type='application/octet-stream')
        filename = os.path.basename(vector.vector_gb.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Vector.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '载体不存在'
        })


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

def test_django_send(request):
    '''测试Django发送邮件'''
    if request.method == 'GET':
        send_mail(
            subject='Django 测试邮件',
            message='这是从 Django 发的测试邮件正文。',
            from_email=config('EMAIL_HOST_USER'),
            recipient_list=['dushiyi@rootpath.com.cn'],
            fail_silently=False
        )
        return HttpResponse('Email sent successfully')
