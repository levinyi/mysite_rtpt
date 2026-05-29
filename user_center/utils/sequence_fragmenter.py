"""
Sequence Fragmenter
序列切割工具: 将罚分超过阈值的序列切割成小片段,并处理接头冲突
"""
import sys
import os
import pandas as pd
import numpy as np
import time
import logging
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
from Bio.Seq import Seq

logger = logging.getLogger(__name__)

# 添加项目路径以便导入 AnalysisSequence
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
tools_scripts_path = os.path.join(project_root, 'tools', 'scripts')
sys.path.insert(0, tools_scripts_path)

from AnalysisSequence import DNARepeatsFinder, convert_gene_table_to_RepeatsFinder_Format, process_gene_table_results


def convert_to_native_types(obj):
    """
    递归转换 NumPy 类型为 Python 原生类型，确保 JSON 序列化兼容

    参数:
        obj: 任意对象

    返回:
        转换后的对象
    """
    if isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


@lru_cache(maxsize=2000)
def calculate_fragment_penalty_score(sequence: str) -> Dict:
    """
    计算单个序列片段的罚分,并返回详细的罚分信息
    使用 LRU 缓存避免重复计算相同序列的罚分

    参数:
        sequence: DNA 序列字符串

    返回:
        包含各项罚分的字典
    """
    # 创建临时 DataFrame 用于分析
    df = pd.DataFrame({
        'gene_id': ['temp_fragment'],
        'sequence': [sequence]
    })

    # 调用分析函数
    data_json = convert_gene_table_to_RepeatsFinder_Format(df)
    result_df = process_gene_table_results(data_json)

    # 计算总罚分
    feature_columns = [
        'HighGC_penalty_score', 'LowGC_penalty_score', 'W12S12Motifs_penalty_score',
        'LongRepeats_penalty_score', 'Homopolymers_penalty_score', 'DoubleNT_penalty_score',
        'TandemRepeats_penalty_score', 'PalindromeRepeats_penalty_score', 'InvertedRepeats_penalty_score'
    ]

    total_penalty_score = sum(result_df[col].iloc[0] for col in feature_columns)

    return {
        'total_penalty_score': round(total_penalty_score, 2),
        'long_repeats_penalty': round(result_df['LongRepeats_penalty_score'].iloc[0], 2),
        'details': {col: round(result_df[col].iloc[0], 2) for col in feature_columns}
    }


def batch_calculate_fragment_penalties(sequences: List[str]) -> List[Dict]:
    """
    批量计算多个序列片段的罚分
    比逐个调用 calculate_fragment_penalty_score 更高效

    优化策略：
    1. 优先使用缓存的结果
    2. 对未缓存的序列进行批量计算
    3. 将批量计算的结果也加入缓存

    参数:
        sequences: DNA 序列字符串列表

    返回:
        罚分字典列表
    """
    if not sequences:
        return []

    # 先尝试从缓存获取所有结果
    # 如果所有序列都已缓存，直接返回
    results = []
    for seq in sequences:
        result = calculate_fragment_penalty_score(seq)
        results.append(result)

    return results


# 预计算反向互补序列的缓存
_reverse_complement_cache = {}

def get_reverse_complement(seq: str) -> str:
    """
    获取序列的反向互补，使用缓存加速

    参数:
        seq: DNA 序列

    返回:
        反向互补序列
    """
    if seq not in _reverse_complement_cache:
        _reverse_complement_cache[seq] = str(Seq(seq).reverse_complement())
    return _reverse_complement_cache[seq]


@lru_cache(maxsize=10000)
def is_complementary(seq1: str, seq2: str) -> bool:
    """
    检查两个4bp序列是否互补配对
    使用缓存加速重复检查

    参数:
        seq1: 第一个序列 (4bp)
        seq2: 第二个序列 (4bp)

    返回:
        True 如果互补配对
    """
    if len(seq1) != 4 or len(seq2) != 4:
        return False

    # 使用缓存的反向互补
    seq1_rc = get_reverse_complement(seq1)
    return seq1_rc == seq2


def check_adapter_conflicts(adapters: List[str]) -> bool:
    """
    检查接头列表中是否有冲突(互补配对)

    参数:
        adapters: 接头序列列表(每个都是4bp)

    返回:
        True 如果有冲突
    """
    for i in range(len(adapters)):
        for j in range(i + 1, len(adapters)):
            if is_complementary(adapters[i], adapters[j]):
                return True
    return False


