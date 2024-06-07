from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from notice.models import Notice
from notice.views import send_email_with_link, send_sms_with_code
from .forms import RegistrationForm, UserProfileForm, ForgotPwForm, PhoneCodeForm
from .models import UserProfile
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.shortcuts import render

# decorators.py
from django.shortcuts import redirect
from functools import wraps


def custom_password_reset_confirm(request, uidb64, token):
    """
    处理用户的密码重置请求。

    POST：从POST数据中获取新密码，然后使用这个新密码重置用户的密码。
    如果成功，用户会被重定向到密码重置完成的页面。

    GET：这个视图会使用Django的PasswordResetConfirmView来处理请求。

    参数:
    request -- Django的HttpRequest对象。
    uidb64 -- 用户ID的base64编码。
    token -- 用于验证密码重置请求的token。
    token和uidb64都是从密码重置链接中获取的，生成方法和Django的
    PasswordResetTokenGenerator类一致，在Notice Model中有实现

    返回:
    HttpResponse对象，根据请求类型和处理结果返回相应页面。
    """

    # 处理密码重置确认表单提交
    if request.method == 'POST':
        user = Notice.get_user_from_uidb64(uidb64)
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
        """
        处理用户的登录请求的额外逻辑，如判断邮箱和手机号验证状态。
        从POST数据中获取用户名和密码，然后验证这些信息。
        如果验证通过，它会检查用户的邮箱和手机号是否已经验证。
        根据邮箱和手机号的验证状态，用户可能会被重定向到不同的页面。
        """
        # 调用原始的登录视图，获取登录表单的验证结果
        response = view_func(request, *args, **kwargs)
        # 如果用户名和密码验证通过
        if response.status_code == 302:
            up = UserProfile.objects.get(user__username=request.POST['username'])
            u = up.user
            if not up.is_verify:
                # 邮箱和手机号都没有，提醒绑定其中一个，或其它，目前是会直接登陆进去
                if not u.email and not up.phone:
                    return response
                # 填了邮箱，没手机号
                elif u.email and not up.phone:
                    target_url = reverse('account:email_not_verify')
                    params = {'username': u.username, 'email': u.email}
                    target_url_with_params = f'{target_url}?{urlencode(params)}'
                    return HttpResponseRedirect(target_url_with_params)
                # 填了手机号，没邮箱
                elif not u.email and up.phone:
                    target_url = reverse('account:phone_not_verify') 
                    params = {'phone': up.phone, 'code': '', 'username':u.username}
                    # 将参数编码并添加到 URL
                    target_url_with_params = f'{target_url}?{urlencode(params)}'
                    # 使用 HttpResponseRedirect 跳转到目标 URL
                    return HttpResponseRedirect(target_url_with_params)
                # 两者都填了，选一个进行验证
                else:
                    # Todo:完善选择其一进行验证页面
                    target_url = reverse('account:email_not_verify') 
                    params = {'username': u.username, 'email': u.email}
                    target_url_with_params = f'{target_url}?{urlencode(params)}'
                    return HttpResponseRedirect(target_url_with_params)
        return response

    return _wrapped_view


def resend_login_verify(request, username, verify_type):
    """
    重新发送登录验证。

    根据提供的验证类型（邮箱或手机），重新发送验证链接或验证码给用户。
    如果验证类型是邮箱，会发送一个包含验证链接的邮件给用户。
    如果验证类型是手机，会发送一个包含验证码的短信给用户。

    参数:
    request -- Django的HttpRequest对象，包含了这个请求的所有信息。
    username -- 需要验证的用户的用户名。
    verify_type -- 验证类型，可以是'email'或'phone'。

    返回:
    如果验证类型是邮箱，返回一个重定向到登录页面的HttpResponseRedirect对象。
    如果验证类型是手机，返回一个包含发送状态的JsonResponse对象。
    如果验证类型不是'email'或'phone'，抛出一个Http404异常。
    """
    print(request, username, verify_type)
    if verify_type is None:
        raise Http404('Not Found.')

    ty = verify_type.lower()
    up = UserProfile.objects.get(user__username=username)
    if ty == 'email':
        send_email_with_link(up.user, purpose='signup', subject='Register rootpath confirm.')
        return HttpResponseRedirect(reverse('account:user_login'))
    elif ty == 'phone':
        if send_sms_with_code(up.user, purpose='signup'):
            return JsonResponse(data={
                'status': 'success'
            })
        else:
            return JsonResponse(data={
                'status': 'error'
            })

    raise Http404('Not Found.')


