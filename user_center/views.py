import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from user_center.models import Order, ShoppingCart
from product.models import GeneSynEnzymeCutSite, Vector
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User

# Create your views here.
@login_required(login_url='/account/login/')
def dashboard(request):
    shopping_cart = ShoppingCart.objects.filter(user=request.user, status='INCOMPLETE')
    production_order = Order.objects.filter(user=request.user, status='CREATED')
    shipping_order = Order.objects.filter(user=request.user, status='SHIPPING')
    return render(request, 'user_center/dashboard.html', {
            'order_number_in_production': len(production_order),
            'order_number_in_shipment': len(shipping_order), 
            'order_number_in_cart': len(shopping_cart), 
            })


@login_required
def shopping_cart(request):
    if request.method == 'GET':
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        order_list = Order.objects.filter(user=request.user)
        return render(request, 'user_center/shopping_cart.html', {'shopping_cart': shopping_cart, 'order_list': order_list})

@login_required
@csrf_exempt
def shopping_cart_remove(request):
    shopping_cart_id = request.POST.get('shopping_id')
    try:
        shopping_cart = ShoppingCart.objects.get(id=shopping_cart_id)
        shopping_cart.delete()
        return HttpResponse('1')
    except:
        return HttpResponse('2')

def order_create(request):
    company_vectors = Vector.objects.filter(user=None)
    
    # 如果用户已登录
    if request.user.is_authenticated:
        customer_vectors = Vector.objects.filter(user=request.user)
        return render(request, 'user_center/manage_order_create.html', {'customer_vectors': customer_vectors, 'company_vectors': company_vectors})
    # 如果用户未登录
    else:
        return render(request, 'user_center/manage_order_create.html', {'company_vectors': company_vectors})


def submit_order(request, shopping_id):
    shopping_cart = get_object_or_404(ShoppingCart, id=shopping_id)
    shopping_cart.status = 'INCOMPLETE'
    shopping_cart.save()
    Order.objects.create(
        user=request.user,
        status='CREATED',
        shopping_cart=shopping_cart,
    )
    return redirect('/user_center/shopping_cart/')

def manage_order(request):
    order_list = Order.objects.filter(user=request.user)
    return render(request, 'user_center/manage_order.html', {'order_list': order_list})

@login_required
def manage_vector(request):
    '''list vectors of the company and the user'''
    company_vectors = Vector.objects.filter(user=None)
    user_vectors = Vector.objects.filter(user=request.user)
    # for vector in Vector.objects.all():
    #     print(vector.user, vector.vector_name, vector.combined_seq, vector.forbid_seq, vector.NC5, vector.NC3, vector.vector_map, vector.status)
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

# checked
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

def process_sequence(seq, forbid_seq, vector_object=None):
    seq = seq.upper().replace(" ", "")
    contained_forbidden_list, forbidden_check_list, forbidden_positions = check_forbiden_seq(seq, len(seq), forbid_seq)
    
    GC_content = calculate_gc_content(seq)
    gc_positions = check_sequence(seq)

    all_positions = forbidden_positions + gc_positions

    all_positions = merge_overlapping_positions(all_positions)
    all_positions.sort(key=lambda x: x[0])
    
    print("all_positions: in process sequence: ", all_positions)

    ##################################################
    tagged_seq = ""
    current_position = 0
    for start, end in all_positions:
        tagged_seq += seq[current_position:start - 1]

        if (start, end) in forbidden_positions:
            tagged_seq += '<span class="bg-danger">' + seq[start - 1:end] + '</span>'
        else:
            tagged_seq += '<em class="text-warning">' + seq[start - 1:end] + '</em>' 
        current_position = end
    
    tagged_seq += seq[current_position:]  # Add the remaining sequence
    ##################################################
    print(tagged_seq)
    if len(contained_forbidden_list) > 0:
        seq_status = "forbidden"
    else:
        seq_status = "validated"

    if vector_object is not None:
        vector_object.status = seq_status
        vector_object.saved_seq = tagged_seq
        vector_object.gc_content = GC_content
        vector_object.forbidden_check_list = forbidden_check_list
        vector_object.contained_forbidden_list = contained_forbidden_list
        vector_object.save()

    return tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, GC_content

def vector_validation(request, vector_id):
    ''' when user click the "Re-analyze" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))
        saved_seq = data.get("sequence")
        gene_id = data.get("gene")
        vector_object = Vector.objects.get(user=user, id=vector_id, vector_name=gene_id)
        original_seq = vector_object.combined_seq
        if original_seq == saved_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})
        
        tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(saved_seq, vector_object.forbid_seq, vector_object)

        return JsonResponse({'status': 'success', 'message': 'Validation process finished'})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def vector_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        for row in data:
            if any(cell is not None for cell in row):
                combined_seq = row[1] + row[2] + row[3]
                tagged_seq, seq_status, forbidden_check_list, contained_forbidden_list, gc_content = process_sequence(combined_seq, row[4])
                saved_seq = tagged_seq

                this_vector, created = Vector.objects.update_or_create(
                    user=request.user,
                    vector_name=row[0],
                    defaults={
                        'combined_seq': tagged_seq,
                        'forbid_seq': row[4],
                        'NC5': row[1],
                        'NC3': row[2],
                        'vector_map': row[3],
                        'status': seq_status,
                        'saved_seq': saved_seq,
                        'gc_content': gc_content,
                        'forbidden_check_list': forbidden_check_list,
                        'contained_forbidden_list': contained_forbidden_list,
                    }
                )
                print(this_vector.vector_name)
        return JsonResponse({'status': 'success', "message": "Data saved successfully"})
    else:
        return render(request, 'user_center/manage_vector_create.html')

@login_required
def vector_detail(request, vector_id):
    ''' when user click the "Edit" button, this function will be called.'''
    vector_object = Vector.objects.get(user=request.user, id=vector_id)
    return render(request, 'user_center/vector_detail.html', {'vector': vector_object})

@login_required
def vector_edit(request, vector_id):
    ''' when user click the "Edit" button, this function will be called.'''
    vector_object = Vector.objects.get(user=request.user, id=vector_id)
    vector_object.status = "validated"
    vector_object.save()
    return redirect(f'/user_center/vector_detail/{vector_id}')

def vector_delete(request, vector_id):
    if request.method == 'POST':
        vector = Vector.objects.get(user=request.user, id=vector_id)
        vector.delete()
        return redirect('/user_center/manage_vector/')
    else:
        return render(request, 'user_center/manage_vector.html')
        

# def download_pdf(request, order_id):
#     data = {}
#     pdf = render_to_pdf('template.html', data)
#     response = HttpResponse(pdf, content_type='application/pdf')
#     filename = "your_file_name.pdf"
#     content = f"attachment; filename='{filename}'"
#     response['Content-Disposition'] = content
#     return response

@login_required
def validation_save(request, vector_id):
    vector_object = Vector.objects.get(user=request.user, id=vector_id)
    vector_object.status = 'saved'
    vector_object.save()
    return redirect(f'/user_center/vector_detail/{vector_id}')