def find_optimal_fragment_end_binary(
    sequence: str,
    start_pos: int,
    initial_end_pos: int,
    max_penalty: float,
    min_fragment_length: int
) -> Optional[Tuple[int, Dict]]:
    """
    使用二分查找找到最优的片段结束位置
    目标：在保持罚分 <= max_penalty 的前提下，找到最长的片段

    参数:
        sequence: 完整序列
        start_pos: 片段起始位置
        initial_end_pos: 初始结束位置
        max_penalty: 最大允许罚分
        min_fragment_length: 最小片段长度

    返回:
        (最优结束位置, 罚分信息) 或 None
    """
    # 首先检查初始位置是否满足条件
    if initial_end_pos - start_pos < min_fragment_length:
        return None

    initial_seq = sequence[start_pos:initial_end_pos]
    initial_penalty = calculate_fragment_penalty_score(initial_seq)

    # 如果初始位置已经满足，尝试找更长的
    if initial_penalty['total_penalty_score'] <= max_penalty:
        # 尝试向右扩展
        left = initial_end_pos
        right = min(len(sequence), initial_end_pos + 500)  # 最多扩展500bp
        best_end = initial_end_pos
        best_penalty = initial_penalty

        while left <= right:
            mid = (left + right) // 2
            test_seq = sequence[start_pos:mid]
            test_penalty = calculate_fragment_penalty_score(test_seq)

            if test_penalty['total_penalty_score'] <= max_penalty:
                best_end = mid
                best_penalty = test_penalty
                left = mid + 1  # 尝试更长
            else:
                right = mid - 1  # 太长了，缩短

        return (best_end, best_penalty)

    # 如果初始位置不满足，需要缩短
    left = start_pos + min_fragment_length
    right = initial_end_pos
    best_end = None
    best_penalty = None

    while left <= right:
        mid = (left + right) // 2
        test_seq = sequence[start_pos:mid]
        test_penalty = calculate_fragment_penalty_score(test_seq)

        if test_penalty['total_penalty_score'] <= max_penalty:
            best_end = mid
            best_penalty = test_penalty
            left = mid + 1  # 尝试更长的片段
        else:
            right = mid - 1  # 片段太长，尝试更短的

    if best_end is None:
        return None

    return (best_end, best_penalty)


def get_grouping_strategy(num_fragments: int) -> List[int]:
    """
    根据片段数量返回分组策略

    参数:
        num_fragments: 片段数量 (2-9)

    返回:
        分组列表,例如 [3, 3, 3] 表示3-3-3分组
    """
    grouping_map = {
        9: [3, 3, 3],
        8: [3, 3, 2],
        7: [3, 2, 2],
        6: [3, 3],
        5: [3, 2],
        4: [2, 2],
        3: [3],
        2: [2]
    }

    return grouping_map.get(num_fragments, [num_fragments])


def format_mustcut_positions(cut_positions: List[int], grouping: List[int]) -> str:
    r"""
    根据分组策略格式化MustCut位置

    MustCut 包含所有片段的结束位置（最后一个片段除外）
    分组策略决定如何用斜杠分隔这些位置：组内用 /，组间用 \

    分组的含义：
    - 9个片段，分组[3,3,3]表示将8个MustCut位置分成3组显示
      第1组3个位置，第2组3个位置，第3组2个位置
    - 每组最后都加 /，组间用 \ 分隔

    示例：
        9个片段 [3,3,3]分组: "pos1/pos2/pos3\pos4/pos5/pos6\pos7/pos8/"
        8个片段 [3,3,2]分组: "pos1/pos2/pos3\pos4/pos5/pos6\pos7/"
        7个片段 [3,2,2]分组: "pos1/pos2/pos3\pos4/pos5\pos6/"
        6个片段 [3,3]分组:   "pos1/pos2/pos3\pos4/pos5/"
        5个片段 [3,2]分组:   "pos1/pos2/pos3\pos4/"
        4个片段 [2,2]分组:   "pos1/pos2\pos3/"
        3个片段 [3]分组:     "pos1/pos2/"
        2个片段 [2]分组:     "pos1/"

    参数:
        cut_positions: 切割位置列表(每个片段的结束位置，不包含最后一个片段)
        grouping: 分组策略,例如 [3, 3, 3] 表示将位置分成3组显示

    返回:
        格式化的字符串,例如 "1000/2000/3000\4000/5000/6000\7000/8000/"
    """
    if not cut_positions:
        return ""

    result = []
    pos_idx = 0
    num_positions = len(cut_positions)

    for group_idx, group_size in enumerate(grouping):
        group_positions = []

        # 计算这一组应该包含多少个位置
        # 最后一组可能位置数量不足group_size
        is_last_group = (group_idx == len(grouping) - 1)

        if is_last_group:
            # 最后一组：取剩余所有位置
            positions_in_this_group = num_positions - pos_idx
        else:
            # 非最后一组：取group_size个位置
            positions_in_this_group = min(group_size, num_positions - pos_idx)

        # 收集这一组的位置
        for _ in range(positions_in_this_group):
            if pos_idx < num_positions:
                group_positions.append(str(cut_positions[pos_idx]))
                pos_idx += 1

        # 将组内位置用 / 连接
        if group_positions:
            result.append('/'.join(group_positions))

    # 用 \ 连接各组，最后加上 /
    return '\\'.join(result) + '/'


