"""
自定义 allauth 账号 Adapter：注册时拦截一次性 / 抛弃型邮箱域名，挡机器人批量注册。

settings.ACCOUNT_ADAPTER 指向本类。clean_email 会被「本地注册表单」和「社交注册表单」
共用，所以这里只放"对两者都该拦"的规则（一次性邮箱）。

⚠️ 公司邮箱（rootpath）禁止注册的规则**不在这里**——它只该作用于用户名密码注册，
若放这里会误伤飞书的社交注册表单（飞书用户的邮箱正是 rootpath）。该规则放在
仅本地注册表单 user_account.forms.LocalSignupForm（ACCOUNT_FORMS['signup']）里。
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
