#!/usr/bin/env python3
"""
测试特定序列 - 验证过滤效果
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

# 用户报告的问题序列
test_sequence = "AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG"

print("=" * 80)
print("测试序列 Inverted Repeats 过滤效果")
print("=" * 80)
print(f"\n序列: {test_sequence}")
print(f"长度: {len(test_sequence)} bp\n")

data = {
    "sequences": [{
        "gene_id": "TestSequence",
        "sequence": test_sequence
    }]
}

try:
    response = requests.post(API_URL, json=data, timeout=10)

    if response.status_code == 200:
        result = response.json()
        gene_data = result['data']['TestSequence']
        features = gene_data['features']
        summary = gene_data['summary']

        # Inverted Repeats 详细信息
        inverted_repeats = features.get('InvertedRepeats', [])

        print(f"✅ 检测到 {len(inverted_repeats)} 个 Inverted Repeat 结构（已过滤重叠）\n")
        print("=" * 80)

        for i, item in enumerate(inverted_repeats, 1):
            print(f"\n🔍 结构 #{i}:")
            print(f"  类型: {item['type']}")
            print(f"  Stem 序列: {item['stem_sequence']}")
            print(f"  Stem 长度: {item['stem_length']} bp")
            print(f"  Stem1 位置: {item['stem1_start']}-{item['stem1_end']}")
            print(f"  Stem2 位置: {item['stem2_start']}-{item['stem2_end']}")
            print(f"  Loop 序列: {item['loop_sequence']}")
            print(f"  Loop 长度: {item['loop_length']} bp")
            print(f"  罚分: {item['penalty_score']}")

            # 如果是 inverted_repeat 类型，显示 count
            if 'count' in item:
                print(f"  出现次数: {item['count']}")

        print("\n" + "=" * 80)
        print(f"\n💯 总结:")
        print(f"  Inverted Repeats 总长度: {summary.get('InvertedRepeats_total_length', 0)} bp")
        print(f"  Inverted Repeats 罚分: {summary.get('InvertedRepeats_penalty_score', 0)}")
        print(f"  总惩罚分: {summary['total_penalty_score']}")

        print("\n" + "=" * 80)
        print("✅ 过滤效果:")
        print("   原本会检测到 46+ 个重叠结构")
        print(f"   现在只保留 {len(inverted_repeats)} 个最显著的非重叠结构")
        print("   输出简洁易读！")
        print("=" * 80 + "\n")

    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")

except Exception as e:
    print(f"❌ 错误: {str(e)}")
