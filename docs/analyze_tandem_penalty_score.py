#!/usr/bin/env python3
"""
分析串联重复罚分为0的原因
"""

print("="*100)
print(" 串联重复罚分分析")
print("="*100)

# 当前罚分计算公式
def calculate_tandem_repeats_penalty_score(length):
    return round((length - 15) / 2 if length > 15 else 0, 1)

print("\n📊 当前罚分公式:")
print("  penalty = (length - 15) / 2  如果 length > 15")
print("  penalty = 0                   如果 length ≤ 15")

print("\n" + "─"*100)
print("测试不同长度的罚分:")
print("─"*100)

test_lengths = [6, 9, 12, 15, 16, 18, 20, 24, 30, 40, 50]

for length in test_lengths:
    penalty = calculate_tandem_repeats_penalty_score(length)
    marker = "👉" if length == 12 else "  "
    print(f"{marker} 长度 {length:2d}bp → 罚分: {penalty}")

print("\n" + "="*100)
print("🔍 用户检测结果分析:")
print("="*100)

detections = [
    {'seq': 'GATGATGTTGGT', 'pos': (885, 896), 'length': 12, 'gc': 41.67},
    {'seq': 'CTTGTTCTTCTC', 'pos': (1274, 1285), 'length': 12, 'gc': 41.67},
    {'seq': 'CGGCGTCGGCGC', 'pos': (1790, 1801), 'length': 12, 'gc': 91.67},
]

for i, det in enumerate(detections, 1):
    penalty = calculate_tandem_repeats_penalty_score(det['length'])
    print(f"\n{i}. 序列: {det['seq']}")
    print(f"   位置: {det['pos'][0]}-{det['pos'][1]}")
    print(f"   长度: {det['length']}bp")
    print(f"   GC含量: {det['gc']:.1f}%")
    print(f"   罚分: {penalty}")
    print(f"   原因: 长度({det['length']}) ≤ 15，所以罚分 = 0")

print("\n" + "="*100)
print("💡 结论:")
print("="*100)
print("\n罚分为0是**正确的**，根据当前算法逻辑：")
print("  • 所有3个串联重复都是12bp")
print("  • 算法规定：长度 ≤ 15bp 的串联重复罚分为0")
print("  • 这意味着算法认为12bp的串联重复对基因合成影响很小")

print("\n" + "─"*100)
print("🤔 是否需要调整罚分逻辑？")
print("─"*100)

print("\n当前逻辑的特点:")
print("  ✓ 优点: 短串联重复（≤15bp）不会被过度惩罚")
print("  ✓ 假设: 短串联重复对合成影响不大")
print("  ? 问题: 12bp的串联重复在某些情况下也可能造成问题")

print("\n如果需要调整，可以考虑:")
print("  1. 方案A - 更早开始罚分:")
print("     例如: length > 10 就开始罚分")
print("     penalty = (length - 10) / 2 if length > 10 else 0")
print("     12bp → 罚分 = (12-10)/2 = 1.0")
print()
print("  2. 方案B - 考虑重复次数:")
print("     例如: 重复4次以上就有基础罚分")
print("     penalty = copies * unit_length / 5")
print("     12bp (4×3) → 罚分 = 4*3/5 = 2.4")
print()
print("  3. 方案C - 考虑GC含量:")
print("     高GC串联重复增加罚分")
print("     CGGCGTCGGCGC (91.67% GC) → 额外罚分")
print()
print("  4. 方案D - 保持现状:")
print("     如果12bp串联重复在实际合成中没问题，保持罚分=0")

print("\n" + "="*100)
print("📋 建议:")
print("="*100)
print("\n需要根据**实际基因合成经验**来决定:")
print("  • 如果12bp串联重复在合成中经常出问题 → 调整阈值")
print("  • 如果12bp串联重复合成没问题 → 保持现状")
print("  • 可以查看合成失败的序列中，串联重复的典型长度是多少")

print("\n" + "="*100 + "\n")
