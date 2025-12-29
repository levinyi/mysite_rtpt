"""
user_center模块的Celery异步任务
"""
import os
import time
import logging
import pandas as pd
import numpy as np
from celery import shared_task
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from product.models import Vector, Species
from user_center.models import GeneInfo, ProcessTask
from user_center.utils.vector_automation import VectorAutomationDesigner
from user_center.utils.sequence_fragmenter import fragment_sequence_by_penalty

logger = logging.getLogger(__name__)


@shared_task
def async_vector_automation_design(vector_id):
    """
    异步执行载体改造自动化设计任务

    Args:
        vector_id: Vector对象的ID

    Returns:
        dict: 设计结果
    """
    try:
        vector = Vector.objects.get(pk=vector_id)

        # 更新状态为Processing
        vector.design_status = 'Processing'
        vector.save()

        # 获取上传的GenBank文件路径
        genbank_file_path = vector.vector_file.path

        # 初始化设计器
        designer = VectorAutomationDesigner(genbank_file_path)

        # 1. 解析GenBank文件
        parsed_data = designer.parse_genbank()
        if not parsed_data:
            vector.design_status = 'Failed'
            vector.design_error = '; '.join(designer.errors)
            vector.save()
            return {'status': 'error', 'errors': designer.errors}

        # 保存iU20和iD20序列
        vector.iu20 = parsed_data['iu20_seq']
        vector.id20 = parsed_data['id20_seq']

        # 2. 选择克隆方法并设计v5NC和v3NC
        design_result = designer.select_cloning_method(parsed_data)
        if not design_result:
            vector.design_status = 'Failed'
            vector.design_error = '没有找到可用的克隆方法。' + '; '.join(designer.errors)
            vector.save()
            return {'status': 'error', 'errors': designer.errors}

        original_filename = os.path.basename(genbank_file_path)
        resistance = designer.extract_resistance_from_filename(original_filename)
        vector_code = designer.extract_vector_code_from_filename(original_filename)
        filename_suffix = designer.extract_filename_suffix(original_filename)
        if resistance:
            vector.vector_id = f"{vector_code}({resistance})"
        else:
            vector.vector_id = vector_code

        def append_error_message(message):
            if vector.design_error:
                vector.design_error = f"{vector.design_error.strip()} {message}"
            else:
                vector.design_error = message

        # 3. 设计NC-PCR引物（仅Gibson方法）
        primer_result = None
        if design_result['method'] == 'Gibson':
            primer_result = designer.design_nc_pcr_primers(design_result, parsed_data, vector_code=vector_code)
            if primer_result:
                forward = primer_result['forward']
                reverse = primer_result['reverse']
                vector.primer_forward = f"{forward['name']}::{forward['sequence']}"
                vector.primer_reverse = f"{reverse['name']}::{reverse['sequence']}"
                vector.primer_forward_tm = primer_result['forward']['tm']
                vector.primer_reverse_tm = primer_result['reverse']['tm']
            else:
                vector.primer_forward = None
                vector.primer_reverse = None
                vector.primer_forward_tm = None
                vector.primer_reverse_tm = None
                append_error_message('引物设计失败：无法在允许边界内找到满足T97=60℃的引物')
        else:
            vector.primer_forward = None
            vector.primer_reverse = None
            vector.primer_forward_tm = None
            vector.primer_reverse_tm = None

        # 保存设计结果（在引物设计后，可能已调整边界）
        vector.cloning_method = design_result['method']
        vector.NC5 = design_result['v5nc']
        vector.NC3 = design_result['v3nc']
        vector.i5NC = design_result.get('i5nc', '')
        vector.i3NC = design_result.get('i3nc', '')

        # 4. 生成改造后GenBank文件
        # 构建输出文件名
        if resistance:
            output_filename = f"{vector_code}M1({resistance})-{filename_suffix}-M1.gb"
        else:
            output_filename = f"{vector_code}M1-{filename_suffix}-M1.gb"
            append_error_message('未在文件名中找到抗性信息')

        # 生成临时输出路径
        output_dir = os.path.dirname(genbank_file_path)
        output_path = os.path.join(output_dir, output_filename)

        # 生成GenBank文件
        designer.generate_modified_genbank(
            design_result,
            parsed_data,
            primer_result,
            output_path,
            output_filename.replace('.gb', '')
        )

        # 保存到vector_gb字段
        with open(output_path, 'rb') as f:
            vector.vector_gb.save(output_filename, File(f), save=False)

        # 保存载体序列（without v5NC/v3NC之间的序列）
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]
        vector_without_insert = parsed_data['sequence'][:v5nc_end] + parsed_data['sequence'][v3nc_start:]
        vector.vector_map = vector_without_insert

        # 更新状态为Completed，并标记为可用
        vector.design_status = 'Completed'
        vector.status = 'ReadyToUse'
        vector.save()

        forward_name = None
        forward_seq = None
        reverse_name = None
        reverse_seq = None
        if vector.primer_forward and '::' in vector.primer_forward:
            forward_name, forward_seq = vector.primer_forward.split('::', 1)
        else:
            forward_seq = vector.primer_forward
        if vector.primer_reverse and '::' in vector.primer_reverse:
            reverse_name, reverse_seq = vector.primer_reverse.split('::', 1)
        else:
            reverse_seq = vector.primer_reverse

        return {
            'status': 'success',
            'method': design_result['method'],
            'v5nc': design_result['v5nc'],
            'v3nc': design_result['v3nc'],
            'i5nc': design_result.get('i5nc', ''),
            'i3nc': design_result.get('i3nc', ''),
            'primer_forward_name': forward_name,
            'primer_forward': forward_seq,
            'primer_reverse_name': reverse_name,
            'primer_reverse': reverse_seq,
            'output_file': output_filename
        }

    except Vector.DoesNotExist:
        return {'status': 'error', 'errors': ['Vector对象不存在']}
    except Exception as e:
        # 捕获所有异常
        try:
            vector = Vector.objects.get(pk=vector_id)
            vector.design_status = 'Failed'
            vector.design_error = f'系统错误: {str(e)}'
            vector.save()
        except:
            pass

        return {'status': 'error', 'errors': [f'系统错误: {str(e)}']}


