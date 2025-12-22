# 载体改造自动化设计功能测试指南

## 测试前准备

### 1. 启动Celery Worker

在开始测试前，确保Celery worker正在运行：

```bash
cd /cygene4/dushiyi/mysite_rtpt
celery -A mysite worker -l info
```

如果使用后台运行：
```bash
celery -A mysite worker -l info --detach
```

查看Celery worker状态：
```bash
celery -A mysite inspect active
```

### 2. 确认数据库迁移已完成

```bash
python manage.py migrate product
```

应该看到：
```
Operations to perform:
  Apply all migrations: product
Running migrations:
  Applying product.0007_vector_cloning_method_vector_design_error_and_more... OK
```

### 3. 准备测试用的GenBank文件

创建一个测试用的GenBank文件，确保包含iU20和iD20标记。

**最小测试文件示例** (保存为 `test_vector.gb`)：

```
LOCUS       pTest_Vector            5000 bp    DNA     circular SYN 22-DEC-2025
DEFINITION  Test vector for automation design
ACCESSION   .
VERSION     .
KEYWORDS    .
SOURCE      synthetic DNA construct
  ORGANISM  synthetic DNA construct
REFERENCE   1  (bases 1 to 5000)
  AUTHORS   Test
  TITLE     Direct Submission
FEATURES             Location/Qualifiers
     misc_feature    100..120
                     /label="iU20"
     misc_feature    3000..3020
                     /label="iD20"
     CDS             500..1500
                     /label="Amp"
                     /note="ampicillin resistance"
ORIGIN
        1 atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg
       61 atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg
      121 atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg atcgatcgat cgatcgatcg
      [继续添加序列直到5000bp]
//
```

## 测试场景

### 测试场景 1: 正常上传和设计（Gibson方法）

**目标**: 测试完整的Gibson方法设计流程

**步骤**:
1. 登录系统
2. 进入 Manage Vectors 页面
3. 点击 "Create New Vector" 按钮
4. 填写表单:
   - Vector Name: `Test_Gibson_Vector`
   - 选择文件: `test_vector.gb`
5. 点击 Submit
6. 在载体列表中找到刚上传的载体
7. 点击 "Design" 按钮
8. 等待设计完成（约10-30秒）
9. 查看状态是否变为 "Completed (Gibson)"
10. 点击 "View" 按钮查看结果
11. 检查是否显示:
    - v5NC和v3NC序列
    - 正向和反向引物
    - Tm值
12. 点击 "Download Modified GenBank" 下载文件

**预期结果**:
- ✅ 上传成功
- ✅ 设计状态从 Pending → Processing → Completed
- ✅ 显示 Gibson 方法
- ✅ 显示引物信息
- ✅ 可以下载改造后的GenBank文件

### 测试场景 2: 文件格式验证

**目标**: 测试文件格式验证功能

**步骤**:
1. 尝试上传非.gb格式的文件（例如.txt, .fasta）
2. 观察是否被拒绝

**预期结果**:
- ✅ 显示错误提示: "Please upload a GenBank file (.gb or .genbank format only)"
- ✅ 文件选择被重置

### 测试场景 3: 缺失iU20/iD20标记

**目标**: 测试缺失必需标记的情况

**步骤**:
1. 创建一个没有iU20或iD20标记的GenBank文件
2. 上传该文件
3. 点击 "Design" 按钮
4. 观察错误提示

**预期结果**:
- ✅ 设计状态变为 Failed
- ✅ 错误信息: "未检测到iU20或iD20位置，该文件不可用"

### 测试场景 4: 状态轮询

**目标**: 测试实时状态更新功能

**步骤**:
1. 上传一个载体文件
2. 点击 "Design" 按钮
3. 打开浏览器开发者工具 → Network 标签
4. 观察网络请求

**预期结果**:
- ✅ 每5秒发送一次状态查询请求到 `/user_center/vector_automation_design_status/`
- ✅ 设计完成后停止轮询
- ✅ 页面自动刷新并显示最新状态

### 测试场景 5: 并发设计

**目标**: 测试多个载体同时设计

**步骤**:
1. 上传3个不同的载体文件
2. 依次点击每个载体的 "Design" 按钮
3. 观察所有设计任务是否都能正常完成

**预期结果**:
- ✅ 所有任务都能成功启动
- ✅ 所有任务都能完成（可能顺序不同）
- ✅ 没有任务冲突或失败

### 测试场景 6: 查看历史结果

**目标**: 测试查看已完成设计的结果

**步骤**:
1. 找到一个已经完成设计的载体
2. 刷新页面
3. 点击 "View" 按钮
4. 检查结果是否正确显示

**预期结果**:
- ✅ 所有设计信息正确显示
- ✅ 可以重复查看
- ✅ 可以下载GenBank文件

## 调试技巧

### 1. 查看Celery任务日志

```bash
# 查看正在运行的任务
celery -A mysite inspect active

# 查看已注册的任务
celery -A mysite inspect registered

# 查看任务执行历史
celery -A mysite events
```

### 2. 查看Django日志

在 `settings.py` 中启用详细日志：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### 3. 数据库查询

检查Vector记录的设计状态：

