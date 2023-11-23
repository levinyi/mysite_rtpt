import json
import re
import os
from django.shortcuts import get_list_or_404, render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from product.models import GeneSynEnzymeCutSite, Species, Vector
from user_center.utils.pagination import Pagination
from .models import Cart, GeneInfo, OrderInfo
from .utils.render_to_pdf import render_to_pdf
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User

# Create your views here.
@login_required(login_url='/account/login/')
def dashboard(request):
    # 如果没有shopping cart，创建一个
    production_order = OrderInfo.objects.filter(user=request.user, status='CREATED')
    shipping_order = OrderInfo.objects.filter(user=request.user, status='SHIPPING')
    shopping_cart = Cart.genes.through.objects.filter(cart__user=request.user)
    return render(request, 'user_center/dashboard.html', {
            'order_number_in_production': len(production_order),
            'order_number_in_shipment': len(shipping_order), 
            'gene_number_in_cart': len(shopping_cart), 
            })

@login_required
def order_create(request):
    '''创建订单页'''
    # 这里只能是GET请求，因为POST请求是提交订单
    if request.method == 'POST':
        # 这里的逻辑是创建订单
        data = json.loads(request.body.decode('utf-8'))
        vector_id = data.get("vectorId")
        gene_table = data.get("genetable")
        # print(gene_table)
        if not gene_table:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})

        try:
            vector = Vector.objects.get(id=vector_id)
        except Vector.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid vector ID'})

        nc5 = vector.NC5
        nc3 = vector.NC3

        cart, created = Cart.objects.get_or_create(user=request.user)
        response_message = ""

        for row in gene_table:
            if not any(cell is not None for cell in row):
                # print("Empty row")
                continue
            
            gene_name = row[0]
            original_seq = row[1]
            species = None
            forbid_seq = None
            aa_nc5 = ''
            aa_nc3 = ''
            combined_seq = original_seq
            saved_seq = original_seq
            gc_content = None
            forbidden_check_list = None
            contained_forbidden_list = None
            status = 'saved'

            # 判断是否为AA序列（通过列数判断）
            if len(row) > 2:
                # print("Processing AA sequence")
                try:
                    species_name = row[2]
                    species = Species.objects.get(species_name=species_name)
                except Species.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Species {species_name} not found'})

                forbid_seq = row[3]
                aa_nc5 = row[4] or ''
                aa_nc3 = row[5] or ''
                nc5 = str(nc5) + str(aa_nc5)
                nc3 = str(nc3) + str(aa_nc3)
                status = 'optimizing'
                forbidden_check_list = forbid_seq
                response_message = 'AA sequence submitted for codon optimization. Please wait 10-20 minutes to check the result.'
            else:
                # print("Processing NT sequence")
                original_seq = f'<span class="text-lowercase">{nc5}</span>{original_seq}<span class="text-lowercase">{nc3}</span>'
                combined_seq = nc5 + row[1] + nc3
                tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(combined_seq, forbid_seq)
                # print("seq_status: ", seq_status, "forbidden_check_list: ", forbidden_check_list, "contained_forbidden_list: ", contained_forbidden_list)
                if seq_status in ['Protein', 'Invalid Protein']:
                    return JsonResponse({'status': 'error', 'message': f'{seq_status} sequence is not allowed.'})
                saved_seq = tagged_seq
                status = seq_status

            # 创建或更新GeneInfo对象
  
            this_gene, created = GeneInfo.objects.update_or_create(
                user=request.user,
                gene_name=gene_name,
                defaults={
                    'original_seq': original_seq,
                    'vector': vector,
                    'species': species,
                    'status': status,
                    'forbid_seq': forbid_seq,
                    'combined_seq': original_seq,

                    'saved_seq': saved_seq,
                    'gc_content': gc_content,
                    'forbidden_check_list': forbidden_check_list,
                    'contained_forbidden_list': contained_forbidden_list,
                }
            )
            cart.genes.add(this_gene)

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

        # 如果用户已登录
        if request.user.is_authenticated:
            customer_vectors = Vector.objects.filter(user=request.user)
            return render(request, 'user_center/manage_order_create.html', {'customer_vectors': customer_vectors, 'company_vectors': company_vectors, 'species_names_json': species_names_json})
        # 如果用户未登录
        else:
            return render(request, 'user_center/manage_order_create.html', {'company_vectors': company_vectors, 'species_names_json': species_names_json})

# checked
def submit_notification(request):
    ''' when user submit AA sequence. this function will be called.'''
    if request.method == 'GET':
        return render(request, 'user_center/aa_sequence_submit_success.html')
    else:
        return render(request, 'user_center/aa_sequence_submit_success.html')