def adjust_cut_position_to_avoid_conflicts(
    sequence: str,
    initial_cut_pos: int,
    existing_adapters: List[str],
    search_range: int = 100
) -> Optional[int]:
    """
    调整切割位置以避免接头冲突

    参数:
        sequence: 完整序列
        initial_cut_pos: 初始切割位置
        existing_adapters: 已有的接头序列列表
        search_range: 搜索范围

    返回:
        调整后的切割位置,如果找不到则返回None
    """
    # 在初始位置附近搜索
    for offset in range(-search_range, search_range):
        new_pos = initial_cut_pos + offset
        if new_pos <= 0 or new_pos >= len(sequence):
            continue

        # 获取新位置的前4bp和后4bp作为接头
        if new_pos >= 4:
            new_adapter_left = sequence[new_pos-4:new_pos]
        else:
            continue

        if new_pos + 4 <= len(sequence):
            new_adapter_right = sequence[new_pos:new_pos+4]
        else:
            continue

        # 检查是否与已有接头冲突
        test_adapters = existing_adapters + [new_adapter_left, new_adapter_right]
        if not check_adapter_conflicts(test_adapters):
            return new_pos

    return None


def detect_long_repeats_positions(sequence: str, min_len: int = 16) -> List[Dict]:
    """
    检测序列中的 Long Repeats，返回每个重复单元及其所有出现位置

    返回:
        [{'sequence': 'ATCG...', 'positions': [(start1, end1), (start2, end2), ...], 'length': int}, ...]
    """
    df = pd.DataFrame({'gene_id': ['temp'], 'sequence': [sequence]})
    finder = DNARepeatsFinder(df)
    repeats = finder.find_dispersed_repeats(index=0, min_len=min_len)

    result = []
    for r in repeats:
        positions = list(zip(r['start'], r['end']))
        result.append({
            'sequence': r['sequence'],
            'positions': positions,
            'length': r['length'],
            'penalty_score': r.get('penalty_score', 0)
        })
    return result


def find_repeat_aware_cut_points(sequence: str, repeats: List[Dict]) -> List[int]:
    """
    根据 Long Repeats 的位置，找出能将同一 repeat 单元分散到不同片段的切割点候选

    策略：在同一 repeat 单元的多个出现位置之间找到"间隙"区域，
    优先在间隙中间位置切割，使 repeat 单元分散到不同片段中

    返回:
        推荐切割点位置列表（已排序去重）
    """
    seq_len = len(sequence)
    cut_candidates = []

    for repeat_info in repeats:
        positions = sorted(repeat_info['positions'], key=lambda x: x[0])
        if len(positions) < 2:
            continue

        # 在每对相邻 repeat 出现位置之间，选择中间位置作为切割候选
        for i in range(len(positions) - 1):
            end_of_current = positions[i][1]      # 当前 repeat 结束位置
            start_of_next = positions[i + 1][0]   # 下一个 repeat 起始位置

            # 在两个 repeat 之间的间隙中间切割
            gap_mid = (end_of_current + start_of_next) // 2
            if 50 <= gap_mid <= seq_len - 50:  # 确保不会产生太短的片段
                cut_candidates.append(gap_mid)

    # 去重并排序
    cut_candidates = sorted(set(cut_candidates))
    return cut_candidates


