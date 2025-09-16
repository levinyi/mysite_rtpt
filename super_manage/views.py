import datetime
import json
import os
from math import ceil
import tempfile
from urllib.parse import quote
import zipfile
from Bio import SeqIO
from io import BytesIO, StringIO
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import pandas as pd
# from account.models import UserProfile
from product.models import Species, Vector
from user_account.models import UserProfile
from user_center.models import OrderInfo
from user_center.views import \
    vector_download as uc_vector_download, \
    vector_delete as uc_vector_delete

# from account.views import is_secondary_admin
from django.http import HttpResponseForbidden
from user_center.utils.pagination import Pagination
# from tools.scripts.ParsingGenBankOld import readGenBank

def custom_user_passes_test(test_func):
    """
    自定义装饰器，用于检查用户是否通过测试，不通过时返回 HttpResponseForbidden。
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                # 用户通过测试，执行正常的视图逻辑
                return view_func(request, *args, **kwargs)
            else:
                # 用户未通过测试，返回 HttpResponseForbidden
                return HttpResponseForbidden("No permission")
        return wrapped_view
    return decorator

# 使用自定义装饰器
# is_secondary_admin_required = custom_user_passes_test(is_secondary_admin)


def get_table_context(table_name, status=None, start=0):
    """
    这里修改给前端Table的数据
    table_name:表名
    status：状态，即表上面Tab的
    start:开始的页面，目前功能不完善
    """
    def vector_line(data):
        return {
            'id': data.id,
            'Custom': data.user.username if data.user is not None else '',
            "File": {},
            "Map": 'vector_download/{}/map'.format(data.id) if data.vector_file else '',
            "Map seq": data.vector_map,
            "Vector ID": data.vector_id,
            "iD20": data.id20,
            "iU20": data.iu20,
            "status": data.status,
            "vector_name":data.vector_name
        }

    def order_line(data):
        return {
            'id': data.id,
            'inquiry_id': data.inquiry_id if data.inquiry_id else 'null',
            "custom": data.user.username,
            "quantity": data.gene_infos.count(),
            "create": data.order_time.strftime('%d/%m/%Y %H:%M:%S'),
            "modify": "",
            "export": 'export_order_to_csv/{}'.format(data.id),
            "report": 'download_report/{}'.format(data.id) if data.report_file else '',
            "status": data.status,
            "url": data.url,
        }

    if table_name == 'order':
        obj = OrderInfo.objects
        if status is not None:
            obj = obj.filter(status=status)
        order_by = 'order_time'
        process_fun = order_line
    elif table_name == 'vector':
        obj = Vector.objects
        if status is not None:
            obj = obj.filter(status=status)
        order_by = 'create_date'
        process_fun = vector_line
    else:
        return {}

    cnt_all = obj.count()
    max_row = 15
    # 这里用来设置一次性返回的值，暂时先设一个足够大的值，以后再改
    if start + max_row * 100 > cnt_all:
        datas = obj.order_by(order_by)
    else:
        datas = obj.order_by(order_by)[start:start + max_row * 100]
    rows = []
    for item in datas:
        rows.append(process_fun(item))
    return {
        'title': "Order Manage",
        'max_page': ceil(cnt_all / max_row),
        'max_row': max_row,
        'rows': json.dumps(rows)
    }


@login_required
# @is_secondary_admin_required
@require_GET
def vector_download(request, vector_id, file_type):
    return uc_vector_download(request, vector_id, file_type, True)


@login_required
# @is_secondary_admin_required
@require_POST
def vector_upload(request):
    vector_file = request.FILES.get('vector_file', default=None)
    vector_id = request.POST.get('vector_id', default=None)
    if vector_id is None or vector_file is None:
        return JsonResponse(data={
            'status': 'error',
            'message': 'Invalid params'
        })
    vector = Vector.objects.get(id=vector_id)
    vector.vector_file = vector_file
    vector.save()
    return JsonResponse(data={
        'status': 'success',
        "newVal": 'vector_download/{}/map'.format(vector_id)
    })

@login_required
# @is_secondary_admin_required
def vector_delete(request):
    vector_id = request.GET.get('vector_id', default=None)
    vector = Vector.objects.get(id=vector_id)
    if vector.vector_file:
        file_path = vector.vector_file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        vector.vector_file.delete()
    return JsonResponse(data={
        'status': 'success',
    })




@login_required
# @is_secondary_admin_required
@require_POST
def upload_report(request):
    file = request.FILES.get('file', default=None)
    order_id = request.POST.get('id', default=None)
    if file is None or order_id is None:
        return JsonResponse(data={
            'status': 'error',
            'message': 'Empty params.'
        })
    order = OrderInfo.objects.get(id=order_id)
    order.report_file = file
    order.save()
    return JsonResponse(data={
        'status': 'success',
        'newVal': 'download_report/{}'.format(order_id)
    })


@login_required
# @is_secondary_admin_required
@require_GET
def delete_report(request):
    order_id = request.GET.get('id', default=None)
    order = OrderInfo.objects.get(id=order_id)
    if order.report_file:
        file_path = order.report_file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        order.report_file.delete()
    return JsonResponse(data={
        'status': 'success',
    })


@login_required
# @is_secondary_admin_required
def download_report(request, order_id):
    order = OrderInfo.objects.get(id=order_id)
    file = order.report_file
    if file:
        response = HttpResponse(file, content_type='application/octet-stream')
        name = order.report_file.name.split('/')[-1]
        # quote编码后下载的中文文件名可以正常显示
        response.headers['Content-Disposition'] = "attachment; filename={}".format(quote(name))
        return response
    else:
        return JsonResponse(data={
            'status': 'error',
            'message': "Can't find the file."
        })


@login_required
# @is_secondary_admin_required
@require_GET
def get_rows(request):
    status = request.GET.get('status')
    table_name = request.GET.get('tableName')
    if status and status.lower() == 'all'.lower():
        status = None
    return JsonResponse(data={
        'status': 'success',
        'data': get_table_context(table_name=table_name, status=status)
    })


@login_required
# @is_secondary_admin_required
@require_GET
def change_url(request):
    row_id = request.GET.get('id')
    val = request.GET.get('newVal')
    try:
        OrderInfo.objects.filter(id=row_id).update(url=val)
        return JsonResponse(data={'status': 'success'})
    except Exception as e:
        return JsonResponse(data={'status': 'error', 'message': str(e)})


@login_required
# @is_secondary_admin_required
@require_POST
def submit_vector_data(request):
    post_data = request.body
    data = json.loads(post_data)
    row_id = data['id']
    try:
        Vector.objects.filter(id=row_id).update(
            vector_map=data.get('Map seq'),
            vector_id=data.get('Vector ID'),
            id20=data.get('iD20'),
            iu20=data.get('iU20')
        )
        return JsonResponse(data={'status': 'success'})
    except Exception as e:
        return JsonResponse(data={'status': 'error', 'message': str(e)})


@login_required
# @is_secondary_admin_required
@require_GET
def change_status(request):
    row_id = request.GET.get('id')
    opr = request.GET.get('opr')
    table = request.GET.get('table')

    if row_id is None or opr is None or table is None or table not in ['order', 'vector']:
        return JsonResponse(data={'status': 'error', 'message': 'Invalid value'})

    if table == 'order':
        obj = OrderInfo.objects
        status_list = ['Cancelled', 'Created', 'Synthesizing', 'Shipped', 'Completed']
    elif table == 'vector':
        obj = Vector.objects
        status_list = ['Submitted', 'ReadyToUse']
    item = obj.get(id=row_id)
    status = item.status

    if status not in status_list:
        return JsonResponse(data={'status': 'error', 'message': 'Backstage error'})
    index = status_list.index(status)
    if opr == 'revoke':
        if index == 0:
            return JsonResponse(data={'status': 'failed', 'message': "Can't revoke the {} status".format(status)})
        obj.filter(id=row_id).update(status=status_list[index - 1])
    elif opr == 'next':
        if index == len(status_list) - 1:
            return JsonResponse(data={'status': 'failed', 'message': "Can't next the {} status".format(status)})
        obj.filter(id=row_id).update(status=status_list[index + 1])
    return JsonResponse(data={
        'status': 'success',
        'message': 'Change success',
        'newVal': obj.get(id=row_id).status
    })


@login_required
# @is_secondary_admin_required
def order_manage_old(request):
    order_list = OrderInfo.objects.all()
    page_object = Pagination(request, order_list, page_size=10)
    context = {
        'order_list': page_object.page_queryset,  # 分完页的数据
        'page_string': page_object.html(),  # 页码
    }
    return render(request, 'super_manage/order_manage_old.html', context)

@login_required
# @is_secondary_admin_required
def order_manage(request):
    return render(request, 'super_manage/order_manage.html')

@login_required
# @is_secondary_admin_required
def order_data_api(request):
    order_list = OrderInfo.objects.select_related('user', 'user__userprofile').annotate(
        gene_infos_count=Count('gene_infos')
    ).values(
        'id', 'inquiry_id', 'order_time', 'status', 'user__username', 'gene_infos_count', 'user__userprofile__photo'
    )
    return JsonResponse({'data': list(order_list)})

def get_seq_aa(combined_seq):
    start_index = 0
    while start_index < min(20, len(combined_seq)) and combined_seq[start_index].islower():
        start_index += 1

    end_index = -1
    while abs(end_index) <= min(20, len(combined_seq)) and combined_seq[end_index].islower():
        end_index -= 1

    # Check if any lowercase character was found in the first 20 characters
    if start_index <= min(20, len(combined_seq)):
        # Check if any lowercase character was found in the last 20 characters
        if abs(end_index) >= min(20, len(combined_seq)):
            return combined_seq[start_index:end_index + 1]

    # No lowercase characters found, return the original sequence
    return combined_seq

def generate_REQID(index, order_time):
    # now = datetime.datetime.now()
    formatted_time = order_time.strftime("%Y%m%d")
    last_two_digits_year = formatted_time[2:4]  # 获取年份的最后两位
    return f"R{last_two_digits_year}{formatted_time[4:]}{index:02}"

@login_required
# @is_secondary_admin_required
def order_to_reqins(request, order_id):
    """把订单信息转换成REQIN格式"""
    order = OrderInfo.objects.get(id=order_id)
    order_time = order.order_time
    # Create a list of dictionaries containing gene information
    gene_info_list = [
        {
            'InquiryID': order.inquiry_id,
            'GeneName': gene_info.gene_name,
            'Seq5NC': gene_info.vector.NC5 + (gene_info.i5nc if gene_info.i5nc is not None else ''),
            'PsNTA_CDS': get_seq_aa(gene_info.combined_seq),
            'Seq3NC': (gene_info.i3nc if gene_info.i3nc is not None else '') + gene_info.vector.NC3,
            'ForbiddenSeqs': gene_info.forbid_seq,
            'VectorName': gene_info.vector.vector_name,
            'VectorID': gene_info.vector.vector_id,
            'Species': gene_info.species.species_name if gene_info.species else None,
            'i5nc': gene_info.i5nc,
            'i3nc': gene_info.i3nc,
        }
        for gene_info in order.gene_infos.all()
    ]

    # Create a DataFrame from the list
    df = pd.DataFrame(gene_info_list)
    # Convert datetime columns to timezone-unaware format
    # 添加新的列
    df["Plate"] = "NS"
    df["WellPos"] = "NS"
    # 将Species列中的空值填充为None，其他有值的不变
    df["Species"] = df["Species"].fillna("None")

    # 将ForbiddenSeqs列中的值去掉空格，逗号替换成分号
    df["DoNotBindPrimers"] = np.nan
    df["Memo"] = np.nan
    df["BaseRoles"] = np.nan
    df["FullSeqFAKE"] = np.nan
    df["FullSeqFAKE_Credit"] = np.nan
    df["FullSeqREAL"] = np.nan
    df["FullSeqREAL_Credit"] = np.nan

    df['PsNTA_CDS'] = df['PsNTA_CDS'].str.upper().str.replace(" ", "")
    df['Seq_length'] = len(df['Seq5NC'] + df['PsNTA_CDS'] + df['Seq3NC'])
        
    # workflow type = if seq_length <=500,"WF3p30", IF( seq_length <= 3400,"MWF5p30", IF(seq_length <= 10000, "MWF7p40", else: Toolong
    df['WorkflowType'] = np.select(
        [
            df['Seq_length'] <= 500,
            df['Seq_length'] <= 3400,
            df['Seq_length'] <= 10000,
        ],
        [
            'WF3p30',
            'MWF5p30',
            'MWF7p40',
        ],
        default='Toolong'
    )
    
    ###############################################
    df['IntraREQSN'] = df.groupby(['WorkflowType', 'InquiryID']).cumcount() + 1
    # 假设df是你的DataFrame，column_name是你要生成新索引的列名
    combined = df['InquiryID'].astype(str) + "_" + df['WorkflowType'].astype(str)
    labels, unique = pd.factorize(combined)

    # 将生成的标签添加到DataFrame作为一个新列
    
    df['REQ_index'] = labels +1
    df['REQID'] = df.apply(lambda row: generate_REQID(row['REQ_index'], order_time), axis=1)

    df['IQID'] = df['InquiryID']
    
    # 获取当前时间并格式化为指定格式
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y%m%d_%H%M%S")

    # Temporary directory to store files
    with tempfile.TemporaryDirectory() as temp_dir:
        full_zip_path = os.path.join(temp_dir, f"{order.inquiry_id}_REQINs.zip")
        # Creating the zip file
        with zipfile.ZipFile(full_zip_path, 'w') as zipf:
            # 对每个WorkFlow和REQID的唯一组合进行遍历
            for (workflow, reqid, inqid), group in df.groupby(['WorkflowType', 'REQID', 'InquiryID']):
                # 生成文件名
                filename = os.path.join(temp_dir, f"REQIN_{workflow}_[{reqid}]_{formatted_time}.txt")
                file_path = os.path.join(temp_dir, filename)
                # Select required columns and write to text file
                required_columns = ["Plate", "WellPos", "GeneName", "IQID", "REQID","IntraREQSN","Seq5NC", "PsNTA_CDS", "Seq3NC","VectorID", "Species", 
                                    "ForbiddenSeqs", "DoNotBindPrimers", "Memo", "BaseRoles", "FullSeqFAKE", "FullSeqFAKE_Credit", "FullSeqREAL", "FullSeqREAL_Credit"]
                df_selected = group[required_columns]
                df_selected.to_csv(file_path, index=False, sep='\t')

                # Add the text file to the zip file
                zipf.write(file_path, arcname=filename)

        # Serve the zip file as a response
        with open(full_zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={order.inquiry_id}_REQINs.zip'
            return response     

# not used
@login_required
# @is_secondary_admin_required
def vector_manage_zxl(request):
    return render(request, 'super_manage/vector_manage.html', get_table_context("vector"))

# building now
@login_required
# @is_secondary_admin_required
def vector_manage_old(request):
    search_query = request.GET.get('search_query', '')
    if search_query:
        company_vector_list = Vector.objects.filter(
            Q(vector_id__icontains=search_query) | Q(vector_name__icontains=search_query),
            user=None
        ).order_by('-create_date')
        company_page_object = Pagination(request, company_vector_list, page_size=100)
        custom_vector_list = Vector.objects.filter(
            Q(vector_id__icontains=search_query) | Q(vector_name__icontains=search_query),
            user__isnull=False
        ).order_by('-create_date')
        custom_page_object = Pagination(request, custom_vector_list, page_size=100)
    else:
        '''list vector'''
        company_vector_list = Vector.objects.filter(user=None).order_by('-create_date')
        company_page_object = Pagination(request, company_vector_list, page_size=100)

        custom_vector_list = Vector.objects.filter(user__isnull=False).order_by('-create_date')
        custom_page_object = Pagination(request, custom_vector_list, page_size=100)

    context = {
        'company_vector_list': company_page_object.page_queryset,  # 分完页的数据
        'company_page_string': company_page_object.html(),  # 页码
        'custom_vector_list': custom_page_object.page_queryset,  # 分完页的数据
        'custom_page_string': custom_page_object.html(),  # 页码
    }
    return render(request, 'super_manage/vector_manage_dsy.html', context)

@login_required
# @is_secondary_admin_required
def vector_manage(request):
    return render(request, 'super_manage/vector_manage.html')

@login_required
# @is_secondary_admin_required
def vector_data_api(request):
    '''获取所有的vector数据,展示在前端表格中'''
    vector_list = Vector.objects.values(
        'id', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20', 
        'status','user__username', 'vector_file', 'vector_png', 'vector_gb'
    )
    return JsonResponse({'data': list(vector_list)})


@csrf_exempt  # 使用此装饰器来禁用 CSRF 保护，如果你在 AJAX 请求中已提供 CSRF token，则不需要这个装饰器
def vector_update_field(request):
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        # 检查是否提供了 vector_id 和字段
        if not vector_id or not field:
            return JsonResponse({'status': 'error', 'message': 'Missing vector ID or field name'})

        # 获取相应的 vector 实例
        vector = Vector.objects.get(id=vector_id)
        
        # 检查并更新字段
        if hasattr(vector, field):
            setattr(vector, field, value)
            vector.save()
            return JsonResponse({'status': 'success', 'message': 'Field updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid field name'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
# @is_secondary_admin_required
def vector_delete(request):
    '''删除vector文件'''
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        vector = Vector.objects.get(id=vector_id)
    
        if vector.vector_file:
            file_path = vector.vector_file.path
            if os.path.exists(file_path):
                os.remove(file_path)
        if vector.vector_gb:
            file_path = vector.vector_gb.path
            if os.path.exists(file_path):
                os.remove(file_path)
        if vector.vector_png:
            file_path = vector.vector_png.path
            if os.path.exists(file_path):
                os.remove(file_path)
        vector.delete()
        return JsonResponse({'status': 'success', 'message': 'Vector deleted Successfully'})
    else:
        return JsonResponse({'status': 'failed', 'message': 'Not A Post Request.'})


@login_required
# @is_secondary_admin_required
@csrf_exempt
def vector_upload_file(request):
    '''for customer's vector file, vector_png and vector_gb files.'''
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        vector_id = request.POST.get('vectorId')
        file_type = request.POST.get('fileType')

        if uploaded_file is None or vector_id is None or file_type is None:
            return JsonResponse({'status': 'failed', 'message': 'Invalid params.'})

        try:
            vector = Vector.objects.get(id=vector_id)
            if file_type == 'vector_file':
                if vector.vector_file:
                    file_path = vector.vector_file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                vector.vector_file = uploaded_file
            elif file_type == 'vector_png':
                # 先验证文件是否为图片文件
                if not uploaded_file.name.endswith('.png') and not uploaded_file.name.endswith('.jpg') and not uploaded_file.name.endswith('.jpeg'):
                    return JsonResponse({'status': 'failed', 'message': 'Not a image file.'})
                # 如果存在旧的图片文件，先删除
                if vector.vector_png:
                    file_path = vector.vector_png.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                vector.vector_png = uploaded_file
            elif file_type == 'vector_gb':
                # 先验证文件是否为genebank文件
                if not uploaded_file.name.endswith('.gb') and not uploaded_file.name.endswith('.gbk'):
                    return JsonResponse({'status': 'failed', 'message': 'Not a genebank file.'})
                # 验证文件是否为合法的genebank文件
                try:
                    file_content = StringIO(uploaded_file.read().decode('utf-8'))
                    record = SeqIO.read(file_content, "genbank")
                except Exception as e:
                    return JsonResponse({'status': 'failed', 'message': str(e)})
                # 如果存在旧的genebank文件，先删除
                if vector.vector_gb:
                    file_path = vector.vector_gb.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                vector.vector_gb = uploaded_file
            else:
                return JsonResponse({'status': 'failed', 'message': 'Invalid params.'})
            vector.save()
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)})
        
        return JsonResponse({'status': 'success', 'message': 'File uploaded Successfully'})

@login_required
# @is_secondary_admin_required
def vector_edit_item(request):
    '''编辑vector的状态， 将vector的状态改为ReadyToUse'''
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        new_status = request.POST.get('new_status')
        try:
            vector = Vector.objects.get(id=vector_id)
            vector.status = new_status
            vector.save()
            return JsonResponse({'status': 'success'})
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Vector not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
# @is_secondary_admin_required
def vector_add_item(request):
    '''添加新的vector 从CSV文件上传'''
    if request.method == 'POST':
        csv_file = request.FILES.get('csvFile')
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({"message": "File is not CSV type", "status": "error"}, status=400)
        
        # 使用 Pandas 读取 CSV 文件
        try:
            df = pd.read_csv(csv_file)
            # 对于 DataFrame 中的每一行，创建一个模型实例并保存
            # 这里 dataframe中的列名与模型中的字段名不一致，它们之间的对应关系是：
            # dataframe中的列名 -> 模型中的字段名
            # Vector_ID -> vector_id
            # Vector_Name -> vector_name
            # Vector_Seq(From_v3NC_Downstream_to_v5NC_Upstream_withoutV3NCv5NC_Seq) -> vector_map
            # v5NC -> NC5
            # v3NC -> NC3
            # iU20 -> iu20
            # iD20 -> id20
            for _, row in df.iterrows():
                vector_data = {
                    'vector_name': row['Vector_Name'],
                    'vector_map': row['Vector_Seq(From_v3NC_Downstream_to_v5NC_Upstream_withoutV3NCv5NC_Seq)'],
                    'NC5': row['v5NC'],
                    'NC3': row['v3NC'],
                    'iu20': row['iU20'],
                    'id20': row['iD20'],
                    'status': 'ReadyToUse'
                }
                
                Vector.objects.update_or_create(
                    vector_id=row['Vector_ID'],
                    defaults=vector_data
                )

            return JsonResponse({"message": "CSV file has been imported", "status": "success"}, status=200)

        except Exception as e:
            return JsonResponse({"message": str(e), "status": "error"}, status=500)
    
    return JsonResponse({"message": "Invalid request", "status": "error"}, status=400)

@login_required
# @is_secondary_admin_required
def user_manage_old(request): 
    user_list = UserProfile.objects.all().order_by('-register_time')
    page_object = Pagination(request, user_list, page_size=15)
    context = {
        'user_list': page_object.page_queryset,  # 分完页的数据
        'page_string':page_object.html(),  # 页码
    }
    return render(request, 'super_manage/user_manage.html', context)

@login_required
# @is_secondary_admin_required
def user_manage(request):
    return render(request, 'super_manage/user_manage.html')

@login_required
# @is_secondary_admin_required
def user_data_api(request):
    """返回所有用户（包括尚未创建UserProfile的）
    使用User为主表，左连接UserProfile。
    """
    qs = (
        User.objects
        .select_related('userprofile')
        .values(
            'id', 'username', 'email',
            'userprofile__first_name', 'userprofile__last_name', 'userprofile__department',
            'userprofile__phone', 'userprofile__company', 'userprofile__shipping_address',
            'userprofile__photo', 'userprofile__register_time', 'userprofile__is_verify'
        )
    )
    data = []
    for u in qs:
        data.append({
            'user__id': u['id'],
            'user__username': u['username'],
            'email': u['email'],
            'first_name': u['userprofile__first_name'],
            'last_name': u['userprofile__last_name'],
            'department': u['userprofile__department'],
            'phone': u['userprofile__phone'],
            'company': u['userprofile__company'],
            'shipping_address': u['userprofile__shipping_address'],
            'photo': u['userprofile__photo'],
            'register_time': u['userprofile__register_time'],
            'is_verify': u['userprofile__is_verify'],
        })
    return JsonResponse({'data': data})

@login_required
# @is_secondary_admin_required
def view_user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    userprofile, _ = UserProfile.objects.get_or_create(user=user)
    return render(request, 'super_manage/user_profile.html', {"user": user, "userprofile": userprofile})

@login_required
# @is_secondary_admin_required
def save_user_profile(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        userprofile, _ = UserProfile.objects.get_or_create(user=user)
        userprofile.first_name = request.POST.get('first_name')
        userprofile.last_name = request.POST.get('last_name')
        # 邮箱属于User模型
        user.email = request.POST.get('email')
        userprofile.department = request.POST.get('department')
        userprofile.phone = request.POST.get('phone')
        userprofile.company = request.POST.get('company')
        userprofile.shipping_address = request.POST.get('shipping_address')
        user.save()
        userprofile.save()
        return render(request, 'super_manage/user_profile.html', {"user": user, "userprofile": userprofile})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def save_user_avatar(request):
    if request.method == 'POST':
        # 前端传参名为 'userid'
        user_id = request.POST.get('user_id') or request.POST.get('userid')
        imagePath = request.POST.get('imagePath')
        UserProfile.objects.filter(user_id=user_id).update(photo=imagePath)
        return redirect('super_manage:view_user_profile', user_id=user_id)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
# @is_secondary_admin_required
def species_manage(request):
    '''这种适合纯模版的'''
    return render(request, 'super_manage/species_codon_manage.html')

@login_required
# @is_secondary_admin_required
def species_data_api(request):
    species_list = Species.objects.values('id', 'species_name', 'species_note', 'species_codon_file')
    return JsonResponse({'data': list(species_list)})
