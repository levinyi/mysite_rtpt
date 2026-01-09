# 购物车前端更新 - 限制性酶切位点决策显示

## 更新概述

购物车页面已更新以显示限制性酶切位点的自动决策结果。这使用户能够在提交订单之前查看每个基因序列的合成可行性。

## 更新内容

### 1. 表格列更名
- **原名称**: "Enzyme Sites"
- **新名称**: "Restriction Sites"
- **位置**: [shoppingCart_view.html:365](../templates/user_center/shoppingCart_view.html#L365)

### 2. 新增模板过滤器

#### `restriction_decision_badge(gene)`
**位置**: [custom_filters.py:238-275](../tools/templatetags/custom_filters.py#L238-L275)

**功能**: 根据基因的限制性酶切位点决策结果生成HTML徽章（紧凑版）

**返回格式**:
- **接受 (Accept)**:
  - 绿色徽章: `BsaI` 或 `BsmBI`
  - 只显示工艺路线名称，无额外图标

- **拒绝 (Reject)**:
  - 红色徽章: `Reject`
  - 如需人工评估: `Reject ⚠`

**示例**:
```html
<!-- 接受合成，BsaI工艺路线 - 紧凑显示 -->
<span class="badge bg-success" data-bs-toggle="tooltip" title="No BsaI sites found. Synthesis accepted via BsaI route.">
    BsaI
</span>

<!-- 拒绝合成，需要人工评估 - 紧凑显示 -->
<span class="badge bg-danger" data-bs-toggle="tooltip" title="Sequence contains 2 BsaI sites and 2 BsmBI sites. Manual review required.">
    Reject ⚠
</span>
```

### 3. 表格单元格更新（紧凑横向布局）

**位置**: [shoppingCart_view.html:456-471](../templates/user_center/shoppingCart_view.html#L456-L471)

**显示内容**（单行横向布局）:
- **酶切位点数量**: BsaI和BsmBI位点徽章（蓝色系）
- **决策结果**: 工艺路线或拒绝状态徽章（绿/红色）
- **工具提示**: 鼠标悬停显示详细决策信息

**布局特点**:
- 使用 flexbox 横向排列
- `align-items-center` 垂直居中对齐
- `gap-2` 元素间距2单位
- `flex-wrap` 允许换行（窄屏）

**示例显示**（单行紧凑布局）:
```
┌──────────────────────────┐
│ BsaI:1  BsmBI:2  BsaI    │  ← 所有信息在一行
└──────────────────────────┘

┌──────────────────────────┐
│ BsaI:2  BsmBI:2  Reject⚠ │  ← 紧凑显示
└──────────────────────────┘

┌──────────────────────────┐
│ -                        │  ← 无位点时只显示 -
└──────────────────────────┘
```

### 4. 样式优化（紧凑版）

**位置**: [shoppingCart_view.html:141-155](../templates/user_center/shoppingCart_view.html#L141-L155)

**新增CSS类**:
```css
.restriction-sites-cell {
    min-width: 160px;  /* 确保横向布局有足够空间 */
    white-space: nowrap;  /* 防止不必要的换行 */
}

.restriction-sites-cell .badge {
    font-size: 0.7rem;  /* 更小的徽章字体 */
    padding: 0.2em 0.4em;  /* 更紧凑的内边距 */
    font-weight: 500;  /* 适中的字重 */
}

.restriction-sites-cell small {
    font-size: 0.75rem;  /* 小文本字体 */
}
```

**优化说明**:
- 减小徽章字体大小和内边距，节省垂直空间
- 使用 `white-space: nowrap` 保持单行显示
- 调整最小宽度以适应横向布局

## 用户体验

### 显示逻辑
1. **无位点**: 显示 "No sites"
2. **有位点，已接受**: 显示位点数量 + 绿色接受徽章
3. **有位点，已拒绝**: 显示位点数量 + 红色拒绝徽章
4. **需要人工评估**: 显示警告图标

### 工具提示
- 鼠标悬停在徽章上显示完整的决策信息
- 例如: "Sequence contains 1 BsaI site and 1 BsmBI site. Length ≤1500bp. Synthesis accepted via BsaI route (auto-processed)."

### 颜色编码
- 🟢 **绿色** (bg-success): 接受合成
- 🔴 **红色** (bg-danger): 拒绝合成
- 🔵 **蓝色** (bg-primary): BsaI位点
- 🔷 **浅蓝** (bg-info): BsmBI位点
- 🟡 **黄色** (text-warning): 需要人工评估

## 数据流

```
订单创建 (order_create)
    ↓
序列分析 (make_restriction_site_decision)
    ↓
保存到数据库 (GeneInfo.restriction_*)
    ↓
购物车视图 (view_cart)
    ↓
模板过滤器 (restriction_decision_badge)
    ↓
前端显示
```

## 向后兼容性

- 旧数据（没有决策结果）显示为 "-"
- 不影响现有功能
- 优雅降级处理异常

## 测试要点

1. ✅ 无酶切位点的基因显示正确
2. ✅ 有BsaI位点的基因显示正确工艺路线
3. ✅ 有BsmBI位点的基因显示正确工艺路线
4. ✅ 拒绝的基因显示红色徽章
5. ✅ 需要人工评估的基因显示警告图标
6. ✅ 工具提示显示完整信息
7. ✅ 响应式布局正常工作
8. ✅ 旧数据兼容性正常

## 后续优化建议

1. **筛选功能**: 添加按决策结果筛选基因的选项
2. **批量操作**: 允许批量查看/导出被拒绝的基因
3. **详细视图**: 在基因详情页面显示位点的具体位置
4. **导出功能**: 在Excel导出中包含决策结果