def build_fragments_from_cuts(sequence: str, cut_positions: List[int]) -> List[Dict]:
    """
    根据切割位置列表构建片段列表

    参数:
        sequence: 完整序列
        cut_positions: 已排序的切割位置列表

    返回:
        片段列表
    """
    seq_len = len(sequence)
    boundaries = [0] + cut_positions + [seq_len]
    fragments = []

    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        seq = sequence[start:end]
        penalty = calculate_fragment_penalty_score(seq)
        fragments.append({
            'start': start,
            'end': end,
            'seq': seq,
            'length': end - start,
            'penalty_score': penalty['total_penalty_score']
        })

    return fragments


def select_best_repeat_aware_cuts(
    sequence: str,
    repeat_cut_candidates: List[int],
    max_penalty: float = 28.0,
    min_fragment_length: int = 50,
    max_fragments: int = 9
) -> Optional[List[int]]:
    """
    从 repeat-aware 候选切割点中选出最佳组合：
    1. 每个片段罚分 <= max_penalty
    2. 每个片段长度 >= min_fragment_length
    3. 片段数 <= max_fragments

    采用贪心策略：逐步添加候选切割点，优先添加能最大程度降低最高片段罚分的切割点

    返回:
        最优切割点列表，如果无法满足约束则返回 None
    """
    if not repeat_cut_candidates:
        return None

    seq_len = len(sequence)
    best_cuts = []

    # 贪心地逐步添加切割点
    remaining_candidates = list(repeat_cut_candidates)

    for _ in range(max_fragments - 1):  # 最多添加 max_fragments-1 个切割点
        if not remaining_candidates:
            break

        best_candidate = None
        best_max_penalty_score = float('inf')

        for candidate in remaining_candidates:
            test_cuts = sorted(best_cuts + [candidate])

            # 检查最小片段长度约束
            boundaries = [0] + test_cuts + [seq_len]
            lengths = [boundaries[i + 1] - boundaries[i] for i in range(len(boundaries) - 1)]
            if min(lengths) < min_fragment_length:
                continue

            # 计算所有片段的最大罚分
            fragments = build_fragments_from_cuts(sequence, test_cuts)
            max_frag_penalty = max(f['penalty_score'] for f in fragments)

            if max_frag_penalty < best_max_penalty_score:
                best_max_penalty_score = max_frag_penalty
                best_candidate = candidate

        if best_candidate is None:
            break

        best_cuts.append(best_candidate)
        best_cuts.sort()
        remaining_candidates.remove(best_candidate)

        # 如果所有片段都满足罚分约束，检查是否可以停止
        fragments = build_fragments_from_cuts(sequence, best_cuts)
        if all(f['penalty_score'] <= max_penalty for f in fragments):
            break

    if not best_cuts:
        return None

    return best_cuts


