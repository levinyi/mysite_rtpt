import itertools
import json, re, os
import tempfile
import zipfile
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from product.models import GeneSynEnzymeCutSite, Species, Vector
from tools.scripts.ParsingGenBank import addFeaturesToGeneBank
from .models import Cart, GeneInfo, OrderInfo
from .utils.render_to_pdf import render_to_pdf
from urllib.parse import quote

# Create your views here.
@login_required(login_url='/account/login/')
def dashboard(request):
    # 如果没有shopping cart，创建一个
    production_order = OrderInfo.objects.filter(user=request.user, status='Created')
    shipping_order = OrderInfo.objects.filter(user=request.user, status='Shipping')
    shopping_cart = Cart.genes.through.objects.filter(cart__user=request.user)
    return render(request, 'user_center/dashboard.html', {
            'order_number_in_production': len(production_order),
            'order_number_in_shipment': len(shipping_order),
            'gene_number_in_cart': len(shopping_cart),
            })

# Step 1 create an order.
@login_required
def order_create_old(request):
    '''创建订单页'''
    # 这里只能是GET请求，因为POST请求是提交订单
    if request.method == 'POST':
        # 这里的逻辑是创建订单
        data = json.loads(request.body.decode('utf-8'))
        vector_id = data.get("vectorId")
        gene_table = data.get("genetable")
        if not gene_table:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})

        try:
            vector = Vector.objects.get(id=vector_id)
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid vector ID'})

        iu20 = vector.iu20
        id20 = vector.id20

        cart, created = Cart.objects.get_or_create(user=request.user)
        response_message = ""

        new_gene_ids_for_session = []
        for row in gene_table:
            if not any(cell is not None for cell in row):
                continue

            gene_name = row[0]
            original_seq = row[1]
            original_seq = original_seq.replace("\n","").replace("\r","").replace(" ","") # 去掉换行符和空格
            species = None
            forbid_seq = None
            combined_seq = original_seq
            saved_seq = original_seq
            gc_content = None
            forbidden_check_list = None
            contained_forbidden_list = None
            status = 'saved'
            i5nc = None
            i3nc = None

            # 判断是否为AA序列（通过列数判断）
            if len(row) > 2:
                try:
                    species_name = row[2]
                    species = Species.objects.get(species_name=species_name)
                except Species.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Species {species_name} not found'})

                forbid_seq = row[3].replace(" ", "").replace(",", ";") if row[3] is not None else None
                i5nc = row[4] or ''
                i3nc = row[5] or ''
                status = 'optimizing'
                forbidden_check_list = forbid_seq
                response_message = 'AA sequence submitted for codon optimization. Please wait 10-20 minutes to check the result.'
            else:
                # print("Processing NT sequence")
                combined_seq = f'{iu20.lower()}{original_seq}{id20.lower()}'
                tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(combined_seq, forbid_seq)
                if seq_status in ['Protein', 'Invalid Protein']:
                    return JsonResponse({'status': 'error', 'message': f'{seq_status} sequence is not allowed.'})
                saved_seq = tagged_seq
                status = seq_status

            # 创建或更新GeneInfo对象
            this_gene = GeneInfo.objects.create(
                user=request.user,
                gene_name=gene_name,
                original_seq = tagged_seq,  # original_seq, 修改成tagged_seq试一下效果
                vector = vector,
                species = species,
                status = status,
                forbid_seq = forbid_seq,
                combined_seq = combined_seq,
                i5nc = i5nc,
                i3nc = i3nc,

                saved_seq = saved_seq,
                gc_content = gc_content,
                forbidden_check_list = forbidden_check_list,
                contained_forbidden_list = contained_forbidden_list,
            )
            cart.genes.add(this_gene)
            new_gene_ids_for_session.append(this_gene.id)

        request.session['new_gene_ids'] = new_gene_ids_for_session
        if response_message:
            return JsonResponse({'status': 'info', 'message': response_message})
        else:
            return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
    else:
        company_vectors = Vector.objects.filter(user=None)
        species_list = Species.objects.all()
        # 假设 species_list 是您的物种模型列表
        species_names = [species.species_name for species in species_list]

        # 然后将这个列表转换为 JSON
        species_names_json = json.dumps(species_names)
        customer_vectors = Vector.objects.filter(user=request.user, status="ReadyToUse")
        return render(request, 'user_center/manage_order_create.html', {'customer_vectors': customer_vectors, 'company_vectors': company_vectors, 'species_names_json': species_names_json})

