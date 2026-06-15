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

