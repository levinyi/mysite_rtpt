"""
序列处理工具函数
这些函数用于序列分析、验证和状态判断
"""
import re
import pandas as pd
import numpy as np


def clean_and_check_dna_sequence(sequence):
    """
    清理DNA序列并检查非法碱基

    参数:
        sequence: DNA序列字符串

    返回:
        (cleaned_sequence, warnings): 清理后的序列和警告信息
    """
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


def check_forbidden_seq(seq, built_in_forbidden_list, customer_forbidden_list=None):
    """
    检查序列中的禁用序列

    参数:
        seq: DNA序列字符串
        built_in_forbidden_list: 内置禁用序列列表
        customer_forbidden_list: 用户自定义禁用序列列表（可选）

    返回:
        forbidden_positions: 禁用序列位置列表
    """
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


def process_contained_forbidden_list(row):
    """
    处理包含的禁用序列列表

    参数:
        row: DataFrame行数据

    返回:
        contained_forbidden_list: 禁用序列列表
    """
    # 获取 forbidden_info 中的 forbidden_seq 列表
    forbidden_seqs = [info['forbidden_seq'] for info in row.get('forbidden_info', [])] if row.get('forbidden_info') else []

    contained_forbidden_list = forbidden_seqs

    return contained_forbidden_list


def process_highlights_positions(row):
    """
    处理高亮位置

    参数:
        row: DataFrame行数据

    返回:
        highlights_positions: 高亮位置列表
    """
    highlights_positions = []

    # 定义一个正则表达式模式来提取所有数字
    pattern = r'\d+'

    def extract_field_numbers(item, field_name):
        match = re.search(rf'{field_name}\s*:\s*([^|]+)', item)
        if not match:
            return []
        return list(map(int, re.findall(pattern, match.group(1))))

    # 遍历每种分析类型以处理 start 和 end 位置
    for analysis_type in ['LongRepeats', 'Homopolymers', 'W12S12Motifs', 'HighGC', 'LowGC', 'DoubleNT',
                          'TandemRepeats', 'PalindromeRepeats', 'InvertedRepeats']:
        if analysis_type not in row:
            continue
        analysis_value = row[analysis_type]
        if not isinstance(analysis_value, str) or not analysis_value.strip():
            continue

        starts = extract_field_numbers(analysis_value, 'start')
        ends = extract_field_numbers(analysis_value, 'end')

        # 确保 starts 和 ends 长度相同
        for start, end in zip(starts, ends):
            highlights_positions.append({
                'start': start,
                'end': end,
                'type': analysis_type
            })

    # 处理 forbidden_info
    if 'forbidden_info' in row and row['forbidden_info']:
        for info in row['forbidden_info']:
            highlights_positions.append({
                'start': info['start'],
                'end': info['end'],
                'type': 'ForbiddenSeq',
                'content': info['forbidden_seq']
            })

    # 处理 Error (非法碱基)
    if 'Error' in row and row['Error']:
        for error in row['Error']:
            highlights_positions.append({
                'start': error['start'],
                'end': error['end'],
                'type': 'Error',
                'content': error['content']
            })

    return highlights_positions


def deal_repeats_warnings(row):
    """
    检查是否有重复序列警告

    参数:
        row: DataFrame行数据

    返回:
        bool: 是否有警告
    """
    for analysis_type in ['LongRepeats', 'Homopolymers', 'W12S12Motifs', 'HighGC', 'LowGC', 'DoubleNT',
                          'TandemRepeats', 'PalindromeRepeats', 'InvertedRepeats']:
        if analysis_type in row and row[analysis_type]:
            return True
    return False


def has_value(value):
    """
    判断值是否有效

    参数:
        value: 任意值

    返回:
        bool: 是否有有效值
    """
    if isinstance(value, (list, dict, set, np.ndarray)):
        return len(value) > 0
    elif isinstance(value, pd.Series):
        return value.any()
    elif pd.isna(value):
        return False
    elif isinstance(value, str):
        return bool(value.strip())
    return True


def process_status(row):
    """
    根据各种条件判断序列状态

    参数:
        row: DataFrame行数据

    返回:
        status: 序列状态 ('error', 'forbidden', 'warning', 'validated')
    """
    forbidden = has_value(row.get('contained_forbidden_list'))
    error = has_value(row.get('Error'))
    warning = has_value(row.get('warnings'))

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
