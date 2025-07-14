from user_account.views import is_secondary_admin
from user_account.models import UserProfile

# Desc: 自定义上下文处理器
def user_context(request):
    # 在每个请求中添加 'user' 到上下文中
    is_secondary_admin_user = is_secondary_admin(request.user)
    user_profile = None
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return {'user': request.user, 'is_secondary_admin': is_secondary_admin_user, 'user_profile': user_profile}