def email_not_verify(request):
    return render(request, "account/email_not_verify.html", context={
        'username': request.GET.get('username', default='null'),
        'email': request.GET.get('email', default='null')
    })


def phone_not_verify(request):
    """
    处理手机未验证的用户请求。

    对于POST请求，验证提交的验证码并根据验证结果进行相应处理。
    对于非POST请求，渲染验证码输入页面。

    参数:
    request -- Django的HttpRequest对象。

    返回:
    一个HttpResponse对象，渲染了一个页面，显示用户的用户名和手机。
    """
    if request.POST:
        form = PhoneCodeForm(request.POST)
    else:
        form = PhoneCodeForm({
            'phone': request.GET.get('phone',default='null'),
            'username': request.GET.get('username',default='null'),
        })
    if request.method == "POST":
        if 'phone' not in request.POST or 'code' not in request.POST:
            return

        status, notice = Notice.verify_code(phone=form.data.get('phone'), code=form.data.get('code'))
        if status:
            UserProfile.objects.filter(user=notice.user).update(is_verify=True)
            return redirect('account:user_login')
        else:
            return render(request, "account/phone_not_verify.html",context={
                'form': form,
                'hidden_failed': False
            })
    return render(request, "account/phone_not_verify.html", context={
        'form':form,
        'hidden_failed':True
    })


def forgot_passwd(request):
    """
    处理用户忘记密码的请求。

    参数:
    request -- Django的HttpRequest对象。

    返回:
    HttpResponse对象，根据请求类型和验证结果渲染相应页面。
    """
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


@require_GET
def verify(request, uidb64, token):
    """
    验证用户的链接。

    参数:
    request -- Django的HttpRequest对象。
    uidb64 -- 用户的id，经过base64编码。
    token -- 用户的token。

    返回:
    HttpResponseRedirect对象，根据验证结果重定向到相应页面。
    """
    # 根据解密后的 user_id 和 verify_code 获取对应的 Notice 记录
    status, notice = Notice.verify_link(uidb64, token)
    if not status:
        raise Http404('The link has expired.')

    if notice.purpose == 'signup':
        user_profile = get_object_or_404(UserProfile, user=notice.user.id)
        user_profile.is_verify = True
        user_profile.save()
        return redirect('account:user_login')
    elif notice.purpose == 'reset':
        return HttpResponseRedirect(
            reverse('account:password_reset_confirm', args=(notice.get_uidb64(), notice.token))
        )


def password_change_done(request):
    return render(request, 'password_change_done.html')


@login_required(login_url='/account/login/')
def myself(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user,'userprofile') else UserProfile.objects.create(user=request.user)
    return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})


@login_required(login_url='/account/login/')
def myself_edit(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user, 'userprofile') \
        else UserProfile.objects.create(user=request.user)

    user_form = UserProfileForm(request.POST or None, instance=userprofile)
    if request.method == "POST":
        if user_form.is_valid():
            up = user_form.save()
            # Email同时写入user表
            User.objects.filter(id=up.user.id).update(email=user_form.data.get('email'))
            return redirect('/account/my-information/')
        else:
            return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})
    else:
        return render(request, "account/myself.html", {"user": request.user, "userprofile": userprofile})


def avatar_edit(request):
    if request.method == 'POST':
        userid = request.POST.get('userid')
        imagePath = request.POST.get('imagePath')
        print(f"userid:{userid}, imagePath:{imagePath}")
        UserProfile.objects.filter(user_id=userid).update(photo=imagePath)
        return HttpResponse('success')
    else:
        return HttpResponse('error')

def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('/user_center/dashboard/'))
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        userprofile_form = UserProfileForm(request.POST)
        # if user_form.is_valid() and userprofile_form.is_valid(): 若添加userprofile_form.is_valid会导致无法验证通过
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            new_profile = UserProfile.objects.create(user=new_user)
            new_profile.company = userprofile_form.data.get('company')
            new_profile.phone = userprofile_form.data.get('phone')
            new_profile.email = user_form.data.get('email')
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

def is_secondary_admin(user):
    """
    判断用户是否是二级管理员。

    参数:
    user -- Django的User对象。

    返回:
    True或False，表示用户是否是二级管理员。
    """
    return user.is_authenticated and user.groups.filter(name='SecondaryAdminGroup').exists()