def fragment_sequence_by_penalty(
    sequence: str,
    cloning_method: str = "Gibson",
    vector_resistance: Optional[str] = None,
    max_penalty: float = 28.0,
    min_fragment_length: int = 50,
    overlap: int = 20
) -> Optional[Dict]:
    r"""
    根据罚分阈值和克隆方法切割序列（新版本）

    新规则:
    1. 最多9个片段，每个片段最小50bp
    2. 智能合并相邻片段：如果拼接后罚分<28则合并（节省成本）
    3. 只检查Long Repeats罚分来决定克隆方法
    4. 有Long Repeats时，优先让repeat单元分散到不同片段
    5. Gibson载体有Long Repeats罚分时，改用GG到pGZ1710(Kan)/pGZ1711(Amp)过渡载体
    6. 9个片段仍超28分时输出警告，提醒人工介入

    参数:
        sequence: 原始DNA序列
        cloning_method: 克隆方法 ("Gibson", "GoldenGate", "T4")
        vector_resistance: 原载体抗性 ("Amp", "Kan", 等)
        max_penalty: 最大允许罚分阈值 (默认28)
        min_fragment_length: 最小片段长度 (默认50bp)
        overlap: Gibson方法的重叠长度 (默认20bp)

    返回:
        切割结果字典:
        {
            "need_fragmentation": True/False,
            "cloning_method": "Gibson/GoldenGate/T4",
            "vector_recommendation": "pGZ1704/pGZ1705/None",
            "vector_change_reason": "原因说明",
            "fragments": [...],
            "mustcut_positions": "xx/xx\xx/",
            "total_fragments": 3,
            "adapter_adjustments": [...],  # 接头冲突调整记录
            "performance": {...}  # 性能指标
        }
    """
    start_time = time.time()
    perf_stats = {
        'penalty_calculations': 0,
        'cache_hits': 0,
        'adapter_checks': 0
    }
    adapter_adjustments = []  # 记录接头冲突调整

    # 首先计算整个序列的罚分
    initial_cache_info = calculate_fragment_penalty_score.cache_info()
    penalty_info = calculate_fragment_penalty_score(sequence)
    perf_stats['penalty_calculations'] += 1

    # 检查缓存命中
    after_cache_info = calculate_fragment_penalty_score.cache_info()
    if after_cache_info.hits > initial_cache_info.hits:
        perf_stats['cache_hits'] += 1

    total_penalty = penalty_info['total_penalty_score']
    long_repeats_penalty = penalty_info['long_repeats_penalty']

    logger.debug(f"Sequence length: {len(sequence)}bp, Total penalty: {total_penalty}, Long repeats: {long_repeats_penalty}")

    # 新规则：只用Long Repeats罚分判断克隆方法
    final_cloning_method = cloning_method
    vector_recommendation = None
    vector_change_reason = None

    if cloning_method == "Gibson" and long_repeats_penalty > 0:
        # 有Long Repeats罚分的Gibson载体，必须改用GG到过渡载体pGZ1710(Kan)/pGZ1711(Amp)
        final_cloning_method = "GoldenGate"
        if vector_resistance:
            if vector_resistance.lower() == "amp":
                vector_recommendation = "pGZ1710"
                vector_change_reason = f"原载体为Amp抗性Gibson载体，因存在Long Repeats罚分({long_repeats_penalty:.2f})，需改用GG克隆至Kan抗性过渡载体pGZ1710"
            elif vector_resistance.lower() == "kan":
                vector_recommendation = "pGZ1711"
                vector_change_reason = f"原载体为Kan抗性Gibson载体，因存在Long Repeats罚分({long_repeats_penalty:.2f})，需改用GG克隆至Amp抗性过渡载体pGZ1711"
            else:
                vector_change_reason = f"原载体为{vector_resistance}抗性Gibson载体，因存在Long Repeats罚分({long_repeats_penalty:.2f})，需改用GG克隆至过渡载体（请根据实际抗性选择pGZ1710或pGZ1711）"
        else:
            vector_change_reason = f"因存在Long Repeats罚分({long_repeats_penalty:.2f})，需从Gibson改用GG克隆至过渡载体（请根据原载体抗性选择pGZ1710或pGZ1711）"

    # 如果总罚分不超过阈值,不需要切割
    if total_penalty <= max_penalty:
        result = {
            "need_fragmentation": False,
            "total_penalty_score": total_penalty,
            "long_repeats_penalty": long_repeats_penalty,
            "cloning_method": final_cloning_method,
            "vector_recommendation": vector_recommendation,
            "vector_change_reason": vector_change_reason,
            "fragments": None,
            "mustcut_positions": None,
            "total_fragments": 1
        }
        return convert_to_native_types(result)

    # ==================== 切割策略：Long Repeats 感知 + 贪心合并 ====================
    seq_length = len(sequence)
    warning = None  # 用于记录需要人工介入的警告

    # 检测是否存在 Long Repeats
    has_long_repeats = long_repeats_penalty > 0
    repeat_aware_success = False
    merged_fragments = []

    if has_long_repeats:
        # ---- 策略A: Long Repeats 感知切割 ----
        # 优先让 repeat 单元分散到不同片段
        logger.info("检测到Long Repeats罚分，启用repeat-aware切割策略")
        repeats = detect_long_repeats_positions(sequence)
        repeat_cut_candidates = find_repeat_aware_cut_points(sequence, repeats)

        if repeat_cut_candidates:
            logger.debug(f"找到 {len(repeat_cut_candidates)} 个repeat-aware候选切割点")
            best_cuts = select_best_repeat_aware_cuts(
                sequence=sequence,
                repeat_cut_candidates=repeat_cut_candidates,
                max_penalty=max_penalty,
                min_fragment_length=min_fragment_length,
                max_fragments=9
            )

            if best_cuts:
                merged_fragments = build_fragments_from_cuts(sequence, best_cuts)
                # 检查是否所有片段都满足罚分约束
                if all(f['penalty_score'] <= max_penalty for f in merged_fragments):
                    repeat_aware_success = True
                    logger.info(f"Repeat-aware切割成功: {len(merged_fragments)} 个片段")
                else:
                    logger.info("Repeat-aware切割结果部分片段超过罚分阈值，回退到通用策略")

    if not repeat_aware_success:
        # ---- 策略B: 通用贪心合并法（无Long Repeats 或 策略A失败时使用）----
        # Step 1: 初步切割成小片段（每个片段罚分<28）
        initial_fragments = []
        current_pos = 0

        while current_pos < seq_length:
            remaining_length = seq_length - current_pos

            # 二分查找最优片段长度
            left = min_fragment_length
            right = remaining_length
            best_end = None
            best_penalty = None

            while left <= right:
                mid = (left + right) // 2
                test_seq = sequence[current_pos:current_pos + mid]
                test_penalty = calculate_fragment_penalty_score(test_seq)
                perf_stats['penalty_calculations'] += 1

                if test_penalty['total_penalty_score'] <= max_penalty:
                    best_end = current_pos + mid
                    best_penalty = test_penalty
                    left = mid + 1
                else:
                    right = mid - 1

            if best_end is None:
                if remaining_length >= min_fragment_length:
                    best_end = current_pos + min_fragment_length
                    best_penalty = calculate_fragment_penalty_score(sequence[current_pos:best_end])
                    perf_stats['penalty_calculations'] += 1
                else:
                    if initial_fragments:
                        initial_fragments[-1]['end'] = seq_length
                        initial_fragments[-1]['seq'] = sequence[initial_fragments[-1]['start']:seq_length]
                        initial_fragments[-1]['length'] = len(initial_fragments[-1]['seq'])
                    break

            initial_fragments.append({
                'start': current_pos,
                'end': best_end,
                'seq': sequence[current_pos:best_end],
                'length': best_end - current_pos,
                'penalty_score': best_penalty['total_penalty_score'] if best_penalty else 0
            })

            current_pos = best_end

        # Step 2: 贪心合并相邻片段
        merged_fragments = []
        i = 0

        while i < len(initial_fragments):
            current_fragment = initial_fragments[i].copy()

            j = i + 1
            while j < len(initial_fragments):
                next_fragment = initial_fragments[j]
                merged_seq = sequence[current_fragment['start']:next_fragment['end']]
                merged_penalty = calculate_fragment_penalty_score(merged_seq)
                perf_stats['penalty_calculations'] += 1

                if merged_penalty['total_penalty_score'] <= max_penalty:
                    current_fragment = {
                        'start': current_fragment['start'],
                        'end': next_fragment['end'],
                        'seq': merged_seq,
                        'length': len(merged_seq),
                        'penalty_score': merged_penalty['total_penalty_score']
                    }
                    j += 1
                else:
                    break

            merged_fragments.append(current_fragment)
            i = j

        # 检查片段数量，超过9个则强制合并
        if len(merged_fragments) > 9:
            while len(merged_fragments) > 9:
                min_combined_penalty = float('inf')
                min_idx = 0

                for k in range(len(merged_fragments) - 1):
                    combined_seq = sequence[merged_fragments[k]['start']:merged_fragments[k+1]['end']]
                    combined_penalty = calculate_fragment_penalty_score(combined_seq)
                    perf_stats['penalty_calculations'] += 1

                    if combined_penalty['total_penalty_score'] < min_combined_penalty:
                        min_combined_penalty = combined_penalty['total_penalty_score']
                        min_idx = k

                merged_seq = sequence[merged_fragments[min_idx]['start']:merged_fragments[min_idx+1]['end']]
                merged_fragments[min_idx] = {
                    'start': merged_fragments[min_idx]['start'],
                    'end': merged_fragments[min_idx+1]['end'],
                    'seq': merged_seq,
                    'length': len(merged_seq),
                    'penalty_score': min_combined_penalty
                }
                merged_fragments.pop(min_idx + 1)

    # 检查最终片段是否仍有超过阈值的情况（9个片段仍然超28分）
    over_threshold_frags = [f for f in merged_fragments if f['penalty_score'] > max_penalty]
    if over_threshold_frags:
        max_frag_penalty = max(f['penalty_score'] for f in over_threshold_frags)
        warning = (f"已切割为{len(merged_fragments)}个片段，但仍有{len(over_threshold_frags)}个片段罚分超过{max_penalty}分"
                   f"（最高{max_frag_penalty:.1f}分），需要人工介入检查")

    # Step 3: 添加接头信息和索引
    fragments = []
    for idx, frag in enumerate(merged_fragments):
        adapter_left = sequence[max(0, frag['start']-4):frag['start']] if frag['start'] >= 4 else ""
        adapter_right = sequence[frag['end']:frag['end']+4] if frag['end'] + 4 <= seq_length else ""

        fragments.append({
            "index": idx + 1,
            "seq": frag['seq'],
            "start": frag['start'],
            "end": frag['end'],
            "length": frag['length'],
            "penalty_score": frag['penalty_score'],
            "adapter_left": adapter_left,
            "adapter_right": adapter_right
        })

    # Step 4: 检查GoldenGate/T4接头冲突并调整
    if final_cloning_method in ["GoldenGate", "T4"] and len(fragments) > 1:
        grouping = get_grouping_strategy(len(fragments))
        adapters_valid = check_adapters_by_grouping(fragments, grouping)

        if not adapters_valid:
            # 尝试微调切割位置以避免接头冲突
            for i in range(len(fragments) - 1):
                # 检查当前切割位置的接头
                cut_pos = fragments[i]['end']
                existing_adapters = []

                # 收集已有接头
                for frag in fragments:
                    if frag['adapter_left']:
                        existing_adapters.append(frag['adapter_left'])
                    if frag['adapter_right']:
                        existing_adapters.append(frag['adapter_right'])

                # 尝试调整切割位置
                adjusted_pos = adjust_cut_position_to_avoid_conflicts(
                    sequence=sequence,
                    initial_cut_pos=cut_pos,
                    existing_adapters=existing_adapters,
                    search_range=100
                )

                if adjusted_pos and adjusted_pos != cut_pos:
                    # 记录调整
                    adapter_adjustments.append({
                        'fragment_index': i + 1,
                        'original_position': cut_pos,
                        'adjusted_position': adjusted_pos,
                        'offset': adjusted_pos - cut_pos
                    })

                    # 更新片段信息
                    fragments[i]['end'] = adjusted_pos
                    fragments[i]['seq'] = sequence[fragments[i]['start']:adjusted_pos]
                    fragments[i]['length'] = len(fragments[i]['seq'])
                    fragments[i]['adapter_right'] = sequence[adjusted_pos:adjusted_pos+4] if adjusted_pos + 4 <= seq_length else ""
                    fragments[i]['penalty_score'] = calculate_fragment_penalty_score(fragments[i]['seq'])['total_penalty_score']

                    fragments[i+1]['start'] = adjusted_pos
                    fragments[i+1]['seq'] = sequence[adjusted_pos:fragments[i+1]['end']]
                    fragments[i+1]['length'] = len(fragments[i+1]['seq'])
                    fragments[i+1]['adapter_left'] = sequence[max(0, adjusted_pos-4):adjusted_pos] if adjusted_pos >= 4 else ""
                    fragments[i+1]['penalty_score'] = calculate_fragment_penalty_score(fragments[i+1]['seq'])['total_penalty_score']

    # Step 5: 生成MustCut位置
    cut_positions = [frag['end'] for frag in fragments[:-1]]
    grouping = get_grouping_strategy(len(fragments))
    mustcut_str = format_mustcut_positions(cut_positions, grouping)

    # 收集性能统计
    elapsed_time = time.time() - start_time
    final_cache_info = calculate_fragment_penalty_score.cache_info()
    perf_stats['total_time'] = round(elapsed_time, 3)
    perf_stats['cache_hit_rate'] = round(final_cache_info.hits / max(final_cache_info.hits + final_cache_info.misses, 1) * 100, 1)

    logger.info(f"Fragmentation completed: {len(fragments)} fragments, {perf_stats['penalty_calculations']} penalty calculations, "
                f"{len(adapter_adjustments)} adapter adjustments, took {elapsed_time:.3f}s")

    result = {
        "need_fragmentation": True,
        "total_penalty_score": total_penalty,
        "long_repeats_penalty": long_repeats_penalty,
        "cloning_method": final_cloning_method,
        "vector_recommendation": vector_recommendation,
        "vector_change_reason": vector_change_reason,
        "fragments": fragments,
        "mustcut_positions": mustcut_str,
        "total_fragments": len(fragments),
        "adapter_adjustments": adapter_adjustments,
        "warning": warning,
        "performance": perf_stats
    }
    return convert_to_native_types(result)


