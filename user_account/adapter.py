"""
自定义 allauth 账号 Adapter：注册时拦截一次性 / 抛弃型邮箱域名，挡机器人批量注册。

settings.ACCOUNT_ADAPTER 指向本类。allauth 的注册表单在校验 email 时会调用
adapter.clean_email()，因此这里是拦截非法邮箱的中心入口（对普通注册与社交注册都生效）。
"""
from allauth.account.adapter import DefaultAccountAdapter
from django import forms

from .disposable_domains import is_disposable_email


class AntiBotAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        if is_disposable_email(email):
            raise forms.ValidationError(
                '该邮箱域名不被接受，请使用常用的企业 / 个人邮箱注册。'
            )
        return email