@shared_task(bind=True)
def async_fragment_genes(self, gene_ids):
    """
    异步执行基因序列片段切割任务

    Args:
        self: Celery task instance (bind=True)
        gene_ids: 需要切割的基因ID列表

    Returns:
        dict: 处理结果
    """
    from django.core.cache import cache

    task_id = self.request.id
    logger.info(f"Starting async fragmentation for {len(gene_ids)} genes (task_id: {task_id})")

    # 在缓存中存储任务状态
    cache_key = f'fragment_task_{task_id}'
    cache.set(cache_key, {
        'status': 'processing',
        'total': len(gene_ids),
        'completed': 0,
        'gene_ids': gene_ids
    }, timeout=3600)  # 1小时过期

    try:
        from user_center.models import GeneInfo

        # 获取需要切割的基因
        genes = GeneInfo.objects.filter(id__in=gene_ids).select_related('vector')

        success_count = 0
        fail_count = 0

        for idx, gene in enumerate(genes):
            try:
                if not gene.penalty_score or gene.penalty_score <= 28:
                    logger.info(f"Gene {gene.gene_name} (ID: {gene.id}) penalty score {gene.penalty_score} <= 28, skipping")
                    continue

                # 获取载体的克隆方法
                cloning_method = gene.vector.cloning_method if gene.vector and gene.vector.cloning_method else "Gibson"

                # 执行片段切割
                fragmentation_result = fragment_sequence_by_penalty(
                    sequence=gene.combined_seq,
                    cloning_method=cloning_method,
                    max_penalty=28.0
                )

                if fragmentation_result and fragmentation_result.get('need_fragmentation'):
                    # 更新基因的 fragments_data
                    gene.fragments_data = fragmentation_result
                    gene.save(update_fields=['fragments_data'])
                    success_count += 1
                    logger.info(
                        f"Gene {gene.gene_name} (ID: {gene.id}, penalty: {gene.penalty_score}) "
                        f"fragmented into {fragmentation_result.get('total_fragments', 0)} pieces using {fragmentation_result.get('cloning_method')}"
                    )
                else:
                    logger.info(f"Gene {gene.gene_name} (ID: {gene.id}) penalty recalculated, no fragmentation needed")

            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to fragment gene {gene.gene_name} (ID: {gene.id}): {str(e)}", exc_info=True)

            # 更新缓存中的进度
            cache.set(cache_key, {
                'status': 'processing',
                'total': len(genes),
                'completed': idx + 1,
                'gene_ids': gene_ids,
                'success': success_count,
                'failed': fail_count
            }, timeout=3600)

        logger.info(f"Fragmentation completed: {success_count} success, {fail_count} failed out of {len(genes)} genes")

        # 更新缓存为完成状态
        cache.set(cache_key, {
            'status': 'completed',
            'total': len(genes),
            'completed': len(genes),
            'gene_ids': gene_ids,
            'success': success_count,
            'failed': fail_count
        }, timeout=3600)

        return {
            'status': 'success',
            'total': len(genes),
            'success': success_count,
            'failed': fail_count
        }

    except Exception as e:
        logger.error(f"Error in async_fragment_genes: {str(e)}", exc_info=True)

        # 更新缓存为失败状态
        cache.set(cache_key, {
            'status': 'failed',
            'total': len(gene_ids),
            'completed': 0,
            'gene_ids': gene_ids,
            'error': str(e)
        }, timeout=3600)

        return {'status': 'error', 'error': str(e)}


