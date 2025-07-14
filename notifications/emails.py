# notifications/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import Group

def send_templated_email(subject, recipient_list, template_name, context=None):
    """
    通用的邮件发送函数：根据模板渲染出 HTML，再用EmailMultiAlternatives发邮件。
    :param subject: 邮件主题
    :param recipient_list: 收件人列表(list或tuple)
    :param template_name: HTML模板名称(如 'emails/register_user.html')
    :param context: dict, 模板渲染上下文
    """
    if context is None:
        context = {}

    # 纯文本(可选): 如果你模板里只写HTML，这里也可以改成简短的文本
    text_content = "请使用支持HTML的邮件客户端查看内容"

    # 渲染HTML模板
    html_content = render_to_string(template_name, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

# checked
def get_group_emails(group_name):
    """
    返回某个用户组内所有活跃用户的邮箱列表
    """
    try:
        group = Group.objects.get(name=group_name)
        users = group.user_set.filter(is_active=True)
        user_emails = []
        for user in users:
            profile = user.userprofile
            user_emails.append(profile.email)
        return user_emails
    except Group.DoesNotExist:
        return []

# =============== 专用函数示例 ================

def send_registration_user_email(user, verify_link):
    """
    用户注册后，发给用户自己一封验证邮件
    """
    subject = "欢迎注册 - 请点击链接完成验证"
    template_name = 'emails/register_user.html'
    context = {
        'user': user,
        'verify_link': verify_link,
    }

    send_templated_email(subject, [user.userprofile.email], template_name, context)

def send_registration_staff_notify(user):
    """
    用户注册后，通知管理员(或某一组人员)
    """
    subject = f"新用户注册 - {user.username}"
    template_name = 'emails/register_staff.html'
    context = {'user': user}
    staff_emails = get_group_emails("StaffGroup")  # 例如你定义了一个叫 StaffGroup 的 group
    if staff_emails:
        send_templated_email(subject, staff_emails, template_name, context)

def send_password_reset_user_email(user, reset_link):
    subject = "密码重置链接"
    template_name = 'emails/password_reset_user.html'
    context = {'user': user, 'reset_link': reset_link}
    send_templated_email(subject, [user.userprofile.email], template_name, context)


def send_order_created_user_email(order):
    subject = f"订单已创建 - #{order.inquiry_id}"
    template_name = 'emails/order_created_user.html'
    context = {'order': order}
    user = order.user
    user_profile = user.userprofile
    email = user_profile.email 
    send_templated_email(subject, [email], template_name, context)

def send_order_created_staff_notify(order):
    subject = f"新订单通知 - #{order.inquiry_id}"
    template_name = 'emails/order_created_staff.html'
    context = {'order': order}
    staff_emails = get_group_emails("StaffGroup")
    if staff_emails:
        send_templated_email(subject, staff_emails, template_name, context)

def send_vector_uploaded_user_email(vector):
    subject = f"文件已上传 - {vector.vector_file}"
    template_name = 'emails/vector_uploaded_user.html'
    context = {'vector': vector}
    user = vector.user
    user_profile = user.userprofile
    email = user_profile.email
    send_templated_email(subject, [email], template_name, context)

def send_vector_uploaded_staff_notify(vector):
    subject = f"用户 {vector.user.username} 上传了文件 - {vector.vector_file}"
    template_name = 'emails/vector_uploaded_staff.html'
    context = {'vector': vector}
    staff_emails = get_group_emails("TechStaffGroup")
    if staff_emails:
        send_templated_email(subject, staff_emails, template_name, context)

def send_vector_approved_user_email(vector):
    subject = f"文件已审核通过 - {vector.filename}"
    template_name = 'emails/vector_approved_user.html'
    context = {'vector': vector}
    send_templated_email(subject, [vector.user.userprofile.email], template_name, context)

def send_vector_approved_staff_notify(vector):
    subject = f"文件审核完成 - {vector.filename}"
    template_name = 'emails/vector_approved_staff.html'
    context = {'vector': vector}
    staff_emails = get_group_emails("TechStaffGroup")
    if staff_emails:
        send_templated_email(subject, staff_emails, template_name, context)

