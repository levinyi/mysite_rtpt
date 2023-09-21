from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from user_center.models import Order, ShoppingCart
from product.models import Product, Vector
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

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
    company_vectors = Vector.objects.filter(user=None)
    user_vectors = Vector.objects.filter(user=request.user)
    return render(request, 'user_center/manage_vector.html', {'company_vectors': company_vectors, 'user_vectors': user_vectors})

def download_pdf(request, order_id):
    data = {}
    pdf = render_to_pdf('template.html', data)
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = "your_file_name.pdf"
    content = f"attachment; filename='{filename}'"
    response['Content-Disposition'] = content
    return response