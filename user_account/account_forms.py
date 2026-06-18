"""
本地（用户名密码）注册表单。单独成模块、惰性加载，避免与
allauth.account.forms 的循环导入（user_account.forms 因 ACCOUNT_SIGNUP_FORM_CLASS
会被 allauth 在加载期提前导入，故不能在那里 import allauth.account.forms）。

ACCOUNT_FORMS['signup'] 指向本类：拦截公司邮箱（rootpath）的用户名密码注册，
引导其改用飞书登录。社交 / 飞书注册用 socialaccount 自己的表单，**不经过本类**，
因此飞书用户的 rootpath 邮箱照常可注册，不受影响。
"""
from django import forms
from allauth.account.forms import SignupForm

from .permissions import is_company_sso_email


class LocalSignupForm(SignupForm):
    def clean_email(self):
        email = super().clean_email()  # 含 adapter.clean_email（一次性邮箱拦截）
        if is_company_sso_email(email):
            raise forms.ValidationError(
                '公司邮箱（rootpath）无需注册，请直接使用页面上的「飞书登录」。'
            )
        return email
