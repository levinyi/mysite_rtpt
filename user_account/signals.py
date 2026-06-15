from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import email_confirmed
from .models import UserProfile
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        print(f"user {instance.username} created, creating user profile")
        UserProfile.objects.create(user=instance)
    else:
        # 如果是更新，但没有UserProfile，也可以自动创建
        print(f"user {instance.username} updated, ensuring user profile exists")
        UserProfile.objects.get_or_create(user=instance)


@receiver(email_confirmed)
def mark_profile_verified(request, email_address, **kwargs):
    """用户点击邮箱确认链接后，把 UserProfile.is_verify 置 True（与 allauth 邮箱验证联动）。"""
    user = email_address.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.is_verify:
        profile.is_verify = True
        profile.save(update_fields=['is_verify'])

