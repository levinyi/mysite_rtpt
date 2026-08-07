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
from product.models import (
    Species, Vector, VectorElement, VectorElementOccurrence, compute_seq_hash,
)
from user_account.models import UserProfile
from user_center.models import OrderInfo
from user_center.views import \
    vector_download as uc_vector_download, \
    vector_delete as uc_vector_delete
from user_center.utils.vector_automation import VectorAutomationDesigner
from user_center.utils.element_extractor import extract_candidates_bulk, commit_candidates
from user_center.utils.element_screen import (
    screen_sequence, find_element_by_sequence, invalidate_index_cache,
    DEFAULT_MIN_LENGTH, DEFAULT_MIN_IDENTITY,
)

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
        'i5NC', 'i3NC',
        'status','user__username', 'vector_file', 'vector_png', 'vector_gb',
        'design_status', 'cloning_method', 'design_error', 'is_public'
    )
    return JsonResponse({'data': list(vector_list)})


@login_required
# @is_secondary_admin_required
@require_GET
def vector_export_excel(request):
    """批量导出 Vector 为 Excel 备份。

    可选 ?status=ReadyToUse 过滤（不传则导出全部）。前 7 列与 CSV 导入模板
    （vector_add_item）表头一致，导出的备份可直接再导回。
    """
    status = request.GET.get('status') or None
    qs = Vector.objects.select_related('user').order_by('-create_date')
    if status:
        qs = qs.filter(status=status)

    seq_col = 'Vector_Seq(From_v3NC_Downstream_to_v5NC_Upstream_withoutV3NCv5NC_Seq)'
    columns = [
        'Vector_ID', 'Vector_Name', 'iU20', 'iD20', 'v5NC', 'v3NC', seq_col,
        'i5NC', 'i3NC', 'Status', 'User', 'Cloning_Method',
        'Antibiotic_Resistance', 'Design_Status', 'Primer_Forward',
        'Primer_Reverse', 'Create_Date',
    ]
    rows = []
    for v in qs:
        rows.append({
            'Vector_ID': v.vector_id,
            'Vector_Name': v.vector_name,
            'iU20': v.iu20,
            'iD20': v.id20,
            'v5NC': v.NC5,
            'v3NC': v.NC3,
            seq_col: v.vector_map,
            'i5NC': v.i5NC,
            'i3NC': v.i3NC,
            'Status': v.status,
            'User': v.user.username if v.user else 'RootPath',
            'Cloning_Method': v.cloning_method,
            'Antibiotic_Resistance': v.antibiotic_resistance,
            'Design_Status': v.design_status,
            'Primer_Forward': v.primer_forward,
            'Primer_Reverse': v.primer_reverse,
            'Create_Date': v.create_date.strftime('%Y-%m-%d %H:%M:%S') if v.create_date else '',
        })

    df = pd.DataFrame(rows, columns=columns)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Vectors')
    output.seek(0)

    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"vectors_{status or 'all'}_{now}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    return response


@login_required
@require_POST
def vector_automation_design_trigger(request):
    """
    管理员触发载体改造自动化设计
    """
    vector_id = request.POST.get('vector_id')
    forced_method = request.POST.get('forced_method') or None
    if not vector_id:
        return JsonResponse({'status': 'error', 'message': 'Missing vector ID'})

    # 校验指定的克隆方法
    valid_methods = {'Gibson', 'GoldenGate', 'T4'}
    if forced_method and forced_method not in valid_methods:
        return JsonResponse({'status': 'error', 'message': f'不支持的克隆方法: {forced_method}'})

    try:
        vector = Vector.objects.get(id=vector_id)
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '载体不存在'})

    if not vector.vector_file:
        return JsonResponse({'status': 'error', 'message': '请先上传载体文件'})

    vector.design_status = 'Pending'
    vector.design_error = None
    vector.save()

    from user_center.tasks import async_vector_automation_design
    task = async_vector_automation_design.delay(vector_id, forced_method=forced_method)

    return JsonResponse({
        'status': 'success',
        'message': '载体改造设计任务已启动',
        'task_id': task.id
    })


