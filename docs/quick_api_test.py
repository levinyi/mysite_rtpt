#!/usr/bin/env python3
"""
快速 API 测试脚本 - 验证新特征

使用方法:
    python docs/quick_api_test.py
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

# 测试序列
test_sequences = {
    "Test_Tandem_Simple": "ATCATCATCATCGGGAAATTTCCC",
    "Test_Palindrome_Simple": "ATCGATCGATCGATCGATCG",
    "Test_Hairpin_Perfect": "ATCGATCGATCGAAAAATCGATCGATCG",
    "Test_Mixed_All": "AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG"
}

def test_sequence(gene_id, sequence):
    """测试单个序列"""
    print(f"\n{'='*60}")
    print(f"🧬 测试: {gene_id}")
    print(f"{'='*60}")
    print(f"序列: {sequence[:50]}{'...' if len(sequence) > 50 else ''}")
    print(f"长度: {len(sequence)} bp")

    data = {
        "sequences": [{
            "gene_id": gene_id,
            "sequence": sequence
        }]
    }

    try:
        response = requests.post(API_URL, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            gene_data = result['data'][gene_id]
            summary = gene_data['summary']
            features = gene_data['features']

            print(f"\n📊 分析结果:")
            print(f"  总惩罚分: {summary['total_penalty_score']}")

            # 检查三个新特征
            print(f"\n🔍 新特征检测:")

            # Tandem Repeats
            tandem_count = len(features.get('TandemRepeats', []))
            tandem_score = summary.get('TandemRepeats_penalty_score', 0)
            status = "✅" if tandem_count > 0 else "⬜"
            print(f"  {status} Tandem Repeats: {tandem_count} 个, 罚分 {tandem_score}")
            if tandem_count > 0:
                for i, item in enumerate(features['TandemRepeats'][:2], 1):
                    print(f"     {i}. 位置 {item['start']}-{item['end']}, 长度 {item['length']} bp")

            # Palindrome Repeats
            palindrome_count = len(features.get('PalindromeRepeats', []))
            palindrome_score = summary.get('PalindromeRepeats_penalty_score', 0)
            status = "✅" if palindrome_count > 0 else "⬜"
            print(f"  {status} Palindrome Repeats: {palindrome_count} 个, 罚分 {palindrome_score}")
            if palindrome_count > 0:
                for i, item in enumerate(features['PalindromeRepeats'][:2], 1):
                    print(f"     {i}. 位置 {item['start']}-{item['end']}, 长度 {item['length']} bp")

            # Inverted Repeats
            inverted_count = len(features.get('InvertedRepeats', []))
            inverted_score = summary.get('InvertedRepeats_penalty_score', 0)
            status = "✅" if inverted_count > 0 else "⬜"
            print(f"  {status} Inverted Repeats: {inverted_count} 个, 罚分 {inverted_score}")
            if inverted_count > 0:
                for i, item in enumerate(features['InvertedRepeats'][:2], 1):
                    print(f"     {i}. 类型 {item['type']}, stem {item['stem_length']} bp, loop {item['loop_length']} bp")

            # 其他特征概览
            print(f"\n📋 其他特征:")
            other_features = {
                'Homopolymers': '单碱基重复',
                'LongRepeats': '分散重复',
                'W12S12Motifs': 'W/S motifs',
                'HighGC': '高GC区域',
                'LowGC': '低GC区域',
                'DoubleNT': '二核苷酸重复'
            }
            for key, name in other_features.items():
                count = len(features.get(key, []))
                if count > 0:
                    score = summary.get(f'{key}_penalty_score', 0)
                    print(f"  • {name}: {count} 个, 罚分 {score}")

            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print(" 快速 API 测试 - 验证新特征")
    print("="*60)

    results = {}
    for gene_id, sequence in test_sequences.items():
        success = test_sequence(gene_id, sequence)
        results[gene_id] = success

    # 总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for gene_id, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status}: {gene_id}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！新特征工作正常！")
    else:
        print("\n⚠️  部分测试失败，请检查 API 服务。")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
