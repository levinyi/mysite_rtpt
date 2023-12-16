from account.views import is_secondary_admin

# Desc: 自定义上下文处理器
def user_context(request):
    # 在每个请求中添加 'user' 到上下文中
    is_secondary_admin_user = is_secondary_admin(request.user)
    return {'user': request.user, 'is_secondary_admin': is_secondary_admin_user}