@login_required
@require_GET
def vector_automation_design_status(request):
    """
    管理员查询载体改造自动化设计状态
    """
    vector_id = request.GET.get('vector_id')
    if not vector_id:
        return JsonResponse({'status': 'error', 'message': 'Missing vector ID'})

    try:
        vector = Vector.objects.get(id=vector_id)
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '载体不存在'})

    def parse_primer(value):
        if value and '::' in value:
            parts = value.split('::', 1)
            return parts[0], parts[1]
        return None, value or ''

    response_data = {
        'status': 'success',
        'design_status': vector.design_status,
        'cloning_method': vector.cloning_method,
        'design_error': vector.design_error
    }

    if vector.design_status == 'Completed':
        forward_name, forward_seq = parse_primer(vector.primer_forward)
        reverse_name, reverse_seq = parse_primer(vector.primer_reverse)
        forward_hairpin_tm = VectorAutomationDesigner.calculate_hairpin_tm(forward_seq) if forward_seq else None
        reverse_hairpin_tm = VectorAutomationDesigner.calculate_hairpin_tm(reverse_seq) if reverse_seq else None
        forward_dg = VectorAutomationDesigner.calculate_dimer_dg(forward_seq) if forward_seq else None
        reverse_dg = VectorAutomationDesigner.calculate_dimer_dg(reverse_seq) if reverse_seq else None
        hetero_dg = None
        if forward_seq and reverse_seq:
            hetero_dg = VectorAutomationDesigner.calculate_dimer_dg(forward_seq, reverse_seq)

        colony_primers = []
        if vector.colony_pcr_primers:
            try:
                colony_primers = json.loads(vector.colony_pcr_primers)
            except (ValueError, TypeError):
                colony_primers = []

        response_data.update({
            'v5nc': vector.NC5,
            'v3nc': vector.NC3,
            'i5nc': vector.i5NC,
            'i3nc': vector.i3NC,
            'iu20': vector.iu20,
            'id20': vector.id20,
            'primer_forward': forward_seq,
            'primer_reverse': reverse_seq,
            'primer_forward_name': forward_name,
            'primer_reverse_name': reverse_name,
            'primer_forward_tm': vector.primer_forward_tm,
            'primer_reverse_tm': vector.primer_reverse_tm,
            'primer_forward_hairpin_tm': forward_hairpin_tm,
            'primer_reverse_hairpin_tm': reverse_hairpin_tm,
            'primer_forward_homodimer_dg': forward_dg,
            'primer_reverse_homodimer_dg': reverse_dg,
            'primer_heterodimer_dg': hetero_dg,
            'colony_pcr_primers': colony_primers,
            'has_genbank': bool(vector.vector_gb),
            'has_colony_csv': bool(colony_primers),
        })

    return JsonResponse(response_data)


