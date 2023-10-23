from django.shortcuts import render
from .models import Tool
from django.contrib.auth.decorators import login_required
# Create your views here.

def tools_list(request):
    tools = Tool.objects.all()
    return render(request, 'tools/tools_list.html', {'tools': tools})

@login_required
def SequenceAnalyzer(request):
    return render(request, 'tools/SequenceAnalyzer.html')