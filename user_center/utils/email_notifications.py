"""
邮件通知工具函数
用于发送序列优化相关的邮件通知
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_optimization_started_email(user, gene_objects, species, optimization_method):
    """
    发送优化开始的邮件通知

    参数:
        user: User对象
        gene_objects: GeneInfo对象列表
        species: Species对象
        optimization_method: 优化方法名称
    """
    try:
        # 准备邮件数据
        gene_names = [gene.gene_name for gene in gene_objects]
        gene_count = len(gene_objects)

        # 优化方法映射
        method_display = {
            'FbdSeqOnly': 'Method 1: Only Optimize Forbidden Sequences',
            'NoFoldingCheck': 'Method 2: Optimize Slightly (No Folding Check)',
            'LongGene_Relaxed': 'Method 3: Full Optimization (LongGene Relaxed)',
        }.get(optimization_method, optimization_method)

        # 构建购物车URL
        shopping_cart_url = f"{settings.BASE_URL}/user_center/view_cart/"

        # 渲染HTML邮件内容
        html_content = render_to_string('user_center/emails/optimization_started.html', {
            'user_name': user.username or user.email,
            'gene_count': gene_count,
            'gene_names': gene_names[:10],  # 最多显示10个
            'species': species.species_name,
            'optimization_method': method_display,
            'submitted_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'shopping_cart_url': shopping_cart_url,
        })

        # 创建邮件主题
        subject = f'Sequence Optimization Started - {gene_count} Gene(s)'

        # 创建邮件对象
        email = EmailMultiAlternatives(
            subject=subject,
            body=f'Your sequence optimization for {gene_count} gene(s) has started.',  # 纯文本备用内容
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        # 附加HTML内容
        email.attach_alternative(html_content, "text/html")

        # 发送邮件
        email.send(fail_silently=False)

        logger.info(f"Optimization started email sent to {user.email} for {gene_count} genes")
        return True

    except Exception as e:
        logger.error(f"Failed to send optimization started email to {user.email}: {str(e)}")
        return False


def send_optimization_completed_email(user, gene, optimization_status, old_penalty_score=None):
    """
    发送优化完成的邮件通知

    参数:
        user: User对象
        gene: GeneInfo对象
        optimization_status: 优化状态 ('Optimized' 或 'failed')
        old_penalty_score: 优化前的罚分（可选）
    """
    try:
        # 构建购物车URL
        shopping_cart_url = f"{settings.BASE_URL}/user_center/view_cart/"

        # 准备邮件数据
        context = {
            'user_name': user.username or user.email,
            'gene_name': gene.gene_name,
            'optimization_status': optimization_status,
            'sequence_status': gene.status,
            'penalty_score': gene.penalty_score,
            'old_penalty_score': old_penalty_score,
            'gc_content': gene.modified_gc_content,
            'completed_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'shopping_cart_url': shopping_cart_url,
        }

        # 如果优化失败，添加错误信息
        if optimization_status == 'failed':
            context['error_message'] = getattr(gene, 'optimization_message', 'Unknown error occurred')

        # 渲染HTML邮件内容
        html_content = render_to_string('user_center/emails/optimization_completed.html', context)

        # 创建邮件主题
        if optimization_status == 'Optimized':
            subject = f'✅ Optimization Completed - {gene.gene_name}'
        else:
            subject = f'❌ Optimization Failed - {gene.gene_name}'

        # 创建邮件对象
        email = EmailMultiAlternatives(
            subject=subject,
            body=f'Optimization for gene {gene.gene_name} has {optimization_status}.',  # 纯文本备用内容
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        # 附加HTML内容
        email.attach_alternative(html_content, "text/html")

        # 发送邮件
        email.send(fail_silently=False)

        logger.info(f"Optimization completed email sent to {user.email} for gene {gene.gene_name} (status: {optimization_status})")
        return True

    except Exception as e:
        logger.error(f"Failed to send optimization completed email to {user.email} for gene {gene.gene_name}: {str(e)}")
        return False


def send_bulk_optimization_summary_email(user, total_genes, success_count, failed_count):
    """
    发送批量优化汇总邮件通知（可选功能，用于批量优化全部完成后）

    参数:
        user: User对象
        total_genes: 总基因数
        success_count: 成功优化的数量
        failed_count: 失败的数量
    """
    try:
        # 构建购物车URL
        shopping_cart_url = f"{settings.BASE_URL}/user_center/view_cart/"

        subject = f'Batch Optimization Summary - {total_genes} Gene(s)'

        # 简单的HTML内容
        html_content = f"""
        <html>
        <body>
            <h2>Batch Optimization Summary</h2>
            <p>Dear {user.username or user.email},</p>
            <p>Your batch optimization has been completed.</p>
            <ul>
                <li>Total Genes: {total_genes}</li>
                <li>Successfully Optimized: {success_count}</li>
                <li>Failed: {failed_count}</li>
            </ul>
            <p><a href="{shopping_cart_url}">View Shopping Cart</a></p>
            <p>Best regards,<br>RootPath Gene Synthesis Team</p>
        </body>
        </html>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=f'Batch optimization completed: {success_count}/{total_genes} successful.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        logger.info(f"Batch optimization summary email sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send batch optimization summary email: {str(e)}")
        return False