```python
from product.models import Vector

# 查看所有载体的设计状态
for v in Vector.objects.all():
    print(f"{v.vector_name}: {v.design_status} - {v.cloning_method}")

# 查看特定载体的详细信息
v = Vector.objects.get(id=1)
print(f"Status: {v.design_status}")
print(f"Method: {v.cloning_method}")
print(f"v5NC: {v.NC5}")
print(f"v3NC: {v.NC3}")
print(f"Error: {v.design_error}")
```

### 4. 测试单个函数

可以在Django shell中测试单个函数：

```python
python manage.py shell

from user_center.utils.vector_automation import VectorAutomationDesigner

# 测试解析GenBank
designer = VectorAutomationDesigner('/path/to/test_vector.gb')
parsed_data = designer.parse_genbank()
print(parsed_data)

# 测试克隆方法选择
result = designer.select_cloning_method(parsed_data)
print(result)
```

## 常见问题排查

### 问题 1: Celery任务一直处于Processing状态

**可能原因**:
- Celery worker没有运行
- 任务执行出错但没有正确捕获异常

**排查步骤**:
1. 检查Celery worker是否运行: `ps aux | grep celery`
2. 查看Celery日志中的错误信息
3. 检查数据库中的`design_error`字段

### 问题 2: 前端无法触发设计任务

**可能原因**:
- CSRF token问题
- URL路由配置错误
- 权限问题

**排查步骤**:
1. 打开浏览器开发者工具查看Console错误
2. 检查Network标签中的请求是否成功发送
3. 确认用户已登录

### 问题 3: 下载GenBank文件失败

**可能原因**:
- 文件路径不存在
- 文件权限问题

**排查步骤**:
1. 检查`vector.vector_gb`字段是否有值
2. 检查文件是否真实存在: `ls -l media/user_*/vector_file/`
3. 检查文件权限

### 问题 4: 设计失败但没有错误信息

**可能原因**:
- 异常没有被正确捕获
- 错误信息没有保存到数据库

**排查步骤**:
1. 查看Celery worker日志
2. 在代码中添加更多的日志输出
3. 使用Django shell手动执行设计流程

## 性能测试

### 测试载体序列大小对性能的影响

```python
import time
from user_center.utils.vector_automation import VectorAutomationDesigner

files = [
    ('small', '/path/to/small_vector_5kb.gb'),
    ('medium', '/path/to/medium_vector_10kb.gb'),
    ('large', '/path/to/large_vector_20kb.gb'),
]

for name, filepath in files:
    designer = VectorAutomationDesigner(filepath)
    start = time.time()
    parsed_data = designer.parse_genbank()
    result = designer.select_cloning_method(parsed_data)
    end = time.time()
    print(f"{name}: {end - start:.2f} seconds - Method: {result['method'] if result else 'Failed'}")
```

## 自动化测试脚本

创建一个简单的测试脚本 `test_vector_automation.py`：

```python
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from product.models import Vector
from user_center.tasks import async_vector_automation_design
from django.contrib.auth import get_user_model

User = get_user_model()

def test_automation():
    # 创建测试用户
    user = User.objects.get(username='test_user')

    # 创建测试载体
    vector = Vector.objects.create(
        user=user,
        vector_name='Test_Automation_Vector',
        vector_file='path/to/test.gb'
    )

    print(f"Created vector: {vector.id}")

    # 触发设计任务
    task = async_vector_automation_design.delay(vector.id)
    print(f"Task ID: {task.id}")

    # 等待任务完成
    max_wait = 60  # 最多等待60秒
    waited = 0
    while waited < max_wait:
        vector.refresh_from_db()
        print(f"Status: {vector.design_status}")

        if vector.design_status in ['Completed', 'Failed']:
            break

        time.sleep(5)
        waited += 5

    # 输出结果
    vector.refresh_from_db()
    print(f"\nFinal Status: {vector.design_status}")
    print(f"Method: {vector.cloning_method}")
    print(f"v5NC: {vector.NC5}")
    print(f"v3NC: {vector.NC3}")

    if vector.design_error:
        print(f"Error: {vector.design_error}")

if __name__ == '__main__':
    test_automation()
```

运行测试：
```bash
python test_vector_automation.py
```

## 测试检查清单

在发布前，请确认以下所有项目：

- [ ] 文件上传功能正常（只接受.gb格式）
- [ ] 文件大小限制有效（5MB）
- [ ] 文件名格式验证正确
- [ ] iU20/iD20标记检测正常
- [ ] Gibson方法设计成功
- [ ] GoldenGate方法设计成功
- [ ] T4方法设计成功
- [ ] NC-PCR引物设计成功（Gibson）
- [ ] 改造后GenBank文件生成正确
- [ ] 状态实时更新（轮询）
- [ ] 设计结果模态框显示正确
- [ ] 文件下载功能正常
- [ ] 错误处理和提示清晰
- [ ] 并发设计任务不冲突
- [ ] 历史结果可以重复查看
- [ ] Celery任务正确执行
- [ ] 数据库字段正确保存
- [ ] 前端UI响应式布局正常
- [ ] 所有JavaScript函数无错误

## 下一步计划

1. **添加单元测试**: 为核心函数编写pytest测试用例
2. **性能优化**: 对大型载体文件的处理进行优化
3. **错误恢复**: 添加任务失败后的重试机制
4. **用户通知**: 设计完成后发送邮件通知
5. **批量处理**: 支持批量上传和设计
6. **结果导出**: 支持导出设计结果为Excel或PDF