@login_required
@require_GET
def vector_colony_pcr_csv(request, vector_id):
    """
    导出菌落PCR 5对引物 CSV
    表头：Plasmid_number, upstream, Start_pos, downstream, upstream+downstream,
          ColonyPCR_primer_F, ColonyPCR_primer_F(5'-3'),
          ColonyPCR_primer_R, ColonyPCR_primer_R(5'-3')
    """
    import csv

    try:
        vector = Vector.objects.get(id=vector_id)
    except Vector.DoesNotExist:
        return HttpResponse('Vector not found', status=404)

    if not vector.colony_pcr_primers:
        return HttpResponse('No colony PCR primers', status=404)

    try:
        pairs = json.loads(vector.colony_pcr_primers)
    except (ValueError, TypeError):
        return HttpResponse('Invalid colony PCR data', status=500)

    plasmid_number = vector.vector_id or vector.vector_name or f'Vector_{vector.id}'
    safe_name = plasmid_number.replace('/', '_').replace('\\', '_')
    filename = f'{safe_name}_ColonyPCR.csv'

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
    response.write('﻿')  # UTF-8 BOM 让 Excel 正确识别中文

    writer = csv.writer(response)
    writer.writerow([
        'Plasmid_number',
        'upstream',
        'Start_pos',
        'downstream',
        'upstream+downstream',
        'ColonyPCR_primer_F',
        "ColonyPCR_primer_F(5'-3')",
        'ColonyPCR_primer_R',
        "ColonyPCR_primer_R(5'-3')",
        'Note',
    ])

    # 兼容历史数据：旧 JSON 没有 is_best 时回退到 index==1
    has_best_flag = any(pair.get('is_best') for pair in pairs)

    for pair in pairs:
        fwd = pair.get('forward') or {}
        rev = pair.get('reverse') or {}
        fwd_seq = fwd.get('sequence', '') or ''
        rev_seq = rev.get('sequence', '') or ''
        pair_idx = pair.get('index') or 0

        # upstream / downstream / 合并长度（设计时已算好，存于 JSON）
        upstream_seq = pair.get('upstream_seq', '') or ''
        downstream_seq = pair.get('downstream_seq', '') or ''
        combined_len = pair.get('combined_flank_length')
        if combined_len is None:
            combined_len = len(upstream_seq) + len(downstream_seq)

        is_best = pair.get('is_best') if has_best_flag else (pair_idx == 1)
        if is_best:
            note = '★ Best (recommended)'
        else:
            note = f'Backup #{pair_idx}'

        writer.writerow([
            plasmid_number,
            upstream_seq,
            pair.get('start_pos', ''),
            downstream_seq,
            combined_len,
            fwd.get('name', ''),
            fwd_seq,
            rev.get('name', ''),
            rev_seq,
            note,
        ])

    return response


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
            # 布尔字段（如 is_public 公开开关）：POST 传来的是字符串，需转成真正的布尔值
            from django.db.models import BooleanField
            model_field = vector._meta.get_field(field)
            if isinstance(model_field, BooleanField):
                value = str(value).strip().lower() in ('1', 'true', 'yes', 'on')
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
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'message': 'Not A Post Request.'})

    vector_id = request.POST.get('vector_id') or request.POST.get('gene_id')
    if not vector_id:
        return JsonResponse({'status': 'failed', 'message': 'Missing vector_id'})

    try:
        vector = Vector.objects.get(id=vector_id)
    except (Vector.DoesNotExist, ValueError):
        return JsonResponse({'status': 'failed', 'message': f'Vector not found: {vector_id}'})

    for field_name in ('vector_file', 'vector_gb', 'vector_png'):
        field = getattr(vector, field_name, None)
        if field:
            try:
                file_path = field.path
                if os.path.exists(file_path):
                    os.remove(file_path)
            except (ValueError, OSError):
                pass

    vector.delete()
    return JsonResponse({'status': 'success', 'message': 'Vector deleted Successfully'})


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
                # SnapGene 在中文 Windows 上导出的 .gb 常用 GBK 编码（feature label 含中文时），
                # 这里按 utf-8 → gbk → latin-1 顺序兜底，避免中文标签直接报错
                raw_bytes = uploaded_file.read()
                text = None
                for enc in ('utf-8', 'gbk', 'latin-1'):
                    try:
                        text = raw_bytes.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                if text is None:
                    return JsonResponse({'status': 'failed', 'message': '文件编码无法识别，请确认是 GenBank 格式文件'})
                try:
                    record = SeqIO.read(StringIO(text), "genbank")
                except Exception as e:
                    return JsonResponse({'status': 'failed', 'message': str(e)})
                # 读完后游标在末尾，重置一下让后续 vector.vector_gb = uploaded_file 能存到完整内容
                uploaded_file.seek(0)
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
            'id', 'username', 'email', 'date_joined',
            'userprofile__first_name', 'userprofile__last_name', 'userprofile__department',
            'userprofile__phone', 'userprofile__company', 'userprofile__shipping_address',
            'userprofile__photo', 'userprofile__register_time', 'userprofile__is_verify'
        )
    )
    data = []
    for u in qs:
        # 注册时间优先用 User.date_joined（每个用户都有、权威），
        # 没有时再退回 UserProfile.register_time（无 profile 的用户会是空）
        joined = u['date_joined']
        register_time = joined.strftime('%Y-%m-%d %H:%M') if joined else (u['userprofile__register_time'] or '')
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
            'register_time': register_time,
            'is_verify': u['userprofile__is_verify'],
        })
    return JsonResponse({'data': data})


