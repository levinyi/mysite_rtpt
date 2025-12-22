#!/usr/bin/env python3
"""
测试关键Bug修复：Palindrome Repeats min_len 奇数问题
"""

import requests
import json

API_URL = "http://192.168.3.185:8000/tools/api/sequence-analysis/"

print("="*80)
print("🐛 测试关键Bug修复：Palindrome Repeats")
print("="*80)
print("\n问题：min_len=15（默认值，奇数）导致功能完全失效")
print("原因：DNA回文必须是偶数长度，但算法从奇数开始搜索")
print("修复：自动将奇数 min_len 调整为偶数")
print("="*80)

# 测试序列：包含真正的DNA回文
test_cases = [
    {
        "name": "Test_Default_MinLen_15",
        "sequence": "AAAAATCGATCGATCGATAAAAA",  # 包含 18bp 的DNA回文
        "min_len": 15,  # 默认值（奇数）
        "expected": "修复前：找不到; 修复后：应该找到 18bp 回文"
    },
    {
        "name": "Test_Even_MinLen_16",
        "sequence": "AAAAATCGATCGATCGATAAAAA",
        "min_len": 16,  # 偶数
        "expected": "修复前后都应该能找到 18bp 回文"
    },
    {
        "name": "Test_Odd_MinLen_17",
        "sequence": "AAAAATCGATCGATCGATAAAAA",
        "min_len": 17,  # 奇数
        "expected": "修复前：找不到; 修复后：自动调整为18，应该找到"
    },
    {
        "name": "Test_Real_Palindrome",
        "sequence": "GGGATCGATCGATCGATCGGGGG",  # 20bp DNA回文
        "min_len": 15,
        "expected": "应该检测到 20bp 的DNA回文"
    }
]

def test_palindrome_with_min_len(test_case):
    """测试特定 min_len 的 Palindrome 检测"""
    print(f"\n{'='*80}")
    print(f"🧪 测试: {test_case['name']}")
    print(f"{'='*80}")
    print(f"序列: {test_case['sequence']}")
    print(f"min_len: {test_case['min_len']} ({'奇数' if test_case['min_len'] % 2 != 0 else '偶数'})")
    print(f"预期: {test_case['expected']}")

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
                print(f"  ✅ 成功检测到 {len(palindromes)} 个DNA回文:")
                for j, pal in enumerate(palindromes, 1):
                    print(f"     {j}. 序列: {pal['sequence']}")
                    print(f"        位置: {pal['start']}-{pal['end']}")
                    print(f"        长度: {pal['length']} bp")
                    print(f"        罚分: {pal['penalty_score']}")
                return True
            else:
                print(f"  ❌ 未检测到DNA回文")
                print(f"  ⚠️  如果预期应该检测到，这说明Bug仍然存在！")
                return False

        else:
            print(f"  ❌ API错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        return False

# 运行所有测试
print("\n\n" + "="*80)
print("🚀 开始测试")
print("="*80)

results = {}
for test_case in test_cases:
    success = test_palindrome_with_min_len(test_case)
    results[test_case['name']] = success

# 总结
print(f"\n\n{'='*80}")
print("📊 测试总结")
print(f"{'='*80}\n")

total = len(results)
passed = sum(1 for v in results.values() if v)

for name, success in results.items():
    status = "✅ 通过" if success else "❌ 失败"
    print(f"  {status}: {name}")

print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

# 关键验证
print(f"\n{'='*80}")
print("🔍 关键验证")
print(f"{'='*80}")

if results.get("Test_Default_MinLen_15"):
    print("\n✅ 关键修复成功！")
    print("   使用默认参数 min_len=15（奇数）现在可以正常工作")
    print("   算法自动将15调整为16（偶数）")
else:
    print("\n❌ 关键修复失败！")
    print("   使用默认参数 min_len=15 仍然无法检测DNA回文")
    print("   Bug可能没有完全修复")

print(f"\n{'='*80}")
print("💡 技术说明")
print(f"{'='*80}")
print("""
DNA回文的数学特性：
- DNA回文必须是偶数长度
- 原因：seq == reverse_complement(seq)
- 例如：ATCGAT (6bp) → 反向互补 ATCGAT ✓
- 但是：ATCGATA (7bp) → 反向互补 TATCGAT ✗ (长度不同)

修复方法：
- 在算法开始时检查 min_len
- 如果是奇数，自动加1变为偶数
- 确保搜索从偶数长度开始
""")

print("="*80 + "\n")
