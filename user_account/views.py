from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import UserProfile
from .forms import UserProfileForm
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.shortcuts import render


@login_required()
def myself(request):
    print("request.user:", request.user)
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user,'userprofile') else UserProfile.objects.create(user=request.user)
    return render(request, "user_account/myself.html", {"user": request.user, "userprofile": userprofile})


@login_required
def myself_edit(request):
    # 先拿到（或创建）当前登录用户对应的 UserProfile
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # 用 UserProfileForm 来更新自己的扩展信息
        # 注意需要把 request.FILES 也传进来, 这样才能处理上传的文件(如 photo)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        if profile_form.is_valid():
            # 保存 UserProfile 表
            profile_form.save()

            return redirect('/user_account/my-information/')
        else:
            # 验证失败时，需要把这两个表单对象一起返回给模板渲染
            return render(request, "user_account/myself.html", {
                "user": request.user,
                "userprofile": userprofile,
                "profile_form": profile_form,
            })
    else:
        # GET 请求时，实例化这两个表单，给前端显示当前用户已有信息
        profile_form = UserProfileForm(instance=userprofile)
        return render(request, "user_account/myself.html", {
            "user": request.user,
            "userprofile": userprofile,
            "profile_form": profile_form,
        })


def avatar_edit(request):
    if request.method == 'POST':
        print(f"request.user:{request.user} is going to change avatar")
        print(f"user email:{request.user.email}")
        userid = request.POST.get('userid')
        print(f"userid:{userid}")
        imagePath = request.POST.get('imagePath')
        print(f"imagePath:{imagePath}")
        UserProfile.objects.filter(user_id=userid).update(photo=imagePath)
        return HttpResponse('success')
    else:
        return HttpResponse('error')

def settings(request):
    return render(request, 'user_account/settings.html')


def contact_us(request):
    return render(request, 'user_account/contact_us.html')

def is_secondary_admin(user):
    """
    判断用户是否是二级管理员。

    参数:
    user -- Django的User对象。

    返回:
    True或False，表示用户是否是二级管理员。
    """
    return user.is_authenticated and user.groups.filter(name='SecondaryAdminGroup').exists()