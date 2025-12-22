#!/usr/bin/env python3
"""
检查更短的串联重复 (min_copies=3, min_unit=2)
"""

user_sequence = "ATGACTACATATAATACGAACGAACCCCTAGGTTCTGCTAGCGCAAAAGTTCTGTACGACAACGCCCAAAACTTTGATCACCTGAGCAATGACCGCGTTAATGAAACCTGGGATGACCGCTTCGGCGTGCCGCGTCTGACCTGGCACGGCATGGAAGAGCGTTACAAAACCGCGCTGGCAAATCTGGGCTTAAATCCGGTTGGGACGTTTCAGGGTGGCGCAGTGATCAACTCGGCGGGTGACATTATCCAAGACGAGACTACCGGCGCTTGGTATCGCTGGGACGATCTGACCACCCTGCCGAAGACCGTGCCACCGGGATCGACCCCTGATAGCAGCGGTGGTACCGGTGTCGGTAAATGGCTGGCTGTCGATGTCTCCGATGTGCTGAGACGTGAACTGGCGCTTCCGACCGGCGCGGATCAGATTGGCTACGGCGACGTTACCGTTGCAGAGCGCCTCAGCTATGATGTGTACTTCACCGGCGGTAGCGGAGCAACCAAAGAGGAGATCCAGGCGTTTCTGGATGAGAACGCGGGTCGAAACTGCCATTTTCCGCCAGGTGACTTCGACATCGAGTGGGGTATGATTCCGCGTAATACCACCATTACCGGTGCGCAAGCTGTGACCGTCCGTAGCCACAGTATGCGCCACGAAGCTACGACTCTGGCAACTCTCATTTCGGATCCGGGTTTTACCCGTTTCAACTTGAAGGGCACGCCGGCGACATACGTTTTGACAGACGTGGTTGAAGGTGCCGATGACCCGGCGATTAGCGCGGGTCTGTGCATCTGCGACCACGGTATTAGCATTAACAACGTGGTCCTTATGGGTTGGCGTAAACGTACCGATGGCACCCTGGAAGCACCGAGCTTAACCGGGGTCGATGATGTTGGTGCCACTGCGTGTTTCAGCTATGGTCTGTTCGTGCCGGCAGTATCTGGCCTGACCCTCTCTGGTACTGCGGTGATCGGCTACTTTGCCAACGACGCAGTTTTGCTGGACTGTAGCCGTAGCGACCAGAATAACGGTAGCGGTAATACCTTTAATATCAATGGCCGTATTAATTCCCAATCCATGTGCGATCTGTCCTTCGATAATTTTTTCGCGTGGCCGCTGGACCCGAAGCAGCCGACACAGCTGGTTTCCGCGATCTCAAGCTACGGCCTCAAGTTGAAGGGCACGGATCGTGATATTCGTGACGGGACCAAGTATCCGCAGGGTGCGAACGGCTACGCTCTGAACTGGATTTGGGGTGGTACGGGCACGTCAGACTTGTTCTTCTCTAACTCCGTGATCAGAGGTGTTTATCTGGATGCGGCGATTAACACGGCGGAAAAACCCGCCAACCGTATGAACGATTATGCAACCGACGGATCCGGCAGCGGCACGACCAGCGTGAACGGTTACCCAAAGGAGTGGCAGGACGGTCGCGGTTCGAAGCTGTTCTTTGTTAACACCACCATCCGCGTGGGCAACCTATATATGAATCGTGTCGCGAACGTGAATCTTGTTAACACGTACAGCGAAGCTGGCACTCATTATATGACCAATTTGACCGGTCGTGTTTCGATCATCGGGGGACATAATGGTCTGGGCGTTTCCGACCTGACGGTGAACAATGTTGACGGTTCTGCTCCGACCGCGTATAACCGTTTGTTCAGCGCGAACTGGATCTGCATTGGCACCGCTAACCCGATGCGTTTGGGACCGGTGTACGAAAGCGGCAGCCACGCCTATCTGCGTCCGCATCGTGATGGCACAATTTCCCTGGGTACTGACGAGGGCACCGGCGTCGGCGCTCTGCGCTACCGCTACGCTGTGATCCATGTTGTGTCTGGCAGCTTTGGTAACATTACCAGCCCGAATAACGTTATCCAAGCGAACAAACCGGTTCGCATCCCGTCTTTCACCACTGCGCTGCGTCCGAGCCTCAACGCGGCTGACGCTGGTGCGCAAATCCTGGACACCACCCTGGGCTACGCCATCACGTGGACCGGTAGTGCGTGGAAAGATGGTGTGGGTAACATCGTG"