@login_required
# @is_secondary_admin_required
@require_POST
def toggle_user_verify(request):
    """管理员在用户列表手动开关某用户的 is_verify（已审核）。
    传 is_verify=1/0 按指定值设置；不传则翻转当前值。"""
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Missing user_id'})
    try:
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError):
        return JsonResponse({'status': 'error', 'message': 'User not found'})

    profile, _ = UserProfile.objects.get_or_create(user=user)
    raw = request.POST.get('is_verify')
    if raw is not None:
        new_val = str(raw).lower() in ('1', 'true', 'yes', 'on')
    else:
        new_val = not profile.is_verify
    profile.is_verify = new_val
    profile.save(update_fields=['is_verify'])
    return JsonResponse({'status': 'success', 'is_verify': new_val})


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


# ============================================================================
# 质粒元件库（Vector Element Library）
# ============================================================================

@login_required
def element_manage(request):
    return render(request, 'super_manage/element_manage.html', {
        # 列表给 Django 的 {% for %} 用；JSON 串给页面里的 JS 用
        # （直接把 Python 的 tuple 列表插进 <script> 会渲染成 [('a', 'b')]，不是合法 JS）
        'element_types': VectorElement.ELEMENT_TYPES,
        'element_types_json': json.dumps(VectorElement.ELEMENT_TYPES),
        'risk_levels_json': json.dumps(VectorElement.RISK_LEVELS),
    })


@login_required
def element_data_api(request):
    """元件列表。occurrence_count 让管理员一眼看出哪些是"跨多个载体复用"的核心元件。"""
    qs = (
        VectorElement.objects
        .annotate(occurrence_count=Count('occurrences'))
        .values('id', 'name', 'element_type', 'seq_length', 'sequence', 'aliases',
                'description', 'source_vector_name', 'source_kind', 'genbank_feature_type',
                'screen_enabled', 'risk_level', 'is_active', 'created_at', 'occurrence_count')
        .order_by('element_type', 'name')
    )
    type_labels = dict(VectorElement.ELEMENT_TYPES)
    data = []
    for row in qs:
        row['element_type_display'] = type_labels.get(row['element_type'], row['element_type'])
        row['created_at'] = row['created_at'].strftime('%Y-%m-%d') if row['created_at'] else ''
        data.append(row)
    return JsonResponse({'data': data, 'element_types': VectorElement.ELEMENT_TYPES})


@login_required
def element_detail_api(request, element_id):
    """元件详情：序列 + 它出现在哪些载体上。"""
    try:
        element = VectorElement.objects.get(pk=element_id)
    except VectorElement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '元件不存在'}, status=404)

    occurrences = [
        {
            'vector_id': occ.vector_id,
            'vector_name': occ.vector.vector_name,
            'vector_code': occ.vector.vector_id or '',
            'owner': occ.vector.user.username if occ.vector.user else '公司',
            'start': occ.start, 'end': occ.end, 'strand': occ.strand,
            'label_in_vector': occ.label_in_vector,
        }
        for occ in element.occurrences.select_related('vector', 'vector__user').all()
    ]
    return JsonResponse({
        'status': 'success',
        'element': {
            'id': element.pk,
            'name': element.name,
            'element_type': element.element_type,
            'element_type_display': element.get_element_type_display(),
            'sequence': element.sequence,
            'seq_length': element.seq_length,
            'aliases': element.aliases or [],
            'description': element.description,
            'source_vector_name': element.source_vector_name,
            'source_kind': element.source_kind,
            'genbank_feature_type': element.genbank_feature_type,
            'screen_enabled': element.screen_enabled,
            'risk_level': element.risk_level,
            'is_active': element.is_active,
        },
        'occurrences': occurrences,
    })


# 只允许改这些字段：VectorElement 上还有 seq_hash / source_vector 等不该被前端直接写的字段
ELEMENT_EDITABLE_FIELDS = {
    'name', 'element_type', 'description', 'screen_enabled', 'risk_level', 'is_active', 'sequence',
}


