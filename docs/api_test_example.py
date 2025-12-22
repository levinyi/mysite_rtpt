#!/usr/bin/env python3
"""
DNA Sequence Analysis API 测试脚本

使用方法:
    python api_test_example.py

修改 API_URL 变量为你的实际 API 地址
"""

import requests
import json

# ============= 配置 =============
API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"
# API_URL = "http://localhost:8000/tools/api/sequence-analysis/"
# API_URL = "http://your-domain.com/tools/api/sequence-analysis/"

# ============= 测试数据 =============

# 测试用例 1: 简单序列
test_case_1 = {
    "sequences": [
        {
            "gene_id": "TestGene1",
            "sequence": "ATCGATCGATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGCATATATATATATAGCTAGCTA"
        }
    ]
}

# 测试用例 2: 多个序列 + 自定义参数
test_case_2 = {
    "sequences": [
        {
            "gene_id": "Gene1",
            "sequence": "ATCGATCGATCGATCGATCGAAAAAAAAATTTTTTTTT"
        },
        {
            "gene_id": "Gene2",
            "sequence": "GCTAGCTAGCTAGCTAATATATATATCGCGCGCG"
        },
        {
            "gene_id": "Gene3",
            "sequence": "AAAAAAAAAATTTTTTTTTCCCCCCCCGGGGGGGG"
        }
    ],
    "parameters": {
        "homopolymers_min_len": 6,
        "tandem_min_copies": 3,
        "palindrome_min_len": 10
    }
}

# 测试用例 3: 包含所有特征的复杂序列
test_case_3 = {
    "sequences": [
        {
            "gene_id": "ComplexGene",
            "sequence": (
                # Homopolymer (A7)
                "AAAAAAA"
                # Tandem repeat (ATC)x4
                "ATCATCATCATC"
                # W12 motif (A/T rich)
                "ATATATATATAT"
                # Palindrome
                "ATCGATCGATCG"
                # High GC region
                "GCGCGCGCGCGCGCGCGCGC"
                # Inverted repeat (potential hairpin)
                "ATCGATCGATCGATCGATCGATCG"
                # Low GC region
                "ATATATATATATATATATAT"
                # Double nucleotide repeat
                "ATATAT"
                # Normal region
                "ACGTACGTACGT"
            )
        }
    ]
}


# ============= 测试函数 =============

def test_api(test_case, case_name):
    """
    测试 API 并打印结果

    Args:
        test_case: 测试数据
        case_name: 测试用例名称
    """
    print(f"\n{'='*60}")
    print(f"测试用例: {case_name}")
    print(f"{'='*60}")

    try:
        # 发送请求
        print(f"正在发送请求到: {API_URL}")
        response = requests.post(API_URL, json=test_case, timeout=30)

        # 检查响应状态
        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # 打印基本信息
            print(f"\n✅ 状态: {result['status']}")
            print(f"📝 消息: {result['message']}")

            # 打印每个基因的分析结果
            for gene_id, gene_data in result['data'].items():
                print(f"\n{'─'*60}")
                print(f"🧬 基因: {gene_id}")
                print(f"{'─'*60}")

                summary = gene_data['summary']
                print(f"\n📊 统计信息:")
                print(f"  • 序列长度: {summary['total_length']} bp")
                print(f"  • 总惩罚分: {summary['total_penalty_score']}")

                print(f"\n🔍 各特征惩罚分:")
                feature_scores = {
                    'LongRepeats': '分散重复',
                    'Homopolymers': '单碱基重复',
                    'W12S12Motifs': 'W12S12 Motifs',
                    'HighGC': '高GC区域',
                    'LowGC': '低GC区域',
                    'DoubleNT': '二核苷酸重复',
                    'TandemRepeats': '串联重复',
                    'PalindromeRepeats': '回文序列',
                    'InvertedRepeats': '倒置重复'
                }

                for key, name in feature_scores.items():
                    score = summary[f'{key}_penalty_score']
                    length = summary[f'{key}_total_length']
                    if score > 0 or length > 0:
                        print(f"  • {name:15s}: 罚分 {score:5.1f}, 长度 {length:4d} bp")

                # 打印具体特征（仅显示有结果的）
                print(f"\n📋 检测到的特征:")
                features = gene_data['features']
                for feature_name, feature_list in features.items():
                    # 只处理列表类型的特征，跳过 'length' 等非列表字段
                    if isinstance(feature_list, list) and feature_list:
                        print(f"  • {feature_name}: {len(feature_list)} 个")

                # 显示一些详细信息（示例）
                tandem_repeats = features.get('TandemRepeats', [])
                if tandem_repeats and isinstance(tandem_repeats, list) and len(tandem_repeats) > 0:
                    print(f"\n  🔸 串联重复详情 (前3个):")
                    for i, item in enumerate(tandem_repeats[:3], 1):
                        print(f"    {i}. 位置: {item['start']}-{item['end']}, "
                              f"长度: {item['length']} bp, "
                              f"罚分: {item['penalty_score']}")

                inverted_repeats = features.get('InvertedRepeats', [])
                if inverted_repeats and isinstance(inverted_repeats, list) and len(inverted_repeats) > 0:
                    print(f"\n  🔸 倒置重复详情 (前3个):")
                    for i, item in enumerate(inverted_repeats[:3], 1):
                        print(f"    {i}. 类型: {item['type']}, "
                              f"stem长度: {item['stem_length']} bp, "
                              f"loop长度: {item['loop_length']} bp, "
                              f"罚分: {item['penalty_score']}")

        else:
            # 打印错误信息
            print(f"\n❌ 请求失败!")
            try:
                error_data = response.json()
                print(f"错误: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"响应内容: {response.text}")

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时! API 可能正在处理大量数据。")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败! 请检查 API_URL 是否正确，服务是否运行。")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")


def save_response_to_file(test_case, filename="api_response.json"):
    """
    保存完整的 API 响应到文件

    Args:
        test_case: 测试数据
        filename: 输出文件名
    """
    try:
        response = requests.post(API_URL, json=test_case, timeout=30)
        if response.status_code == 200:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
            print(f"\n✅ 完整响应已保存到: {filename}")
        else:
            print(f"\n❌ 请求失败，未保存文件")
    except Exception as e:
        print(f"\n❌ 保存文件时出错: {str(e)}")


# ============= 主程序 =============

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" DNA Sequence Analysis API 测试脚本")
    print("="*60)

    # 运行测试用例
    test_api(test_case_1, "测试用例 1: 简单序列")
    test_api(test_case_2, "测试用例 2: 多个序列 + 自定义参数")
    test_api(test_case_3, "测试用例 3: 复杂序列（包含所有特征）")

    # 可选：保存最后一个测试的完整响应
    print(f"\n{'='*60}")
    print("保存完整响应到文件...")
    save_response_to_file(test_case_3, "complex_gene_analysis.json")

    print(f"\n{'='*60}")
    print("✅ 所有测试完成!")
    print(f"{'='*60}\n")
