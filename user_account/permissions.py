"""
后台管理员判定 + 公司邮箱判定（单一来源）。

“后台管理员”= 超级用户 / staff / 属于 SecondaryAdminGroup（组名可用
settings.SUPER_MANAGE_GROUP 覆盖）。super_manage 访问控制与“上传载体归属”
都用这个判断，避免各处口径不一致。
"""
from django.conf import settings

_DEFAULT_COMPANY_DOMAINS = ('rootpath.com.cn', 'rootpathgx.com')


def admin_group_name():
    return getattr(settings, 'SUPER_MANAGE_GROUP', 'SecondaryAdminGroup')


def is_backend_admin(user):
    """user 是否具有后台管理员权限。"""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name=admin_group_name()).exists()


def vector_owner_for(user):
    """按上传者身份决定新建 vector 的归属：管理员 -> None（公司）；客户 -> 本人。"""
    return None if is_backend_admin(user) else user


def company_sso_domains():
    """公司邮箱域名（这些域名禁止用户名密码注册，须走飞书 SSO）。settings 可覆盖；空 = 关闭。"""
    raw = getattr(settings, 'COMPANY_SSO_EMAIL_DOMAINS', _DEFAULT_COMPANY_DOMAINS)
    return tuple(
        str(d).strip().lower().lstrip('@').rstrip('.')
        for d in raw if str(d).strip()
    )


def is_company_sso_email(email):
    """邮箱是否属于公司域名（含子域名）。"""
    email = (email or '').strip().lower()
    if '@' not in email:
        return False
    domain = email.rsplit('@', 1)[-1].rstrip('.')
    for d in company_sso_domains():
        if domain == d or domain.endswith('.' + d):
            return True
    return False