@login_required
def order_create(request):
    '''创建订单页'''
    # 这里只能是GET请求，因为POST请求是提交订单
    if request.method == 'POST':
        # 这里的逻辑是创建订单
        data = json.loads(request.body.decode('utf-8'))
        vector_id = data.get("vectorId")
        gene_table = data.get("genetable")
        if not gene_table:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})
        ##############################################
        # deal with Vector 
        try:
            vector = Vector.objects.get(id=vector_id)
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid vector ID'})
        ###############################################
        # create a cart record.
        cart, created = Cart.objects.get_or_create(user=request.user)
        response_message = ""

        new_gene_ids_for_session = []  # 用于存储新创建的基因的id, 用于session

        for row in gene_table:
            if not any(cell is not None for cell in row):
                # "Empty row"
                # 去掉多余的空行
                continue

            gene_name = row[0]
            original_seq = row[1]
            original_seq = original_seq.replace("\n","").replace("\r","").replace(" ","") # 去掉换行符和空格
            species = None
            user_forbidden_seq = None
            combined_seq = original_seq
            saved_seq = original_seq
            gc_content = None
            forbidden_check_list = None
            contained_forbidden_list = None
            status = 'saved'
            i5nc = None
            i3nc = None
            # 初始化变量，防止未赋值报错
            original_gc_content = None
            original_highlights_positions = None
            # 判断是否为AA序列（通过列数判断）
            if len(row) > 2:
                # ("Processing AA sequence")
                try:
                    species_name = row[2]
                    species = Species.objects.get(species_name=species_name)
                except Species.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Species {species_name} not found'})

                user_forbidden_seq = row[3].replace(" ", "").replace(",", ";") if row[3] is not None else None
                i5nc = row[4] or ''
                i3nc = row[5] or ''
                status = 'optimizing'
                forbidden_check_list = user_forbidden_seq
                response_message = 'AA sequence submitted for codon optimization. Please wait 10-20 minutes to check the result.'
            else:
                # ("Processing NT sequence")
                combined_seq = f'{vector.iu20.lower()}{original_seq}{vector.id20.lower()}'
                tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, original_gc_content, original_highlights_positions = process_sequence_get_highlight_position(combined_seq, user_forbidden_seq)
                # print("seq_status: ", seq_status, "forbidden_check_list: ", forbidden_check_list, "contained_forbidden_list: ", contained_forbidden_list, "original_gc_content: ", original_gc_content, "original_highlights_positions: ", original_highlights_positions)
                if seq_status in ['Protein', 'Invalid Protein']:
                    return JsonResponse({'status': 'error', 'message': f'{seq_status} sequence is not allowed.'})
                saved_seq = tagged_seq
                status = seq_status

            # 创建或更新GeneInfo对象
            this_gene = GeneInfo.objects.create(
                user=request.user,
                gene_name=gene_name,
                original_seq = combined_seq,   # test
                vector = vector,
                species = species,
                status = status,
                forbid_seq = user_forbidden_seq,
                combined_seq = combined_seq,
                i5nc = i5nc,
                i3nc = i3nc,

                saved_seq = saved_seq,
                forbidden_check_list = forbidden_check_list,
                contained_forbidden_list = contained_forbidden_list,

                original_gc_content = original_gc_content,
                modified_gc_content = original_gc_content,
                original_highlights = original_highlights_positions,
                modified_highlights = original_highlights_positions,
            )
            cart.genes.add(this_gene)
            new_gene_ids_for_session.append(this_gene.id)

        request.session['new_gene_ids'] = new_gene_ids_for_session
        if response_message:
            return JsonResponse({'status': 'info', 'message': response_message})
        else:
            return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
    else:
        company_vectors = Vector.objects.filter(user=None)
        species_list = Species.objects.all()
        # 假设 species_list 是您的物种模型列表
        species_names = [species.species_name for species in species_list]

        # 然后将这个列表转换为 JSON, 用于前端Handsontable中展示物种列表
        species_names_json = json.dumps(species_names)
        customer_vectors = Vector.objects.filter(user=request.user, status="ReadyToUse")
        return render(request, 'user_center/manage_order_create.html', {'customer_vectors': customer_vectors, 'company_vectors': company_vectors, 'species_names_json': species_names_json})


# checked
def submit_notification(request):
    ''' when user submit AA sequence. this function will be called.'''
    if request.method == 'GET':
        return render(request, 'user_center/aa_sequence_submit_success.html')
    else:
        return render(request, 'user_center/aa_sequence_submit_success.html')

@login_required
def gene_detail_old(request):
    ''' when user click the "submit & analysis" button, this function will be called.'''
    # 从session中获取新创建的基因
    new_gene_ids = request.session.get('new_gene_ids', [])

    if not new_gene_ids:
        gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')

    gene_list = GeneInfo.objects.filter(user=request.user, id__in=new_gene_ids)

    species_list = Species.objects.all()
    species_names = sorted([species.species_name for species in species_list])
    return render(request, 'user_center/gene_detail_old.html', {'gene_list': gene_list, 'species_names': species_names})

