"""
自定义 allauth 账号 Adapter：
1) 注册时拦截一次性 / 抛弃型邮箱域名，挡机器人批量注册；
2) 拦截公司邮箱（rootpath）的用户名密码注册，引导其改用飞书登录。

settings.ACCOUNT_ADAPTER 指向本类。allauth 的本地注册表单在校验 email 时会调用
adapter.clean_email()，因此这里是拦截入口。

⚠️ 飞书等社交登录默认 SOCIALACCOUNT_AUTO_SIGNUP=True，自动建号走
save_user(form=None)，**不经过 signup 表单、不调用 clean_email**，因此下面对公司
邮箱的拦截只作用于「用户名密码注册」，不影响飞书登录建号。
"""
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django import forms

from .disposable_domains import is_disposable_email

# 公司邮箱域名（这些域名禁止用户名密码注册，必须走飞书 SSO）。可用 settings 覆盖。
_DEFAULT_COMPANY_DOMAINS = ('rootpath.com.cn', 'rootpathgx.com')


def _company_domains():
    return tuple(
        str(d).strip().lower().lstrip('@').rstrip('.')
        for d in getattr(settings, 'COMPANY_SSO_EMAIL_DOMAINS', _DEFAULT_COMPANY_DOMAINS)
        if str(d).strip()
    )


class AntiBotAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        domain = email.rsplit('@', 1)[-1].lower().strip().rstrip('.')

        # 1) 一次性 / 抛弃型邮箱：直接拒。
        if is_disposable_email(email):
            raise forms.ValidationError(
                '该邮箱域名不被接受，请使用常用的企业 / 个人邮箱注册。'
            )

        # 2) 公司邮箱：不允许用户名密码注册，引导走飞书登录。
        for d in _company_domains():
            if domain == d or domain.endswith('.' + d):
                raise forms.ValidationError(
                    '公司邮箱（rootpath）无需注册，请直接使用页面上的「飞书登录」。'
                )

        return email
