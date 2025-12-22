#!/usr/bin/env python3
"""
简单分析用户序列 - 手动检查重复模式
"""

user_sequence = "ATGACTACATATAATACGAACGAACCCCTAGGTTCTGCTAGCGCAAAAGTTCTGTACGACAACGCCCAAAACTTTGATCACCTGAGCAATGACCGCGTTAATGAAACCTGGGATGACCGCTTCGGCGTGCCGCGTCTGACCTGGCACGGCATGGAAGAGCGTTACAAAACCGCGCTGGCAAATCTGGGCTTAAATCCGGTTGGGACGTTTCAGGGTGGCGCAGTGATCAACTCGGCGGGTGACATTATCCAAGACGAGACTACCGGCGCTTGGTATCGCTGGGACGATCTGACCACCCTGCCGAAGACCGTGCCACCGGGATCGACCCCTGATAGCAGCGGTGGTACCGGTGTCGGTAAATGGCTGGCTGTCGATGTCTCCGATGTGCTGAGACGTGAACTGGCGCTTCCGACCGGCGCGGATCAGATTGGCTACGGCGACGTTACCGTTGCAGAGCGCCTCAGCTATGATGTGTACTTCACCGGCGGTAGCGGAGCAACCAAAGAGGAGATCCAGGCGTTTCTGGATGAGAACGCGGGTCGAAACTGCCATTTTCCGCCAGGTGACTTCGACATCGAGTGGGGTATGATTCCGCGTAATACCACCATTACCGGTGCGCAAGCTGTGACCGTCCGTAGCCACAGTATGCGCCACGAAGCTACGACTCTGGCAACTCTCATTTCGGATCCGGGTTTTACCCGTTTCAACTTGAAGGGCACGCCGGCGACATACGTTTTGACAGACGTGGTTGAAGGTGCCGATGACCCGGCGATTAGCGCGGGTCTGTGCATCTGCGACCACGGTATTAGCATTAACAACGTGGTCCTTATGGGTTGGCGTAAACGTACCGATGGCACCCTGGAAGCACCGAGCTTAACCGGGGTCGATGATGTTGGTGCCACTGCGTGTTTCAGCTATGGTCTGTTCGTGCCGGCAGTATCTGGCCTGACCCTCTCTGGTACTGCGGTGATCGGCTACTTTGCCAACGACGCAGTTTTGCTGGACTGTAGCCGTAGCGACCAGAATAACGGTAGCGGTAATACCTTTAATATCAATGGCCGTATTAATTCCCAATCCATGTGCGATCTGTCCTTCGATAATTTTTTCGCGTGGCCGCTGGACCCGAAGCAGCCGACACAGCTGGTTTCCGCGATCTCAAGCTACGGCCTCAAGTTGAAGGGCACGGATCGTGATATTCGTGACGGGACCAAGTATCCGCAGGGTGCGAACGGCTACGCTCTGAACTGGATTTGGGGTGGTACGGGCACGTCAGACTTGTTCTTCTCTAACTCCGTGATCAGAGGTGTTTATCTGGATGCGGCGATTAACACGGCGGAAAAACCCGCCAACCGTATGAACGATTATGCAACCGACGGATCCGGCAGCGGCACGACCAGCGTGAACGGTTACCCAAAGGAGTGGCAGGACGGTCGCGGTTCGAAGCTGTTCTTTGTTAACACCACCATCCGCGTGGGCAACCTATATATGAATCGTGTCGCGAACGTGAATCTTGTTAACACGTACAGCGAAGCTGGCACTCATTATATGACCAATTTGACCGGTCGTGTTTCGATCATCGGGGGACATAATGGTCTGGGCGTTTCCGACCTGACGGTGAACAATGTTGACGGTTCTGCTCCGACCGCGTATAACCGTTTGTTCAGCGCGAACTGGATCTGCATTGGCACCGCTAACCCGATGCGTTTGGGACCGGTGTACGAAAGCGGCAGCCACGCCTATCTGCGTCCGCATCGTGATGGCACAATTTCCCTGGGTACTGACGAGGGCACCGGCGTCGGCGCTCTGCGCTACCGCTACGCTGTGATCCATGTTGTGTCTGGCAGCTTTGGTAACATTACCAGCCCGAATAACGTTATCCAAGCGAACAAACCGGTTCGCATCCCGTCTTTCACCACTGCGCTGCGTCCGAGCCTCAACGCGGCTGACGCTGGTGCGCAAATCCTGGACACCACCCTGGGCTACGCCATCACGTGGACCGGTAGTGCGTGGAAAGATGGTGTGGGTAACATCGTG"

print("="*100)
print(" 用户序列手动分析 - 查找串联重复模式")
print("="*100)

