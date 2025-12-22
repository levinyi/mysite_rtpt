#!/usr/bin/env python3
"""
分析用户报告的可疑检测：GCCGCCGTCCCCGCCGCG
"""

sequence = "GCCGCCGTCCCCGCCGCG"

print("="*100)
print(" 分析检测结果：GCCGCCGTCCCCGCCGCG")
print("="*100)

print(f"\n序列: {sequence}")
print(f"长度: {len(sequence)}bp")
print(f"GC含量: 94.44%")

print("\n" + "─"*100)
print("尝试不同单元长度的分割:")
print("─"*100)

# 尝试3碱基单元
print("\n【3碱基单元】(18/3=6次)")
unit_len = 3
copies = []
for i in range(0, len(sequence), unit_len):
    copy = sequence[i:i+unit_len]
    if len(copy) == unit_len:
        copies.append(copy)

print(f"分割: {'-'.join(copies)}")

# 找出最常见的单元作为参考
from collections import Counter
counter = Counter(copies)
reference_unit = counter.most_common(1)[0][0]
print(f"\n最常见单元: {reference_unit} (出现{counter[reference_unit]}次)")

print(f"\n与 {reference_unit} 比较:")
total_mismatches = 0
perfect_copies = 0
for i, copy in enumerate(copies, 1):
    mismatches = sum(1 for j in range(len(copy)) if copy[j] != reference_unit[j])
    total_mismatches += mismatches
    if mismatches == 0:
        perfect_copies += 1
    marker = "✓" if mismatches <= 1 else "✗"
    print(f"  Copy {i}: {copy} (错配={mismatches}) {marker}")

identity = (len(sequence) - total_mismatches) / len(sequence) * 100
perfect_ratio = perfect_copies / len(copies) * 100

print(f"\n统计:")
print(f"  总错配数: {total_mismatches}")
print(f"  总体身份: {identity:.1f}%")
print(f"  完美匹配: {perfect_copies}/{len(copies)} ({perfect_ratio:.1f}%)")

# 尝试6碱基单元
print("\n" + "─"*100)
print("【6碱基单元】(18/6=3次)")
unit_len = 6
copies = []
for i in range(0, len(sequence), unit_len):
    copy = sequence[i:i+unit_len]
    if len(copy) == unit_len:
        copies.append(copy)

print(f"分割: {'-'.join(copies)}")
print(f"拷贝数: {len(copies)} (不满足min_copies=4)")

print("\n" + "="*100)
print("🔍 问题分析")
print("="*100)

print("\n这个序列为什么被检测为串联重复?")
print("  1. 3碱基分割: GCC-GCC-GTC-CCC-GCC-GCG")
print("  2. 参考单元: GCC")
print("  3. 错配检查:")
print("     • GCC vs GCC: 0 ✓")
print("     • GCC vs GCC: 0 ✓")
print("     • GCC vs GTC: 1 ✓ (C→T)")
print("     • GCC vs CCC: 1 ✓ (G→C)")
print("     • GCC vs GCC: 0 ✓")
print("     • GCC vs GCG: 1 ✓ (C→G)")
print("  4. 总错配: 3个，身份: 15/18 = 83.3% ✓")
print("  5. 满足条件:")
print("     • 每个copy的错配 ≤ 1 ✓")
print("     • 总体身份 ≥ 80% ✓")
print("     • 长度 > 15bp ✓")

print("\n❌ 但是，这真的是串联重复吗?")
print("\n问题:")
print("  • 虽然每个copy错配≤1，但6个copy中有3个有错配(50%)")
print("  • 真正的串联重复应该是：大部分copy完美，偶尔1-2个突变")
print("  • 这个序列看起来更像是：高GC区域的随机相似序列")

print("\n" + "="*100)
print("💡 改进建议")
print("="*100)

print("\n需要添加新的约束条件:")
print("\n  方案A: 要求至少50%的copy是完美匹配")
print("     perfect_copies / total_copies ≥ 0.5")
print("     这个序列: 3/6 = 50% (刚好达标)")
print("     可以调整为60%或更高")
print()
print("  方案B: 限制总错配数")
print("     total_mismatches / total_length ≤ 15%")
print("     这个序列: 3/18 = 16.7% (超标)")
print("     可以设置阈值为15%")
print()
print("  方案C: 考虑最长完美重复")
print("     至少有连续2个完美copy")
print("     这个序列: 开头有GCC-GCC连续完美 ✓")
print("     但后面就乱了")
print()
print("  方案D: 综合评分")
print("     score = perfect_ratio * 0.5 + identity * 0.5")
print("     只有综合得分高的才算串联重复")

print("\n推荐：方案B（限制总错配率≤15%）")
print("  • 简单明确")
print("  • 保证重复质量")
print("  • 这个序列(16.7%)会被过滤")

print("\n" + "="*100 + "\n")
