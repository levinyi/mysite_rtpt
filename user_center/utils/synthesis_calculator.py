"""
Synthesis Success Rate Calculator
计算基因合成成功率
"""
import math
import re
from typing import Dict, List, Tuple, Optional

# 常量定义
PRIMARY = {
    'LongRepeats': 0.998976679,
    'Homopolymers': 0.999381548,
    'W12S12Motifs': 0.996537999,
    'HighGC': 0.999716263,
    'LowGC': 0.999942378,
}

SECONDARY = {
    'LongRepeats': 0.999488209,
    'Homopolymers': 0.999690726,
    'W12S12Motifs': 0.998267499,
    'HighGC': 0.999858121,
    'LowGC': 0.999971189,
}

P0 = 0.99998363
FEATURES = list(PRIMARY.keys())


def parse_intervals(annotation_text: str) -> List[Tuple[int, int]]:
    """
    从注释文本中提取区间 (start, end)

    参数:
        annotation_text: 包含 start 和 end 信息的文本

    返回:
        区间列表 [(start1, end1), (start2, end2), ...]
    """
    if not annotation_text or not isinstance(annotation_text, str):
        return []

    starts = []
    ends = []

    # 提取 start 和 end
    start_chunks = re.findall(r'start:\s*(\[[^\]]+\]|[0-9]+)', annotation_text)
    end_chunks = re.findall(r'end:\s*(\[[^\]]+\]|[0-9]+)', annotation_text)

    for chunk in start_chunks:
        starts.extend([int(n) for n in re.findall(r'\d+', chunk)])

    for chunk in end_chunks:
        ends.extend([int(n) for n in re.findall(r'\d+', chunk)])

    intervals = []
    for s, e in zip(starts, ends):
        if e < s:
            s, e = e, s
        intervals.append((s, e))

    return intervals


def calculate_synthesis_success_rate(
    sequence: str,
    analysis_results: Optional[Dict] = None
) -> Optional[float]:
    """
    计算序列的合成成功率

    参数:
        sequence: DNA 序列字符串
        analysis_results: 序列分析结果 (JSON/dict 格式)

    返回:
        合成成功率 (0-1 之间的浮点数)，如果无法计算则返回 None
    """
    if not sequence or not isinstance(sequence, str):
        return None

    if not analysis_results:
        # 如果没有分析结果，返回基础成功率
        return P0 ** len(sequence)

    L = len(sequence)

    # 构建覆盖图: 每个碱基位置上有哪些特征
    coverage = [[] for _ in range(L)]

    # 提取每个特征的惩罚分数
    scores = {}
    for feature in FEATURES:
        penalty_key = f'{feature}_penalty_score'
        scores[feature] = analysis_results.get(penalty_key, 0.0) or 0.0

    # 为每个特征标记其覆盖的区间
    for feature in FEATURES:
        feature_annotation = analysis_results.get(feature)
        if not feature_annotation:
            continue

        intervals = parse_intervals(str(feature_annotation))
        for start, end in intervals:
            # 注意：区间是 1-based，需要转换为 0-based
            for i in range(max(0, start - 1), min(L, end)):
                coverage[i].append(feature)

    # 计算每个碱基的成功率
    log_prob = 0.0
    for features_at_pos in coverage:
        if not features_at_pos:
            # 没有特征的位置，使用基础成功率
            prob = P0
        else:
            # 找出惩罚分数最高的特征作为主要特征
            max_score = max(scores[f] for f in features_at_pos)
            primary_features = [f for f in features_at_pos if scores[f] == max_score]

            prob = 1.0
            # 主要特征使用 PRIMARY 成功率
            for f in primary_features:
                prob *= PRIMARY[f]

            # 次要特征使用 SECONDARY 成功率
            for f in features_at_pos:
                if f not in primary_features:
                    prob *= SECONDARY[f]

        log_prob += math.log(prob)

    return math.exp(log_prob)


def format_success_rate(rate: Optional[float], format_type: str = 'percentage') -> str:
    """
    格式化成功率显示

    参数:
        rate: 成功率 (0-1)
        format_type: 格式类型 ('percentage' 或 'decimal')

    返回:
        格式化后的字符串
    """
    if rate is None:
        return 'N/A'

    if format_type == 'percentage':
        return f'{rate * 100:.2f}%'
    else:
        return f'{rate:.4f}'


def get_success_rate_color_class(rate: Optional[float]) -> str:
    """
    根据成功率返回 CSS 颜色类名

    参数:
        rate: 成功率 (0-1)

    返回:
        CSS 类名
    """
    if rate is None:
        return 'text-secondary'

    if rate >= 0.95:
        return 'text-success'
    elif rate >= 0.85:
        return 'text-warning'
    else:
        return 'text-danger'
