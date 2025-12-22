# DNA Sequence Analysis API 文档

## 📋 概述

本 API 提供 DNA 序列的全面分析功能，包括重复序列检测、GC 含量分析等。

**API 端点：** `POST /tools/api/sequence-analysis/`

---

## 🔑 认证

当前版本：**无需认证**（未来版本可能需要 API Key）

---

## 📤 请求格式

### HTTP 方法
```
POST
```

### Content-Type
```
application/json
```

### 请求体结构

```json
{
    "sequences": [
        {
            "gene_id": "string",
            "sequence": "string (DNA序列，仅包含ATCG)"
        }
    ],
    "parameters": {
        "long_repeats_min_len": 16,
        "homopolymers_min_len": 7,
        "min_w_length": 12,
        "min_s_length": 12,
        "window_size": 30,
        "min_gc_content": 20,
        "max_gc_content": 80,
        "tandem_min_unit": 3,
        "tandem_min_copies": 4,
        "tandem_max_mismatch": 1,
        "palindrome_min_len": 15,
        "inverted_min_stem_len": 10
    }
}
```

### 字段说明

#### sequences (必需)
- **类型**: Array
- **说明**: 要分析的 DNA 序列列表
- **限制**:
  - 最多 100 个序列
  - 每个序列最长 50,000 bp
  - 只能包含 A、T、C、G 字符（大小写不敏感）

#### gene_id (必需)
- **类型**: String
- **说明**: 基因或序列的唯一标识符

#### sequence (必需)
- **类型**: String
- **说明**: DNA 序列字符串

#### parameters (可选)
所有参数都有默认值，可以省略整个 `parameters` 对象。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `long_repeats_min_len` | int | 16 | 分散重复的最小长度 |
| `homopolymers_min_len` | int | 7 | 单碱基重复的最小长度 |
| `min_w_length` | int | 12 | W motif (A/T富集) 最小长度 |
| `min_s_length` | int | 12 | S motif (G/C富集) 最小长度 |
| `window_size` | int | 30 | GC 含量分析窗口大小 |
| `min_gc_content` | int | 20 | 低 GC 含量阈值 (%) |
| `max_gc_content` | int | 80 | 高 GC 含量阈值 (%) |
| `tandem_min_unit` | int | 3 | 串联重复最小单元长度 |
| `tandem_min_copies` | int | 4 | 串联重复最小重复次数 |
| `tandem_max_mismatch` | int | 1 | 串联重复允许的最大错配数 |
| `palindrome_min_len` | int | 15 | 回文序列最小长度 |
| `inverted_min_stem_len` | int | 10 | 倒置重复最小 stem 长度 |

---

## 📥 响应格式

### 成功响应 (HTTP 200)

```json
{
    "status": "success",
    "message": "Analysis completed successfully",
    "data": {
        "Gene1": {
            "summary": {
                "total_length": 1000,
                "total_penalty_score": 25.5,
                "LongRepeats_penalty_score": 5.0,
                "Homopolymers_penalty_score": 3.5,
                "W12S12Motifs_penalty_score": 2.0,
                "HighGC_penalty_score": 4.0,
                "LowGC_penalty_score": 3.0,
                "DoubleNT_penalty_score": 2.0,
                "TandemRepeats_penalty_score": 3.0,
                "PalindromeRepeats_penalty_score": 2.0,
                "InvertedRepeats_penalty_score": 1.0,
                "LongRepeats_total_length": 150,
                "Homopolymers_total_length": 70,
                "W12S12Motifs_total_length": 48,
                "HighGC_total_length": 90,
                "LowGC_total_length": 60,
                "DoubleNT_total_length": 36,
                "TandemRepeats_total_length": 60,
                "PalindromeRepeats_total_length": 45,
                "InvertedRepeats_total_length": 40
            },
            "features": {
                "LongRepeats": [
                    {
                        "sequence": "ATCGATCGATCG...",
                        "start": [10, 100],
                        "end": [25, 115],
                        "length": 16,
                        "gc_content": 50.0,
                        "penalty_score": 0.5
                    }
                ],
                "Homopolymers": [...],
                "W12S12Motifs": [...],
                "HighGC": [...],
                "LowGC": [...],
                "DoubleNT": [...],
                "TandemRepeats": [...],
                "PalindromeRepeats": [...],
                "InvertedRepeats": [
                    {
                        "type": "hairpin",
                        "stem_sequence": "ATCGATCG",
                        "stem_length": 8,
                        "stem1_start": 10,
                        "stem1_end": 17,
                        "stem2_start": 24,
                        "stem2_end": 31,
                        "loop_sequence": "ATAT",
                        "loop_length": 4,
                        "full_sequence": "ATCGATCGATATCGATCGAT",
                        "penalty_score": 1.0
                    }
                ]
            }
        }
    }
}
```

### 错误响应

#### 400 Bad Request
```json
{
    "status": "error",
    "message": "Invalid JSON format"
}
```

