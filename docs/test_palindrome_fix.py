#!/usr/bin/env python3
"""
测试 Palindrome Repeats 算法修复
验证DNA回文的正确检测
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

print("="*80)
print("🧬 Palindrome Repeats 算法修复验证")
print("="*80)
print("\nDNA回文定义: 序列 == 反向互补序列")
print("  例如: ATCGAT → 反向互补 ATCGAT (是DNA回文)")
print("       CGGGGGC → 反向互补 GCCCCCG (不是DNA回文)")
print("="*80)

# 测试序列
test_cases = [
    {
        "name": "User_Reported_Bug",
        "sequence": "ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG",
        "description": "用户报告的问题序列，CGGGGGGGGGGGGGC不应该是回文",
        "expected": "应该没有回文（或只有真正的DNA回文）"
    },
    {
        "name": "True_Palindrome_1",
        "sequence": "AAAAAATCGATAAAAA",
        "description": "真正的DNA回文: ATCGAT",
        "expected": "应检测到 ATCGAT (6bp)"
    },
    {
        "name": "True_Palindrome_2",
        "sequence": "GGGGGAATTCGGGG",
        "description": "EcoRI限制性位点: GAATTC",
        "expected": "应检测到 GAATTC (6bp) - 但低于min_len=15"
    },
    {
        "name": "True_Palindrome_Long",
        "sequence": "AAAACTAGTACTAGTAGCTAGGGGG",
        "description": "长回文: CTAGTACTAGTAG (13bp回文部分)",
        "expected": "可能检测到较长的DNA回文"
    },
    {
        "name": "String_Palindrome_Not_DNA",
        "sequence": "AAACGGGGGGGGGGGCAAA",
        "description": "字符串回文但不是DNA回文: CGGGGGGGGGGGGGC",
        "expected": "不应该检测到回文"
    },
    {
        "name": "Homopolymer",
        "sequence": "AAAGGGGGGGGGGGAAA",
        "description": "Homopolymer: GGGGGGGGGGGG (13个G)",
        "expected": "不应该检测到回文"
    }
]

def reverse_complement(seq):
    """计算反向互补"""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(complement[base] for base in reversed(seq.upper()))

def check_palindrome_manually(seq):
    """手动检查是否是DNA回文"""
    rc = reverse_complement(seq)
    return seq == rc

# 测试每个序列
for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"测试 #{i}: {test_case['name']}")
    print(f"{'='*80}")
    print(f"序列: {test_case['sequence']}")
    print(f"说明: {test_case['description']}")
    print(f"预期: {test_case['expected']}")

    # 手动检查序列中是否有DNA回文
    seq = test_case['sequence']
    print(f"\n手动验证:")
    for start in range(len(seq) - 5):
        for length in [6, 8, 10, 12, 14, 16, 18, 20]:
            if start + length <= len(seq):
                subseq = seq[start:start+length]
                if check_palindrome_manually(subseq):
                    print(f"  ✓ 位置 {start}-{start+length-1}: {subseq} 是DNA回文")

    # 通过API测试
    data = {
        "sequences": [{
            "gene_id": test_case['name'],
            "sequence": test_case['sequence']
        }],
        "parameters": {
            "palindrome_min_len": 15
        }
    }

    try:
        response = requests.post(API_URL, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            gene_data = result['data'][test_case['name']]
            palindromes = gene_data['features'].get('PalindromeRepeats', [])

            print(f"\nAPI 检测结果:")
            if palindromes:
                print(f"  ✅ 检测到 {len(palindromes)} 个回文:")
                for j, pal in enumerate(palindromes, 1):
                    print(f"     {j}. 序列: {pal['sequence']}")
                    print(f"        位置: {pal['start']}-{pal['end']}")
                    print(f"        长度: {pal['length']} bp")
                    print(f"        罚分: {pal['penalty_score']}")
                    # 验证
                    if check_palindrome_manually(pal['sequence']):
                        print(f"        验证: ✅ 确实是DNA回文")
                    else:
                        print(f"        验证: ❌ 不是DNA回文！(BUG)")
            else:
                print(f"  ⬜ 未检测到回文 (min_len=15)")

        else:
            print(f"  ❌ API错误: {response.status_code}")

    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")

# 特别关注用户报告的问题
print(f"\n{'='*80}")
print("🎯 重点验证: 用户报告的问题序列")
print(f"{'='*80}")

problem_seq = "ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG"
problem_region = "CGGGGGGGGGGGGGC"  # 位置 14-28

print(f"\n完整序列: {problem_seq}")
print(f"问题区域: {problem_region} (位置 14-28)")
print(f"\n检查这个区域是否是DNA回文:")
print(f"  原序列:     {problem_region}")
print(f"  反向互补:   {reverse_complement(problem_region)}")
print(f"  是DNA回文?  {check_palindrome_manually(problem_region)}")

if check_palindrome_manually(problem_region):
    print(f"\n  ❌ 这是DNA回文，不应该被排除")
else:
    print(f"\n  ✅ 这不是DNA回文，修复后不应该被检测到！")

print("\n" + "="*80)
print("✅ 测试完成")
print("="*80)
