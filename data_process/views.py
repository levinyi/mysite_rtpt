from django.http import JsonResponse, Http404
from django.shortcuts import render

# Create your views here.
from django.views.decorators.http import require_GET

from user_center.models import OrderInfo

TOKEN = '65f4c2c7143d4a1a90050f193859dc4b'


@require_GET
def request_order(request):
    # 暂时先随便写一个token作为简单的验证，由于Https自带加密，不需要担心传输过程中信息泄露
    # Token是防止无权限的人访问该页面，窃取数据
    if request.GET.get('token', default=None) is None or \
            request.GET['token'] != TOKEN:
        raise  Http404('Page Not Found!')

    created_orders = OrderInfo.objects.filter(status='Created')
    result_data = {}
    # 遍历每个Order，获取关联的GeneInfo信息
    for order in created_orders:
        order_data = []

        # 遍历每个关联的GeneInfo
        for gene_info in order.gene_infos.all():
            v = gene_info.vector
            if not v:
                continue
            v_info_data = {
                'vector_id': v.id,
                'vector_name': v.vector_name,
                'vector_map': v.vector_map,
                'NC5': v.NC5,
                'NC3': v.NC3,
                'iu20': v.iu20,
                'id20': v.id20
            }

            order_data.append(v_info_data)
        result_data[order.id] = order_data
    return JsonResponse(result_data, json_dumps_params={'ensure_ascii': False})