@shared_task(bind=True)
def async_process_gene_sequences(self, process_task_id, user_id, vector_id, species_id, df_dict):
    """
    异步处理基因序列并保存到购物车

    Args:
        self: Celery task instance (bind=True)
        process_task_id: ProcessTask对象的ID
        user_id: 用户ID
        vector_id: Vector对象的ID
        species_id: Species对象的ID (可以为None)
        df_dict: DataFrame转换为字典格式 (使用df.to_dict('records'))

    Returns:
        dict: 处理结果
    """
    from django.contrib.auth.models import User
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import sys
    import os

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
        process_highlights_positions
    )

    try:
        # 获取ProcessTask对象
        process_task = ProcessTask.objects.get(pk=process_task_id)
        process_task.status = 'processing'
        process_task.save()

        # 获取相关对象
        user = User.objects.get(pk=user_id)
        vector = Vector.objects.get(pk=vector_id)
        species = Species.objects.get(pk=species_id) if species_id else None

        # 获取或创建购物车
        from user_center.models import Cart
        cart, created = Cart.objects.get_or_create(user=user)

        # 将字典转换回DataFrame
        df = pd.DataFrame(df_dict)
        total_sequences = len(df)
        process_task.total = total_sequences
        process_task.save()

        logger.info(f"Starting async processing of {total_sequences} sequences for user {user.username}")

        # 计算GC含量
        def calc_gc_content(seq):
            upper_seq = seq.upper()
            return round((upper_seq.count('G') + upper_seq.count('C')) / len(seq) * 100, 2) if len(seq) > 0 else 0

        df['original_gc_content'] = df['OriginalSeq'].apply(calc_gc_content)
        df['modified_gc_content'] = df['CombinedSeq'].apply(calc_gc_content)

        # 清理序列并检查是否包含非法碱基
        from user_center.utils.sequence_processing import clean_and_check_dna_sequence
        df['CombinedSeq'], df['Error'] = zip(*df['CombinedSeq'].apply(clean_and_check_dna_sequence))

        # 1. Forbidden sequence检查
        built_in_forbidden_list = [
            'GAAGAC', 'GGTCTC', 'CGTCTC', 'CACCTGC', 'GCAGGTG',
            'CTGCAG', 'CTCGAG', 'AGATCT', 'ACTAGT', 'TCTAGA',
            'GGATCC', 'GAATTC', 'GCGGCCGC', 'TTAATTAA'
        ]

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

        if len(df) > 10:
            df['forbidden_info'] = check_forbidden_parallel(df['CombinedSeq'].tolist(), built_in_forbidden_list)
        else:
            df['forbidden_info'] = df['CombinedSeq'].apply(
                lambda seq: check_forbidden_seq(seq, built_in_forbidden_list)
            )

        # 更新进度: 20%
        process_task.progress = int(total_sequences * 0.2)
        process_task.save()

        # 2. Repeats分析
        df['gene_id'] = df['GeneName']
        df['sequence'] = df['CombinedSeq']
        data_json = convert_gene_table_to_RepeatsFinder_Format(df)
        result_df = process_gene_table_results(data_json)

        feature_columns = [
            'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score',
            'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
            'TandemRepeats_penalty_score', 'PalindromeRepeats_penalty_score', 'InvertedRepeats_penalty_score'
        ]
        result_df['total_penalty_score'] = sum(result_df[col] for col in feature_columns).round(2)
        df = df.merge(result_df, left_on='GeneName', right_on='GeneName', how='left')

        # 更新进度: 50%
        process_task.progress = int(total_sequences * 0.5)
        process_task.save()

        # 3. 整合数据
        df['contained_forbidden_list'] = df.apply(process_contained_forbidden_list, axis=1)
        df['highlights_positions'] = df.apply(lambda row: process_highlights_positions(row), axis=1)
        df['saved_seq'] = df['OriginalSeq']
        df['warnings'] = df.apply(deal_repeats_warnings, axis=1)
        df['status'] = df.apply(process_status, axis=1)

        # 更新进度: 70%
        process_task.progress = int(total_sequences * 0.7)
        process_task.save()

        # 4. 创建GeneInfo对象
        gene_objects = []
        for idx, row in df.iterrows():
            gene_id = row['gene_id']
            analysis_results = data_json.get(gene_id, {})

            # 标记优化状态
            if row['status'] == 'forbidden':
                optimization_status = 'NeedsOptimization'
            elif row['status'] == 'error':
                optimization_status = 'Error'
            elif row['status'] == 'warning':
                optimization_status = 'NotOptimized'
            else:
                optimization_status = 'NotOptimized'

            # 检查是否需要切割
            total_penalty = row.get('total_penalty_score', 0)
            fragments_data = None
            if total_penalty and total_penalty > 28:
                try:
                    cloning_method = vector.cloning_method if vector.cloning_method else "Gibson"
                    fragmentation_result = fragment_sequence_by_penalty(
                        sequence=row['CombinedSeq'],
                        cloning_method=cloning_method,
                        max_penalty=28.0
                    )

                    if fragmentation_result and fragmentation_result.get('need_fragmentation'):
                        fragments_data = fragmentation_result
                        logger.info(f"Gene {gene_id} fragmented into {fragmentation_result.get('total_fragments', 0)} pieces")
                except Exception as e:
                    logger.error(f"Failed to fragment gene {gene_id}: {str(e)}")
                    fragments_data = None

            # 转换 NumPy 类型为 Python 原生类型
            def safe_convert(value):
                """安全转换值，处理 NumPy 类型"""
                if pd.isna(value):
                    return None
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    return int(value)
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    return float(value)
                elif isinstance(value, np.ndarray):
                    return value.tolist()
                else:
                    return value

            # 创建GeneInfo对象
            gene_objects.append(
                GeneInfo(
                    user=user,
                    gene_name=str(gene_id),
                    original_seq=str(row['OriginalSeq']),
                    vector=vector,
                    species=species,
                    status=str(row.get('status', 'validated')),
                    forbid_seq=str(row.get('forbidden_check_list', '')),
                    combined_seq=str(row['CombinedSeq']),
                    i5nc=str(row.get('i5nc', '')),
                    i3nc=str(row.get('i3nc', '')),
                    saved_seq=str(row.get('saved_seq', '')),
                    forbidden_check_list=str(row.get('forbidden_check_list', '')),
                    contained_forbidden_list=row.get('contained_forbidden_list', []),
                    original_gc_content=safe_convert(row.get('original_gc_content', '')),
                    modified_gc_content=safe_convert(row.get('modified_gc_content', '')),
                    original_highlights=row.get('highlights_positions', []),
                    modified_highlights=row.get('highlights_positions', []),
                    penalty_score=safe_convert(row.get('total_penalty_score', None)),
                    seq_type='NT',
                    optimization_status=optimization_status,
                    analysis_results=analysis_results,
                    fragments_data=fragments_data
                )
            )

            # 更新进度
            process_task.progress = int(total_sequences * 0.7) + int((idx + 1) / total_sequences * 0.2 * total_sequences)
            process_task.save()

        # 5. 批量保存
        current_timestamp = timezone.now()
        with transaction.atomic():
            GeneInfo.objects.bulk_create(gene_objects)

            gene_objects_with_ids = GeneInfo.objects.select_related('vector', 'species').filter(
                user=user,
                gene_name__in=df['gene_id'],
                create_date__gte=current_timestamp
            )

            # 保存gene_ids到ProcessTask
            gene_ids = list(gene_objects_with_ids.values_list('id', flat=True))
            process_task.gene_ids = gene_ids

            # 添加到购物车
            cart.genes.add(*gene_objects_with_ids)

        # 更新任务状态为完成
        process_task.status = 'completed'
        process_task.progress = total_sequences
        process_task.completed_at = timezone.now()
        process_task.save()

        logger.info(f"Successfully processed {total_sequences} sequences for user {user.username}")

        return {
            'status': 'success',
            'total_processed': total_sequences,
            'gene_ids': gene_ids
        }

    except ProcessTask.DoesNotExist:
        logger.error(f"ProcessTask {process_task_id} does not exist")
        return {'status': 'error', 'error': 'ProcessTask不存在'}

    except Exception as e:
        logger.error(f"Error processing sequences: {str(e)}", exc_info=True)

        # 更新任务状态为失败
        try:
            process_task = ProcessTask.objects.get(pk=process_task_id)
            process_task.status = 'failed'
            process_task.error_message = str(e)
            process_task.save()
        except:
            pass

        return {'status': 'error', 'error': str(e)}
