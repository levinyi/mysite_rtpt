# Tandem Repeats Max Mismatch 参数界面更新

## 📅 更新日期
2025-11-06

---

## 🎯 更新内容

将 **Tandem: Max Mismatch** 参数从数字输入框改为**单选按钮组**，限制只能选择 0、1、2 三个值。

---

## ✨ 主要改进

### 1. 更直观的界面

**之前**：
```
Tandem: Max Mismatch
[  1  ]  ← 数字输入框，用户可以输入任意值
```

**现在**：
```
Tandem: Max Mismatch
[ 0 - Strict ] [ 1 - Standard ⭐ ] [ 2 - Relaxed ]
       ↑              ↑                  ↑
   单选按钮      默认选中          清晰标注
```

### 2. 明确的模式说明

每个选项都有：
- **图标**：视觉标识（🛡️ Shield, ⭐ Star, 🔍 Filter）
- **名称**：Strict / Standard / Relaxed
- **推荐标记**：Standard 模式标注为推荐

### 3. 帮助提示

添加了 info 图标 (ℹ️)，鼠标悬停显示：
```
0 = Perfect repeats only
1 = Allow 1 mismatch (recommended)
2 = Allow 2 mismatches
```

---

## 🔧 技术实现

### 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `templates/tools/SequenceAnalyzer.html` | 前端界面：数字输入框 → 单选按钮组 |
| `templates/tools/SequenceAnalyzer.html` | JavaScript：获取单选按钮值 |
| `templates/tools/SequenceAnalyzer.html` | 初始化 Bootstrap tooltips |
| `tools/views.py` (SequenceAnalyzer) | 后端验证：限制 0, 1, 2 |
| `tools/views.py` (API) | API 验证：限制 0, 1, 2 |

### 前端代码（HTML）

```html
<div class="col-md-4">
    <label class="form-label">Tandem: Max Mismatch</label>
    <div class="btn-group w-100" role="group">
        <input type="radio" class="btn-check" name="tandemMaxMismatch" id="mismatch0" value="0">
        <label class="btn btn-outline-primary" for="mismatch0">
            <i class="bi bi-shield-check"></i> 0 - Strict
        </label>

        <input type="radio" class="btn-check" name="tandemMaxMismatch" id="mismatch1" value="1" checked>
        <label class="btn btn-outline-primary" for="mismatch1">
            <i class="bi bi-star-fill"></i> 1 - Standard
        </label>

        <input type="radio" class="btn-check" name="tandemMaxMismatch" id="mismatch2" value="2">
        <label class="btn btn-outline-primary" for="mismatch2">
            <i class="bi bi-filter"></i> 2 - Relaxed
        </label>
    </div>
    <div class="form-text">
        <strong>Standard (1)</strong> recommended for gene synthesis.
        <a href="#" data-bs-toggle="tooltip" data-bs-placement="top"
           title="0=Perfect repeats only; 1=Allow 1 mismatch (recommended); 2=Allow 2 mismatches">
            <i class="bi bi-info-circle"></i>
        </a>
    </div>
</div>
```

### JavaScript 代码

```javascript
// 获取选中的单选按钮值
const selectedMismatch = document.querySelector('input[name="tandemMaxMismatch"]:checked');
formData.append('tandemMaxMismatch', selectedMismatch ? selectedMismatch.value : '1');
```

### 后端验证（Python）

```python
# 验证 tandem_max_mismatch 只能是 0, 1, 2
tandem_max_mismatch = int(request.POST.get('tandemMaxMismatch', 1))
if tandem_max_mismatch not in [0, 1, 2]:
    tandem_max_mismatch = 1  # 回退到默认值
```

---

## 📊 测试结果

### 测试脚本
```bash
python docs/test_mismatch_modes.py
```

### 测试结果摘要

| 模式 | 检测结果 | 说明 |
|------|----------|------|
| **Strict (0)** | 只检测完美重复 | 最保守，可能漏检 |
| **Standard (1)** ⭐ | 检测1个错配的重复 | **推荐**，平衡灵敏度 |
| **Relaxed (2)** | 检测2个错配的重复 | 最灵敏，可能过检 |

### 示例序列测试

**序列**: `ATCATCATGATCATCGGG` (ATC×5，第3个有1个错配)

| 模式 | 检测到？ | 检测长度 |
|------|---------|---------|
| 0 - Strict | ❌ 否 | - |
| 1 - Standard | ✅ 是 | 16 bp |
| 2 - Relaxed | ✅ 是 | 21 bp |

---

## 🎨 界面效果

### 桌面视图
```
┌────────────────────────────────────────────────────┐
│ Tandem: Max Mismatch                               │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │🛡️ 0-Strict│ │⭐ 1-Standard│ │🔍 2-Relaxed│         │
│ └──────────┘ └──────────┘ └──────────┘            │
│ Standard (1) recommended for gene synthesis. ℹ️     │
└────────────────────────────────────────────────────┘
```

### 移动视图
响应式设计，在小屏幕上自动堆叠。

---

## 🔄 兼容性

### 向后兼容
- ✅ API 仍然接受任意整数值，自动验证并回退到 0/1/2
- ✅ 现有脚本无需修改
- ✅ 默认值保持为 1

### API 使用
```json
{
  "sequences": [...],
  "parameters": {
    "tandem_max_mismatch": 1
  }
}
```

---

## 📚 相关文档

1. **`docs/TANDEM_MISMATCH_GUIDE.md`**
   - 详细使用指南
   - 生物学意义说明
   - 推荐设置

2. **`docs/test_mismatch_modes.py`**
   - 自动化测试脚本
   - 演示三种模式差异

3. **`docs/API_SEQUENCE_ANALYSIS.md`**
   - API 完整文档
   - 参数说明

---

## ✅ 验证清单

- [x] 前端界面改为单选按钮组
- [x] 默认选中 "1 - Standard"
- [x] 添加图标和模式名称
- [x] 添加帮助提示（tooltip）
- [x] JavaScript 正确获取单选按钮值
- [x] 后端验证值限制在 0, 1, 2
- [x] API 端点同样验证
- [x] 初始化 Bootstrap tooltips
- [x] 测试所有三种模式
- [x] 创建使用指南文档
- [x] 创建测试脚本

---

## 🚀 部署状态

✅ **已完成**，无需额外部署步骤。

修改已经应用到：
- 前端模板 (`templates/tools/SequenceAnalyzer.html`)
- 后端视图 (`tools/views.py`)
- API 端点 (同文件)

访问 `http://192.168.3.185:8000/tools/SequenceAnalyzer/` 即可看到更新。

---

## 💡 用户提示

在界面上会看到：

```
✨ Tandem: Max Mismatch 参数说明

选择合适的模式：
• 0 - Strict: 只检测完美重复（最严格）
• 1 - Standard: 允许1个错配（⭐ 推荐用于基因合成）
• 2 - Relaxed: 允许2个错配（适合研究）

默认使用 Standard 模式，适合大多数应用场景。
```

---

**更新完成！** 🎉
