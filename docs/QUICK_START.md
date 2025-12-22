# DNA Sequence Analysis API - 快速开始

## 🚀 API 地址

```
POST http://192.168.3.185:8000/tools/api/sequence-analysis/
```

---

## 📝 最简单的使用示例

### Python

```python
import requests

response = requests.post(
    'http://192.168.3.185:8000/tools/api/sequence-analysis/',
    json={
        "sequences": [{
            "gene_id": "MyGene",
            "sequence": "ATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGC"
        }]
    }
)

result = response.json()
print(f"惩罚分: {result['data']['MyGene']['summary']['total_penalty_score']}")
```

### cURL

```bash
curl -X POST http://192.168.3.185:8000/tools/api/sequence-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [{
      "gene_id": "MyGene",
      "sequence": "ATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGC"
    }]
  }'
```

---

## 🎯 分析的特征（9种）

1. **LongRepeats** - 分散重复序列
2. **Homopolymers** - 单碱基重复 (AAAAAA...)
3. **W12S12Motifs** - A/T 或 G/C 富集区域
4. **HighGC** - 高 GC 含量区域
5. **LowGC** - 低 GC 含量区域
6. **DoubleNT** - 二核苷酸重复 (ATATAT...)
7. **TandemRepeats** ⭐ - 串联重复序列
8. **PalindromeRepeats** ⭐ - 回文序列
9. **InvertedRepeats** ⭐ - 倒置重复（Hairpin、Stem-Loop）

---

## 📊 返回的数据

```json
{
  "status": "success",
  "data": {
    "MyGene": {
      "summary": {
        "total_length": 40,
        "total_penalty_score": 21.5,
        "TandemRepeats_penalty_score": 3.5,
        "PalindromeRepeats_penalty_score": 2.0,
        "InvertedRepeats_penalty_score": 1.5
      },
      "features": {
        "TandemRepeats": [...],
        "PalindromeRepeats": [...],
        "InvertedRepeats": [...]
      }
    }
  }
}
```

---

## ⚙️ 可选参数

```json
{
  "sequences": [...],
  "parameters": {
    "homopolymers_min_len": 7,
    "tandem_min_copies": 4,
    "palindrome_min_len": 15,
    "inverted_min_stem_len": 10
  }
}
```

---

## 🧪 测试工具

运行测试脚本：
```bash
cd /cygene4/dushiyi/mysite_rtpt
python docs/api_test_example.py
```

---

## 📚 完整文档

- **API 文档**: `docs/API_SEQUENCE_ANALYSIS.md`
- **测试报告**: `docs/API_TEST_REPORT.md`
- **测试脚本**: `docs/api_test_example.py`

---

## ✅ 测试状态

**最后测试**: 2025-01-06
**状态**: ✅ 所有测试通过
**通过率**: 100%

---

**需要帮助？** 查看完整文档或联系技术支持。