@login_required
def gene_detail(request):
    ''' when user click the "submit & analysis" button, this function will be called.'''
    # 从session中获取新创建的基因
    new_gene_ids = request.session.get('new_gene_ids', [])

    if not new_gene_ids:
        # 如果没有新创建的基因ID，从数据库中筛选符合条件的基因
        gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')
    else:
        # 如果有新创建的基因ID，从数据库中获取这些基因
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=new_gene_ids)

    # 获取所有物种的名称
    species_list = Species.objects.all()
    species_names = sorted([species.species_name for species in species_list])
    
    return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})

@login_required
def bulk_view_gene_detail(request):
    ''' 批量查看基因详情 '''
    try:
        gene_ids = request.POST.getlist('gene_ids')
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)
        
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)
        species_list = Species.objects.all()
        species_names = sorted([species.species_name for species in species_list])
        return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def gene_data_api(request):
    '''返回基因数据的json格式'''
    gene_ids = request.session.get('new_gene_ids', [])
    if not gene_ids:
        gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')
    else:
        gene_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)

    data = gene_list.values('id', 'gene_name', 'original_seq', 'status', 'forbid_seq', 'vector__vector_id','modified_gc_content')
    return JsonResponse({'data': list(data)}, safe=False)
        

@login_required
def save_species(request):
    data = json.loads(request.body.decode('utf-8'))
    species = data['species']
    gene_id = data['gene_id']
    this_gene = GeneInfo.objects.get(user=request.user, id=gene_id)
    this_gene.species = Species.objects.get(species_name=species)
    this_gene.save()
    return JsonResponse({'status': 'success', 'message': 'Species saved successfully'})

@login_required
def gene_edit(request, gene_id):
    ''' when user click the "Edit" button, this function will be called.'''
    if request.method == 'POST':
        gene_object = GeneInfo.objects.get(user=request.user, id=gene_id)
        gene_object.status = "validated"
        gene_object.save()
        return JsonResponse({'status': 'success', 'message': 'Gene saved successfully'})
    else:
        gene_object = GeneInfo.objects.get(user=request.user, id=gene_id)
        # 将单个对象封装成列表
        gene_list = [gene_object]
        species_list = Species.objects.all()
        species_names = sorted([species.species_name for species in species_list])
        return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list, 'species_names': species_names})

@login_required
def protein_edit(request, gene_id):
    gene_list = GeneInfo.objects.filter(user=request.user, status__in=['optimizing', 'optimized', 'failed'])
    return render(request, 'user_center/protein_detail.html', {'gene_list': gene_list})


def handle_gene_saving(gene_object, edited_seq):
    """
    用于基因序列验证和保存的统一函数
    """
    original_seq = gene_object.original_seq
    if original_seq == edited_seq:
        if gene_object.status == 'validated':
            gene_object.status = 'saved'
            gene_object.save()
            return True
        else:
            return False

    tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, \
        modified_gc_content, modified_highlights = process_sequence_get_highlight_position(edited_seq, gene_object.forbid_seq)
    
    gene_object.saved_seq = tagged_seq
    gene_object.forbidden_check_list = forbidden_check_list
    gene_object.contained_forbidden_list = contained_forbidden_list
    gene_object.combined_seq = edited_seq
    gene_object.modified_highlights = modified_highlights
    gene_object.modified_gc_content = modified_gc_content

    if seq_status == 'validated':
        gene_object.status = 'saved'
        gene_object.save()
        return True
    else:
        gene_object.status = seq_status
        gene_object.save()
        return False
    
@login_required
def gene_validation(request):
    ''' when user click the "Re-analyze" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        edited_seq = data.get("sequence") # 换个变量名，好区分
        gene_id = data.get("gene_id")  # 应该换成gene_id，

        gene_object = GeneInfo.objects.get(user=user, id=gene_id)
        combined_seq = gene_object.combined_seq     # 不带格式有小写 {iu20}.lower() + seq + {id20}.lower(), 可以直接比较

        if combined_seq == edited_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})

        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, \
            modified_gc_content, modified_highlights = process_sequence_get_highlight_position(edited_seq, gene_object.forbid_seq)

        if seq_status in ['Protein', 'Invalid Protein']:
            return JsonResponse({'status': 'error', 'message': 'Squence is not allowed. Your sequence may has '+ seq_status + ' sequence.'})
        gene_object.status = seq_status
        gene_object.saved_seq = tagged_seq
        gene_object.forbidden_check_list = forbidden_check_list
        gene_object.contained_forbidden_list = contained_forbidden_list
        gene_object.combined_seq = edited_seq
        gene_object.modified_highlights = modified_highlights
        gene_object.modified_gc_content = modified_gc_content
        gene_object.save()
        return JsonResponse({'status': 'success', 'message': 'Validation process finished', 'new_seq': tagged_seq, 'seq_status': seq_status})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def validation_save(request, id):
    ''' when user click the "Save" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        edited_seq = data.get("sequence")
        gene_object = GeneInfo.objects.get(user=user, id=id)

        if handle_gene_saving(gene_object, edited_seq):
            return JsonResponse({'status': 'success', 'message': 'Gene saved successfully', 'new_seq': gene_object.saved_seq})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please check your sequence and analysis first.'})
    except GeneInfo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Gene not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def bulk_optimization(request):
    return HttpResponse("Our team is still working on this feature. Please come back later.")


