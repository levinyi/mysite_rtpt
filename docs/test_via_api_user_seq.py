#!/usr/bin/env python3
"""
通过API测试用户序列
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

user_sequence = "ATGACTACATATAATACGAACGAACCCCTAGGTTCTGCTAGCGCAAAAGTTCTGTACGACAACGCCCAAAACTTTGATCACCTGAGCAATGACCGCGTTAATGAAACCTGGGATGACCGCTTCGGCGTGCCGCGTCTGACCTGGCACGGCATGGAAGAGCGTTACAAAACCGCGCTGGCAAATCTGGGCTTAAATCCGGTTGGGACGTTTCAGGGTGGCGCAGTGATCAACTCGGCGGGTGACATTATCCAAGACGAGACTACCGGCGCTTGGTATCGCTGGGACGATCTGACCACCCTGCCGAAGACCGTGCCACCGGGATCGACCCCTGATAGCAGCGGTGGTACCGGTGTCGGTAAATGGCTGGCTGTCGATGTCTCCGATGTGCTGAGACGTGAACTGGCGCTTCCGACCGGCGCGGATCAGATTGGCTACGGCGACGTTACCGTTGCAGAGCGCCTCAGCTATGATGTGTACTTCACCGGCGGTAGCGGAGCAACCAAAGAGGAGATCCAGGCGTTTCTGGATGAGAACGCGGGTCGAAACTGCCATTTTCCGCCAGGTGACTTCGACATCGAGTGGGGTATGATTCCGCGTAATACCACCATTACCGGTGCGCAAGCTGTGACCGTCCGTAGCCACAGTATGCGCCACGAAGCTACGACTCTGGCAACTCTCATTTCGGATCCGGGTTTTACCCGTTTCAACTTGAAGGGCACGCCGGCGACATACGTTTTGACAGACGTGGTTGAAGGTGCCGATGACCCGGCGATTAGCGCGGGTCTGTGCATCTGCGACCACGGTATTAGCATTAACAACGTGGTCCTTATGGGTTGGCGTAAACGTACCGATGGCACCCTGGAAGCACCGAGCTTAACCGGGGTCGATGATGTTGGTGCCACTGCGTGTTTCAGCTATGGTCTGTTCGTGCCGGCAGTATCTGGCCTGACCCTCTCTGGTACTGCGGTGATCGGCTACTTTGCCAACGACGCAGTTTTGCTGGACTGTAGCCGTAGCGACCAGAATAACGGTAGCGGTAATACCTTTAATATCAATGGCCGTATTAATTCCCAATCCATGTGCGATCTGTCCTTCGATAATTTTTTCGCGTGGCCGCTGGACCCGAAGCAGCCGACACAGCTGGTTTCCGCGATCTCAAGCTACGGCCTCAAGTTGAAGGGCACGGATCGTGATATTCGTGACGGGACCAAGTATCCGCAGGGTGCGAACGGCTACGCTCTGAACTGGATTTGGGGTGGTACGGGCACGTCAGACTTGTTCTTCTCTAACTCCGTGATCAGAGGTGTTTATCTGGATGCGGCGATTAACACGGCGGAAAAACCCGCCAACCGTATGAACGATTATGCAACCGACGGATCCGGCAGCGGCACGACCAGCGTGAACGGTTACCCAAAGGAGTGGCAGGACGGTCGCGGTTCGAAGCTGTTCTTTGTTAACACCACCATCCGCGTGGGCAACCTATATATGAATCGTGTCGCGAACGTGAATCTTGTTAACACGTACAGCGAAGCTGGCACTCATTATATGACCAATTTGACCGGTCGTGTTTCGATCATCGGGGGACATAATGGTCTGGGCGTTTCCGACCTGACGGTGAACAATGTTGACGGTTCTGCTCCGACCGCGTATAACCGTTTGTTCAGCGCGAACTGGATCTGCATTGGCACCGCTAACCCGATGCGTTTGGGACCGGTGTACGAAAGCGGCAGCCACGCCTATCTGCGTCCGCATCGTGATGGCACAATTTCCCTGGGTACTGACGAGGGCACCGGCGTCGGCGCTCTGCGCTACCGCTACGCTGTGATCCATGTTGTGTCTGGCAGCTTTGGTAACATTACCAGCCCGAATAACGTTATCCAAGCGAACAAACCGGTTCGCATCCCGTCTTTCACCACTGCGCTGCGTCCGAGCCTCAACGCGGCTGACGCTGGTGCGCAAATCCTGGACACCACCCTGGGCTACGCCATCACGTGGACCGGTAGTGCGTGGAAAGATGGTGTGGGTAACATCGTG"

print("="*80)
print("🧪 通过API测试用户序列")
print("="*80)

print(f"\n序列长度: {len(user_sequence)} bp")

# 测试1：默认参数
print(f"\n{'='*80}")
print("测试1: 默认参数")
print(f"{'='*80}")

data1 = {
    "sequences": [{
        "gene_id": "UserSequence_Default",
        "sequence": user_sequence
    }]
}

try:
    response = requests.post(API_URL, json=data1, timeout=60)
    if response.status_code == 200:
        result = response.json()
        gene_data = result['data']['UserSequence_Default']

        print(f"\n✅ API响应成功")
        print(f"总惩罚分: {gene_data['summary']['total_penalty_score']}")

        # Tandem Repeats
        tandems = gene_data['features'].get('TandemRepeats', [])
        print(f"\n📍 Tandem Repeats: {len(tandems)} 个")
        if tandems:
            for i, t in enumerate(tandems, 1):
                print(f"  {i}. 位置 {t['start']}-{t['end']} (长度 {t['length']}bp)")
                print(f"     序列: {t['sequence'][:80]}{'...' if len(t['sequence']) > 80 else ''}")
                print(f"     罚分: {t['penalty_score']}")

        # 其他特征概览
        print(f"\n📊 其他特征:")
        features_summary = {
            'Homopolymers': len(gene_data['features'].get('Homopolymers', [])),
            'PalindromeRepeats': len(gene_data['features'].get('PalindromeRepeats', [])),
            'InvertedRepeats': len(gene_data['features'].get('InvertedRepeats', [])),
            'LongRepeats': len(gene_data['features'].get('LongRepeats', [])),
            'HighGC': len(gene_data['features'].get('HighGC', [])),
            'LowGC': len(gene_data['features'].get('LowGC', [])),
        }
        for feature_name, count in features_summary.items():
            if count > 0:
                score = gene_data['summary'].get(f'{feature_name}_penalty_score', 0)
                print(f"  • {feature_name}: {count} 个, 罚分 {score}")

    else:
        print(f"❌ API错误: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ 异常: {str(e)}")

# 测试2：宽松参数 (min_copies=3)
print(f"\n{'='*80}")
print("测试2: 宽松参数 (tandem_min_copies=3)")
print(f"{'='*80}")

data2 = {
    "sequences": [{
        "gene_id": "UserSequence_Relaxed",
        "sequence": user_sequence
    }],
    "parameters": {
        "tandem_min_copies": 3
    }
}

try:
    response = requests.post(API_URL, json=data2, timeout=60)
    if response.status_code == 200:
        result = response.json()
        gene_data = result['data']['UserSequence_Relaxed']

        tandems = gene_data['features'].get('TandemRepeats', [])
        print(f"\n✅ Tandem Repeats: {len(tandems)} 个")
        if tandems:
            for i, t in enumerate(tandems, 1):
                print(f"  {i}. 位置 {t['start']}-{t['end']} (长度 {t['length']}bp)")
                print(f"     序列: {t['sequence']}")
                print(f"     罚分: {t['penalty_score']}")
        else:
            print("  未检测到")

    else:
        print(f"❌ API错误: {response.status_code}")

except Exception as e:
    print(f"❌ 异常: {str(e)}")

print(f"\n{'='*80}")
print("✅ 测试完成")
print("="*80)
