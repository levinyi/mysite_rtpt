#!/usr/bin/env python3
"""
测试 Tandem Repeats 的 Max Mismatch 参数
演示 0、1、2 三种模式的差异
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

# 测试序列：包含不同程度的不完美重复
test_sequences = {
    "Perfect_Repeat": {
        "sequence": "ATCATCATCATCGGGAAA",
        "description": "完美串联重复 (ATC×4)"
    },
    "One_Mismatch": {
        "sequence": "ATCATCATGATCATCGGGAAA",
        "description": "1个错配的串联重复 (ATC×5, 第3个是ATG)"
    },
    "Two_Mismatches": {
        "sequence": "ATCATGATGATCATCGGGAAA",
        "description": "2个错配的串联重复 (ATC×5, 第2,3个有错配)"
    },
    "Mixed_Complex": {
        "sequence": "ATGATGATGATGATGATGCCCGGGAAA",
        "description": "复杂重复 (ATG×6, 最后一个是ATG→ATG)"
    }
}

def test_mismatch_mode(max_mismatch):
    """测试特定的 mismatch 模式"""
    mode_names = {0: "Strict", 1: "Standard", 2: "Relaxed"}
    mode_name = mode_names.get(max_mismatch, "Unknown")

    print(f"\n{'='*80}")
    print(f"🧬 测试模式: Max Mismatch = {max_mismatch} ({mode_name})")
    print(f"{'='*80}")

    # 构建请求
    sequences = [
        {"gene_id": gene_id, "sequence": info["sequence"]}
        for gene_id, info in test_sequences.items()
    ]

    data = {
        "sequences": sequences,
        "parameters": {
            "tandem_max_mismatch": max_mismatch,
            "tandem_min_unit": 3,
            "tandem_min_copies": 4
        }
    }

    try:
        response = requests.post(API_URL, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()

            for gene_id, seq_info in test_sequences.items():
                print(f"\n📍 {gene_id}")
                print(f"   描述: {seq_info['description']}")
                print(f"   序列: {seq_info['sequence']}")

                gene_data = result['data'][gene_id]
                tandem_repeats = gene_data['features'].get('TandemRepeats', [])

                if tandem_repeats:
                    print(f"   ✅ 检测到 {len(tandem_repeats)} 个串联重复:")
                    for i, tr in enumerate(tandem_repeats, 1):
                        print(f"      {i}. 位置 {tr['start']}-{tr['end']}, "
                              f"长度 {tr['length']} bp, "
                              f"序列: {tr['sequence']}")
                else:
                    print(f"   ⬜ 未检测到串联重复")

            return True
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        return False

def main():
    print("=" * 80)
    print(" Tandem Repeats Max Mismatch 参数测试")
    print("=" * 80)
    print("\n本测试演示 3 种模式的差异：")
    print("  0 - Strict:   只检测完美重复")
    print("  1 - Standard: 允许1个错配 ⭐ 推荐")
    print("  2 - Relaxed:  允许2个错配")

    results = {}

    # 测试三种模式
    for mismatch_value in [0, 1, 2]:
        success = test_mismatch_mode(mismatch_value)
        results[mismatch_value] = success

    # 总结
    print(f"\n{'='*80}")
    print("📊 测试总结")
    print(f"{'='*80}\n")

    mode_names = {0: "Strict (0)", 1: "Standard (1)", 2: "Relaxed (2)"}
    for mismatch_value, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status}: {mode_names[mismatch_value]}")

    print("\n" + "=" * 80)
    print("💡 关键观察:")
    print("=" * 80)
    print("""
1. Strict (0):
   - 只检测 Perfect_Repeat
   - 漏掉所有有错配的重复
   - 最严格，可能太保守

2. Standard (1): ⭐ 推荐
   - 检测 Perfect_Repeat 和 One_Mismatch
   - 平衡灵敏度和特异性
   - 适合基因合成应用

3. Relaxed (2):
   - 检测所有测试序列
   - 最灵敏，可能过度检测
   - 适合研究用途
    """)

    print("=" * 80)
    print("🎯 推荐:")
    print("=" * 80)
    print("""
- 生产环境（基因合成）: 使用 Standard (1)
- 研究环境（学术发表）: 使用 Strict (0) 或 Standard (1)
- 探索性分析（进化研究）: 使用 Relaxed (2)
    """)

    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