@login_required
@require_POST
def element_update_field(request):
    element_id = request.POST.get('element_id')
    field = request.POST.get('field')
    value = request.POST.get('value')

    if not element_id or field not in ELEMENT_EDITABLE_FIELDS:
        return JsonResponse({'status': 'error', 'message': f'字段不可编辑: {field}'})

    try:
        element = VectorElement.objects.get(pk=element_id)
    except VectorElement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '元件不存在'})

    if field in ('screen_enabled', 'is_active'):
        value = str(value).strip().lower() in ('1', 'true', 'yes', 'on')
    elif field == 'sequence':
        value = ''.join(str(value).split()).upper()
        if not value:
            return JsonResponse({'status': 'error', 'message': '序列不能为空'})
        clash = VectorElement.objects.filter(seq_hash=compute_seq_hash(value)).exclude(pk=element.pk).first()
        if clash:
            return JsonResponse({'status': 'error',
                                 'message': f'该序列已存在于元件「{clash.name}」，不能重复'})

    setattr(element, field, value)
    element.save()
    invalidate_index_cache()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def element_delete(request):
    element_id = request.POST.get('element_id')
    try:
        element = VectorElement.objects.get(pk=element_id)
    except (VectorElement.DoesNotExist, ValueError):
        return JsonResponse({'status': 'error', 'message': '元件不存在'})
    name = element.name
    element.delete()   # occurrences 级联删除
    invalidate_index_cache()
    return JsonResponse({'status': 'success', 'message': f'已删除元件「{name}」'})


MAX_EXTRACT_VECTORS = 200   # 一次解析的载体数上限，防止手滑全选几千个把请求拖死


