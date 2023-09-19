from django.shortcuts import get_object_or_404, render
from .models import Product, ExpressionHost, PurificationMethod, Addon, ExpressionScale
from user_center.models import ShoppingCart, Order
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your views here.
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product/products.html' , {'products': products})


def create_order_old(request):
    if request.method == 'POST':
        # POST请求逻辑，要求用户登录
        if request.user.is_authenticated:
            # 已登录，处理post请求
            # 获取用户提交的信息
            project_name = request.POST.get('project_name')
            number = request.POST.get('antibody_number')
            purification_method = request.POST.get('purification_method')
            expression_host = request.POST.get('expression_host')
            selected_card  = request.POST.get('selected_card')
            selected_button = request.POST.get('selected_button')
            print("selected_card: ", selected_card)
            print("selected_button: ", selected_button)
            print("project_name: ", project_name)
            print("number: ", number)
            print("purification_method: ", purification_method)
            print("expression_host: ", expression_host)

            card_dict = {
                'info1': 'Fast Plasmid',
                'info2': 'HT Plasmid',
                'info3': 'Fast Antibody',
                'info4': 'HT Antibody',
                'info5': 'SEC-HPLC',
                'info6': 'Endotoxin',
            }
            btn_dict = {
                'btn1': 'Plasmid',
                'btn2': 'Antibody',
                'btn3': 'Analysis',
            }
            product = get_object_or_404(
                Product, 
                product_type=btn_dict[selected_button], 
                product_name=card_dict[selected_card])
            price = product.price
            total_price = int(number) * int(price)
            # 创建一个新的购物车

            ShoppingCart.objects.create(
                user=request.user, 
                project_name=project_name,
                product = product,
                express_host = expression_host,
                purification_method = purification_method,
                total_price = total_price,)
            return JsonResponse({'redirect_url': '/user_center/shopping_cart/'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please login.'}, status=401)
    else:
        return render(request, 'product/create_order.html')

def create_order(request):
    if request.method == "GET":
        return render(request, 'product/create_order.html', {})
    else:
        product_button  = request.POST.get('product_type')
        selected_button = request.POST.get('selected_button')
        print("product_button: ", product_button)  # btn1, btn2
        print("selected_button: ", selected_button) # HT, Fast
        
        btn_dict = {
            'btn1': 'Plasmid',
            'btn2': 'Antibody',
        }
        product_type = btn_dict[product_button]
        product_name = f"{selected_button} {product_type}"
        print("product_name: ", product_name)
        print("product_type: ", product_type)
        product = get_object_or_404(Product, product_type=product_type, product_name=product_name)
        price = product.price
        print("price: ", price)

        # 判读是否登录
        if not request.user.is_authenticated:
            temp_user, created = User.objects.get_or_create(username='temp_user')
            # 创建一个新的购物车
            shopping_cart = ShoppingCart.objects.create(
                product=product,
                user=temp_user,
            )
        else:
            shopping_cart = ShoppingCart.objects.create(
                user=request.user,
                product=product,
            )
        return JsonResponse({'redirect_url': '/product/order_selection/', 'order_id': shopping_cart.id})

def order_selection(request, order_id):
    if request.method == "GET":
        # 判读是否登录
        if not request.user.is_authenticated: # 未登录
            shopping_cart = ShoppingCart.objects.get(user__username='temp_user', id=order_id)
        else:
            shopping_cart = ShoppingCart.objects.get(user=request.user, id=order_id)
        # 获取数据库中的信息, 以后再说
        # expression_host = ExpressionHost.objects.all()
        # purification_method = PurificationMethod.objects.all()
        # expression_scale = ExpressionScale.objects.all()
        # addon = Addon.objects.all()
        return render(request, 'product/order_selection.html', {'shopping_cart': shopping_cart})
    elif request.method == "POST":
        # 判读是否登录
        if not request.user.is_authenticated: # 未登录
            return JsonResponse({'status': 'error', 'message': 'Please login.'}, status=401)
        
        shopping_cart = ShoppingCart.objects.get(id=order_id)
        shopping_cart.user = request.user # 更新购物车的用户信息

        # 获取用户提交的信息
        purification_method = request.POST.get('purification_method')
        expression_host = request.POST.get('expression_host')
        scale = request.POST.get('scale')
        antibody_number = request.POST.get('antibody_number')
        analysis = request.POST.get('analysis')
        total_price = request.POST.get('total_price')
        # 目前得到的是网页端固定的id，需要根据id获取数据库中的信息
        select_dict = {
            'protein1': 'Protein A',
            'protein2': 'Protein G',
            'host1': '293F',
            'host2': 'CHO',
            'scale1': '30mL',
            'scale2': '3mL',
            'analysis1': 'SEC-HPLC',
            'analysis2': 'Endotoxin',
            'analysis0': 'NO',
        }
        
        purification_method_instance = PurificationMethod.objects.get(method_name=select_dict[purification_method])
        expression_host_instance = ExpressionHost.objects.get(host_name=select_dict[expression_host])
        scale_instance = ExpressionScale.objects.get(scale=select_dict[scale])
        addon_instance = Addon.objects.get(name=select_dict[analysis])

        shopping_cart.purification_method = purification_method_instance
        shopping_cart.antibody_number = antibody_number
        shopping_cart.express_host = expression_host_instance
        shopping_cart.total_price = float(total_price)
        shopping_cart.scale = scale_instance
        shopping_cart.analysis = addon_instance
        shopping_cart.save()
        return JsonResponse({'redirect_url': f'/product/order_quotation/{order_id}'})

@login_required
def order_quotation(request, order_id):
    if request.method == "GET":
        shopping_cart = ShoppingCart.objects.get(user=request.user, id=order_id)
        return render(request, 'product/order_quotation.html', {'shopping_cart': shopping_cart})


