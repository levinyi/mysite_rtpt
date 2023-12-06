from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import RegistrationForm, UserProfileForm
from .models import UserProfile

# Create your views here.
# def register_old(request):
#     if request.user.is_authenticated:
#         return HttpResponseRedirect(reverse('home'))
#     if request.method == 'POST':
#         user_form = RegistrationForm(request.POST)
#         userprofile_form = UserProfileForm(request.POST)
#         if user_form.is_valid()*userprofile_form.is_valid():
#             new_user = user_form.save(commit=False)
#             new_user.set_password(user_form.cleaned_data['password'])
#             new_user.save()
#             new_profile = userprofile_form.save(commit=False)
#             new_profile.user = new_user
#             new_profile.save()
#             return HttpResponseRedirect(reverse('account:user_login'))
#         else:
#             return HttpResponse('sorry, your username or password is not right')
#     else:
#         user_form = RegistrationForm()
#         userprofile_form = UserProfileForm()
#         return render(request, 'account/register.html',{'form':user_form, "profile":userprofile_form})

@login_required(login_url='/account/login/')
def myself(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user, 'userprofile') else UserProfile.objects.create(user=request.user)
    return render(request, "account/myself.html", {"user":request.user, "userprofile":userprofile})

@login_required(login_url='/account/login/')
def myself_edit(request):
    userprofile = UserProfile.objects.get(user=request.user) if hasattr(request.user, 'userprofile') else UserProfile.objects.create(user=request.user)
    print(userprofile.email)
    print(userprofile.user)
    user_form = UserProfileForm(request.POST or None, instance=userprofile)
    
    if request.method == "POST":
        if user_form.is_valid():
            user_form.save()
            return redirect('/account/my-information/')
        else:
            return render(request, "account/myself.html", {"user":request.user, "userprofile":userprofile})
    else:
        return render(request, "account/myself.html", {"user":request.user, "userprofile":userprofile})

def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('/user_center/dashboard/'))
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        userprofile_form = UserProfileForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            new_profile = userprofile_form.save(commit=False)
            new_profile.user = new_user
            new_profile.save()
            return HttpResponseRedirect(reverse('account:user_login'))
        else:
            return HttpResponse('sorry, your username or password is not right')
    else:
        user_form = RegistrationForm()
        userprofile_form = UserProfileForm()
        return render(request, 'account/register.html',{'form':user_form, "profile":userprofile_form})
    
def settings(request):
    return render(request, 'account/settings.html')

def contact_us(request):
    return render(request, 'account/contact_us.html')