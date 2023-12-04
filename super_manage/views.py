from django.shortcuts import render

# Create your views here.

def order_manage(request):
    # cart = Cart.objects.get(user=request.user)
    # shopping_cart = cart.genes.all()
    # page_object = Pagination(request, shopping_cart)
    # context = {
    #     'shopping_cart': page_object.page_queryset,  # 分完页的数据
    #     'page_string':page_object.html(),  # 页码
    # }
    context = {
        'title':"Order Manage"
    }
    return render(request, 'super_manage/order_manage.html', context)

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
