#!/usr/bin/env python3
"""
测试用户提供的序列 - Tandem Repeats 检查
"""

import sys
sys.path.insert(0, '/cygene4/dushiyi/mysite_rtpt')

import pandas as pd
from tools.scripts.AnalysisSequence import DNARepeatsFinder

# 用户提供的序列
user_sequence = "ATGACTACATATAATACGAACGAACCCCTAGGTTCTGCTAGCGCAAAAGTTCTGTACGACAACGCCCAAAACTTTGATCACCTGAGCAATGACCGCGTTAATGAAACCTGGGATGACCGCTTCGGCGTGCCGCGTCTGACCTGGCACGGCATGGAAGAGCGTTACAAAACCGCGCTGGCAAATCTGGGCTTAAATCCGGTTGGGACGTTTCAGGGTGGCGCAGTGATCAACTCGGCGGGTGACATTATCCAAGACGAGACTACCGGCGCTTGGTATCGCTGGGACGATCTGACCACCCTGCCGAAGACCGTGCCACCGGGATCGACCCCTGATAGCAGCGGTGGTACCGGTGTCGGTAAATGGCTGGCTGTCGATGTCTCCGATGTGCTGAGACGTGAACTGGCGCTTCCGACCGGCGCGGATCAGATTGGCTACGGCGACGTTACCGTTGCAGAGCGCCTCAGCTATGATGTGTACTTCACCGGCGGTAGCGGAGCAACCAAAGAGGAGATCCAGGCGTTTCTGGATGAGAACGCGGGTCGAAACTGCCATTTTCCGCCAGGTGACTTCGACATCGAGTGGGGTATGATTCCGCGTAATACCACCATTACCGGTGCGCAAGCTGTGACCGTCCGTAGCCACAGTATGCGCCACGAAGCTACGACTCTGGCAACTCTCATTTCGGATCCGGGTTTTACCCGTTTCAACTTGAAGGGCACGCCGGCGACATACGTTTTGACAGACGTGGTTGAAGGTGCCGATGACCCGGCGATTAGCGCGGGTCTGTGCATCTGCGACCACGGTATTAGCATTAACAACGTGGTCCTTATGGGTTGGCGTAAACGTACCGATGGCACCCTGGAAGCACCGAGCTTAACCGGGGTCGATGATGTTGGTGCCACTGCGTGTTTCAGCTATGGTCTGTTCGTGCCGGCAGTATCTGGCCTGACCCTCTCTGGTACTGCGGTGATCGGCTACTTTGCCAACGACGCAGTTTTGCTGGACTGTAGCCGTAGCGACCAGAATAACGGTAGCGGTAATACCTTTAATATCAATGGCCGTATTAATTCCCAATCCATGTGCGATCTGTCCTTCGATAATTTTTTCGCGTGGCCGCTGGACCCGAAGCAGCCGACACAGCTGGTTTCCGCGATCTCAAGCTACGGCCTCAAGTTGAAGGGCACGGATCGTGATATTCGTGACGGGACCAAGTATCCGCAGGGTGCGAACGGCTACGCTCTGAACTGGATTTGGGGTGGTACGGGCACGTCAGACTTGTTCTTCTCTAACTCCGTGATCAGAGGTGTTTATCTGGATGCGGCGATTAACACGGCGGAAAAACCCGCCAACCGTATGAACGATTATGCAACCGACGGATCCGGCAGCGGCACGACCAGCGTGAACGGTTACCCAAAGGAGTGGCAGGACGGTCGCGGTTCGAAGCTGTTCTTTGTTAACACCACCATCCGCGTGGGCAACCTATATATGAATCGTGTCGCGAACGTGAATCTTGTTAACACGTACAGCGAAGCTGGCACTCATTATATGACCAATTTGACCGGTCGTGTTTCGATCATCGGGGGACATAATGGTCTGGGCGTTTCCGACCTGACGGTGAACAATGTTGACGGTTCTGCTCCGACCGCGTATAACCGTTTGTTCAGCGCGAACTGGATCTGCATTGGCACCGCTAACCCGATGCGTTTGGGACCGGTGTACGAAAGCGGCAGCCACGCCTATCTGCGTCCGCATCGTGATGGCACAATTTCCCTGGGTACTGACGAGGGCACCGGCGTCGGCGCTCTGCGCTACCGCTACGCTGTGATCCATGTTGTGTCTGGCAGCTTTGGTAACATTACCAGCCCGAATAACGTTATCCAAGCGAACAAACCGGTTCGCATCCCGTCTTTCACCACTGCGCTGCGTCCGAGCCTCAACGCGGCTGACGCTGGTGCGCAAATCCTGGACACCACCCTGGGCTACGCCATCACGTGGACCGGTAGTGCGTGGAAAGATGGTGTGGGTAACATCGTG"

print("="*80)
print("🧪 测试用户序列 - Tandem Repeats 分析")
print("="*80)
print(f"\n序列长度: {len(user_sequence)} bp")
print(f"序列开头: {user_sequence[:100]}...")

# 创建DataFrame
df = pd.DataFrame({
    'gene_id': ['UserSequence'],
    'sequence': [user_sequence]
})

