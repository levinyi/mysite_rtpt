# SequenceAnalyzer 前端更新总结

**更新日期**: 2025-01-06
**更新内容**: 将 Tandem Repeats、Palindrome Repeats、Inverted Repeats 三个新功能从 "Soon" 改为 "Supported"

---

## 📋 更新文件列表

### 1. **前端模板** - templates/tools/SequenceAnalyzer.html

#### 修改 1: 更新功能介绍文本 (Line 93)
**变更**:
```html
<!-- 之前 -->
Long repeats, homopolymers, W/S motifs, local GC window, and dinucleotide repeats

<!-- 之后 -->
Long repeats, homopolymers, W/S motifs, local GC window, dinucleotide repeats,
tandem repeats, palindrome repeats, and inverted repeats
```

#### 修改 2: 更新特征支持状态 (Line 143-151)
**变更**: 将三个特征从 "Soon" 改为 "Supported"

```html
<!-- 之前 -->
<div class="feature-chip soon">
    <i class="bi bi-dash-circle"></i>
    <span>Tandem Repeats</span>
    <span class="badge bg-secondary-subtle text-secondary">Soon</span>
</div>

<!-- 之后 -->
<div class="feature-chip supported">
    <i class="bi bi-check2-circle text-success"></i>
    <span>Tandem Repeats</span>
    <span class="badge bg-success-subtle text-success">Supported</span>
</div>
```

同样应用于：
- Tandem Repeats ✅
- Palindrome Repeats ✅
- Inverted Repeats ✅

#### 修改 3: 添加新特征参数输入框 (Line 206-235)
**新增内容**:
```html
<hr class="my-3">
<h6 class="text-muted mb-3"><i class="bi bi-stars me-2"></i>New Feature Parameters</h6>
<div class="row g-3">
    <!-- Tandem Repeats Parameters -->
    <div class="col-md-4">
        <label for="tandemMinUnit" class="form-label">Tandem: Min Unit Length</label>
        <input type="number" class="form-control" id="tandemMinUnit" value="3">
        <div class="form-text">Minimum repeat unit length. Default 3.</div>
    </div>
    <div class="col-md-4">
        <label for="tandemMinCopies" class="form-label">Tandem: Min Copies</label>
        <input type="number" class="form-control" id="tandemMinCopies" value="4">
        <div class="form-text">Minimum number of repeats. Default 4.</div>
    </div>
    <div class="col-md-4">
        <label for="tandemMaxMismatch" class="form-label">Tandem: Max Mismatch</label>
        <input type="number" class="form-control" id="tandemMaxMismatch" value="1">
        <div class="form-text">Allow mismatches. Default 1.</div>
    </div>

    <!-- Palindrome Repeats Parameters -->
    <div class="col-md-6">
        <label for="palindromeMinLen" class="form-label">Palindrome: Min Length</label>
        <input type="number" class="form-control" id="palindromeMinLen" value="15">
        <div class="form-text">Minimum palindrome length. Default 15.</div>
    </div>

    <!-- Inverted Repeats Parameters -->
    <div class="col-md-6">
        <label for="invertedMinStemLen" class="form-label">Inverted: Min Stem Length</label>
        <input type="number" class="form-control" id="invertedMinStemLen" value="10">
        <div class="form-text">Minimum stem length for hairpin/inverted. Default 10.</div>
    </div>
</div>
```

#### 修改 4: 更新 JavaScript 提交逻辑 (Line 484-489)
**新增代码**:
```javascript
// New feature parameters
formData.append('tandemMinUnit', document.getElementById('tandemMinUnit').value);
formData.append('tandemMinCopies', document.getElementById('tandemMinCopies').value);
formData.append('tandemMaxMismatch', document.getElementById('tandemMaxMismatch').value);
formData.append('palindromeMinLen', document.getElementById('palindromeMinLen').value);
formData.append('invertedMinStemLen', document.getElementById('invertedMinStemLen').value);
```

---

### 2. **后端视图** - tools/views.py

#### 修改: SequenceAnalyzer 函数 (Line 403-424)
**新增参数读取**:
```python
# ========== 新增三个特征的参数 ==========
tandem_min_unit = int(request.POST.get('tandemMinUnit', 3))
tandem_min_copies = int(request.POST.get('tandemMinCopies', 4))
tandem_max_mismatch = int(request.POST.get('tandemMaxMismatch', 1))
palindrome_min_len = int(request.POST.get('palindromeMinLen', 15))
inverted_min_stem_len = int(request.POST.get('invertedMinStemLen', 10))
```

