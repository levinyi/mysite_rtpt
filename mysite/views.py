from django.views.generic import TemplateView
from product.models import Product

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView,self).get_context_data(**kwargs)
        context['my_product'] = Product.objects.all()
        return context