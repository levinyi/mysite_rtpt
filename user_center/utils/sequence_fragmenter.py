"""
Sequence Fragmenter
序列切割工具: 将罚分超过阈值的序列切割成小片段,并处理接头冲突
"""
import sys
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from Bio.Seq import Seq

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


def calculate_fragment_penalty_score(sequence: str) -> Dict:
    """
    计算单个序列片段的罚分,并返回详细的罚分信息

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


def is_complementary(seq1: str, seq2: str) -> bool:
    """
    检查两个4bp序列是否互补配对

    参数:
        seq1: 第一个序列 (4bp)
        seq2: 第二个序列 (4bp)

    返回:
        True 如果互补配对
    """
    if len(seq1) != 4 or len(seq2) != 4:
        return False

    # 计算seq1的反向互补序列
    seq1_obj = Seq(seq1)
    seq1_rc = str(seq1_obj.reverse_complement())

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

    参数:
        cut_positions: 切割位置列表(每个片段的结束位置)
        grouping: 分组策略,例如 [3, 3, 3]

    返回:
        格式化的字符串,例如 "1000/2000/3000\4000/5000/6000\7000/8000/"
    """
    result = []
    pos_idx = 0

    for group_size in grouping:
        group_positions = []
        for _ in range(group_size - 1):  # 每组内的分隔符数量是组大小-1
            if pos_idx < len(cut_positions):
                group_positions.append(str(cut_positions[pos_idx]))
                pos_idx += 1
        result.append('/'.join(group_positions))

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


