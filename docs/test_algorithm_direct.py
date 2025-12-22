#!/usr/bin/env python3
"""
直接测试算法（不通过API）
"""

import sys
sys.path.insert(0, '/cygene4/dushiyi/mysite_rtpt')

import pandas as pd
from tools.scripts.AnalysisSequence import DNARepeatsFinder

print("="*80)
print("🧪 直接测试算法")
print("="*80)

# 测试序列
test_sequences = {
    "Test1": "AAAAATCGATCGATCGATAAAAA",  # 包含 18bp DNA回文
    "Test2": "GGGATCGATCGATCGATCGGGGG",  # 包含 20bp DNA回文
    "User_Problem": "ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG"
}

for name, sequence in test_sequences.items():
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    print(f"序列: {sequence}")
    print(f"长度: {len(sequence)} bp")

    try:
        # 创建DataFrame
        df = pd.DataFrame({
            'gene_id': [name],
            'sequence': [sequence]
        })
        finder = DNARepeatsFinder(df)

        # 测试 Palindrome Repeats with 不同 min_len
        print(f"\n📍 Palindrome Repeats:")
        for min_len in [15, 16, 17, 18]:
            print(f"\n  min_len={min_len} ({'奇数' if min_len % 2 != 0 else '偶数'}):")
            try:
                palindromes = finder.find_palindrome_repeats(index=0, min_len=min_len)
                if palindromes:
                    print(f"    ✅ 检测到 {len(palindromes)} 个:")
                    for p in palindromes:
                        print(f"       - {p['sequence']} (位置 {p['start']}-{p['end']}, {p['length']}bp)")
                else:
                    print(f"    ⬜ 未检测到")
            except Exception as e:
                print(f"    ❌ 错误: {str(e)}")

        # 测试 Tandem Repeats
        print(f"\n📍 Tandem Repeats:")
        try:
            tandems = finder.find_tandem_repeats(index=0)
            if tandems:
                print(f"  ✅ 检测到 {len(tandems)} 个:")
                for t in tandems[:3]:  # 只显示前3个
                    print(f"     - {t['sequence'][:20]}... (位置 {t['start']}-{t['end']}, {t['length']}bp)")
            else:
                print(f"  ⬜ 未检测到")
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")

        # 测试 Inverted Repeats
        print(f"\n📍 Inverted Repeats:")
        try:
            inverted = finder.find_inverted_repeats(index=0)
            if inverted:
                print(f"  ✅ 检测到 {len(inverted)} 个:")
                for inv in inverted[:3]:  # 只显示前3个
                    print(f"     - {inv['type']}: stem={inv['stem_length']}bp, loop={inv['loop_length']}bp")
            else:
                print(f"  ⬜ 未检测到")
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")

    except Exception as e:
        print(f"\n❌ 初始化错误: {str(e)}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print("✅ 测试完成")
print("="*80)
