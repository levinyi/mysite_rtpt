# 载体改造自动化设计功能使用指南

## 功能概述

载体改造自动化设计功能可以自动分析用户上传的GenBank格式载体文件，选择最优的克隆方法（Gibson/GoldenGate/T4），设计v5NC和v3NC序列，并生成改造后的载体图谱。

## 使用流程

### 1. 准备载体文件

**文件要求：**
- 格式：GenBank (.gb或.genbank)
- 大小：不超过5MB
- 必须包含iU20和iD20的feature标记
- 建议文件命名格式：`pCVaXXX(抗性)-描述.gb`
  - 例如：`pCVa001(Amp)-expression-vector.gb`
  - 系统会自动从文件名中提取抗性信息

**GenBank文件中的必需标记：**
```
FEATURES             Location/Qualifiers
     misc_feature    100..120
                     /label="iU20"
     misc_feature    3000..3020
                     /label="iD20"
```

### 2. 上传载体文件

1. 登录系统后，进入 **Manage Vectors** 页面
2. 点击 **Create New Vector** 按钮
3. 填写载体名称（建议使用有意义的名称）
4. 选择GenBank文件（.gb或.genbank格式）
5. 点击 **Submit** 上传

### 3. 启动自动化设计

1. 上传成功后，在载体列表的 **Automation Design** 列可以看到当前状态（Pending）
2. 点击 **Design** 按钮启动自动化设计
3. 系统会弹出确认对话框，确认后开始设计
4. 设计过程中状态会显示为 **Processing**（黄色标签）
5. 系统会自动轮询状态，完成后自动刷新页面

### 4. 查看设计结果

设计完成后，状态会显示为 **Completed (方法名称)**（绿色标签），例如：
- `Completed (Gibson)`
- `Completed (GoldenGate)`
- `Completed (T4)`

点击 **View** 按钮可以查看详细设计结果，包括：

#### 基本信息
- **克隆方法**：Gibson/GoldenGate/T4
- **v5NC序列**：设计的5'端同源臂序列
- **v3NC序列**：设计的3'端同源臂序列
- **i5NC/i3NC**：如果有序列移位，会显示移位的碱基
- **iU20/iD20序列**：原始标记序列

#### Gibson方法特有信息
如果使用Gibson方法，还会显示：
- **正向引物（Forward Primer）**：
  - 引物序列
  - Tm值（约60℃）
- **反向引物（Reverse Primer）**：
  - 引物序列
  - Tm值（约60℃）

### 5. 下载改造后的GenBank文件

在查看结果的模态框中，点击 **Download Modified GenBank** 按钮即可下载改造后的载体文件。

改造后的文件包含：
- 移除了v5NC和v3NC之间的原始序列
- 插入了Cm-ccdB固定序列
- 标记了所有重要的features（iU20, iD20, v5NC, v3NC, Cm-ccdB）

## 克隆方法选择逻辑

系统按以下优先级自动选择克隆方法：

### 1. Gibson方法（优先级最高）

**优势：**
- 同源臂较长（≥30bp），克隆效率高
- 适合大多数情况

**要求：**
- 插入位点上下游各1000bp范围内（共2000bp）Long repeat罚分≤28分
- v5NC和v3NC序列长度≥30bp
- v5NC和v3NC的Tm值≥48℃（快速计算公式：2×A/T + 4×G/C）
- GC含量在20%-80%范围内
- 不能有连续7bp以上的G或C同聚物
- 连续12bp内不能有11个G或11个C

**如果设计成功，系统会自动设计NC-PCR引物：**
- 目标Tm值：60℃
- 引物长度：16-35nt
- 检查hairpin结构和引物间相互配对

### 2. GoldenGate方法（优先级第二）

**优势：**
- 操作简单，一步克隆
- 序列要求较短（4bp）

**要求：**
- 载体上**不能同时**含有BsaI和BsmBI位点
  - 如果同时存在这两个位点，无法使用GG方法
- v5NC取iU20的最后4bp
- v3NC取iD20的最开始4bp
- v5NC和v3NC都不能是回文序列
- v5NC和v3NC不会相互错搭
  - 即这4个序列（v5NC、v3NC、v5NC反向互补、v3NC反向互补）相互之间每个位置比较，不能有3个或4个碱基相同

### 3. T4方法（优先级最低）

**说明：**
- 要求与GoldenGate方法完全相同
- 作为GoldenGate的备选方案

**要求：**
- v5NC取iU20的最后4bp
- v3NC取iD20的最开始4bp
- v5NC和v3NC都不能是回文序列
- v5NC和v3NC不会相互错搭