print("="*100)
print(" 检查短串联重复 (更宽松的参数)")
print("="*100)

findings = []

# 1. 二碱基重复 (min_copies=3, 即至少6bp)
print(f"\n🔍 二碱基重复 (min_copies=3, 至少6bp):")
checked = set()
for i in range(len(user_sequence) - 6):
    if i in checked:
        continue
    unit = user_sequence[i:i+2]
    if len(set(unit)) == 1:  # 跳过AA, TT, CC, GG
        continue
    j = i
    count = 0
    while j + 2 <= len(user_sequence) and user_sequence[j:j+2] == unit:
        count += 1
        j += 2
    if count >= 3:
        print(f"  {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:j]}")
        findings.append({
            'unit': unit,
            'copies': count,
            'start': i,
            'end': j-1,
            'sequence': user_sequence[i:j]
        })
        for k in range(i, j):
            checked.add(k)

# 2. 三碱基重复 (min_copies=3, 即至少9bp)
print(f"\n🔍 三碱基重复 (min_copies=3, 至少9bp):")
checked = set()
for i in range(len(user_sequence) - 9):
    if i in checked:
        continue
    unit = user_sequence[i:i+3]
    if len(set(unit)) == 1:  # 跳过AAA, TTT, CCC, GGG
        continue
    j = i
    count = 0
    while j + 3 <= len(user_sequence) and user_sequence[j:j+3] == unit:
        count += 1
        j += 3
    if count >= 3:
        print(f"  {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:j]}")
        findings.append({
            'unit': unit,
            'copies': count,
            'start': i,
            'end': j-1,
            'sequence': user_sequence[i:j]
        })
        for k in range(i, j):
            checked.add(k)

# 3. 四碱基重复 (min_copies=3, 即至少12bp)
print(f"\n🔍 四碱基重复 (min_copies=3, 至少12bp):")
checked = set()
for i in range(len(user_sequence) - 12):
    if i in checked:
        continue
    unit = user_sequence[i:i+4]
    if len(set(unit)) <= 2:  # 跳过简单重复
        continue
    j = i
    count = 0
    while j + 4 <= len(user_sequence) and user_sequence[j:j+4] == unit:
        count += 1
        j += 4
    if count >= 3:
        print(f"  {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:min(j, i+60)]}")
        findings.append({
            'unit': unit,
            'copies': count,
            'start': i,
            'end': j-1,
            'sequence': user_sequence[i:j]
        })
        for k in range(i, j):
            checked.add(k)

# 4. 五碱基重复 (min_copies=3, 即至少15bp)
print(f"\n🔍 五碱基重复 (min_copies=3, 至少15bp):")
checked = set()
for i in range(len(user_sequence) - 15):
    if i in checked:
        continue
    unit = user_sequence[i:i+5]
    if len(set(unit)) <= 2:
        continue
    j = i
    count = 0
    while j + 5 <= len(user_sequence) and user_sequence[j:j+5] == unit:
        count += 1
        j += 5
    if count >= 3:
        print(f"  {unit}×{count} 在位置 {i}-{j-1}: {user_sequence[i:min(j, i+60)]}")
        findings.append({
            'unit': unit,
            'copies': count,
            'start': i,
            'end': j-1,
            'sequence': user_sequence[i:j]
        })
        for k in range(i, j):
            checked.add(k)

# 总结
print(f"\n{'='*100}")
print(f"📊 总结")
print(f"{'='*100}")

if findings:
    print(f"\n✅ 找到 {len(findings)} 个串联重复（min_copies=3）:")
    for i, f in enumerate(findings, 1):
        print(f"  {i}. {f['unit']}×{f['copies']} 在位置 {f['start']}-{f['end']} ({f['end']-f['start']+1}bp)")
else:
    print("\n⬜ 未找到任何串联重复（即使使用 min_copies=3）")

print(f"\n{'='*100}\n")