@login_required
def gene_detail(request):
    ''' when user click the "submit & analysis" button, this function will be called.'''
    gene_list = GeneInfo.objects.filter(user=request.user).exclude(status='submitted').exclude(status='optimizing')
    return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list})

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
        return render(request, 'user_center/gene_detail.html', {'gene_list': gene_list})

@login_required
def protein_edit(request, gene_id):
    gene_list = GeneInfo.objects.filter(user=request.user, status__in=['optimizing', 'optimized', 'failed'])
    return render(request, 'user_center/protein_detail.html', {'gene_list': gene_list})


@login_required
def gene_validation(request):
    ''' when user click the "Re-analyze" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        saved_seq = data.get("sequence")
        gene_name = data.get("gene")
        gene_object = GeneInfo.objects.get(user=user, gene_name=gene_name)
        original_seq = gene_object.combined_seq
        if original_seq == saved_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})
        
        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(saved_seq, gene_object.forbid_seq)
        # print(seq_status)
        if seq_status in ['Protein', 'Invalid Protein']:
            return JsonResponse({'status': 'error', 'message': 'Squence is not allowed. Your sequence may has '+ seq_status + ' sequence.'})
        gene_object.status = seq_status
        gene_object.saved_seq = tagged_seq
        gene_object.gc_content = gc_content
        gene_object.forbidden_check_list = forbidden_check_list
        gene_object.contained_forbidden_list = contained_forbidden_list
        gene_object.combined_seq = saved_seq
        gene_object.save()
        return JsonResponse({'status': 'success', 'message': 'Validation process finished'})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def validation_save(request, id):
    ''' when user click the "Save" button, this function will be called. '''
    def validation_and_save_seq(request, id):
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        saved_seq = data.get("sequence")
        gene_object = GeneInfo.objects.get(user=user, id=id)
        original_seq = gene_object.combined_seq
        if original_seq == saved_seq:
            if gene_object.status == 'validated' :
                gene_object.status = 'saved'
                gene_object.save()
                return True
            else:
                return False
            
        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(saved_seq, gene_object.forbid_seq)
        gene_object.saved_seq = tagged_seq
        gene_object.gc_content = gc_content
        gene_object.forbidden_check_list = forbidden_check_list
        gene_object.contained_forbidden_list = contained_forbidden_list
        gene_object.combined_seq = saved_seq
        if seq_status == 'validated':
            gene_object.status = 'saved'
            gene_object.save()
            return True
        else:
            gene_object.status = seq_status
            gene_object.save()
            return False

    try:
        if(validation_and_save_seq(request, id)):
            return JsonResponse({'status': 'success', 'message': 'Gene saved successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please check your sequence and analysis first.'})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# checked
@login_required
def gene_delete(request):
    '''从shopping cart中删除gene'''
    if request.method == 'POST':
        gene_id = request.POST.get('gene_id')
        gene = GeneInfo.objects.get(user=request.user, id=gene_id)
        gene.delete()
        return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_order_create.html')

@login_required
def view_cart(request):
    cart = Cart.objects.get(user=request.user)
    shopping_cart = cart.genes.all()
    # page_object = Pagination(request, shopping_cart)
    # context = {
    #     'shopping_cart': page_object.page_queryset,  # 分完页的数据
    #     'page_string':page_object.html(),  # 页码
    # }
    context = {
        'shopping_cart': shopping_cart,
    }
    return render(request, 'user_center/cart_view.html', context)


@login_required
@require_POST
def checkout(request):
    # 获取所有选中的gene_ids, 提交订单。
    gene_ids = request.POST.getlist('gene_ids')
    # print("you selected these genes id: ", gene_ids)
    if not gene_ids:
        return JsonResponse({'status': 'error', 'message': 'No gene selected'})
    
    # 为选中的gene创建一个订单
    order = OrderInfo.objects.create(user=request.user)
    # 获取所有选中的gene对象
    genes = get_list_or_404(GeneInfo, user=request.user, id__in=gene_ids)
    
    # 将gene添加到订单中
    order.gene_infos.add(*genes)
    order.status = 'CREATED'
    order.save()
    # print("order.gene_infos.all(): ", order.gene_infos.all())

    # 将选中的gene从购物车中删除
    cart = Cart.objects.get(user=request.user)
    cart.genes.remove(*genes)
    cart.save()

    # 不删除GeneInfo对象，改变status为submitted
    for gene_id in gene_ids:
        GeneInfo.objects.filter(user=request.user, id=gene_id).update(status='submitted')

    # 重定向到订单详情页面
    return JsonResponse({'status': 'success', 'message': 'Order created successfully', 'redirect_url': f'/user_center/manage_order/'})

# not used
def view_order_detail(request, order_id):
    # 这里的逻辑是展示订单详情
    order = OrderInfo.objects.get(id=order_id)
    return render(request, 'user_center/view_order_detail.html', {'order': order})

# checked
def manage_order(request):
    order_list = OrderInfo.objects.filter(user=request.user)
    return render(request, 'user_center/order_view.html', {'order_list': order_list})

@login_required
def manage_vector(request):
    '''list vectors of the company and the user'''
    company_vectors = Vector.objects.filter(user=None)
    user_vectors = Vector.objects.filter(user=request.user)
    return render(request, 'user_center/manage_vector.html', {'company_vectors': company_vectors, 'user_vectors': user_vectors})

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

    all_positions.sort()
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
    gc_count = sequence.count('G') + sequence.count('C')
    total_count = len(sequence)
    gc_content = (gc_count / total_count) * 100
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

    all_positions = forbidden_positions + gc_positions

    all_positions = merge_overlapping_positions(all_positions)
    all_positions.sort(key=lambda x: x[0])
    
    # print("all_positions: in process sequence: ", all_positions)

    ##################################################
    tagged_seq = ""
    current_position = 0
    # print("all positions: ", all_positions)
    for start, end in all_positions:
        tagged_seq += seq[current_position:start]

        tagged_seq += '<i class="text-warning">'
        if (start, end) in forbidden_positions:
            # tagged_seq += '<i class="bg-danger">' + seq[start:end] + '</i>'
            for i in range(start, end):
                tagged_seq += '<i class="bg-danger">' + seq[i] + '</i>'
        else:
            # tagged_seq += '<em class="text-warning">' + seq[start:end] + '</em>' 
            for i in range(start, end):
                tagged_seq += '<em class="text-warning">' + seq[i] + '</em>'
        tagged_seq += '</i>'
        
        current_position = end

    tagged_seq += seq[current_position:]  # Add the remaining sequence

    ##################################################
    if len(contained_forbidden_list) > 0:
        seq_status = "forbidden"
    else:
        seq_status = "validated"

    return tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, GC_content


# checked
@login_required
def vector_upload(request):
    if request.method == 'POST':
        vector_file = request.FILES.get('vector_file')
        vector_name = request.POST.get('vector_name')
        # print("vector_file", vector_file, vector_name)
        this_vector, created = Vector.objects.update_or_create(
            user=request.user,
            vector_name=vector_name,
            vector_file=vector_file,
            defaults={
                'status': 'Received',
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
        file_path = vector.vector_file.path
        if os.path.exists(file_path):
            os.remove(file_path)

        vector.delete()
        return JsonResponse({'status': 'success', 'message': 'Gene deleted successfully'})
    else:
        return render(request, 'user_center/manage_vector.html')
        
def vector_download(request, vector_id, file_type):
    # user只能下载自己的vector和公司的vector，不能下载别人的vector，所以需要验证
    try:
        # 获取当前用户的vector或公司的vector
        vector_object = Vector.objects.get(user=request.user, id=vector_id)
    except Vector.DoesNotExist:
        # 如果当前用户没有这个vector，检查是否为公司的vector
        vector_object = get_object_or_404(Vector, id=vector_id, user=None)

    # 从vector_object中提取数据
    vector_name = vector_object.vector_name
    NC5 = vector_object.NC5
    NC3 = vector_object.NC3
    vector_map = vector_object.vector_map
    vector_file = vector_object.vector_file

    data = {
        'vector_name': vector_name,
        'NC5': NC5,
        'NC3': NC3,
        'vector_map': vector_map,
    }

    if file_type == 'pdf':
        # 生成PDF文件
        pdf_buffer = render_to_pdf(data)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{vector_name}.pdf"'
        return response
    elif file_type == 'txt':
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{vector_name}.txt"'
        response.write(f"Vector Name: {vector_name}\n")
        response.write(f"NC5: {NC5}\n")
        response.write(f"NC3: {NC3}\n")
        response.write(f"Vector Map: {vector_map}\n")
        return response
    elif file_type == 'dna':
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{vector_name}.dna"'
        response.write(f"{NC5}{vector_map}{NC3}")
        return response
    elif file_type == 'map':
        # 把vector_map文件直接返回
        if vector_file:
            response = HttpResponse(vector_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{vector_file.name}"'
            return response
        else:
            return HttpResponse("No vector map found")
    else:
        return HttpResponse("File type not supported")

