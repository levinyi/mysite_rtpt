# super_manage页面说明
## 逻辑

### super_manage/view.py
1. 函数get_table_context(table_name, status=None, start=0)：获取表内容
2. 函数change_status：修改状态
3. upload/download：上传下载

### order_manage.html/vector_manage.html
可在代码中搜索注释label.x找到对应代码块
1. label.0 css style
2. label.1 行模板，其中每个<td>标签为一个列的样式，设置列的显示样式
3. label.2 顶部点击筛选标签，设置筛选标签
3. label.3 表头文本，设置每列的列名
3. label.4 根据后端传值，为前端设置每一行内容

## 增加修改
1. 新增列流程
    1. 修改views.py 函数get_table_context：若vector页面新增列，则在get_table_context的vector_line中添加对应列数据
    2. 修改label.1 行模板：在其中插入需要的列模板，即显示的样式
       1. 插入内容可参照（复制）本文'列模板说明'部分
       2. 注意从上往下的td顺序就是在表中从左往右的顺序，记住该位置
    3. 修改label.3 表头文本：在这里插入列名称，需要与第二步插入位置对应
    4. 修改label.4 设置行内容：根据td顺序，通过td[x]的形式为列内容赋值（参考'列模板说明'）
       1. 注意被影响顺序的后续列，应当对应修改其x值
    5. 增加对应js，内容参考本文'列模板说明'部分
2. 增删行状态流程
    1. 增删顶部筛选选项
       1. 修改label.2 顶部点击筛选标签：增删标签
       2. 修改function clickTab(e, id)，增删标签名称
    2. 增删点击左右切换状态
       1. 若修改了初状态或末状态：修改label.6
          1. 若修改了初状态：最后一行bns[1].disabled = value.toLowerCase() == "{初状态文本}";
          2. 若修改了末状态：if (value.toLowerCase() == "{末状态文本}")
    3. 修改views.py 函数change_status：**按照逻辑顺序**将新增状态加入对应table的status_list内，或直接删除需要删除的状态


## 列模板说明
- **简单文本列**
    </br>
    在label.1:
    ```html
    <!-- 如order_manage的Custom列 -->
    <td>{文本默认内容，js会修改为所需内容}</td>
    ```
    在label.4:
    ```javascript
    td[x].textContent = rowJson['{data name}'];
    ```
  
- **单下载列**：有下载链接时显示蓝色，无下载链接时显示灰色不可用，其中bi-cloud-download为显示图标，a标签为可用显示，button标签为不可用时的显示
    </br></br>
    在label.1:
    ```html
     <!-- 如order_manage的Export列 -->
     <td>
         <a href="" class="row-button"><i class="bi bi-cloud-download"></i></a>
         <button disabled type="button" class="btn btn-link row-button"><i class="bi bi-cloud-download"></i></button>
     </td>        
    ```
    在label.4:
  
    ```javascript
    let ep = td[x].getElementsByTagName("a"), un = td[x].getElementsByTagName("button");
    ep[0].href = rowJson['{data name}'];
    if (rowJson['{data name}'].length) {
        un[0].hidden = true;
        ep[0].hidden = false;
    } else {
        un[0].hidden = false;
        ep[0].hidden = true;
    }    
    ```

- **状态切换列**
    </br>
    在label.1:   
    ```html
    <!-- 如order_manage的status列 -->
     <td>
         <button type="button" class="btn btn-link row-button bi-box-arrow-left text-danger icon-btn"
                 onclick="clickRevokeOrNext(this, 'revoke')">
         </button>
         <span style="display: inline-block;color: darkseagreen;min-width: 96px;">Created</span>
         <button type="button" class="btn btn-link row-button bi-box-arrow-right icon-btn" onclick="clickRevokeOrNext(this,'next')">
         </button>
     </td>
    ```
    在label.4:
    ```javascript
    setRowStatus(td[x], rowJson['{data name}']);
    ```
    类似label.6，创建函数
    ```javascript
    function setRowStatus(e, value) {
        e.querySelector("span").textContent = value;
    
        let bns = e.getElementsByTagName("button");
        if (value.toLowerCase() == "cancelled") {
            bns[0].disabled = true;
            bns[0].classList.remove('text-danger')
        } else {
            bns[0].disabled = false;
            bns[0].classList.add('text-danger');
        }
        bns[1].disabled = value.toLowerCase() == "completed";
    }
    ```
- **文本输入列**
    </br>
    在label.1:  
    ```html
     <!-- 如order_manage的Url列 -->
     <td class="input-td">
         <input onchange="changeXXX(this)" type="text" class="align-middle" placeholder="Please input..."/>
     </td>
   ```
    在label.4:
    ```javascript
    td[x].querySelector("input").value = rowJson['{data name}'];
    ```
    类似label.8，创建函数
    ```javascript
    function changeXXX(e) {
    let row = get_row_content(e);
    $.ajax({
        url: "{指定url}",
        type: "GET",
        data: {
            "id": row.id,
            "newVal": e.value
        },
        async: false,
        success: function (res) {
            // do something
        }
    });
    }
    ```
- **文件下载上传列**：下载状态：有下载链接时显示’删除‘和’下载‘；待上传状态：上传图标；预上传状态：预上传时显示‘文件名’，‘删除预上传’，‘submit’
    </br></br>
    在label.1:    
    ```html
     <!-- 如order_manage的Report列 -->
     <td>
         <!--     下载状态     -->
         <div class="file-down">
             <button type="button" class="btn row-button bi-trash text-danger icon-btn"
                     onclick="clickDelFun(this)">
             </button>
             <a href="" class="bi bi-download icon-btn"></a>
         </div>
         <!--     待上传状态     -->
         <button type="button" class="btn btn-link row-button upload bi-upload icon-btn" onclick="this.querySelector('input').click();">
             <input type="file" style="display: none;" onchange="fileChange(this)">
         </button>
         <!--     预上传状态     -->
         <div class="pre-upload">
             <p style="margin: 0px;font-size: 13px;"></p>
             <button type="button" class="btn row-button bi-trash text-danger icon-btn"
                     onclick="clickDelPreUpload(this)">
             </button>
             <button type="button" class="btn btn-link row-button upload " onclick="clickUpSubmit(this)">
                 {submit之类的上传文本}
             </button>
         </div>
     </td>
    ```
    在label.4:
    ```javascript
    if (rowJson['report'].length) {
        setRowXXX(td[6], "file-down", null, rowJson['report']);
    } else {
        setRowXXX(td[6], "upload");
    }    
    ```
    类似label.5，创建函数
    ```javascript
    function setRowXXX(e, status, filename = null, filepath = null) {
        const fileDown = e.querySelector('.file-down'),
            upload = e.querySelector('.upload'),
            preUpload = e.querySelector('.pre-upload');
        if (status == "file-down") {
            fileDown.hidden = false;
            upload.hidden = true;
            preUpload.hidden = true;
            fileDown.querySelector('a').href = filepath;
        } else if (status == "upload") {
            fileDown.hidden = true;
            upload.hidden = false;
            preUpload.hidden = true;
        } else if (status == "pre-upload") {
            fileDown.hidden = true;
            upload.hidden = true;
            preUpload.hidden = false;
            preUpload.querySelector('p').textContent = filename;
        } else
            console.log("Unknown report element status", status, filename, filepath);
    }
    ```
    关联函数：参考label.7
  - 包括clickDelPreUpload、fileChange、clickDelXXX、clickUpSubmit 
  - clickDelXXX、clickUpSubmit需要根据需要，修改url
  