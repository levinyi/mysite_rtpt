"""
super_manage 管理后台访问控制中间件（修复越权访问漏洞）。

历史问题：super_manage 各视图本应只允许「二级管理员」(SecondaryAdminGroup) 访问，
但视图上的 `@is_secondary_admin_required` 被逐个注释掉，只剩 `@login_required`，
导致**任何登录用户**（包括注册并验证邮箱的机器人）都能直达 /super_manage/ 读到
全站订单 / 用户资料 / 载体序列，甚至改删数据。

这里在「一个总入口」统一拦截：凡 /super_manage/ 路径，要求请求者满足
is_superuser / is_staff / 属于 SecondaryAdminGroup 之一；否则 403。
未登录则跳登录页。新增的 super_manage 视图自动受保护，不会再漏。

允许的组名可用 settings.SUPER_MANAGE_GROUP 覆盖（默认 'SecondaryAdminGroup'）。
"""
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

SUPER_MANAGE_PREFIX = '/super_manage/'


def _admin_group():
    return getattr(settings, 'SUPER_MANAGE_GROUP', 'SecondaryAdminGroup')


def _access_state(user):
    """返回 'anon' / 'denied' / 'allowed'。"""
    if not user.is_authenticated:
        return 'anon'
    if user.is_superuser or user.is_staff:
        return 'allowed'
    if user.groups.filter(name=_admin_group()).exists():
        return 'allowed'
    return 'denied'


class SuperManageAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(SUPER_MANAGE_PREFIX) or path == '/super_manage':
            state = _access_state(request.user)
            if state == 'anon':
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if state == 'denied':
                return HttpResponseForbidden('No permission')
        return self.get_response(request)
