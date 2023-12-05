import json
from math import ceil

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from user_center.models import OrderInfo

def get_table_context(status=None):
    if status is None:
        orders = OrderInfo.objects
    else:
        orders = OrderInfo.objects.filter(status=status)

    cnt_all = orders.count()
    max_row = 10
    if max_row * 10 > cnt_all:
        datas = orders.order_by('order_time')
    else:
        datas = orders.order_by('order_time')[:max_row * 10]
    rows = []
    for data in datas:
        rows.append({
            'id': data.id,
            'inquiry_id': data.inquiry_id if data.inquiry_id is not None else 'null',
            "custom": data.user.username,
            "quantity": data.quantity,
            "create": data.order_time.strftime('%d/%m/%Y %H:%M:%S'),
            "modify": "",
            "export": {},
            "report": data.report_file.url if data.inquiry_id is not None else '',
            "status": data.status,
            "url": data.url,
        })
    return {
        'title': "Order Manage",
        'max_page': ceil(cnt_all / max_row),
        'max_row': 10,
        'rows': json.dumps(rows)
    }

@login_required
@require_GET
def get_rows(request):
    status = request.GET.get('status')
    if status and status.lower() == 'all'.lower():
        status = None
    return JsonResponse(data={'status': 'success', 'data':get_table_context(status)})

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
@require_GET
def change_status(request):
    row_id = request.GET.get('id')
    opr = request.GET.get('opr')
    order_info = OrderInfo.objects.get(id=row_id)
    if row_id is None or opr is None:
        return JsonResponse(data={'status': 'error', 'message': 'Invalid value'})
    if opr == 'revoke':
        pass
    elif opr == 'next':
        pass
    status = 'CREATED'
    return JsonResponse(data={'status': 'success', 'message': 'Change success', 'newVal': status})

@login_required
def order_manage(request):
    return render(request, 'super_manage/order_manage.html', get_table_context())


@login_required
def vector_manage(request):
    # cart = Cart.objects.get(user=request.user)
    # shopping_cart = cart.genes.all()
    # page_object = Pagination(request, shopping_cart)
    # context = {
    #     'shopping_cart': page_object.page_queryset,  # 分完页的数据
    #     'page_string':page_object.html(),  # 页码
    # }
    context = {
        'shopping_cart': "shopping_cart",
    }
    return render(request, 'super_manage/vector_manage.html', context)
