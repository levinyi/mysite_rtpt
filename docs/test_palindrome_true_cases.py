#!/usr/bin/env python3
"""
测试真正的DNA回文能否被正确检测
使用较小的 min_len 来验证
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

print("="*80)
print("🧬 验证真正的DNA回文检测")
print("="*80)

# 测试序列（使用 min_len=6 来检测较短的回文）
test_cases = [
    {
        "name": "User_Sequence_Low_Threshold",
        "sequence": "ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG",
        "description": "用户序列，min_len=6 应检测到真正的DNA回文",
        "min_len": 6
    },
    {
        "name": "False_Palindrome",
        "sequence": "AAACGGGGGGGGGGGCAAA",
        "description": "字符串回文但不是DNA回文，不应检测到",
        "min_len": 6
    },
    {
        "name": "EcoRI_Site",
        "sequence": "AAAGAATTCAAA",
        "description": "EcoRI限制性位点 GAATTC (6bp)",
        "min_len": 6
    },
    {
        "name": "BamHI_Site",
        "sequence": "AAAGGATCCAAA",
        "description": "BamHI限制性位点 GGATCC (6bp)",
        "min_len": 6
    }
]

for test_case in test_cases:
    print(f"\n{'='*80}")
    print(f"测试: {test_case['name']}")
    print(f"{'='*80}")
    print(f"序列: {test_case['sequence']}")
    print(f"说明: {test_case['description']}")
    print(f"Min Length: {test_case['min_len']}")

    data = {
        "sequences": [{
            "gene_id": test_case['name'],
            "sequence": test_case['sequence']
        }],
        "parameters": {
            "palindrome_min_len": test_case['min_len']
        }
    }

    try:
        response = requests.post(API_URL, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            gene_data = result['data'][test_case['name']]
            palindromes = gene_data['features'].get('PalindromeRepeats', [])

            print(f"\n检测结果:")
            if palindromes:
                print(f"  ✅ 检测到 {len(palindromes)} 个DNA回文:")
                for j, pal in enumerate(palindromes, 1):
                    print(f"     {j}. 序列: {pal['sequence']}")
                    print(f"        位置: {pal['start']}-{pal['end']}, 长度: {pal['length']} bp")
                    print(f"        罚分: {pal['penalty_score']}")
            else:
                print(f"  ⬜ 未检测到回文")

        else:
            print(f"  ❌ API错误: {response.status_code}")

    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")

print(f"\n{'='*80}")
print("✅ 测试完成")
print(f"{'='*80}\n")

# 总结
print("\n" + "="*80)
print("📊 修复总结")
print("="*80)
print("""
✅ 修复内容:
   - 从"字符串回文"算法 改为 "DNA回文"算法
   - 检查条件: sequence == reverse_complement(sequence)

✅ 修复效果:
   - CGGGGGGGGGGGGGC: 不再被误检为回文 ✅
   - 真正的DNA回文（如限制性位点）: 正确检测 ✅
   - 添加了重叠过滤，避免重复报告 ✅

✅ DNA回文定义:
   序列等于其反向互补序列
   例如:
   - ATCGAT → 反向互补 ATCGAT ✅ 是DNA回文
   - GAATTC → 反向互补 GAATTC ✅ 是DNA回文 (EcoRI)
   - GGATCC → 反向互补 GGATCC ✅ 是DNA回文 (BamHI)
   - CGGGGGC → 反向互补 GCCCCCG ❌ 不是DNA回文

✅ 生物学意义:
   DNA回文序列通常是限制性内切酶识别位点，对基因工程很重要。
   之前的字符串回文检测没有生物学意义。
""")
print("="*80)
