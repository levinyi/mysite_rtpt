from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone

from notice.models import get_user, Notice
from notice.views import send_email_with_link
from .forms import RegistrationForm, UserProfileForm, ForgotPwForm
from .models import UserProfile
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.shortcuts import render

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

# decorators.py

from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps

def custom_password_reset_confirm(request, uidb64, token):
    # 根据 uidb64 获取用户对象

    # 处理密码重置确认表单提交
    if request.method == 'POST':
        user = get_user(uidb64)
        user = User.objects.get(pk=user.id)
        new_password = request.POST['new_password2']
        # 使用 set_password 方法设置新密码
        user.set_password(new_password)
        # 保存用户对象到数据库
        user.save()

        # 重定向到密码重置完成的页面或其他页面
        return redirect('account:password_reset_complete')

    # 如果是 GET 请求，继续使用 PasswordResetConfirmView 处理
    return PasswordResetConfirmView.as_view(
        template_name='account/password_reset_confirm.html',
        success_url='/account/password-reset-complete/'
    )(request, uidb64=uidb64, token=token)


def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 调用原始的登录视图，获取登录表单的验证结果
        response = view_func(request, *args, **kwargs)
        # 如果用户名和密码验证通过
        if response.status_code == 302:
            # 在这里添加你的额外验证逻辑
            up = UserProfile.objects.get(user__username=request.POST['username'])
            u = up.user
            if not up.is_verify:
                target_url = reverse('account:login_verify_failed')  # 使用你的目标视图的名称
                params = {'username': u.username, 'email': u.email}
                # 将参数编码并添加到 URL
                target_url_with_params = f'{target_url}?{urlencode(params)}'
                # 使用 HttpResponseRedirect 跳转到目标 URL
                return HttpResponseRedirect(target_url_with_params)
        return response

    return _wrapped_view


def resend_login_verify(request, username):
    up = UserProfile.objects.get(user__username=username)
    send_email_with_link(up.user, purpose='signup', subject='Register rootpath confirm.')
    return HttpResponseRedirect(reverse('account:user_login'))


def login_verify_failed(request):
    return render(request, "account/login_verify_failed.html", context={
        'username': request.GET.get('username', default='null'),
        'email': request.GET.get('email', default='null')
    })


def forgot_passwd(request):
    if request.method == 'POST':
        print(request.POST)
        if 'email' in request.POST and 'username' in request.POST:
            u = User.objects.get(email=request.POST['email'], username=request.POST['username'])
            if u:
                send_email_with_link(u, purpose='reset', subject='Reset rootpath password')
            return HttpResponseRedirect(reverse('account:password_reset_done'))
        else:
            return HttpResponse('Sorry, the input of your username or email is invalid')
    else:
        form = ForgotPwForm()
        return render(request, 'account/forgot_password.html', {'form': form})


def verify(request, uidb64, token):
    # 根据解密后的 user_id 和 verify_code 获取对应的 Notice 记录
    user = get_user(uidb64)
    notice = get_object_or_404(Notice, user=user.id, token=token)
    print(notice.token,notice.used)
    # 判断链接是否已过期
    if notice.expired_time < timezone.now():
        return HttpResponse("Verification link has expired.")

    if notice.used:
        return HttpResponse("Verification link has been used.")

    # 处理验证逻辑，例如将 used 设置为 True
    notice.used = True
    notice.save()
    print('used',notice.token,notice.used)
    if notice.purpose == 'signup':
        user_profile = UserProfile.objects.get(user=user.id)
        if not user_profile:
            return HttpResponse("Verification failed. Please try to register again.")
        user_profile.is_verify = True
        user_profile.save()
        return redirect('account:user_login')
    elif notice.purpose == 'reset':
        return HttpResponseRedirect(
            reverse('account:password_reset_confirm', args=(uidb64, token))
        )


def password_change_done(request):
    return render(request, 'password_change_done.html')


@login_required(login_url='/account/login/')
def myself(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user,
                                                                        'userprofile') else UserProfile.objects.create(
        user=request.user)
    return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})


@login_required(login_url='/account/login/')
def myself_edit(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user, 'userprofile') \
        else UserProfile.objects.create(user=request.user)

    user_form = UserProfileForm(request.POST or None, instance=userprofile)

    if request.method == "POST":
        if user_form.is_valid():
            user_form.save()
            return redirect('/account/my-information/')
        else:
            return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})
    else:
        return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})


def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('/user_center/dashboard/'))
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        userprofile_form = UserProfileForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            print(new_user.email)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            new_profile = userprofile_form.save(commit=False)
            new_profile.user = new_user
            new_profile.save()
            send_email_with_link(new_user, purpose='signup', subject='Register rootpath confirm')
            return HttpResponseRedirect(reverse('account:register_confirm'))
        else:
            return HttpResponse('sorry, your username or password is not right')
    else:
        user_form = RegistrationForm()
        userprofile_form = UserProfileForm()
        return render(request, 'account/register.html', {'form': user_form, "profile": userprofile_form})


def register_confirm(request):
    return render(request, 'account/register_confirm.html')


def settings(request):
    return render(request, 'account/settings.html')


def contact_us(request):
    return render(request, 'account/contact_us.html')