**新增函数调用参数**:
```python
data = convert_gene_table_to_RepeatsFinder_Format(
    gene_table,
    # ... 原有参数 ...
    # ========== 新增三个特征的参数 ==========
    tandem_min_unit=tandem_min_unit,
    tandem_min_copies=tandem_min_copies,
    tandem_max_mismatch=tandem_max_mismatch,
    palindrome_min_len=palindrome_min_len,
    inverted_min_stem_len=inverted_min_stem_len
)
```

---

## 🎯 新增参数说明

| 参数名 | 默认值 | 说明 | 影响的功能 |
|-------|--------|------|-----------|
| `tandemMinUnit` | 3 | 串联重复最小单元长度 | Tandem Repeats |
| `tandemMinCopies` | 4 | 串联重复最小重复次数 | Tandem Repeats |
| `tandemMaxMismatch` | 1 | 允许的最大错配数 | Tandem Repeats |
| `palindromeMinLen` | 15 | 回文序列最小长度 | Palindrome Repeats |
| `invertedMinStemLen` | 10 | 倒置重复最小 stem 长度 | Inverted Repeats |

---

## 🔄 数据流

### 前端 → 后端
```
用户输入参数
    ↓
HTML 表单字段 (id: tandemMinUnit, etc.)
    ↓
JavaScript FormData.append()
    ↓
POST 请求到 /tools/SequenceAnalyzer/
    ↓
views.py SequenceAnalyzer() 函数
    ↓
request.POST.get('tandemMinUnit', 3)
    ↓
convert_gene_table_to_RepeatsFinder_Format()
    ↓
分析结果
```

---

## ✅ 测试清单

### 前端显示
- [x] 页面上三个新功能显示为 "Supported"（绿色勾）
- [x] "What it checks" 描述已更新
- [x] 高级参数中显示 5 个新参数输入框
- [x] 参数输入框有默认值

### 功能测试
- [ ] 提交表单时新参数正确传递到后端
- [ ] 修改参数值后分析结果有相应变化
- [ ] 不填写新参数时使用默认值

### 集成测试
- [ ] 前端提交 → 后端处理 → 结果展示 完整流程正常
- [ ] 新功能的分析结果正确显示在结果页面

---

## 🎨 UI 展示效果

### 特征状态卡片
```
✅ Long Repeats          [Supported]  ← 原有
✅ Homopolymers          [Supported]  ← 原有
✅ Special Motifs        [Supported]  ← 原有
✅ Local GC content      [Supported]  ← 原有
✅ Dinucleotide Repeats  [Supported]  ← 原有
✅ Tandem Repeats        [Supported]  ← 新增 🌟
✅ Palindrome Repeats    [Supported]  ← 新增 🌟
✅ Inverted Repeats      [Supported]  ← 新增 🌟
```

### 参数面板
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌟 New Feature Parameters
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Tandem: Min Unit Length]    [3]
[Tandem: Min Copies]          [4]
[Tandem: Max Mismatch]        [1]
[Palindrome: Min Length]      [15]
[Inverted: Min Stem Length]   [10]
```

---

## 📝 注意事项

1. **兼容性**: 所有修改向后兼容，不影响现有功能
2. **默认值**: 新参数都有合理的默认值，用户可不填
3. **验证**: 前端使用 HTML5 number 输入验证
4. **折叠面板**: 新参数在 "Advanced Parameters" 折叠面板中，不会干扰主界面

---

## 🚀 部署说明

### 需要重启的服务
1. Django 开发服务器（如果正在运行）
   ```bash
   # Ctrl+C 停止
   python manage.py runserver
   ```

### 浏览器缓存
建议用户清除浏览器缓存或使用硬刷新（Ctrl+F5）以看到最新的前端变化。

---

## 🔗 相关文档

- 算法文档: `tools/scripts/AnalysisSequence.py`
- API 文档: `docs/API_SEQUENCE_ANALYSIS.md`
- 测试报告: `docs/API_TEST_REPORT.md`
- 后端适配: `tools/views.py:374-440`
- 前端模板: `templates/tools/SequenceAnalyzer.html`

---

**更新完成！** ✅ 所有三个新功能现已在前端标记为 "Supported" 并可通过参数面板配置。
