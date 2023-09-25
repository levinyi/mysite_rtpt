from typing import Any
from django import forms
from django.contrib.auth.models import User

from .models import UserProfile
# from .models import UserProfile, UserInfo

class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Password'}),
        }

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("passwords don not match.")
        return cd['password2']
        

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'company', 
                  'department', 'phone', 'photo', 'shipping_address']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance.id:  # 如果 instance 存在，说明是修改，而不是创建新对象
            if UserProfile.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise forms.ValidationError("This email address has been used.")
        elif UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address has been used.")
        return email