@login_required
@require_POST
def element_extract_api(request):
    """批量解析载体图谱，列出候选元件（不落库）。

    同一条序列在多个载体上只返回一行，带 occurrences —— 勾一次就能把它在所有
    载体上的出现位置一起入库。
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '请求体不是合法 JSON'})

    try:
        vector_ids = [int(v) for v in (payload.get('vector_ids') or [])]
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': '载体 ID 格式不对'})

    if not vector_ids:
        return JsonResponse({'status': 'error', 'message': '请先选择载体'})
    if len(vector_ids) > MAX_EXTRACT_VECTORS:
        return JsonResponse({'status': 'error',
                             'message': f'一次最多解析 {MAX_EXTRACT_VECTORS} 个载体，'
                                        f'当前选了 {len(vector_ids)} 个，请分批来'})

    vectors = list(Vector.objects.filter(pk__in=vector_ids).select_related('user'))
    if not vectors:
        return JsonResponse({'status': 'error', 'message': '选中的载体都不存在'}, status=404)

    result = extract_candidates_bulk(vectors)
    result['status'] = 'success'
    result['element_types'] = VectorElement.ELEMENT_TYPES
    return JsonResponse(result)


@login_required
@require_POST
def element_commit_api(request):
    """把管理员勾选的候选元件写进库。"""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '请求体不是合法 JSON'})

    selections = payload.get('selections') or []
    if not selections:
        return JsonResponse({'status': 'error', 'message': '未选择任何元件'})

    stats = commit_candidates(selections, user=request.user)
    invalidate_index_cache()

    parts = [f"新建 {stats['created']} 条元件"]
    if stats['linked']:
        parts.append(f"关联 {stats['linked']} 条已有元件")
    parts.append(f"登记 {stats['occurrences']} 处载体出现位置")
    if stats['skipped']:
        parts.append(f"跳过 {stats['skipped']} 条")
    return JsonResponse({'status': 'success', 'message': '，'.join(parts), **stats})


@login_required
@require_GET
def vector_elements_api(request, vector_id):
    """某载体上已登记的元件（vector_manage 抽屉里的「本载体元件」）。"""
    occurrences = (
        VectorElementOccurrence.objects
        .filter(vector_id=vector_id)
        .select_related('element')
        .order_by('start')
    )
    return JsonResponse({'status': 'success', 'data': [
        {
            'element_id': occ.element_id,
            'name': occ.element.name,
            'element_type': occ.element.element_type,
            'element_type_display': occ.element.get_element_type_display(),
            'length': occ.element.seq_length,
            'start': occ.start, 'end': occ.end, 'strand': occ.strand,
            'label_in_vector': occ.label_in_vector,
            'risk_level': occ.element.risk_level,
            'screen_enabled': occ.element.screen_enabled,
        }
        for occ in occurrences
    ]})


@login_required
@require_POST
def element_search_api(request):
    """序列查询：库里有没有这段序列。"""
    sequence = request.POST.get('sequence', '')
    try:
        min_length = int(request.POST.get('min_length') or DEFAULT_MIN_LENGTH)
        min_identity = float(request.POST.get('min_identity') or DEFAULT_MIN_IDENTITY)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '参数格式不对'})

    result = find_element_by_sequence(sequence, min_length=min_length, min_identity=min_identity)
    if not result.get('ok'):
        return JsonResponse({'status': 'error', 'message': result.get('error', '查询失败')})
    result['status'] = 'success'
    return JsonResponse(result)


@login_required
@require_POST
def element_screen_api(request):
    """重组风险筛查：客户序列 vs（元件库 + 目标载体骨架）。"""
    sequence = request.POST.get('sequence', '')
    vector_id = request.POST.get('vector_id')
    try:
        min_length = int(request.POST.get('min_length') or DEFAULT_MIN_LENGTH)
        min_identity = float(request.POST.get('min_identity') or DEFAULT_MIN_IDENTITY)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '参数格式不对'})

    target_vector = None
    if vector_id:
        try:
            target_vector = Vector.objects.get(pk=vector_id)
        except (Vector.DoesNotExist, ValueError):
            return JsonResponse({'status': 'error', 'message': '目标载体不存在'})

    result = screen_sequence(sequence, target_vector=target_vector,
                             min_length=min_length, min_identity=min_identity)
    if not result.get('ok'):
        return JsonResponse({'status': 'error', 'message': result.get('error', '筛查失败')})
    result['status'] = 'success'
    return JsonResponse(result)


@login_required
@require_GET
def element_vector_options_api(request):
    """载体下拉数据源，两个 tab 共用，各自按标记过滤。

    筛查 tab 要的是有骨架序列的（vector_map 或图谱都能出骨架）；抽取 tab 只能用有
    GenBank 图谱的 —— 只有裸序列的载体没有 feature 标注，解析出来必然是空的，
    以前这类载体也列在抽取下拉里，点进去只会得到"无法读取图谱"。
    """
    vectors = (
        Vector.objects
        .filter(Q(vector_map__gt='') | Q(vector_file__gt='') | Q(vector_gb__gt=''))
        .annotate(element_count=Count('element_occurrences', distinct=True))
        .values('id', 'vector_name', 'vector_id', 'status', 'element_count',
                'vector_file', 'vector_gb')
        .order_by('vector_name')
    )
    return JsonResponse({'data': [{
        'id': v['id'],
        'vector_name': v['vector_name'],
        'vector_id': v['vector_id'],
        'status': v['status'],
        # 有 GenBank 图谱才谈得上抽取元件
        'parseable': bool(v['vector_file'] or v['vector_gb']),
        'element_count': v['element_count'],
    } for v in vectors]})


@login_required
@require_GET
def element_export_csv(request):
    """导出元件库 CSV。"""
    qs = VectorElement.objects.annotate(occurrence_count=Count('occurrences')).order_by('element_type', 'name')
    type_labels = dict(VectorElement.ELEMENT_TYPES)

    rows = [{
        '元件名': e.name,
        '类型': type_labels.get(e.element_type, e.element_type),
        '长度(bp)': e.seq_length,
        '出现载体数': e.occurrence_count,
        '来源载体': e.source_vector_name,
        '来源类型': e.get_source_kind_display(),
        '别名': '; '.join(e.aliases or []),
        '纳入筛查': '是' if e.screen_enabled else '否',
        '风险等级': e.get_risk_level_display(),
        '启用': '是' if e.is_active else '否',
        '备注': e.description,
        '序列': e.sequence,
    } for e in qs]

    df = pd.DataFrame(rows, columns=['元件名', '类型', '长度(bp)', '出现载体数', '来源载体',
                                     '来源类型', '别名', '纳入筛查', '风险等级', '启用', '备注', '序列'])
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f"vector_elements_{datetime.date.today():%Y%m%d}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('﻿')   # BOM，Excel 打开中文不乱码
    df.to_csv(path_or_buf=response, index=False)
    return response