###################### 以下是shopping cart 管理的函数 ############################
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    shopping_cart = cart.genes.all()

    grouped_shopping_cart = []
    for key, group in itertools.groupby(shopping_cart, key=lambda x: x.create_date.date()):
        grouped_shopping_cart.append({
            'date': key,
            'genes': list(group)
        })
    context = {
        'grouped_shopping_cart': grouped_shopping_cart,
    }
    return render(request, 'user_center/shoppingCart_view.html', context)

# checked
@login_required
def gene_delete(request):
    '''从shopping cart中删除gene'''
    if request.method == 'POST':
        gene_ids = request.POST.getlist('gene_ids[]')  # Use getlist to retrieve multiple values
        if gene_ids:
            # Batch deletion
            GeneInfo.objects.filter(user=request.user, id__in=gene_ids).delete()
            return JsonResponse({'status': 'success', 'message': 'Genes deleted successfully'})
        else:
            # Single deletion
            gene_id = request.POST.get('gene_id')
            gene = GeneInfo.objects.get(user=request.user, id=gene_id)
            gene.delete()
            return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_order_create.html')


@login_required
def cart_genbank_download(request, gene_id):
    '''下载购物车中的基因的genbank文件'''
    gene = GeneInfo.objects.get(user=request.user, id=gene_id)
    sequence = re.sub(r'<[^>]*>', '', gene.saved_seq)
    # 删除序列前后的小写字母
    sequence = re.sub(r'^[a-z]+|[a-z]+$', '', sequence)

    vector = gene.vector
    if vector.vector_gb:
        vector_genbank_file_path = vector.vector_gb.path  # Get the file path
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=False) as temp_file:
            # addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name)  # old
            addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name, 'iU20', 'iD20', gene)
            
            temp_file.seek(0)
            response = HttpResponse(temp_file.read(), content_type='application/genbank')
            response['Content-Disposition'] = f'attachment; filename="RootPath-{vector.vector_name}-{gene.gene_name}-{gene.status}.gb"'
            return response
    else:
        return HttpResponse("No vector genbank file found")

