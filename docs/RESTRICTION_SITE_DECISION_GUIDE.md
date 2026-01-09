# 限制性酶切位点自动决策系统

## 概述

该系统用于自动判断基因序列是否可以接受合成，决策基于序列中的BsaI和BsmBI限制性酶切位点数量、克隆方法和序列长度。

## 核心功能

### 1. 酶切位点检测

系统自动检测两种限制性酶切位点：

- **BsaI位点**：`GGTCTC` (正向) 和 `GAGACC` (反向互补)
- **BsmBI位点**：`CGTCTC` (正向) 和 `GAGACG` (反向互补)

### 2. 决策规则

#### 情况1: 无BsaI位点
- **条件**：BsaI = 0，BsmBI 任意数量
- **结果**：✅ 接受合成
- **工艺路线**：BsaI工艺路线
- **提示**：无

#### 情况2: 有BsaI但无BsmBI
- **条件**：BsaI ≥ 1，BsmBI = 0
- **结果**：✅ 接受合成
- **工艺路线**：BsmBI工艺路线
- **提示**：无

#### 情况3: 1个BsaI + ≥1个BsmBI
**步骤1：检查克隆方法**
- 如果克隆方法 = Gibson：
  - ❌ **直接拒绝**
  - 提示：`"Genes with internal BsaI cannot be cloned into vectors by Gibson"`

- 如果克隆方法 = GG 或 T4：继续步骤2

**步骤2：检查序列长度**
- 如果长度 ≤ 1500bp：
  - ✅ **接受合成**
  - **工艺路线**：BsaI工艺路线
  - 备注：系统自动处理

- 如果长度 > 1500bp：
  - ❌ **拒绝合成**
  - 备注：需人工评估

#### 情况4: ≥2个BsaI + 1个BsmBI
**步骤1：检查克隆方法**
- 如果克隆方法 = Gibson：
  - ❌ **直接拒绝**
  - 提示：`"Genes with internal BsmBI cannot be cloned into vectors by Gibson"`

- 如果克隆方法 = GG 或 T4：继续步骤2

**步骤2：检查序列长度**
- 如果长度 ≤ 1500bp：
  - ✅ **接受合成**
  - **工艺路线**：BsmBI工艺路线
  - 备注：系统自动处理

- 如果长度 > 1500bp：
  - ❌ **拒绝合成**
  - 备注：需人工评估

#### 情况5: ≥2个BsaI + ≥2个BsmBI
- **条件**：BsaI ≥ 2，BsmBI ≥ 2
- **结果**：❌ **无条件拒绝**（无论序列长度和克隆方法）
- **备注**：需人工评估

## 技术实现

### 1. 核心函数

#### `make_restriction_site_decision(seq, cloning_method)`

位置：`user_center/utils/sequence_processing.py`

**参数**：
- `seq`: DNA序列字符串
- `cloning_method`: 克隆方法 ('Gibson', 'GG', 或 'T4')

**返回值**：
```python
{
    'decision': 'accept' 或 'reject',
    'process_route': 'BsaI' 或 'BsmBI' 或 None,
    'message': '决策提示信息',
    'bsai_count': BsaI位点数量,
    'bsmbi_count': BsmBI位点数量,
    'bsai_positions': [位点位置列表],
    'bsmbi_positions': [位点位置列表],
    'seq_length': 序列长度,
    'requires_manual_review': 是否需要人工评估
}
```

### 2. 数据库字段

在 `GeneInfo` 模型中添加了以下字段：

- `restriction_decision`: 决策结果 (accept/reject)
- `restriction_process_route`: 工艺路线 (BsaI/BsmBI)
- `restriction_message`: 决策提示信息
- `restriction_requires_manual_review`: 是否需要人工评估
- `bsai_count`: BsaI位点数量
- `bsmbi_count`: BsmBI位点数量
- `bsai_positions`: BsaI位点位置列表 (JSONField)
- `bsmbi_positions`: BsmBI位点位置列表 (JSONField)

### 3. 集成流程

在 `order_create` 视图中，决策逻辑在以下位置执行：

1. 获取载体的克隆方法
2. 对每个序列调用 `make_restriction_site_decision()`
3. 将结果合并到DataFrame
4. 在 `process_highlights_positions()` 中将酶切位点添加到高亮列表
5. 保存到数据库

### 4. 前端展示

酶切位点在序列编辑器中会高亮显示：

- **BsaI位点**：标记类型为 `BsaI`
- **BsmBI位点**：标记类型为 `BsmBI`

每个位点包含：
- `start`: 起始位置
- `end`: 结束位置
- `type`: 位点类型
- `content`: 位点序列

## 测试

运行测试脚本验证所有决策规则：

```bash
python test_restriction_decision.py
```

测试覆盖所有5种情况和各种边界条件。

## 使用示例

```python
from user_center.utils.sequence_processing import make_restriction_site_decision

# 示例1：无BsaI位点
seq1 = "ATCGATCGATCG" * 50
result1 = make_restriction_site_decision(seq1, "Gibson")
# 结果：accept, BsaI工艺路线

# 示例2：1个BsaI + 1个BsmBI, Gibson克隆
seq2 = "ATCGATCGATCGGGTCTCATCGCGTCTCATCGATCG" * 20
result2 = make_restriction_site_decision(seq2, "Gibson")
# 结果：reject, 因为Gibson克隆不能包含BsaI

# 示例3：2个BsaI + 1个BsmBI, 短序列, GG克隆
seq3 = "ATCGATCGATCGGGTCTCATCGGAGACCATCGCGTCTCATCGATCG" * 10
result3 = make_restriction_site_decision(seq3, "GG")
# 结果：accept, BsmBI工艺路线
```

## 前端显示

### 购物车页面

购物车页面已更新以显示限制性酶切位点的决策结果。详见 [购物车更新文档](SHOPPING_CART_UPDATES.md)。

**显示内容**:
1. **酶切位点数量**: BsaI和BsmBI位点的数量（徽章显示）
2. **决策结果**: 接受/拒绝状态和工艺路线
3. **人工评估标记**: 需要人工评估的序列显示警告图标

**模板过滤器**:
- `count_enzyme_sites(gene, enzyme_name)`: 统计位点数量
- `restriction_decision_badge(gene)`: 生成决策结果徽章

**示例**:
```django
<!-- 在购物车模板中使用 -->
{% load custom_filters %}

<!-- 显示位点数量 -->
BsaI: {{ gene|count_enzyme_sites:"BsaI" }}
BsmBI: {{ gene|count_enzyme_sites:"BsmBI" }}

<!-- 显示决策结果 -->
{{ gene|restriction_decision_badge }}
```

## 注意事项

1. 克隆方法必须在载体 (Vector) 模型中正确配置
2. 如果载体未配置克隆方法，默认使用 'T4'
3. 所有酶切位点的搜索都是大小写不敏感的
4. 位点位置基于0索引
5. 人工评估标记 (`requires_manual_review`) 用于标识需要额外审查的序列
6. 前端显示会自动处理空值和异常情况，确保向后兼容
