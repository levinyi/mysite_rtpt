from django.db import models
from django.contrib.auth.models import User


# Create your models here.
# class Account(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
#     first_name = models.CharField(max_length=200)
#     last_name = models.CharField(max_length=200)
#     email = models.EmailField(max_length=254)
#     company = models.CharField(max_length=254)
#     department = models.CharField(max_length=200, blank=True)
#     phone = models.CharField(max_length=200, null=True)
#     register_time = models.DateField(auto_now_add=True)
#     photo = models.ImageField(blank=True)
#     level = models.SmallIntegerField(default=1, blank=True)
#     shipping_address = models.CharField(max_length=500)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(max_length=254)
    company = models.CharField(max_length=254)
    department = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=200, null=True, unique=True)
    register_time = models.DateField(auto_now_add=True)
    photo = models.ImageField(blank=True)
    level = models.SmallIntegerField(default=1, blank=True)
    shipping_address = models.CharField(max_length=500)
    is_verify = models.BooleanField(default=False)

    def confirm_verify(self):
        self.is_verify = True
        self.save()

    def __str__(self):
        return f'user {self.user.username}'