def check_adapters_by_grouping(fragments: List[Dict], grouping: List[int]) -> bool:
    """
    根据分组策略检查接头冲突

    参数:
        fragments: 片段列表
        grouping: 分组策略,例如 [3, 3, 3]

    返回:
        True 如果没有冲突
    """
    # 1. 检查组间接头(每组的首末接头)
    inter_group_adapters = []
    frag_idx = 0

    for group_size in grouping:
        # 获取这个组的首末片段
        first_frag = fragments[frag_idx]
        last_frag = fragments[frag_idx + group_size - 1]

        # 添加首末接头
        if first_frag['adapter_left']:
            inter_group_adapters.append(first_frag['adapter_left'])
        if last_frag['adapter_right']:
            inter_group_adapters.append(last_frag['adapter_right'])

        frag_idx += group_size

    # 检查组间接头冲突
    if check_adapter_conflicts(inter_group_adapters):
        return False

    # 2. 检查组内接头
    frag_idx = 0
    for group_size in grouping:
        group_adapters = []

        for i in range(group_size):
            frag = fragments[frag_idx + i]
            if frag['adapter_left']:
                group_adapters.append(frag['adapter_left'])
            if frag['adapter_right']:
                group_adapters.append(frag['adapter_right'])

        # 检查组内接头冲突
        if check_adapter_conflicts(group_adapters):
            return False

        frag_idx += group_size

    return True


