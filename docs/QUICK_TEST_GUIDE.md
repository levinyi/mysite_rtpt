# 快速测试指南 - 新特征验证

**目标**: 快速验证 Tandem Repeats、Palindrome Repeats、Inverted Repeats 三个新功能

---

## 🚀 方法 1: 直接在网页表格中输入（最快）

### 步骤：
1. 访问：`http://192.168.3.185:8000/tools/SequenceAnalyzer/`
2. 直接复制下面的表格（包括表头）
3. 在网页的输入表格中粘贴（支持从Excel粘贴）
4. 点击 "Submit & Analyze Sequences"

### 复制这个表格 ⬇️

```
GeneName	SeqNT
Test_Tandem_Simple	ATCATCATCATCGGGAAATTTCCC
Test_Palindrome_Simple	ATCGATCGATCGATCGATCG
Test_Hairpin_Perfect	ATCGATCGATCGAAAAATCGATCGATCG
Test_Mixed_All	AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG
```

**提示**: 直接 Ctrl+A 全选上面的文本，然后 Ctrl+C 复制，在网页表格第一行第一列粘贴即可！

---

## 📄 方法 2: 上传 FASTA 文件

### 步骤：
1. 下载文件：`docs/test_sequences.fasta`
2. 访问：`http://192.168.3.185:8000/tools/SequenceAnalyzer/`
3. 点击 "Upload Fasta File" 标签页
4. 拖拽或选择 `test_sequences.fasta` 文件
5. 点击 "Submit & Analyze Sequences"

---

## 📊 方法 3: 使用 CSV 文件

### 步骤：
1. 下载并打开：`docs/test_sequences.csv`
2. 在 Excel 中复制所有内容（Ctrl+A, Ctrl+C）
3. 访问：`http://192.168.3.185:8000/tools/SequenceAnalyzer/`
4. 在网页表格中粘贴（Ctrl+V）
5. 点击 "Submit & Analyze Sequences"

---

## 🎯 预期结果速查

### Test_Tandem_Simple
- ✅ **应该检测到**: Tandem Repeats
- 📍 **位置**: 0-11 (ATC×4)
- 💯 **罚分**: 0 (长度12<15)

### Test_Palindrome_Simple
- ✅ **应该检测到**: Palindrome Repeats
- 📍 **位置**: 整个序列 (20 bp)
- 💯 **罚分**: 2.5

### Test_Hairpin_Perfect
- ✅ **应该检测到**: Inverted Repeats (Hairpin type)
- 📍 **特征**: stem=12bp, loop=4bp
- 💯 **罚分**: 3.0

### Test_Mixed_All
- ✅ **应该检测到**: 所有特征类型
  - Homopolymers (AAAAAAAA, GGGGGGGG)
  - Tandem Repeats
  - Palindrome Repeats
  - Inverted Repeats
- 💯 **总罚分**: 应该比较高（>30）

---

## 🔍 结果页面检查清单

在结果页面检查以下内容：

### 1. 特征芯片（Summary）
```
✅ 应该看到以下芯片（如果检测到）：
   [Tandem Repeats: XX bp]
   [Palindrome Repeats: XX bp]
   [Inverted Repeats: XX bp]
```

### 2. 展开详情（点击 "Findings"）
```
✅ 应该看到详细信息：
   - Tandem Repeats: sequence, start, end, length, penalty_score
   - Palindrome Repeats: sequence, start, end, length, penalty_score
   - Inverted Repeats: type, stem_sequence, stem_length, loop_length, penalty_score
```

### 3. 序列高亮
```
✅ 鼠标悬停在特征名称上时，序列应该高亮显示对应区域
```

---

## 🧪 单个特征测试（极简版）

### 只测试 Tandem Repeats
```
GeneName	SeqNT
TandemTest	ATCATCATCATCGGG
```

### 只测试 Palindrome
```
GeneName	SeqNT
PalindromeTest	ATCGATCGATCGATCGATCG
```

### 只测试 Hairpin
```
GeneName	SeqNT
HairpinTest	ATCGATCGATCGAAAAATCGATCGATCG
```

---

## ⚙️ 参数调整测试

### 测试参数敏感性：
1. 打开 "Advanced Parameters (Optional)"
2. 修改参数，例如：
   - Tandem: Min Copies = 3（应检测到更多）
   - Palindrome: Min Length = 10（应检测到更多）
   - Inverted: Min Stem Length = 15（应检测到更少）
3. 重新提交，观察结果变化

---

## 🐛 常见问题

### Q: 为什么 Test_Palindrome_Excluded 没有检测到 Palindrome？
**A**: 这是正常的！这个序列是两碱基交替（ATATAT...），根据设计被排除了。

### Q: Inverted Repeats 检测到很多结果？
**A**: 这是正常的！短序列中可能有多个stem-loop组合。查看 `type` 字段区分 hairpin 和 inverted_repeat。

### Q: 罚分为什么是 0？
**A**: 如果特征长度小于阈值（如15），罚分为0。这是正常的设计。

---

## 📸 预期结果截图说明

**Test_Mixed_All 的结果应该类似这样：**

```
🧬 Test_Mixed_All
├─ 序列长度: 70 bp
├─ 总惩罚分: ~35-45
└─ 检测到的特征:
   ├─ [Homopolymers: 16 bp]
   ├─ [Tandem Repeats: 20 bp]
   ├─ [Palindrome Repeats: 20 bp]
   └─ [Inverted Repeats: XX bp]
```

---

## ✅ 测试完成检查表

- [ ] 所有测试序列都成功提交
- [ ] Tandem Repeats 正确检测
- [ ] Palindrome Repeats 正确检测
- [ ] Inverted Repeats 正确检测并区分 hairpin/inverted
- [ ] Test_Palindrome_Excluded 正确被排除
- [ ] 参数调整能影响结果
- [ ] 罚分计算合理
- [ ] 序列高亮功能正常
- [ ] 可以下载结果 CSV

---

## 🎉 测试通过标准

如果以上检查都符合预期，说明新功能已经完美集成！🌟

---

**需要帮助？** 查看完整文档：
- `docs/TEST_SEQUENCES.md` - 详细测试序列说明
- `docs/API_TEST_REPORT.md` - API 测试报告
- `docs/FRONTEND_UPDATE_SUMMARY.md` - 前端更新说明
