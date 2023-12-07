import json
import os
from math import ceil
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
import pandas as pd

from product.models import Vector
from user_center.models import OrderInfo
from user_center.views import \
    vector_download as uc_vector_download, \
    vector_delete as uc_vector_delete


def get_table_context(table_name, status=None, start=0):
    def vector_line(data):
        return {
            'id': data.id,
            'Custom': data.user.username if data.user is not None else '',
            "File": {},
            "Map": 'vector_download/{}/map'.format(data.id) if data.vector_file else '',
            "Map seq": data.vector_map,
            "Vector ID": data.vector_id,
            "iD20": data.id20,
            "iU20": data.iu20
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
@require_GET
def vector_download(request, vector_id, file_type):
    return uc_vector_download(request, vector_id, file_type, True)


@login_required
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

@require_GET
@login_required
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
def download_report(request, order_id):
    print('down report {}'.format(order_id))
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
@require_GET
def change_status(request):
    row_id = request.GET.get('id')
    opr = request.GET.get('opr')
    status = OrderInfo.objects.get(id=row_id).status
    if row_id is None or opr is None:
        return JsonResponse(data={'status': 'error', 'message': 'Invalid value'})
    status_list = ['Created', 'Synthesizing', 'Shipped', 'Completed']
    status = status[0].upper() + status[1:].lower()
    if status == 'Pending':
        status = 'Created'
    if status not in status_list:
        return JsonResponse(data={'status': 'error', 'message': 'Backstage error'})
    index = status_list.index(status)
    if opr == 'revoke':
        if index == 0:
            return JsonResponse(data={'status': 'failed', 'message': "Can't revoke the {} status".format(status)})
        OrderInfo.objects.filter(id=row_id).update(status=status_list[index - 1])
    elif opr == 'next':
        if index == len(status_list) - 1:
            return JsonResponse(data={'status': 'failed', 'message': "Can't next the {} status".format(status)})
        OrderInfo.objects.filter(id=row_id).update(status=status_list[index + 1])
    return JsonResponse(data={
        'status': 'success',
        'message': 'Change success',
        'newVal': OrderInfo.objects.get(id=row_id).status
    })


@login_required
def order_manage(request):
    return render(request, 'super_manage/order_manage.html', get_table_context("order"))


@login_required
def vector_manage(request):
    return render(request, 'super_manage/vector_manage.html', get_table_context("vector"))


@login_required
def export_order_to_csv(request, order_id):
    # Retrieve the order
    order = OrderInfo.objects.get(id=order_id)

    # Create a list of dictionaries containing gene information
    gene_info_list = [
        {
            'GeneName': gene_info.gene_name,
            'Seq5NC': gene_info.vector.NC5,
            'SeqAA': gene_info.saved_seq,
            'Seq3NC': gene_info.vector.NC3,
            'ForbiddenSeqs': gene_info.forbid_seq,
            'VectorID': gene_info.vector.vector_id,
            'Species': gene_info.species.species_name if gene_info.species else None,
        }
        for gene_info in order.gene_infos.all()
    ]

    # Create a DataFrame from the list
    df = pd.DataFrame(gene_info_list)
    # Convert datetime columns to timezone-unaware format
    # df['create_date'] = df['create_date'].dt.tz_localize(None)
    # Create a new column 'order_type' based on the condition
    max_sequence_length = 0
    if df.get('SeqAA') is not None:
        max_sequence_length += df['SeqAA'].str.len().max()
    if df.get('Seq5NC') is not None:
        max_sequence_length += df['Seq5NC'].str.len().max()
    if df.get('Seq3NC') is not None:
        max_sequence_length += df['Seq3NC'].str.len().max()

    order_type = 2 if max_sequence_length > 650 else 1

    # Prepare response with CSV content
    # response = HttpResponse(content_type='text/csv')
    # response['Content-Disposition'] = f'attachment; filename="{order.inquiry_id}-{order_type}-{request.user}-RootPath_Gene_Library_Order_Infomation.csv"'
    # df.to_excel(path_or_buf=response, index=False)
    
    # Prepare response with Excel content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{order.inquiry_id}-{order_type}-{request.user}-RootPath_Gene_Library_Order_Information.xlsx"'
    df.to_excel(excel_writer=response, index=False, engine='openpyxl')

    return response
