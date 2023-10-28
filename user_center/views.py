import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from user_center.models import Order, ShoppingCart
from product.models import Product, Vector
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


def manage_vector(request):
    '''list vectors of the company and the user'''
    company_vectors = Vector.objects.filter(user=None)
    user_vectors = Vector.objects.filter(user=request.user)
    return render(request, 'user_center/manage_vector.html', {'company_vectors': company_vectors, 'user_vectors': user_vectors})

def check_forbiden_seq(seq, seq_length, customer_forbidden_list=None):
    '''根据序列长度检查正义和反义链'''
    seq = seq.upper().replace(" ", "")

    forbidden_list_objects = GeneSynEnzymeCutSite.objects.all()
    raw_forbidden_list = []
    forbidden_list = []
    for enzyme in forbidden_list_objects:
        enzyme_name = enzyme.enzyme_name
        enzyme_seq = enzyme.enzyme_seq
        enzyme_scope = enzyme.usescope
        start,end = enzyme_scope.split("-")
        start = int(start)
        end = int(end)

        if start <= seq_length <= end:
            forbidden_list.append(enzyme_seq)
        raw_forbidden_list.append(enzyme_seq)
    print("company forbidden_list: ", forbidden_list)
    if customer_forbidden_list and isinstance(customer_forbidden_list, str):
        formated_list = customer_forbidden_list.split(",")
        forbidden_list.extend(formated_list)
    print("forbidden_list + customer list: ", forbidden_list)
    # 检查序列中是否包含禁止的序列
    raw_forbidden_list.extend(customer_forbidden_list.split(","))
    contained_forbidden_list = [forbiden_seq for forbiden_seq in forbidden_list if forbiden_seq in seq]    

    return contained_forbidden_list, raw_forbidden_list

@login_required
def vector_add(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)            
            print("data: ", data)
            # user vector_name cloning_site vector_map NC5 NC3 is_ready_to_use, status, create_date
            for row in data:
                if any(cell is not None for cell in row): 
                    combined_seq = row[1] + row[2] + row[3]
                    forbidden_list = check_forbiden_seq(combined_seq, len(combined_seq), row[4])
                    
                    if forbidden_list: 
                        for forbidden_seq in forbidden_list:
                            combined_seq = combined_seq.replace(forbidden_seq, f'<em class="bg-warning">{forbidden_seq}</em>')
                            seq_status = "forbidden"
                    else:
                        seq_status = "validated"
                        combined_seq = combined_seq

                    gene_data, created = Vector.objects.update_or_create(
                        user = request.user,
                        vector_name = row[0],
                        defaults={
                            "NC5" : row[1],
                            "vector_map" : row[2],
                            "NC3" : row[3],
                            "forbid_seq" : row[4],
                            "combined_seq" : combined_seq,
                            "saved_seq" : combined_seq,
                            "status" : seq_status,
                        }
                    )
            return JsonResponse({'status': 'success', "message": "Data saved successfully"})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        return HttpResponse('1')
    else:
        return render(request, 'user_center/manage_vector_create.html')
    
def vector_delete(request):
    if request.method == 'POST':
        vector_id = request.POST.get('vector_id')
        vector = get_object_or_404(Vector, id=vector_id)
        vector.user = None
        vector.save()
        return HttpResponse('1')
    else:
        return HttpResponse('2')

def vector_edit(request, pk):
    ''' when user click the "Analysis" button, this function will be called.'''
    if request.method == "GET":
        user = request.user

        vector = Vector.objects.get(user=user, id=pk)
        return render(request, 'tools/inquiry_detail.html',{'new_gene_list': new_gene_list})

def download_pdf(request, order_id):
    data = {}
    pdf = render_to_pdf('template.html', data)
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = "your_file_name.pdf"
    content = f"attachment; filename='{filename}'"
    response['Content-Disposition'] = content
    return response

# @require_POST
def inquiry_validation(request, pk):
    ''' when user click the "validate" button, this function will be called. '''
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))

        saved_seq = data.get("sequence")
        gene_id = data.get("gene")

        gene_object = Vector.objects.get(user=user, inquiry_id=pk, gene_name=gene_id)

        original_seq = gene_object.combined_seq
        if original_seq == saved_seq:
            return JsonResponse({'status': 'error', 'message': 'No changes made.'})
        
        forbidden_list = check_forbiden_seq(saved_seq, len(saved_seq), gene_object.forbid_seq)

        if forbidden_list: 
            for forbidden_seq in forbidden_list:
                saved_seq = saved_seq.replace(forbidden_seq, f'<em class="bg-warning">{forbidden_seq}</em>')
            gene_status = 'forbidden'
        else:
            gene_status = 'validated'
        
        print("gene_status: ", gene_status)
        gene_object.status = gene_status
        gene_object.saved_seq = saved_seq
        gene_object.save()

        return JsonResponse({'status': 'success', 'message': 'validation process finished'})
    except Vector.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Vector not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def validation_save(request, pk):
    try:
        user = request.user
        data = json.loads(request.body.decode('utf-8'))

        gene_id = data.get("gene")

        gene_object = Vector.objects.get(user=user, inquiry_id=pk, gene_name=gene_id)
        
        gene_object.status = 'saved'
        gene_object.save()

        return JsonResponse({'status': 'success', 'message': 'validation process finished'})
    except InquiryGeneSeqValidation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'InquiryGeneSeqValidation not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