常见错误信息：
- `"Missing required field: sequences"`
- `"sequences list cannot be empty"`
- `"Too many sequences. Maximum allowed: 100"`
- `"Each sequence must have gene_id and sequence fields"`
- `"Invalid sequence for {gene_id}. Only ATCG characters allowed."`
- `"Empty sequence for {gene_id}"`
- `"Sequence too long for {gene_id}. Maximum length: 50000 bp"`

#### 500 Internal Server Error
```json
{
    "status": "error",
    "message": "Internal server error: {详细错误信息}"
}
```

---

## 💡 使用示例

### Python (使用 requests)

```python
import requests
import json

# API 端点
url = "http://your-domain.com/tools/api/sequence-analysis/"

# 准备数据
data = {
    "sequences": [
        {
            "gene_id": "Gene1",
            "sequence": "ATCGATCGATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGC"
        },
        {
            "gene_id": "Gene2",
            "sequence": "GCTAGCTAGCTAGCTAATATATATATCGCGCGCG"
        }
    ],
    "parameters": {
        "homopolymers_min_len": 7,
        "tandem_min_copies": 4
    }
}

# 发送请求
response = requests.post(url, json=data)

# 解析结果
if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")

    # 遍历每个基因的分析结果
    for gene_id, gene_data in result['data'].items():
        print(f"\n=== {gene_id} ===")
        summary = gene_data['summary']
        print(f"Total Length: {summary['total_length']} bp")
        print(f"Total Penalty Score: {summary['total_penalty_score']}")
        print(f"Tandem Repeats Penalty: {summary['TandemRepeats_penalty_score']}")

        # 查看具体特征
        tandem_repeats = gene_data['features']['TandemRepeats']
        print(f"Found {len(tandem_repeats)} Tandem Repeats")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### cURL

```bash
curl -X POST http://your-domain.com/tools/api/sequence-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "sequences": [
      {
        "gene_id": "TestGene",
        "sequence": "ATCGATCGATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGC"
      }
    ]
  }'
```

### JavaScript (使用 fetch)

```javascript
const url = 'http://your-domain.com/tools/api/sequence-analysis/';

const data = {
    sequences: [
        {
            gene_id: 'Gene1',
            sequence: 'ATCGATCGATCGATCGATCGAAAAAAAAATTTTTTTTTGCGCGCGCGC'
        }
    ],
    parameters: {
        homopolymers_min_len: 7
    }
};

fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
    console.log('Status:', result.status);
    console.log('Data:', result.data);
})
.catch(error => {
    console.error('Error:', error);
});
```

---

## 📊 返回数据说明

### Summary 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_length` | int | 序列总长度 (bp) |
| `total_penalty_score` | float | 所有特征的惩罚分总和 |
| `*_penalty_score` | float | 各特征的惩罚分 |
| `*_total_length` | int | 各特征的总长度 (bp) |

### Features 字段

每个特征类型包含一个数组，数组中的每个对象代表检测到的一个特征实例。

#### 通用字段
- `sequence`: 特征序列
- `start`: 起始位置（0-based）
- `end`: 结束位置（0-based）
- `length`: 长度
- `penalty_score`: 惩罚分

#### 特殊字段

**InvertedRepeats:**
- `type`: "hairpin" 或 "inverted_repeat"
- `stem_sequence`: stem 序列
- `stem_length`: stem 长度
- `stem1_start`, `stem1_end`: 第一个 stem 位置
- `stem2_start`, `stem2_end`: 第二个 stem 位置
- `loop_sequence`: loop 序列
- `loop_length`: loop 长度
- `count`: 重复次数（仅 inverted_repeat）

---

## ⚠️ 限制与注意事项

1. **序列数量限制**: 单次请求最多 100 个序列
2. **序列长度限制**: 单个序列最长 50,000 bp
3. **字符限制**: 只接受 A、T、C、G 字符
4. **速率限制**: 当前无速率限制（未来可能添加）
5. **超时**: 大量或长序列分析可能需要较长时间

---

## 🔧 故障排查

### 问题：请求返回 400 错误
**解决方案**:
- 检查 JSON 格式是否正确
- 确认所有必需字段都已提供
- 验证序列只包含 ATCG 字符
- 检查序列数量和长度是否超限

### 问题：请求超时
**解决方案**:
- 减少序列数量
- 缩短序列长度
- 分批提交请求

### 问题：结果中某些特征为空数组
**解决方案**:
- 这是正常现象，表示未检测到该类型特征
- 可以调整 `parameters` 中的阈值来获得更多或更少的检测结果

---

## 📞 技术支持

如有问题，请联系：
- Email: support@your-domain.com
- GitHub Issues: [项目地址]

---

## 📝 更新日志

### v1.0.0 (2025-01-XX)
- 初始版本发布
- 支持 9 种序列特征分析
- 包括 Tandem Repeats、Palindrome Repeats、Inverted Repeats 等

---

## 📄 许可证

[您的许可证信息]
