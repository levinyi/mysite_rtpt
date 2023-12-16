import json

from django.http import JsonResponse, Http404
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from notice.views import send_email
from user_center.models import GeneInfo
from decouple import config

TOKEN = config('TOKEN')


def check(token):
    return token == TOKEN


@require_GET
def request_genes(request):
    # 暂时先随便写一个token作为简单的验证，由于Https自带加密，不需要担心传输过程中信息泄露
    #
    # Token是防止无权限的人访问该页面，窃取数据
    def get_str_len(ss):
        return len(ss) if ss else 0

    if request.GET.get('token', default=None) is None or not check(request.GET['token']):
        raise Http404('Page Not Found!')

    genes = GeneInfo.objects.filter(status='optimizing')
    result_data = {}

    for gene in genes.all():
        v = gene.vector
        if gene.user.id not in result_data:
            result_data[gene.user.id] = []
        length = \
            get_str_len(gene.i5nc) + get_str_len(v.NC5) + get_str_len(gene.original_seq) * 3 + \
            get_str_len(gene.i3nc) + get_str_len(v.NC3)

        result_data[gene.user.id].append({
            'GeneName': v.vector_name,
            'Seq5NC': v.NC5 + gene.i5nc,
            'SeqAA': gene.original_seq,
            'Seq3NC': v.NC3 + gene.i3nc,
            'VectorID': v.vector_id,
            'Species': gene.species.species_name if gene.species else None,
            'ForbiddenSeqs': gene.forbid_seq,
            'length': length
        })
    # print(result_data)
    return JsonResponse(result_data, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_POST
def upload_genes(request):
    if request.headers.get('token', default=None) is None or not check(request.headers['token']):
        raise Http404('Page Not Found!')
    data_list = json.loads(request.body.decode('utf-8'))
    obj = GeneInfo.objects
    for key, value in data_list.items():
        user_id = int(value['user_id'])
        datas = value['datas']
        for v in datas:
            obj.filter(vector__vector_id=v['VectorID']) \
                .update(status='optimized', saved_seq=v['FullSeqREAL'])
        # 发送消息的内容，统一在Notice view中设置
        send_email(user_id, purpose='notice_synthesized')
    # raise Http404('Page Not Found!')
    return JsonResponse({'status': 'success'}, json_dumps_params={'ensure_ascii': False})
