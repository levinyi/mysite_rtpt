from django import forms
from .models import UserProfile


class CustomSignupForm(forms.Form):
    """注册页扩展字段：手机 + 公司（均选填）。

    settings.ACCOUNT_SIGNUP_FORM_CLASS 指向本类，字段会自动出现在
    allauth 注册页（signup.html 用 {% for field in form %} 遍历渲染）。
    signup() 在用户创建后把值写进 UserProfile。
    """
    phone = forms.CharField(
        max_length=200, required=False, label='Phone',
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'}),
    )
    company = forms.CharField(
        max_length=254, required=False, label='Company / Institute',
        widget=forms.TextInput(attrs={'placeholder': 'Company / Institute (optional)'}),
    )
    # 蜜罐字段：页面上对真人隐藏（signup.html 把它渲染到屏幕外），脚本/机器人通常会
    # 把所有 input 一并填上 → 填了即判为机器人。与邮箱域名无关，能挡换用 gmail/yahoo
    # 等真实域名的批量注册。真人留空 → 校验通过。
    website = forms.CharField(
        required=False, label='',
        widget=forms.TextInput(attrs={
            'autocomplete': 'off', 'tabindex': '-1', 'aria-hidden': 'true',
            'style': 'position:absolute!important;left:-9999px!important;height:0;',
        }),
    )

    def clean_website(self):
        if (self.cleaned_data.get('website') or '').strip():
            # 不暴露真实原因，避免提示机器人；表单整体失败 → 不建号、不发通知。
            raise forms.ValidationError('注册校验失败，请重试。')
        return ''

    def clean_phone(self):
        # phone 在模型上是 unique，注册时若与已有号码重复要友好报错（而非 500）
        phone = (self.cleaned_data.get('phone') or '').strip()
        if phone and UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError('该手机号已被注册')
        return phone

    def signup(self, request, user):
        # 用户已创建并保存（UserProfile 由 post_save 信号建好），这里补填扩展字段。
        # 空手机保持 NULL，避免多个空字符串撞 unique 约束。
        profile, _ = UserProfile.objects.get_or_create(user=user)
        phone = (self.cleaned_data.get('phone') or '').strip()
        company = (self.cleaned_data.get('company') or '').strip()
        if phone:
            profile.phone = phone
        if company:
            profile.company = company
        profile.save()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'company', 'department', 'phone', 'photo', 'shipping_address']
        

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

