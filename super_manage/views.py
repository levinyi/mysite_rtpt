import json
import os
from math import ceil
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from account.models import UserProfile
from product.models import Vector
from user_center.models import OrderInfo
from user_center.views import \
    vector_download as uc_vector_download, \
    vector_delete as uc_vector_delete

from account.views import is_secondary_admin
from django.http import HttpResponseForbidden
from user_center.utils.pagination import Pagination


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
is_secondary_admin_required = custom_user_passes_test(is_secondary_admin)


def get_table_context(table_name, status=None, start=0):
    """
    这里修改给前端Table的数据
    table_name:表名
    status：状态，即表上面Tab的
    start:开始的页面，目前功能不完善
    """
    def vector_line(data):
        # print(data.vector_map)
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
@is_secondary_admin_required
@require_GET
def vector_download(request, vector_id, file_type):
    return uc_vector_download(request, vector_id, file_type, True)


@login_required
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
def download_report(request, order_id):
    # print('down report {}'.format(order_id))
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
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
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
@is_secondary_admin_required
def order_manage(request):
    return render(request, 'super_manage/order_manage.html', get_table_context("order"))


@login_required
@is_secondary_admin_required
def vector_manage_zxl(request):
    return render(request, 'super_manage/vector_manage.html', get_table_context("vector"))

@login_required
@is_secondary_admin_required
def vector_manage(request):
    '''list vector'''
    company_vector_list = Vector.objects.filter(user=None).order_by('-create_date')
    company_page_object = Pagination(request, company_vector_list, page_size=10)

    custom_vector_list = Vector.objects.filter(user__isnull=False).order_by('-create_date')
    custom_page_object = Pagination(request, custom_vector_list, page_size=10)

    context = {
        'company_vector_list': company_page_object.page_queryset,  # 分完页的数据
        'company_page_string': company_page_object.html(),  # 页码
        'custom_vector_list': custom_page_object.page_queryset,  # 分完页的数据
        'custom_page_string': custom_page_object.html(),  # 页码
    }
    return render(request, 'super_manage/vector_manage_dsy.html', context)


@login_required
@is_secondary_admin_required
def vector_delete(request):
    if request.method == 'POST':
        vector_id = request.POST.get('gene_id')
        vector = Vector.objects.get(id=vector_id)
        print(f"{request.user} delete this {vector_id} {vector.vector_id} {vector.vector_name}")
    
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
@is_secondary_admin_required
@csrf_exempt
def vector_upload_file(request):
    '''for customer's vector file, vector_png and vector_gb files.'''
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        vector_id = request.POST.get('vectorId')
        print(vector_id)
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
                if vector.vector_png:
                    file_path = vector.vector_png.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                vector.vector_png = uploaded_file
            elif file_type == 'vector_gb':
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


def vector_edit_item(request):
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        new_status = request.POST.get('new_status')
        print(f"vector_id: {vector_id}, new_status: {new_status}")
        try:
            vector = Vector.objects.get(id=vector_id)
            print(f"vector: {vector}")
            vector.status = new_status
            vector.save()
            return JsonResponse({'status': 'success'})
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Vector not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@is_secondary_admin_required
def vector_add_item(request):
    '''can edit any item in vector model, eg. 'status','''
    if request.method == 'POST':
        csv_file = request.FILES.get('csvFile')
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("File is not CSV type", status=400)

        # 使用 Pandas 读取 CSV 文件
        try:
            df = pd.read_csv(csv_file)

            # 对于 DataFrame 中的每一行，创建一个模型实例并保存
            for _, row in df.iterrows():
                model_instance = Vector(**row.to_dict())
                model_instance.save()

            return HttpResponse("CSV file has been imported", status=200)

        except Exception as e:
            # 处理异常
            return HttpResponse(str(e), status=500)

    # 如果不是 POST 请求，返回错误
    return HttpResponse("Invalid request", status=400)


@login_required
@is_secondary_admin_required
def user_manage(request): 
    user_list = UserProfile.objects.all().order_by('-register_time')
    page_object = Pagination(request, user_list, page_size=15)
    context = {
        'user_list': page_object.page_queryset,  # 分完页的数据
        'page_string':page_object.html(),  # 页码
    }
    return render(request, 'super_manage/user_manage.html', context)
