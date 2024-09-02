import json

from django.http import JsonResponse, Http404
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import pandas as pd

from notice.views import send_email
from user_center.models import GeneOptimization
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

    # if request.GET.get('token', default=None) is None or not check(request.GET['token']):
    #     raise Http404('Page Not Found!')

    genes = GeneOptimization.objects.filter(status='pending')
    print(genes)
    result_data = {}

    # 处理成dataframe
    for gene in genes.all():
        result_data[gene.id] = {
            'GeneID': gene.id,
            'GeneName': gene.gene.gene_name,
            'VectorID': gene.vector.vector_id,
            'VectorName': gene.vector.vector_name,
            'SpeciesName': gene.species.species_name,
            'GeneSeq': gene.gene.saved_seq,
            'Vector5NC': gene.vector.NC5,
            'Vector3NC': gene.vector.NC3,
        }
    print(result_data)
    result_data_df = pd.DataFrame(result_data).T
    print(result_data_df)
    return JsonResponse(result_data, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_POST
def upload_genes(request):
    if request.headers.get('token', default=None) is None or not check(request.headers['token']):
        raise Http404('Page Not Found!')
    data_list = json.loads(request.body.decode('utf-8'))
    obj = GeneOptimization.objects
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