def format_fragments_for_display(fragmentation_result: Optional[Dict]) -> str:
    """
    格式化片段信息用于显示

    参数:
        fragmentation_result: 切割结果字典

    返回:
        格式化的字符串
    """
    if not fragmentation_result or not fragmentation_result.get('need_fragmentation'):
        return "未切割"

    fragments = fragmentation_result.get('fragments', [])
    mustcut = fragmentation_result.get('mustcut_positions', '')
    method = fragmentation_result.get('cloning_method', '')
    warning = fragmentation_result.get('warning', '')

    parts = [f"克隆方法: {method}", f"片段数: {len(fragments)}", f"MustCut: {mustcut}"]

    if warning:
        parts.append(f"警告: {warning}")

    return " | ".join(parts)


# 测试代码
if __name__ == "__main__":
    # 测试序列
    test_seq = "ATCGATCGATCG" * 100  # 简单的重复序列

    print("=" * 80)
    print("测试新的Fragment Sequence切割算法")
    print("=" * 80)

    # 测试案例1: Gibson载体 + Amp抗性
    print("\n【测试1】Gibson载体 + Amp抗性")
    result = fragment_sequence_by_penalty(
        test_seq,
        cloning_method="Gibson",
        vector_resistance="Amp",
        max_penalty=28
    )

    print(f"原序列长度: {len(test_seq)}")
    print(f"总罚分: {result['total_penalty_score']:.2f}")
    print(f"Long Repeats罚分: {result['long_repeats_penalty']:.2f}")
    print(f"是否需要切割: {result['need_fragmentation']}")
    print(f"克隆方法: {result['cloning_method']}")

    if result.get('vector_recommendation'):
        print(f"推荐载体: {result['vector_recommendation']}")
        print(f"更换原因: {result['vector_change_reason']}")

    if result['need_fragmentation']:
        print(f"切割成 {result['total_fragments']} 个片段")
        print(f"MustCut: {result['mustcut_positions']}")
        print("\n片段详情:")
        for frag in result['fragments']:
            print(f"  Fragment {frag['index']}: "
                  f"位置 {frag['start']}-{frag['end']}, "
                  f"长度 {frag['length']}bp, "
                  f"罚分 {frag['penalty_score']:.2f}")

        if result.get('adapter_adjustments'):
            print(f"\n接头冲突调整记录 ({len(result['adapter_adjustments'])}处):")
            for adj in result['adapter_adjustments']:
                print(f"  片段{adj['fragment_index']}: "
                      f"位置 {adj['original_position']} → {adj['adjusted_position']} "
                      f"(偏移 {adj['offset']:+d}bp)")

        print(f"\n性能统计:")
        print(f"  罚分计算次数: {result['performance']['penalty_calculations']}")
        print(f"  耗时: {result['performance']['total_time']}s")

    print("\n" + "=" * 80)
