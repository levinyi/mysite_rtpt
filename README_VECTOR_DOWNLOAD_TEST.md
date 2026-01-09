# 质粒图谱下载API测试文档

## API状态检查结果

✅ **API工作正常** - 测试通过

### 测试结果摘要

- **测试时间**: 2026-01-05
- **测试质粒**: pET-28(+) (ID: 195)
- **测试文件类型**: GenBank格式 (.gb)
- **测试结果**: 成功下载 14,573 字节的GenBank文件
- **文件格式**: 正确的GenBank格式，包含完整的序列注释

## API接口信息

### 端点
```
/user_center/vector_download/<vector_id>/<file_type>/
```

### 参数
- `vector_id` (int): 质粒的数据库ID
- `file_type` (str): 文件类型
  - `gb`: GenBank格式文件
  - `map`: PNG图谱文件
  - `file`: 用户上传的原始文件

### 权限
- 用户只能下载自己的质粒或公司的质粒（user字段为null）
- 需要登录认证 (@login_required)

### 响应
- **成功**: HTTP 200, 返回文件下载
- **失败**: HTTP 404, 文件不存在

## 测试脚本使用方法

### 基本用法

```bash
# 列出所有可用的质粒
python test_vector_download.py --list

# 通过质粒名称下载（支持模糊匹配）
python test_vector_download.py --vector-name "pET-28"

# 通过质粒ID下载
python test_vector_download.py --vector-id 195

# 下载PNG图谱
python test_vector_download.py --vector-id 195 --file-type map

# 指定输出目录
python test_vector_download.py --vector-id 195 --output-dir ./my_downloads
```

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--vector-id` | 质粒的数据库ID | `--vector-id 195` |
| `--vector-name` | 质粒名称（模糊匹配） | `--vector-name "pET-28"` |
| `--output-dir` | 下载文件保存目录 | `--output-dir ./downloads` |
| `--file-type` | 文件类型（gb/map/file） | `--file-type gb` |
| `--list` | 列出所有质粒 | `--list` |
| `--list-limit` | 列出质粒的数量限制 | `--list-limit 50` |

### 示例输出

```
============================================================
开始测试质粒图谱下载API
============================================================
✓ 找到质粒: ID=195, 名称=pET-28(+)

质粒信息:
  - ID: 195
  - 名称: pET-28(+)
  - 载体ID: pGZ1477(Kan)
  - 序列长度: 5161 bp
  - 所有者: 公司质粒

文件状态:
  - GenBank文件: ✓ 存在
  - PNG图谱: ✗ 不存在
  - 原始文件: ✗ 不存在

✓ 文件已保存: ./downloads/RootPath_pGZ1477-pET-28.gb
  文件大小: 14573 字节
```

## 数据库中的质粒列表

目前数据库中有 **43 个质粒**，以下是部分有GenBank文件的质粒：

| ID | 名称 | 载体ID | 序列长度 | GenBank | PNG | 所有者 |
|----|------|--------|----------|---------|-----|--------|
| 210 | myvector3 | - | 5212 bp | ✓ | ✗ | dushiyi |
| 196 | pUC19_Kan | - | 2459 bp | ✓ | ✗ | 公司 |
| 195 | pET-28(+) | pGZ1477(Kan) | 5161 bp | ✓ | ✗ | 公司 |
| 190 | pUC19 | - | 2597 bp | ✓ | ✗ | 公司 |
| 168 | pcDNA3.4_hs_IGHE | - | 7343 bp | ✓ | ✗ | 公司 |
| 167 | pcDNA3.4_hs_IGHA2 | - | 7075 bp | ✓ | ✗ | 公司 |
| 166 | pcDNA3.4_hs_IGHA1 | - | 7114 bp | ✓ | ✗ | 公司 |
| 162 | pPICZalpha | - | 3414 bp | ✓ | ✓ | 公司 |
| 155 | pESC-URA | - | 6529 bp | ✓ | ✓ | 公司 |

## 关于 pGZ1522(Amp)

⚠️ **注意**: 数据库中目前没有名为 `pGZ1522(Amp)` 的质粒。

如果需要测试该质粒，请先：
1. 在系统中上传或创建该质粒
2. 确保生成了GenBank文件（vector_gb字段）
3. 然后使用测试脚本进行测试

## API代码位置

- **URL配置**: `user_center/urls.py:44`
- **视图函数**: `user_center/views.py:2293-2394`
- **模型定义**: `product/models.py:13-43`

## 技术细节

### API实现逻辑 (user_center/views.py:2365-2379)

```python
elif file_type == 'gb':
    # 返回vector_genebank文件
    vector_gb = vector_object.vector_gb
    if vector_gb:
        name = vector_gb.name
        file_path = default_storage.path(name)
        basename = os.path.basename(file_path)
        with default_storage.open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/octet-stream')
            custom_filename = f'RootPath_{basename}'
            response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
            return response
    else:
        return HttpResponse("No vector GeneBank file found", status=404)
```

### 文件命名规则

下载的文件名格式：`RootPath_{原始文件名}`

例如：
- GenBank文件: `RootPath_pGZ1477-pET-28.gb`
- PNG图谱: `RootPath_pET-28.png`

## 常见问题

### Q: 如何找到质粒的ID？
A: 使用 `python test_vector_download.py --list` 查看所有质粒及其ID。

### Q: 下载失败提示"No vector GeneBank file found"？
A: 该质粒没有GenBank文件，请检查质粒的vector_gb字段是否有值。

### Q: 提示权限错误？
A: 确保你的用户账户有权限访问该质粒（自己的质粒或公司质粒）。

### Q: 如何批量下载？
A: 可以编写脚本循环调用测试脚本，或者修改脚本添加批量下载功能。

## 相关文档

- Vector模型字段说明: `product/models.py`
- URL路由配置: `user_center/urls.py`
- 视图函数实现: `user_center/views.py`
