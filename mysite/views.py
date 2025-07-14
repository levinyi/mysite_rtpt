from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import activate
from django.shortcuts import redirect


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView,self).get_context_data(**kwargs)
        return context

def switch_language(request):
    lang_code = request.GET.get('language', settings.LANGUAGE_CODE)
    if lang_code in dict(settings.LANGUAGES):
        activate(lang_code)
        request.session[settings.LANGUAGE_COOKIE_NAME] = lang_code
    return redirect(request.META.get('HTTP_REFERER', '/'))