try:
    finder = DNARepeatsFinder(df)

    # 测试 Tandem Repeats - 使用不同参数
    print(f"\n{'='*80}")
    print("📍 Tandem Repeats 检测")
    print(f"{'='*80}")

    # 测试1：默认参数
    print(f"\n🔍 测试1: 默认参数 (min_unit=3, min_copies=4, max_mismatch=1)")
    print("-"*80)
    tandems = finder.find_tandem_repeats(index=0, min_unit=3, min_copies=4, max_mismatch=1)

    if tandems:
        print(f"✅ 检测到 {len(tandems)} 个串联重复:")
        for i, t in enumerate(tandems, 1):
            print(f"\n  {i}. 位置 {t['start']}-{t['end']} (长度 {t['length']} bp)")
            print(f"     序列: {t['sequence'][:60]}{'...' if len(t['sequence']) > 60 else ''}")
            print(f"     错配数: {t.get('mismatches', 0)}")
            print(f"     罚分: {t['penalty_score']}")

            # 分析重复单元
            seq = t['sequence']
            # 尝试找出重复单元
            for unit_len in range(3, min(20, len(seq)//4 + 1)):
                unit = seq[:unit_len]
                # 检查是否整个序列都是这个单元的重复
                if len(seq) % unit_len == 0:
                    copies = len(seq) // unit_len
                    if copies >= 4:
                        reconstructed = unit * copies
                        # 计算错配
                        mismatches = sum(1 for i in range(len(seq)) if i < len(reconstructed) and seq[i] != reconstructed[i])
                        if mismatches <= 1 * copies:  # 允许一些错配
                            print(f"     重复单元: {unit} × {copies} (错配: {mismatches})")
                            break
    else:
        print("⬜ 未检测到串联重复")

    # 测试2：更严格的参数（不允许错配）
    print(f"\n{'='*80}")
    print(f"🔍 测试2: 严格参数 (min_unit=3, min_copies=4, max_mismatch=0)")
    print("-"*80)
    tandems_strict = finder.find_tandem_repeats(index=0, min_unit=3, min_copies=4, max_mismatch=0)

    if tandems_strict:
        print(f"✅ 检测到 {len(tandems_strict)} 个串联重复:")
        for i, t in enumerate(tandems_strict, 1):
            print(f"\n  {i}. 位置 {t['start']}-{t['end']} (长度 {t['length']} bp)")
            print(f"     序列: {t['sequence'][:60]}{'...' if len(t['sequence']) > 60 else ''}")
            print(f"     罚分: {t['penalty_score']}")
    else:
        print("⬜ 未检测到串联重复")

    # 测试3：宽松参数（更小的min_copies）
    print(f"\n{'='*80}")
    print(f"🔍 测试3: 宽松参数 (min_unit=3, min_copies=3, max_mismatch=1)")
    print("-"*80)
    tandems_relaxed = finder.find_tandem_repeats(index=0, min_unit=3, min_copies=3, max_mismatch=1)

    if tandems_relaxed:
        print(f"✅ 检测到 {len(tandems_relaxed)} 个串联重复:")
        for i, t in enumerate(tandems_relaxed[:5], 1):  # 只显示前5个
            print(f"\n  {i}. 位置 {t['start']}-{t['end']} (长度 {t['length']} bp)")
            print(f"     序列: {t['sequence'][:60]}{'...' if len(t['sequence']) > 60 else ''}")
            print(f"     错配数: {t.get('mismatches', 0)}")
            print(f"     罚分: {t['penalty_score']}")
        if len(tandems_relaxed) > 5:
            print(f"\n  ... 还有 {len(tandems_relaxed) - 5} 个串联重复")
    else:
        print("⬜ 未检测到串联重复")

    # 手动检查序列中明显的重复
    print(f"\n{'='*80}")
    print("🔍 手动检查序列中的重复模式")
    print(f"{'='*80}")

    # 检查开头的 ATATATA
    print(f"\n序列开头: {user_sequence[:50]}")
    if "ATATATA" in user_sequence[:50]:
        idx = user_sequence.find("ATATATA")
        print(f"✓ 发现 ATATATA 模式在位置 {idx}")
        # 扩展查看
        extended = user_sequence[idx:idx+20]
        print(f"  扩展查看: {extended}")

    # 检查 CCC, GGG 等
    for pattern in ["CCC", "GGG", "AAA", "TTT"]:
        if pattern * 3 in user_sequence:
            idx = user_sequence.find(pattern * 3)
            print(f"✓ 发现 {pattern}×3 在位置 {idx}: {user_sequence[idx:idx+15]}")

    # 检查其他特征
    print(f"\n{'='*80}")
    print("📊 其他特征检测")
    print(f"{'='*80}")

    # Homopolymers
    homopolymers = finder.find_homopolymers(index=0, min_len=7)
    print(f"\n🔹 Homopolymers: {len(homopolymers)} 个")
    for h in homopolymers[:3]:
        print(f"   - {h['sequence']} (位置 {h['start']}-{h['end']}, {h['length']}bp)")

    # Palindromes
    palindromes = finder.find_palindrome_repeats(index=0, min_len=16)
    print(f"\n🔹 Palindrome Repeats: {len(palindromes)} 个")
    for p in palindromes[:3]:
        print(f"   - {p['sequence']} (位置 {p['start']}-{p['end']}, {p['length']}bp)")

    # Inverted Repeats
    inverted = finder.find_inverted_repeats(index=0, min_stem_len=10)
    print(f"\n🔹 Inverted Repeats: {len(inverted)} 个")
    for inv in inverted[:3]:
        print(f"   - {inv['type']}: stem={inv['stem_length']}bp, loop={inv['loop_length']}bp")

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("✅ 测试完成")
print("="*80)