@require_POST
@login_required
def bulk_download_genbank(request):
    '''批量下载购物车中的基因的genbank文件'''
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        temp_zip = tempfile.NamedTemporaryFile(delete=False)
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            for gene_id in gene_ids:
                try:
                    gene = GeneInfo.objects.get(user=request.user, id=gene_id)
                    sequence = re.sub(r'<[^>]*>', '', gene.saved_seq)
                    sequence = re.sub(r'^[a-z]+|[a-z]+$', '', sequence)
                    vector = gene.vector
                    if vector.vector_gb:
                        vector_genbank_file_path = vector.vector_gb.path
                        with tempfile.NamedTemporaryFile(mode='w+', suffix='.gb', delete=False) as temp_file:
                            # addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name)
                            addFeaturesToGeneBank(vector_genbank_file_path, sequence, temp_file.name, 'iU20', 'iD20', gene)
                            temp_file.seek(0)
                            genbank_content = temp_file.read()
                            genbank_filename = f"RootPath-{vector.vector_name}-{gene.gene_name}-{gene.status}.gb"
                            zf.writestr(genbank_filename, genbank_content)
                    else:
                        zf.writestr(f"Error-{gene_id}.txt", "No vector GenBank file found")
                except GeneInfo.DoesNotExist:
                    zf.writestr(f"Error-{gene_id}.txt", "Gene not found")

        temp_zip.seek(0)
        response = HttpResponse(temp_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="RootPath-Online-Submission.zip"'
        temp_zip.close()
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def bulk_download_geneinfo_excel(request):
    '''批量下载购物车中的基因信息到Excel文件'''
    try:
        data = json.loads(request.body)
        gene_ids = data.get('gene_ids', [])
        if not gene_ids:
            return JsonResponse({"error": "No genes selected"}, status=400)

        gene_info_list = GeneInfo.objects.filter(user=request.user, id__in=gene_ids)
        gene_info_list = gene_info_list.values(
            'gene_name', 'species__species_name', 'vector__vector_name', 'vector__vector_id', 
            'i5nc', 'i3nc', 'forbid_seq', 'original_seq','original_gc_content','saved_seq',
            'modified_gc_content','status'
        )

        df = pd.DataFrame(gene_info_list)
        # 重新修改一下列名
        df.columns = ['GeneName', 'Species', 'VectorName', 'VectorID', 'i5nc', 'i3nc', 'ForbiddenSeqs', 
                      'OriginalSeq', 'OriginalGCContent', 'ModifiedSeq', 'ModifiedGCContent', 'Status']

        # Prepare response with Excel content
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="RootPath-Online-Submission-Gene-Information-{request.user}.xlsx"'
        df.to_excel(excel_writer=response, index=False, engine='openpyxl')
        return response
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@require_POST
def checkout(request):
    # 获取所有选中的gene_ids, 提交订单。
    gene_ids = request.POST.getlist('gene_ids')
    if not gene_ids:
        return JsonResponse({'status': 'error', 'message': 'No gene selected'})

    # 为选中的gene创建一个订单
    order = OrderInfo.objects.create(user=request.user)
    # 获取所有选中的gene对象
    genes = get_list_or_404(GeneInfo, user=request.user, id__in=gene_ids)

    # 将gene添加到订单中
    order.gene_infos.add(*genes)
    order.status = 'Created'
    time_strf = order.order_time.strftime('%Y%m%d')[2:]
    order.inquiry_id = f'IQ{time_strf}{order.id:02d}'
    order.save()

    # 将选中的gene从购物车中删除
    cart = Cart.objects.get(user=request.user)
    cart.genes.remove(*genes)
    cart.save()

    # 不删除GeneInfo对象，改变status为submitted
    for gene_id in gene_ids:
        GeneInfo.objects.filter(user=request.user, id=gene_id).update(status='submitted')

    # 重定向到订单详情页面
    return JsonResponse({'status': 'success', 'message': 'Order created successfully', 'redirect_url': f'/user_center/manage_order/'})

@login_required
def view_order_detail(request, order_id):
    # retrieve the order
    order = OrderInfo.objects.get(id=order_id)
    return render(request, 'user_center/order_detail_view.html', {'order': order})

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

@login_required
def export_order_to_csv(request, order_id):
    # Retrieve the order with optimized query
    order = OrderInfo.objects.get(id=order_id)

    # Create a list of dictionaries containing gene information
    gene_info_list = [
        {
            'GeneName': gene_info.gene_name,
            'SeqAA': get_seq_aa(gene_info.combined_seq),
            'Species': gene_info.species.species_name if gene_info.species else None,
            'ForbiddenSeqs': gene_info.forbid_seq,
            'VectorID': gene_info.vector.vector_id if gene_info.vector else None,
            'VectorName': gene_info.vector.vector_name,
            'Seq5NC': gene_info.vector.NC5 + (gene_info.i5nc if gene_info.i5nc is not None else ''),
            'Seq3NC': (gene_info.i3nc if gene_info.i3nc is not None else '') + gene_info.vector.NC3,
            'i5nc': gene_info.i5nc,
            'i3nc': gene_info.i3nc,
            'InquiryID': order.inquiry_id,
        }
        for gene_info in order.gene_infos.all()
    ]

    # Create a DataFrame from the list
    df = pd.DataFrame(gene_info_list)

    # Prepare response with Excel content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{order.inquiry_id}-{order.user}-RootPath_Gene_Library_Order_Information.xlsx"'
    df.to_excel(excel_writer=response, index=False, engine='openpyxl')

    return response

@login_required
def manage_order(request):
    order_list = OrderInfo.objects.filter(user=request.user)
    return render(request, 'user_center/order_view.html', {'order_list': order_list})

@login_required
def order_delete(request):
    '''删除订单
        只有status为Cancelled的订单才能被删除!
    '''
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = OrderInfo.objects.get(id=order_id)
        if order.status == 'Cancelled':
            order.delete()
            return JsonResponse({'status': 'success', 'message': 'Order deleted successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Only cancelled order can be deleted'})
    else:
        return render(request, 'user_center/order_view.html')
         

def check_forbiden_seq(seq, seq_length, customer_forbidden_list=None):
    '''根据序列长度检查正义和反义链'''
    seq = seq.upper().replace(" ", "")

    forbidden_check_list = []
    forbidden_list_objects = GeneSynEnzymeCutSite.objects.all()
    for enzyme in forbidden_list_objects:
        enzyme_name = enzyme.enzyme_name
        enzyme_seq = enzyme.enzyme_seq
        enzyme_scope = enzyme.usescope
        start,end = enzyme_scope.split("-")
        start = int(start)
        end = int(end)

        if start <= seq_length <= end:
            forbidden_check_list.append(enzyme_seq)
    ###############################
    if customer_forbidden_list and isinstance(customer_forbidden_list, str):
        formated_list = re.split(r'[;,]', customer_forbidden_list)
        forbidden_check_list.extend(formated_list)

    contained_forbidden_list = [forbiden_seq for forbiden_seq in forbidden_check_list if forbiden_seq in seq]

    # find start and end positions of contained forbidden sequences
    positions = []
    for forbidden in contained_forbidden_list:
        start_positions = [match.start() for match in re.finditer(forbidden, seq)]
        end_poitions = [start + len(forbidden) for start in start_positions]
        positions.extend(list(zip(start_positions, end_poitions)))
    positions = merge_overlapping_positions(positions)
    return contained_forbidden_list, forbidden_check_list, positions

def find_sequence_positions(sequence, pattern):
    positions = []
    for match in re.finditer(pattern, sequence):
        start = match.start()
        end = match.end()
        positions.append((start, end))
    return positions

def merge_overlapping_positions(all_positions):
    '''合并所有重叠的区间'''
    if not all_positions:
        return []

    all_positions.sort(key=lambda x: x[0])
    merged_positions = [all_positions[0]]

    for current in all_positions[1:]:
        previous = merged_positions[-1]

        if current[0] <= previous[1]:
            merged = (previous[0], max(previous[1], current[1]))
            merged_positions[-1] = merged
        else:
            merged_positions.append(current)

    return merged_positions

def check_S8W8G6_sequence(sequence):
    '''consecutive NTs
    如果含有 S8 W8 G6结构的需要标注成Warning
    S8表示：含有8个连续的G或C e.g. GCGGCCGG,
    W8表示：含有8个连续的A或T e.g. ATATATAT,
    G6表示：含有6个连续的G，e.g. GGGGGG'''

    # Check for S8 (8 consecutive G or C) using regular expression
    s8_positions = find_sequence_positions(sequence, r'[GC]{8,}')

    # Check for W8 (8 consecutive A or T) using regular expression
    w8_positions = find_sequence_positions(sequence, r'[AT]{8,}')

    # Check for G6 (6 consecutive G) using regular expression
    g6_positions = find_sequence_positions(sequence, r'G{6,}')

    all_positions = s8_positions + w8_positions + g6_positions
    # 对所有的区间取并集
    all_positions = merge_overlapping_positions(all_positions)

    return all_positions

def calculate_gc_content(sequence):
    sequence = sequence.upper().replace(" ", "")
    gc_count = sequence.count('G') + sequence.count('C')
    gc_content = (gc_count / len(sequence)) * 100
    return gc_content

def check_regional_gc_content(sequence, window_size=20, threshold_low=20, threshold_high=80):
    positions = []
    for i in range(len(sequence) - window_size + 1):
        window = sequence[i:i + window_size]
        gc_content = calculate_gc_content(window)
        if gc_content <= threshold_low or gc_content >= threshold_high:
            start = i
            end = i + window_size
            positions.append((start, end))
    positions = merge_overlapping_positions(positions)

    return positions

def check_sequence(seq):
    '''检查序列GC含量
        overall GC content (only for NT submission)
            30% < Overall < 70% --> Pass 
            20% < Overall =< 30% OR 70% <= Overall < 80% --> Warning
            Overall <= 20% OR >= 80% --> Fail
        regional GC content (only for NT submission)
            20% < Regional < 80% --> Pass
            10% < Regional =< 20% OR 80% <= Regional < 90% --> Warning
            Regional <= 10% OR >= 90% --> Fail
        consecutive NTs
            S8W8G6 --> Warning
    '''
    seq = seq.upper().replace(" ", "")
    # check regional GC content
    regional_GC_positions = check_regional_gc_content(seq)
    # check consecutive NTs
    consecutive_NT_positions = check_S8W8G6_sequence(seq)

    all_positions = regional_GC_positions + consecutive_NT_positions
    return all_positions

def identify_sequence(seq):
    if not isinstance(seq, str):
        return "Invalid input, expected a string."

    seq = seq.upper().replace(" ", "")

    if not seq:
        return "Empty sequence"

    nucleotides_DNA = set("ATCG")
    nucleotides_RNA = set("AUCG")
    amino_acids = set("ACDEFGHIKLMNPQRSTVWY")

    # 允许"*"出现，但必须出现在最后
    if seq.endswith("*"):
        seq = seq[:-1]

    if all(base in nucleotides_DNA for base in seq):
        return "DNA sequence"
    elif all(base in nucleotides_RNA for base in seq):
        return "RNA sequence"
    elif all(aa in amino_acids for aa in seq):
        return "Protein sequence"
    else:
        invalid_bases = set(seq).difference(nucleotides_DNA.union(amino_acids))
        if invalid_bases:
            return f"Invalid sequence, containing: {', '.join(invalid_bases)}"
        else:
            return "Invalid or unknown sequence"

def process_sequence(seq, forbid_seq):
    seq = seq.upper().replace(" ", "")
    seq = re.sub(r'[^a-zA-Z]', '', seq)
    seq = seq[:20].lower() + seq[20:-20]  + seq[-20:].lower() # Add lower case to the first and last 20 bases
    # 删除所有非字母的字符
    # 如果seq是氨基酸序列，则不需要检查forbid_seq，不需要计算gc_content，不需要检查consecutive NTs，直接返回
    if identify_sequence(seq) == "Protein sequence":
        return seq, "Protein", None, None, None
    elif identify_sequence(seq) == "Invalid sequence, containing: *":
        return seq, "Invalid Protein", None, None, None

    contained_forbidden_list, forbidden_check_list, forbidden_positions = check_forbiden_seq(seq, len(seq), forbid_seq)

    GC_content = calculate_gc_content(seq)
    gc_positions = check_sequence(seq)

    all_positions = merge_overlapping_positions(forbidden_positions + gc_positions)
    all_positions.sort(key=lambda x: x[0])

    ##################################################
    tagged_seq = ""
    current_position = 0

    for start, end in all_positions:
        tagged_seq += seq[current_position:start]
        
        if (start, end) in forbidden_positions:
            for i in range(start, end):
                tagged_seq += '<i class="bg-danger">' + seq[i] + '</i>'
        else:
            for i in range(start, end):
                tagged_seq += '<em class="text-warning">' + seq[i] + '</em>'
            
        current_position = end

    tagged_seq += seq[current_position:]  # 添加剩余的序列

    return tagged_seq, "validated", forbidden_check_list, contained_forbidden_list, GC_content

def process_sequence_get_highlight_position(seq, forbidden_seq):
    seq = seq.upper().replace(" ", "")
    seq = re.sub(r'[^a-zA-Z]', '', seq) # 删除所有非字母的字符
    seq = seq[:20].lower() + seq[20:-20]  + seq[-20:].lower() # Add lower case to the first and last 20 bases
    # 删除所有非字母的字符
    # 如果seq是氨基酸序列，则不需要检查forbid_seq，不需要计算gc_content，不需要检查consecutive NTs，直接返回
    if identify_sequence(seq) == "Protein sequence":
        return seq, "Protein", None, None, None
    elif identify_sequence(seq) == "Invalid sequence, containing: *":
        return seq, "Invalid Protein", None, None, None

    GC_content = calculate_gc_content(seq)
    gc_positions = check_sequence(seq)

    contained_forbidden_list, forbidden_check_list, forbidden_positions = check_forbiden_seq(seq, len(seq), forbidden_seq)

    # 把GC_positions和forbidden_positions 都写到json里面，这些都是需要highlight的位置
    highlights_positions = []
    for position in gc_positions:
        highlights_positions.append({
            'start': position[0],
            'end': position[1],
            'type': 'text-warning'
        })
    
    for position in forbidden_positions:
        highlights_positions.append({
            'start': position[0],
            'end': position[1],
            'type': 'bg-danger'
        })

    if len(forbidden_positions) > 0:
        return seq, "forbidden", forbidden_check_list, contained_forbidden_list, GC_content, highlights_positions
    
    return seq, "validated", forbidden_check_list, contained_forbidden_list, GC_content, highlights_positions


@login_required
def manage_vector_old(request):
    '''list vectors of the company and the user'''
    company_vectors = Vector.objects.filter(user=None)
    user_vectors = Vector.objects.filter(user=request.user)
    return render(request, 'user_center/manage_vector_old.html', {'company_vectors': company_vectors, 'user_vectors': user_vectors})

@login_required
def manage_vector(request):
    '''list vectors of the company and the user'''
    return render(request, 'user_center/manage_vector.html')

@login_required
def customer_vector_data_api(request):
    '''获取用户的vector数据'''
    vector_list = Vector.objects.filter(user=request.user).values(
        'id', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20', 
        'status', 'user__username', 'vector_file', 'vector_png', 'vector_gb'
    )
    return JsonResponse({'data': list(vector_list)}, safe=False)


@login_required
def rootpath_vector_data_api(request):
    '''获取公司的vector数据'''
    vector_list = Vector.objects.filter(user=None).values(
        'id', 'vector_id', 'vector_name', 'vector_map', 'NC5', 'NC3', 'iu20', 'id20',
        'status', 'user__username', 'vector_file', 'vector_png', 'vector_gb'
    )
    return JsonResponse({'data': list(vector_list)}, safe=False)

# checked
@login_required
def vector_upload(request):
    '''当用户在manage_vector页面点击上传按钮时，调用此函数，上传自己的vector文件'''
    if request.method == 'POST':
        vector_file = request.FILES.get('vector_file')
        vector_name = request.POST.get('vector_name')
        this_vector, created = Vector.objects.update_or_create(
            user=request.user,
            vector_name=vector_name,
            vector_file=vector_file,
            defaults={
                'status': 'Submitted',
            }
        )
        return redirect('user_center:manage_vector')
    else:
        return redirect('user_center:manage_vector')

# checked
@login_required
def vector_delete(request):
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        vector = Vector.objects.get(user=request.user, id=vector_id)

        # 删除与之关联的文件
        if vector.vector_file:
            file_path = vector.vector_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        vector.delete()
        return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_vector.html')


@login_required
def vector_download(request, vector_id, file_type, is_admin=False):
    # user只能下载自己的vector和公司的vector，不能下载别人的vector，所以需要验证
    if not is_admin:
        try:
            # 获取当前用户的vector或公司的vector
            vector_object = Vector.objects.get(user=request.user, id=vector_id)
        except Vector.DoesNotExist:
            # 如果当前用户没有这个vector，检查是否为公司的vector
            vector_object = get_object_or_404(Vector, id=vector_id, user=None)
    else:
        vector_object = Vector.objects.get(id=vector_id)
    # 从vector_object中提取数据
    vector_name = vector_object.vector_name
    vector_id = vector_object.vector_id
    NC5 = vector_object.NC5
    NC3 = vector_object.NC3
    iu20 = vector_object.iu20
    id20 = vector_object.id20
    vector_map = vector_object.vector_map  # 
    vector_file = vector_object.vector_file # 这是用户上传的原始文件，通常是一个没有处理的序列文件，可以是多种格式。不是png的文件, 
    # pdf not used
    if file_type == 'pdf':
        '''Not used'''
        # 生成PDF文件
        data = {
            'vector_id': vector_id,
            'vector_name': vector_name,
            'NC5': NC5,
            'NC3': NC3,
            'iu20': iu20,
            'id20': id20,
            'vector_map': vector_map,
        }
        pdf_buffer = render_to_pdf(data)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{vector_name}.pdf"'
        return response
    elif file_type == 'txt':
        '''Not used'''
        # 使用 quote 可以确保浏览器正确解析文件名。特别是文件名包含空格或其他特殊字符时
        response = HttpResponse(content_type='text/plain')
        custom_filename = f'RootPath_{vector_id}_{vector_name}.txt'
        response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
        response.write(f"Vector Name: {vector_name}\n")
        response.write(f"iD20: {iu20}\n")
        response.write(f"iD20: {id20}\n")
        response.write(f"Vector Map: {NC3}{vector_map}{NC5}\n")
    
        return response
    elif file_type == 'dna':
        '''Not used'''
        response = HttpResponse(content_type='text/plain')
        custom_filename = f'RootPath_{vector_id}_{vector_name}.dna'
        response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
        response.write(f"{NC3}{vector_map}{NC5}")
        return response
    elif file_type == 'map':
        # 返回vector_png文件
        vector_png = vector_object.vector_png  # 这是改造后的Vector_png
        if vector_png:
            response = HttpResponse(vector_png, content_type='application/octet-stream')
            name = vector_png.name   # user/vector_file/pCVa001M1Kan_pET-28.png
            file_path = default_storage.path(name)  # /path/to/media/user/vector_file/pCVa001M1Kan_pET-28.png
            basename = os.path.basename(file_path)  # pCVa001M1Kan_pET-28.png
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='image/png')
                custom_filename = f'RootPath_{basename}'
                response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'

                return response
        else:
            return HttpResponse("No vector map found")
    elif file_type == 'gb':
        # 返回vector_genebank文件
        vector_gb = vector_object.vector_gb
        if vector_gb:
            response = HttpResponse(vector_gb, content_type='application/octet-stream')
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
    elif file_type == 'file':
        # 返回vector_file文件
        vector_file = vector_object.vector_file
        if vector_file:
            response = HttpResponse(vector_file, content_type='application/octet-stream')
            name = vector_file.name
            file_path = default_storage.path(name)
            basename = os.path.basename(file_path)
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                custom_filename = f'RootPath_{basename}'
                response['Content-Disposition'] = f'attachment; filename="{quote(custom_filename)}"'
                return response
        else:
            return HttpResponse("No vector file found", status=404)
    else:
        return HttpResponse("File type not supported", status=400)


def test(request):
    return render(request, 'user_center/test.html')