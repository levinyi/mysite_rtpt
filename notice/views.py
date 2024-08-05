# notice/views.py
from email.mime.image import MIMEImage
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from .models import Notice
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import re

def send_email(user, purpose):
    if isinstance(user, int):
        user = User.objects.get(id=user)
    subject = ''
    message = ''
    if purpose == 'notice_synthesized':
        subject = 'Notice synthesized'
        message = 'Your genes have been synthesized.'

    send_mail(
        subject,
        message,
        None,
        recipient_list=[user.email],  # 收件人邮箱
    )


def send_email_with_link(user, purpose, subject, message=""):
    """
    user: user model
    purpose: [
        ('reset', 'Reset'),
        ('verify', 'Verify'),
        ('login', 'Login'),
        ('signup', 'Signup'),
    ]
    subject: Subject of the email
    """
    try:
        # 创建 Notice 记录, 必须使用 Notice.create 才能正确 create 模型
        notice = Notice.create(user=user, verify_type="Email", purpose=purpose)
        notice.save()
    except ValidationError as e:
        return False

    # 发送邮件
    send_mail(
        subject,
        message
        + f" Click the link to verify your {purpose}: {settings.BASE_URL}{notice.get_verification_url()}",
        None,
        recipient_list=[user.email],  # 收件人邮箱
    )
    return True

def test(request):
    return render(request, 'notice/email_input_list.html')


import os
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
from django.conf import settings

def images_to_html(images):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Email</title>
        <style>
            .image-container { margin-bottom: 20px; text-align: center; }
            img { max-width: 100%; height: auto; }
        </style>
    </head>
    <body>
        {% for image in images %}
            <div class="image-container">
                <img src="cid:{{ image }}">
            </div>
        {% endfor %}
    </body>
    </html>
    '''

    from jinja2 import Template
    template = Template(html_template)
    html_content = template.render(images=[f'image_{i}' for i in range(len(images))])
    return html_content, images

def send_html_email_with_images(to_email, images, name, subject):
    content = f'Hello {name},<br><br>Here are some information:<br><br>'
    html_content, image_files = images_to_html(images)
    text_content = strip_tags(html_content)  # 提取纯文本部分
    text_content = content + text_content

    email = EmailMultiAlternatives(subject, text_content, None, [to_email])
    email.attach_alternative(html_content, "text/html")

    for i, image_file in enumerate(image_files):
        email_img = MIMEImage(image_file.read())
        email_img.add_header('Content-ID', f'<image_{i}>')
        email.attach(email_img)

    email.send()


def send_html_email(to_email, name, subject):
    to = to_email

    # 渲染HTML模板
    html_content = render_to_string('notice/email_template.html', {'name': name})
    text_content = strip_tags(html_content)  # 提取纯文本部分

    # 创建邮件对象
    email = EmailMultiAlternatives(subject, text_content, None, to)
    email.attach_alternative(html_content, "text/html")

    # 发送邮件
    email.send()

def send_email(request):
    if request.method == 'POST':
        to_email = request.POST.get('to_email')
        to_email = re.split(r'[;, ]+', to_email.strip())
        print(to_email)
        name = request.POST.get('to_name')
        subject = request.POST.get('subject')
        send_html_email(to_email, name, subject)
        return render(request, 'notice/email_sent.html')
    return render(request, 'notice/email_form.html')