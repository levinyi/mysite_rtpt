# DNA 序列测试集 - 新特征验证

**用途**: 测试 Tandem Repeats、Palindrome Repeats、Inverted Repeats 三个新功能

---

## 📋 测试序列列表

### 1. Tandem Repeats（串联重复）测试

#### Test_Tandem_Simple
**序列**:
```
ATCATCATCATCGGGAAATTTCCC
```
**特征**:
- 串联重复单元: `ATC` × 4 (位置 0-11)
- 预期检测: ✅ 应该检测到 12 bp 的串联重复

#### Test_Tandem_Long
**序列**:
```
ATGCATGCATGCATGCATGCATGCGGGCCCAAATTT
```
**特征**:
- 串联重复单元: `ATGC` × 6 (位置 0-23)
- 预期检测: ✅ 应该检测到 24 bp 的串联重复
- 预期罚分: (24-15)/2 = 4.5

#### Test_Tandem_WithMismatch
**序列**:
```
ATGATGATCATGATGATGCCCGGG
```
**特征**:
- 串联重复单元: `ATG` 有 1 个错配 (ATG-ATG-ATC-ATG-ATG)
- 预期检测: ✅ 应该检测到（max_mismatch=1）
- 测试目的: 验证错配容忍功能

---

### 2. Palindrome Repeats（回文序列）测试

#### Test_Palindrome_Simple
**序列**:
```
ATCGATCGATCGATCGATCG
```
**特征**:
- 完美回文: ATCGATCGATCGATCGATCG (20 bp)
- 预期检测: ✅ 应该检测到
- 预期罚分: (20-15)/2 = 2.5

#### Test_Palindrome_Long
**序列**:
```
ATGCGCATTTTAATGCGCATAAAGGG
```
**特征**:
- 回文序列: ATGCGCAT...ATGCGCAT (部分镜像)
- 预期检测: ✅ 应该检测到

#### Test_Palindrome_Excluded
**序列**:
```
ATATATATATATATGGGCCCAAA
```
**特征**:
- 两碱基交替: ATATAT... (应该被排除)
- 预期检测: ❌ 不应该检测为回文（因为是交替模式）
- 测试目的: 验证排除规则

#### Test_Palindrome_RealPalindrome
**序列**:
```
GGATCCTAGGATCCTAG
```
**特征**:
- 真正的回文结构
- 预期检测: ✅ 应该检测到

---

### 3. Inverted Repeats（倒置重复）测试

#### Test_Hairpin_Perfect
**序列**:
```
ATCGATCGATCGAAAAATCGATCGATCG
```
**特征**:
- Stem1: ATCGATCGATCG (12 bp, 位置 0-11)
- Loop: AAAA (4 bp, 位置 12-15)
- Stem2: ATCGATCGATCG 的反向互补 (12 bp, 位置 16-27)
- 类型: Hairpin (loop 4-8 bp)
- 预期检测: ✅ 应该检测为 hairpin
- 预期罚分: stem_length - 9 = 12 - 9 = 3

#### Test_Hairpin_Loop6
**序列**:
```
GCTAGCTAGCTTTTTTGCTAGCTAGC
```
**特征**:
- Stem: GCTAGCTAGC (10 bp)
- Loop: TTTTTT (6 bp)
- 类型: Hairpin (loop 4-8 bp)
- 预期检测: ✅ 应该检测为 hairpin
- 预期罚分: 10 - 9 = 1

#### Test_Inverted_LongLoop
**序列**:
```
ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG
```
**特征**:
- Stem: ATCGATCGATCGATCG (16 bp)
- Loop: GGGGGGGGGGGG (12 bp, ≥8 bp)
- 类型: Inverted Repeat (loop ≥8)
- 预期检测: ✅ 应该检测为 inverted repeat
- 预期罚分: ((16-15)/2) * count

#### Test_Inverted_ShortLoop
**序列**:
```
ATCGATCGATCGATCGAACGATCGATCGATCG
```
**特征**:
- Stem: ATCGATCGATCGATCG (16 bp)
- Loop: AA (2 bp, ≤3 bp)
- 类型: Inverted Repeat (loop ≤3)
- 预期检测: ✅ 应该检测为 inverted repeat

---

### 4. 混合特征测试

#### Test_Mixed_All
**序列**:
```
AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG
```
**特征**:
- Homopolymer: AAAAAAAA (8 bp, 位置 0-7)
- Tandem Repeats: ATCATCATCATC (16 bp)
- Palindrome: ATCGATCGATCGATCGATCG (20 bp)
- Hairpin: stem + AAAA + stem
- Homopolymer: GGGGGGGG (8 bp)
- 预期检测: ✅ 应该检测到所有特征类型

#### Test_Complex_Real
**序列**:
```
ATGCATGCATGCATGCGCTAGCTAGCTAGCTAGCAAAAAAGCTAGCTAGCTAGCTAGCTTTTTTTCCCCCCC
```
**特征**:
- 串联重复: ATGC × 4
- 串联重复: GCTAGC × 4
- Hairpin 结构
- Homopolymers: AAAAAA, TTTTTTT, CCCCCCC
- 预期检测: ✅ 多种特征同时存在

---

## 🧪 Excel 测试表格格式

### 方案 1: 单独测试每个特征

| GeneName | SeqNT |
|----------|-------|
| Test_Tandem_Simple | ATCATCATCATCGGGAAATTTCCC |
| Test_Tandem_Long | ATGCATGCATGCATGCATGCATGCGGGCCCAAATTT |
| Test_Palindrome_Simple | ATCGATCGATCGATCGATCG |
| Test_Hairpin_Perfect | ATCGATCGATCGAAAAATCGATCGATCG |
| Test_Inverted_LongLoop | ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG |

### 方案 2: 综合测试

| GeneName | SeqNT |
|----------|-------|
| Mixed_All_Features | AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG |
| Complex_Real_World | ATGCATGCATGCATGCGCTAGCTAGCTAGCTAGCAAAAAAGCTAGCTAGCTAGCTAGCTTTTTTTCCCCCCC |

---

## 📝 测试步骤

### 1. 访问页面
```
http://192.168.3.185:8000/tools/SequenceAnalyzer/
```

### 2. 输入测试序列
- 点击 "Use example" 清空当前数据
- 复制上面的测试序列到表格中
- 或者使用下方的 FASTA 格式

### 3. 设置参数（可选）
点击 "Advanced Parameters (Optional)"，调整参数：
- Tandem: Min Unit = 3
- Tandem: Min Copies = 4
- Tandem: Max Mismatch = 1
- Palindrome: Min Length = 15
- Inverted: Min Stem Length = 10

### 4. 提交分析
点击 "Submit & Analyze Sequences"

### 5. 检查结果
在结果页面验证：
- ✅ 是否检测到预期的特征
- ✅ 罚分是否正确
- ✅ 位置信息是否准确

---

## 📄 FASTA 格式（可直接上传）

```fasta
>Test_Tandem_Simple
ATCATCATCATCGGGAAATTTCCC

>Test_Tandem_Long
ATGCATGCATGCATGCATGCATGCGGGCCCAAATTT

>Test_Tandem_WithMismatch
ATGATGATCATGATGATGCCCGGG

>Test_Palindrome_Simple
ATCGATCGATCGATCGATCG

>Test_Palindrome_Excluded
ATATATATATATATGGGCCCAAA

>Test_Palindrome_RealPalindrome
GGATCCTAGGATCCTAG

>Test_Hairpin_Perfect
ATCGATCGATCGAAAAATCGATCGATCG

>Test_Hairpin_Loop6
GCTAGCTAGCTTTTTTGCTAGCTAGC

>Test_Inverted_LongLoop
ATCGATCGATCGATCGGGGGGGGGGGGGCGATCGATCGATCG

>Test_Inverted_ShortLoop
ATCGATCGATCGATCGAACGATCGATCGATCG

>Test_Mixed_All
AAAAAAAATCATCATCATCATCGATCGATCGATCGATCGAAAATCGATCGATCGATCGATCGGGGGGGG

>Test_Complex_Real
ATGCATGCATGCATGCGCTAGCTAGCTAGCTAGCAAAAAAGCTAGCTAGCTAGCTAGCTTTTTTTCCCCCCC
```

---

## 🎯 预期结果

### Tandem Repeats
| 序列 | 应检测到 | 预期罚分 |
|------|---------|---------|
| Test_Tandem_Simple | ✅ ATC×4 | 0 (12<15) |
| Test_Tandem_Long | ✅ ATGC×6 | 4.5 |
| Test_Tandem_WithMismatch | ✅ ATG (with mismatch) | 5.5 |

### Palindrome Repeats
| 序列 | 应检测到 | 预期罚分 |
|------|---------|---------|
| Test_Palindrome_Simple | ✅ 20 bp | 2.5 |
| Test_Palindrome_Excluded | ❌ 应排除 | 0 |
| Test_Palindrome_RealPalindrome | ✅ Yes | > 0 |

### Inverted Repeats
| 序列 | 类型 | 应检测到 | 预期罚分 |
|------|------|---------|---------|
| Test_Hairpin_Perfect | Hairpin | ✅ stem=12 bp | 3.0 |
| Test_Hairpin_Loop6 | Hairpin | ✅ stem=10 bp | 1.0 |
| Test_Inverted_LongLoop | Inverted | ✅ stem=16 bp | 0.5+ |
| Test_Inverted_ShortLoop | Inverted | ✅ stem=16 bp | 0.5+ |

---

## 🐛 故障排查

### 如果未检测到预期特征
1. **检查参数设置**: 确认阈值未设置过高
2. **查看详细输出**: 检查 features 数组内容
3. **验证序列**: 确认序列复制正确，无额外空格

### 如果检测到意外特征
1. **降低灵敏度**: 提高最小长度/次数阈值
2. **检查序列**: 可能存在未注意到的重复结构

---

## 📊 测试报告模板

```
测试日期: __________
测试人员: __________

测试结果:
[ ] Tandem Repeats:
    - Test_Tandem_Simple: ___
    - Test_Tandem_Long: ___
    - Test_Tandem_WithMismatch: ___

[ ] Palindrome Repeats:
    - Test_Palindrome_Simple: ___
    - Test_Palindrome_Excluded: ___
    - Test_Palindrome_RealPalindrome: ___

[ ] Inverted Repeats:
    - Test_Hairpin_Perfect: ___
    - Test_Hairpin_Loop6: ___
    - Test_Inverted_LongLoop: ___
    - Test_Inverted_ShortLoop: ___

[ ] Mixed Features:
    - Test_Mixed_All: ___
    - Test_Complex_Real: ___

问题记录:
_________________________________
_________________________________
```

---

**祝测试顺利！** 🧪✨

如有问题，请查看：
- API 文档: `docs/API_SEQUENCE_ANALYSIS.md`
- 测试报告: `docs/API_TEST_REPORT.md`