print(f"\n📊 序列基本信息:")
print(f"  长度: {len(user_sequence)} bp")
print(f"  开头: {user_sequence[:100]}")

# 手动查找明显的重复模式
print(f"\n{'='*100}")
print("🔍 手动查找明显的重复模式")
print(f"{'='*100}")

findings = []

# 1. 查找 AT 重复
print(f"\n1️⃣ 查找 AT 重复:")
for i in range(len(user_sequence) - 6):
    substr = user_sequence[i:i+6]
    if substr == "ATATAT":
        print(f"   位置 {i}: {user_sequence[i:i+20]}")
        # 扩展查看
        j = i
        while j + 2 <= len(user_sequence) and user_sequence[j:j+2] == "AT":
            j += 2
        if j > i + 6:
            findings.append(f"AT×{(j-i)//2} 在位置 {i}-{j-1}")
            print(f"   ✓ 扩展: AT × {(j-i)//2} (位置 {i}-{j-1})")

# 2. 查找 GC 重复
print(f"\n2️⃣ 查找 GC 重复:")
for i in range(len(user_sequence) - 6):
    substr = user_sequence[i:i+6]
    if substr == "GCGCGC":
        print(f"   位置 {i}: {user_sequence[i:i+20]}")
        # 扩展查看
        j = i
        while j + 2 <= len(user_sequence) and user_sequence[j:j+2] == "GC":
            j += 2
        if j > i + 6:
            findings.append(f"GC×{(j-i)//2} 在位置 {i}-{j-1}")
            print(f"   ✓ 扩展: GC × {(j-i)//2} (位置 {i}-{j-1})")

# 3. 查找同聚物 (Homopolymers)
print(f"\n3️⃣ 查找同聚物 (≥7bp):")
for base in ['A', 'T', 'C', 'G']:
    pattern = base * 7
    idx = 0
    while idx < len(user_sequence):
        idx = user_sequence.find(pattern, idx)
        if idx == -1:
            break
        # 扩展查看
        j = idx
        while j < len(user_sequence) and user_sequence[j] == base:
            j += 1
        print(f"   {base}×{j-idx} 在位置 {idx}-{j-1}: {user_sequence[max(0,idx-5):j+5]}")
        findings.append(f"{base}×{j-idx} 在位置 {idx}-{j-1}")
        idx = j

# 4. 查找三碱基重复
print(f"\n4️⃣ 查找三碱基重复 (至少4次):")
checked_positions = set()
for i in range(len(user_sequence) - 12):
    if i in checked_positions:
        continue
    unit = user_sequence[i:i+3]
    # 检查是否是同聚物
    if len(set(unit)) == 1:
        continue
    # 检查重复
    j = i
    count = 0
    while j + 3 <= len(user_sequence) and user_sequence[j:j+3] == unit:
        count += 1
        j += 3
    if count >= 4:
        print(f"   {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:j]}")
        findings.append(f"{unit}×{count} 在位置 {i}-{j-1}")
        for k in range(i, j):
            checked_positions.add(k)

# 5. 查找四碱基重复
print(f"\n5️⃣ 查找四碱基重复 (至少4次):")
checked_positions = set()
for i in range(len(user_sequence) - 16):
    if i in checked_positions:
        continue
    unit = user_sequence[i:i+4]
    # 检查是否是简单重复
    if len(set(unit)) <= 2:
        continue
    # 检查重复
    j = i
    count = 0
    while j + 4 <= len(user_sequence) and user_sequence[j:j+4] == unit:
        count += 1
        j += 4
    if count >= 4:
        print(f"   {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:min(j, i+60)]}")
        findings.append(f"{unit}×{count} 在位置 {i}-{j-1}")
        for k in range(i, j):
            checked_positions.add(k)

# 总结
print(f"\n{'='*100}")
print(f"📊 发现的串联重复总结")
print(f"{'='*100}")

if findings:
    for i, finding in enumerate(findings, 1):
        print(f"  {i}. {finding}")
else:
    print("  未发现明显的串联重复（min_copies=4）")

# 序列特征统计
print(f"\n{'='*100}")
print(f"📈 序列组成统计")
print(f"{'='*100}")
print(f"  A: {user_sequence.count('A')} ({user_sequence.count('A')/len(user_sequence)*100:.1f}%)")
print(f"  T: {user_sequence.count('T')} ({user_sequence.count('T')/len(user_sequence)*100:.1f}%)")
print(f"  C: {user_sequence.count('C')} ({user_sequence.count('C')/len(user_sequence)*100:.1f}%)")
print(f"  G: {user_sequence.count('G')} ({user_sequence.count('G')/len(user_sequence)*100:.1f}%)")
print(f"  GC含量: {(user_sequence.count('G') + user_sequence.count('C'))/len(user_sequence)*100:.1f}%")

print(f"\n{'='*100}\n")
