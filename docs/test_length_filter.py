#!/usr/bin/env python3
"""
测试长度过滤：≤15bp不检测，>15bp检测
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.scripts.AnalysisSequence import DNARepeatsFinder

print("="*100)
print(" 测试串联重复长度过滤")
print("="*100)

# 测试1: 12bp串联重复（应该被过滤）
print("\n" + "─"*100)
print("测试1: 12bp串联重复（4×3，应该不检测）")
print("─"*100)

seq1 = "ATGATGATGATG" + "AAAAAAA"  # GAT×4 = 12bp
print(f"序列: {seq1}")
print(f"期望: 不检测（长度12 ≤ 15）")

finder1 = DNARepeatsFinder(sequence=seq1)
result1 = finder1.find_tandem_repeats(index=None, min_unit=3, min_copies=4, max_mismatch=0)

print(f"结果: {'✅ 正确 - 未检测' if len(result1) == 0 else '❌ 错误 - 检测到了'}")
if result1:
    for r in result1:
        print(f"  检测到: {r['sequence']} (长度{r['length']}bp)")

# 测试2: 15bp串联重复（应该被过滤）
print("\n" + "─"*100)
print("测试2: 15bp串联重复（5×3，应该不检测）")
print("─"*100)

seq2 = "ATGATGATGATGATG" + "AAAAAAA"  # GAT×5 = 15bp
print(f"序列: {seq2}")
print(f"期望: 不检测（长度15 ≤ 15）")

finder2 = DNARepeatsFinder(sequence=seq2)
result2 = finder2.find_tandem_repeats(index=None, min_unit=3, min_copies=4, max_mismatch=0)

print(f"结果: {'✅ 正确 - 未检测' if len(result2) == 0 else '❌ 错误 - 检测到了'}")
if result2:
    for r in result2:
        print(f"  检测到: {r['sequence']} (长度{r['length']}bp)")

# 测试3: 18bp串联重复（应该检测）
print("\n" + "─"*100)
print("测试3: 18bp串联重复（6×3，应该检测）")
print("─"*100)

seq3 = "ATGATGATGATGATGATG" + "AAAAAAA"  # GAT×6 = 18bp
print(f"序列: {seq3}")
print(f"期望: 检测（长度18 > 15）")

finder3 = DNARepeatsFinder(sequence=seq3)
result3 = finder3.find_tandem_repeats(index=None, min_unit=3, min_copies=4, max_mismatch=0)

print(f"结果: {'✅ 正确 - 检测到' if len(result3) == 1 else '❌ 错误 - 未检测'}")
if result3:
    for r in result3:
        print(f"  序列: {r['sequence']}")
        print(f"  长度: {r['length']}bp")
        print(f"  罚分: {r['penalty_score']}")
        print(f"  计算: (18-15)/2 = 1.5")

# 测试4: 24bp串联重复（应该检测）
print("\n" + "─"*100)
print("测试4: 24bp串联重复（8×3，应该检测）")
print("─"*100)

seq4 = "ATGATGATGATGATGATGATGATG" + "AAAAAAA"  # GAT×8 = 24bp
print(f"序列: {seq4}")
print(f"期望: 检测（长度24 > 15）")

finder4 = DNARepeatsFinder(sequence=seq4)
result4 = finder4.find_tandem_repeats(index=None, min_unit=3, min_copies=4, max_mismatch=0)

print(f"结果: {'✅ 正确 - 检测到' if len(result4) == 1 else '❌ 错误 - 未检测'}")
if result4:
    for r in result4:
        print(f"  序列: {r['sequence']}")
        print(f"  长度: {r['length']}bp")
        print(f"  罚分: {r['penalty_score']}")
        print(f"  计算: (24-15)/2 = 4.5")

print("\n" + "="*100)
print("📊 总结")
print("="*100)

all_passed = (
    len(result1) == 0 and  # 12bp不检测
    len(result2) == 0 and  # 15bp不检测
    len(result3) == 1 and  # 18bp检测
    len(result4) == 1      # 24bp检测
)

if all_passed:
    print("\n✅ 所有测试通过！")
    print("\n规则确认:")
    print("  • 长度 ≤ 15bp: 不检测（罚分为0，不报告）")
    print("  • 长度 > 15bp: 检测并报告（罚分 > 0）")
else:
    print("\n❌ 有测试失败")

print("\n" + "="*100 + "\n")