def fragment_sequence_by_penalty(
    sequence: str,
    cloning_method: str = "Gibson",
    max_penalty: float = 28.0,
    min_fragment_length: int = 200,
    max_fragment_length: int = 3000,
    overlap: int = 20
) -> Optional[Dict]:
    r"""
    根据罚分阈值和克隆方法切割序列

    参数:
        sequence: 原始DNA序列
        cloning_method: 克隆方法 ("Gibson", "GoldenGate", "T4")
        max_penalty: 最大允许罚分阈值 (默认28)
        min_fragment_length: 最小片段长度 (默认200bp)
        max_fragment_length: 最大片段长度 (默认3000bp)
        overlap: Gibson方法的重叠长度 (默认20bp)

    返回:
        切割结果字典:
        {
            "need_fragmentation": True/False,
            "cloning_method": "Gibson/GoldenGate/T4",
            "fragments": [...],
            "mustcut_positions": "xx/xx\xx/",
            "total_fragments": 3
        }
    """
    # 首先计算整个序列的罚分
    penalty_info = calculate_fragment_penalty_score(sequence)
    total_penalty = penalty_info['total_penalty_score']
    long_repeats_penalty = penalty_info['long_repeats_penalty']

    # 如果罚分不超过阈值,不需要切割
    if total_penalty <= max_penalty:
        result = {
            "need_fragmentation": False,
            "total_penalty_score": total_penalty,
            "long_repeats_penalty": long_repeats_penalty,
            "cloning_method": cloning_method,
            "fragments": None,
            "mustcut_positions": None,
            "total_fragments": 1
        }
        return convert_to_native_types(result)

    # 判断克隆方法
    # Gibson方法: 如果Long repeat罚分<=28,仍用Gibson;否则改用GG
    final_cloning_method = cloning_method
    if cloning_method == "Gibson":
        if long_repeats_penalty > max_penalty:
            final_cloning_method = "GoldenGate"  # 改用GG,克隆至pGZ1704或pGZ1705

    # 开始切割序列
    fragments = []
    cut_positions = []  # 记录每个切割位置(每个片段的结束位置)
    seq_length = len(sequence)
    current_pos = 0
    fragment_index = 1

    # 尝试切割成不同数量的片段,从最少开始
    max_fragments = min(9, seq_length // min_fragment_length)

    for num_fragments in range(2, max_fragments + 1):
        # 计算每个片段的理想长度
        ideal_fragment_length = seq_length // num_fragments

        fragments = []
        cut_positions = []
        current_pos = 0
        fragment_index = 1
        all_fragments_valid = True

        for i in range(num_fragments):
            # 计算这个片段的目标长度
            if i == num_fragments - 1:
                # 最后一个片段包含剩余所有序列
                end_pos = seq_length
            else:
                # 其他片段使用理想长度
                end_pos = min(current_pos + ideal_fragment_length, seq_length)

            # Gibson方法需要考虑重叠
            if final_cloning_method == "Gibson" and i < num_fragments - 1:
                fragment_end = end_pos
            else:
                fragment_end = end_pos

            fragment_seq = sequence[current_pos:fragment_end]

            # 检查片段长度
            if len(fragment_seq) < min_fragment_length:
                all_fragments_valid = False
                break

            # 计算片段罚分
            fragment_penalty_info = calculate_fragment_penalty_score(fragment_seq)

            # 如果罚分仍超过阈值,尝试微调
            if fragment_penalty_info['total_penalty_score'] > max_penalty:
                # 尝试缩短片段
                for shrink in range(100, ideal_fragment_length // 2, 100):
                    new_end = end_pos - shrink
                    if new_end - current_pos < min_fragment_length:
                        break

                    test_seq = sequence[current_pos:new_end]
                    test_penalty_info = calculate_fragment_penalty_score(test_seq)

                    if test_penalty_info['total_penalty_score'] <= max_penalty:
                        fragment_end = new_end
                        fragment_seq = test_seq
                        fragment_penalty_info = test_penalty_info
                        break

                # 如果仍然超标,标记为无效
                if fragment_penalty_info['total_penalty_score'] > max_penalty:
                    all_fragments_valid = False
                    break

            # 获取接头序列(GG和T4方法)
            adapter_left = sequence[max(0, current_pos-4):current_pos] if current_pos >= 4 else ""
            adapter_right = sequence[fragment_end:fragment_end+4] if fragment_end + 4 <= seq_length else ""

            fragments.append({
                "index": fragment_index,
                "seq": fragment_seq,
                "start": current_pos,
                "end": fragment_end,
                "length": len(fragment_seq),
                "penalty_score": fragment_penalty_info['total_penalty_score'],
                "adapter_left": adapter_left,
                "adapter_right": adapter_right
            })

            if i < num_fragments - 1:
                cut_positions.append(fragment_end)

            # 移动到下一个片段
            if final_cloning_method == "Gibson":
                current_pos = fragment_end - overlap  # Gibson有重叠
            else:
                current_pos = fragment_end

            fragment_index += 1

        # 如果所有片段都有效,检查接头冲突(仅GG和T4)
        if all_fragments_valid:
            if final_cloning_method in ["GoldenGate", "T4"]:
                # 检查接头冲突
                grouping = get_grouping_strategy(num_fragments)
                adapters_valid = check_adapters_by_grouping(fragments, grouping)

                if adapters_valid:
                    # 找到有效的切割方案
                    break
            else:
                # Gibson方法不需要检查接头
                break
    else:
        # 如果所有尝试都失败,返回强制切割的结果(带警告)
        result = {
            "need_fragmentation": True,
            "total_penalty_score": total_penalty,
            "long_repeats_penalty": long_repeats_penalty,
            "cloning_method": final_cloning_method,
            "fragments": fragments,
            "mustcut_positions": format_mustcut_positions(cut_positions, get_grouping_strategy(len(fragments))),
            "total_fragments": len(fragments),
            "warning": "无法找到完全满足条件的切割方案,可能存在接头冲突或罚分超标"
        }
        return convert_to_native_types(result)

    # 格式化MustCut位置
    grouping = get_grouping_strategy(len(fragments))
    mustcut_str = format_mustcut_positions(cut_positions, grouping)

    result = {
        "need_fragmentation": True,
        "total_penalty_score": total_penalty,
        "long_repeats_penalty": long_repeats_penalty,
        "cloning_method": final_cloning_method,
        "fragments": fragments,
        "mustcut_positions": mustcut_str,
        "total_fragments": len(fragments)
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

    result = fragment_sequence_by_penalty(test_seq, cloning_method="GoldenGate", max_penalty=28)

    if result['need_fragmentation']:
        print(f"原序列长度: {len(test_seq)}")
        print(f"总罚分: {result['total_penalty_score']}")
        print(f"克隆方法: {result['cloning_method']}")
        print(f"切割成 {result['total_fragments']} 个片段:")
        print(f"MustCut: {result['mustcut_positions']}")
        for frag in result['fragments']:
            print(f"  Fragment {frag['index']}: 位置 {frag['start']}-{frag['end']}, "
                  f"长度 {frag['length']}, 罚分 {frag['penalty_score']}")
    else:
        print("序列罚分未超过阈值,无需切割")