## 序列移位机制

如果初始设计的v5NC或v3NC序列不符合要求，系统会自动尝试移位：

### Gibson方法
- 系统会逐步调整v5NC和v3NC的边界位置
- 最多尝试100次，每次移动1bp
- 移位的碱基会记录在i5NC和i3NC字段中

### GoldenGate/T4方法
- v5NC如果是回文序列，向前移动1bp
- v3NC如果是回文序列，向后移动1bp
- 如果存在错搭，两者都移动
- 最多移位20bp

## 常见问题

### Q1: 上传文件后提示"未检测到iU20或iD20位置"怎么办？

**A:** 请检查GenBank文件中是否包含正确的feature标记：
```
FEATURES             Location/Qualifiers
     misc_feature    起始位置..结束位置
                     /label="iU20"
                     或
                     /note="iU20"
```
标记可以使用`label`或`note`字段，feature类型可以是`misc_feature`或`primer_bind`。

### Q2: 设计失败，提示"没有找到可用的克隆方法"怎么办？

**A:** 这说明三种克隆方法都不满足要求。可能的原因：
1. Gibson方法：Long repeat罚分过高（>28分）
2. GoldenGate方法：同时含有BsaI和BsmBI位点
3. 所有方法：无法设计出符合要求的v5NC/v3NC序列

**解决方案：**
- 检查载体序列是否包含过多重复序列
- 考虑修改载体设计，移除不必要的限制性位点
- 调整iU20和iD20的位置

### Q3: Gibson方法引物设计失败怎么办？

**A:** 引物设计失败不会影响整体设计流程，v5NC和v3NC序列仍然有效。可能原因：
- 无法找到Tm=60℃的引物
- 引物存在严重的hairpin结构
- 引物间存在明显配对

**解决方案：**
- 可以手动设计引物
- 调整引物设计参数（需要修改代码）

### Q4: 如何确认抗性信息被正确识别？

**A:** 系统会从文件名中提取抗性信息，格式为：`(抗性)`
- 正确示例：`pCVa001(Amp)-vector.gb` → 抗性：Amp
- 正确示例：`pCVa002(Kan)-expression.gb` → 抗性：Kan
- 错误示例：`pCVa003-Amp-vector.gb` → 无法识别抗性

如果文件名中没有抗性信息，系统会给出警告，但不影响设计流程。

### Q5: 设计过程需要多长时间？

**A:** 通常需要5-30秒，取决于：
- 载体序列长度
- Long repeat分析复杂度
- 服务器负载

系统会每5秒轮询一次状态，最多等待5分钟（60次轮询）。

## 技术参数说明

### Tm值计算方法

1. **简单计算（用于v5NC/v3NC验证）：**
   ```
   Tm = 2 × (A+T数量) + 4 × (G+C数量)
   ```

2. **T97计算（用于引物设计）：**
   - 对于长度<14bp的序列：使用Wallace规则
   - 对于长度≥14bp的序列：使用改进公式
   ```
   Tm = 64.9 + 41 × (GC数量 - 16.4) / 总碱基数
   ```
   - 加上盐浓度校正

### Long Repeat罚分

使用现有的`DNARepeatsFinder`工具计算分散重复序列（Dispersed Repeats）的罚分：
- 最小长度：16bp
- 罚分公式：`((length - 15) / 2) × count`
- 检查范围：插入位点上下游各1000bp（共2000bp）
- 最大允许罚分：28分

### Cm-ccdB序列

当前使用的固定序列长度为1011bp，包含：
- 氯霉素抗性基因（Cm）
- ccdB基因（用于阴性筛选）

## 系统架构

### 后端组件
- **Model**: [product/models.py](../product/models.py) - Vector数据模型
- **Utils**: [user_center/utils/vector_automation.py](../user_center/utils/vector_automation.py) - 核心设计算法
- **Tasks**: [user_center/tasks.py](../user_center/tasks.py) - Celery异步任务
- **Views**: [user_center/views.py](../user_center/views.py) - API端点

### 前端组件
- **Template**: [templates/user_center/manage_vector.html](../templates/user_center/manage_vector.html)
- **JavaScript**: 实时状态轮询和结果展示

### 依赖
- Biopython: GenBank文件解析
- Celery: 异步任务处理
- Django: Web框架

## 更新历史

### Version 1.0 (2025-12-22)
- 初始版本发布
- 支持三种克隆方法（Gibson/GoldenGate/T4）
- 自动设计NC-PCR引物（Gibson方法）
- 生成改造后GenBank文件
- 实时状态监控

## 联系与支持

如有问题或建议，请联系技术支持团队。
