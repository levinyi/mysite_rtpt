#!/usr/bin/env python3
"""
调试串联重复算法 - 追踪为什么检测到假阳性
"""

def is_homopolymer(seq):
    """检查是否是同聚物"""
    return len(set(seq)) == 1

def debug_tandem_repeats(sequence, min_unit=3, min_copies=4, max_mismatch=1):
    """
    串联重复检测算法 - 带详细调试输出
    """
    s = sequence
    n = len(s)

    print(f"\n{'='*100}")
    print(f"🔍 调试串联重复检测")
    print(f"{'='*100}")
    print(f"序列: {s}")
    print(f"长度: {n} bp")
    print(f"参数: min_unit={min_unit}, min_copies={min_copies}, max_mismatch={max_mismatch}")
    print(f"{'='*100}\n")

    repeats_temp = []
    checked_positions = set()
    MAX_UNIT_LENGTH = 50

    detection_count = 0

    for start_pos in range(n):
        if start_pos in checked_positions:
            continue

        # 尝试不同的重复单元长度
        for unit_length in range(min_unit, min(MAX_UNIT_LENGTH, (n - start_pos) // min_copies + 1)):
            repeat_unit = s[start_pos:start_pos + unit_length]

            # 跳过同聚物
            if is_homopolymer(repeat_unit):
                continue

            # 检查从当前位置开始，这个单元重复了多少次
            repeat_count = 0
            total_mismatches = 0
            pos = start_pos

            match_details = []

            while pos + unit_length <= n:
                current_segment = s[pos:pos + unit_length]
                # 计算错配数
                mismatches = sum(1 for k in range(unit_length) if current_segment[k] != repeat_unit[k])

                if mismatches <= max_mismatch:
                    repeat_count += 1
                    total_mismatches += mismatches
                    match_details.append(f"  [{pos:3d}:{pos+unit_length:3d}] {current_segment} (mismatches={mismatches})")
                    pos += unit_length
                else:
                    match_details.append(f"  [{pos:3d}:{pos+unit_length:3d}] {current_segment} (mismatches={mismatches}) ❌ BREAK")
                    break

            # 如果找到了足够的重复
            if repeat_count >= min_copies:
                actual_length = repeat_count * unit_length

                # 计算身份百分比
                total_bases = actual_length
                matching_bases = total_bases - total_mismatches
                identity_percent = matching_bases / total_bases if total_bases > 0 else 0

                # 应用身份阈值过滤（80%）
                MIN_IDENTITY = 0.80
                passed_filter = identity_percent >= MIN_IDENTITY

                detection_count += 1
                end_pos = start_pos + actual_length - 1
                detected_sequence = s[start_pos:start_pos + actual_length]

                status = "✅ 通过" if passed_filter else "❌ 被过滤"
                print(f"\n🚨 检测 #{detection_count} {status}")
                print(f"{'─'*100}")
                print(f"起始位置: {start_pos}")
                print(f"重复单元: '{repeat_unit}' (长度={unit_length})")
                print(f"重复次数: {repeat_count}")
                print(f"总错配数: {total_mismatches}")
                print(f"身份百分比: {identity_percent*100:.1f}% (阈值: {MIN_IDENTITY*100:.0f}%)")
                print(f"匹配详情:")
                for detail in match_details:
                    print(detail)
                print(f"检测序列: [{start_pos}:{end_pos}] {detected_sequence}")
                print(f"{'─'*100}")

                if not passed_filter:
                    continue

                repeats_temp.append({
                    'sequence': detected_sequence,
                    'start': start_pos,
                    'end': end_pos,
                    'mismatches': total_mismatches,
                    'unit': repeat_unit,
                    'unit_length': unit_length,
                })

                # 标记这些位置已检查
                for p in range(start_pos, start_pos + actual_length):
                    checked_positions.add(p)

                # 找到一个重复后，跳出unit_length循环
                break

    print(f"\n{'='*100}")
    print(f"📊 检测总结")
    print(f"{'='*100}")
    print(f"总检测数: {detection_count}")
    print(f"{'='*100}\n")

    return repeats_temp


# 测试1: 用户序列中第一个假阳性检测
print("\n" + "="*100)
print("测试1: 假阳性检测案例 - 位置56-67的'CGACAACGCCCA'")
print("="*100)

# 从用户序列中提取这段（假设是独立的）
test_seq_1 = "CGACAACGCCCA"
print(f"\n手动分析:")
print(f"序列: {test_seq_1}")
print(f"可能的3-base分割: CGA-CAA-CGC-CCA")
print(f"  CGA vs CAA: 2处不同")
print(f"  CAA vs CGC: 3处全不同")
print(f"  CGC vs CCA: 2处不同")
print(f"结论: 不应该被检测为串联重复！")

result1 = debug_tandem_repeats(test_seq_1, min_unit=3, min_copies=4, max_mismatch=1)

if result1:
    print(f"\n❌ 错误：算法检测到了 {len(result1)} 个串联重复（应该是0）")
else:
    print(f"\n✅ 正确：算法没有检测到串联重复")


# 测试2: 从用户序列中提取包含上下文的更长片段
print("\n\n" + "="*100)
print("测试2: 带上下文的片段测试")
print("="*100)

user_sequence = "ATGACTACATATAATACGAACGAACCCCTAGGTTCTGCTAGCGCAAAAGTTCTGTACGACAACGCCCAAAACTTTGATCACCTGAGCAATGACCGCGTTAATGAAACCTGGGATGACCGCTTCGGCGTGCCGCGTCTGACCTGGCACGGCATGGAAGAGCGTTACAAAACCGCGCTGGCAAATCTGGGCTTAAATCCGGTTGGGACGTTTCAGGGTGGCGCAGTGATCAACTCGGCGGGTGACATTATCCAAGACGAGACTACCGGCGCTTGGTATCGCTGGGACGATCTGACCACCCTGCCGAAGACCGTGCCACCGGGATCGACCCCTGATAGCAGCGGTGGTACCGGTGTCGGTAAATGGCTGGCTGTCGATGTCTCCGATGTGCTGAGACGTGAACTGGCGCTTCCGACCGGCGCGGATCAGATTGGCTACGGCGACGTTACCGTTGCAGAGCGCCTCAGCTATGATGTGTACTTCACCGGCGGTAGCGGAGCAACCAAAGAGGAGATCCAGGCGTTTCTGGATGAGAACGCGGGTCGAAACTGCCATTTTCCGCCAGGTGACTTCGACATCGAGTGGGGTATGATTCCGCGTAATACCACCATTACCGGTGCGCAAGCTGTGACCGTCCGTAGCCACAGTATGCGCCACGAAGCTACGACTCTGGCAACTCTCATTTCGGATCCGGGTTTTACCCGTTTCAACTTGAAGGGCACGCCGGCGACATACGTTTTGACAGACGTGGTTGAAGGTGCCGATGACCCGGCGATTAGCGCGGGTCTGTGCATCTGCGACCACGGTATTAGCATTAACAACGTGGTCCTTATGGGTTGGCGTAAACGTACCGATGGCACCCTGGAAGCACCGAGCTTAACCGGGGTCGATGATGTTGGTGCCACTGCGTGTTTCAGCTATGGTCTGTTCGTGCCGGCAGTATCTGGCCTGACCCTCTCTGGTACTGCGGTGATCGGCTACTTTGCCAACGACGCAGTTTTGCTGGACTGTAGCCGTAGCGACCAGAATAACGGTAGCGGTAATACCTTTAATATCAATGGCCGTATTAATTCCCAATCCATGTGCGATCTGTCCTTCGATAATTTTTTCGCGTGGCCGCTGGACCCGAAGCAGCCGACACAGCTGGTTTCCGCGATCTCAAGCTACGGCCTCAAGTTGAAGGGCACGGATCGTGATATTCGTGACGGGACCAAGTATCCGCAGGGTGCGAACGGCTACGCTCTGAACTGGATTTGGGGTGGTACGGGCACGTCAGACTTGTTCTTCTCTAACTCCGTGATCAGAGGTGTTTATCTGGATGCGGCGATTAACACGGCGGAAAAACCCGCCAACCGTATGAACGATTATGCAACCGACGGATCCGGCAGCGGCACGACCAGCGTGAACGGTTACCCAAAGGAGTGGCAGGACGGTCGCGGTTCGAAGCTGTTCTTTGTTAACACCACCATCCGCGTGGGCAACCTATATATGAATCGTGTCGCGAACGTGAATCTTGTTAACACGTACAGCGAAGCTGGCACTCATTATATGACCAATTTGACCGGTCGTGTTTCGATCATCGGGGGACATAATGGTCTGGGCGTTTCCGACCTGACGGTGAACAATGTTGACGGTTCTGCTCCGACCGCGTATAACCGTTTGTTCAGCGCGAACTGGATCTGCATTGGCACCGCTAACCCGATGCGTTTGGGACCGGTGTACGAAAGCGGCAGCCACGCCTATCTGCGTCCGCATCGTGATGGCACAATTTCCCTGGGTACTGACGAGGGCACCGGCGTCGGCGCTCTGCGCTACCGCTACGCTGTGATCCATGTTGTGTCTGGCAGCTTTGGTAACATTACCAGCCCGAATAACGTTATCCAAGCGAACAAACCGGTTCGCATCCCGTCTTTCACCACTGCGCTGCGTCCGAGCCTCAACGCGGCTGACGCTGGTGCGCAAATCCTGGACACCACCCTGGGCTACGCCATCACGTGGACCGGTAGTGCGTGGAAAGATGGTGTGGGTAACATCGTG"

# 测试位置56附近（假设原始检测从这里开始）
# 让我们测试位置50-80的片段
test_fragment = user_sequence[50:80]
print(f"\n测试片段 [50:80]: {test_fragment}")

result2 = debug_tandem_repeats(test_fragment, min_unit=3, min_copies=4, max_mismatch=1)

if result2:
    print(f"\n❌ 在此片段中检测到 {len(result2)} 个串联重复")
    for i, r in enumerate(result2, 1):
        print(f"  {i}. 位置 {r['start']}-{r['end']}: {r['sequence']}")
else:
    print(f"\n✅ 在此片段中未检测到串联重复")


# 测试3: 完整用户序列（只显示摘要）
print("\n\n" + "="*100)
print("测试3: 完整用户序列（2034bp）")
print("="*100)

print("\n⚠️  由于输出会很长，只显示检测摘要...")
print("如果需要详细日志，请单独运行\n")

# 暂时禁用详细输出，只计数
import sys
from io import StringIO

old_stdout = sys.stdout
sys.stdout = StringIO()

result3 = debug_tandem_repeats(user_sequence, min_unit=3, min_copies=4, max_mismatch=1)

output = sys.stdout.getvalue()
sys.stdout = old_stdout

# 只显示检测总数
detections = output.count("🚨 检测")
print(f"检测总数: {detections} 个")

if result3:
    print(f"\n检测到的串联重复:")
    for i, r in enumerate(result3, 1):
        print(f"  {i}. 位置 {r['start']}-{r['end']} ({r['end']-r['start']+1}bp): {r['sequence'][:50]}{'...' if len(r['sequence']) > 50 else ''}")
        print(f"      单元: '{r['unit']}' × {(r['end']-r['start']+1)//r['unit_length']} 次")

print(f"\n{'='*100}")
print("💡 如需查看详细调试日志，将测试3的输出恢复")
print(f"{'='*100}\n")
