"""
把现有用户的邮箱标记为「已验证」，用于切到
ACCOUNT_EMAIL_VERIFICATION=mandatory 之前的一次性 backfill，
避免从没验证过的老用户 / admin / demo 被锁在登录外。

做两件事（均幂等，可重复运行）：
  1. 为每个有邮箱的用户创建 / 更新 allauth EmailAddress，置 verified=True
     （用户若还没有 primary 邮箱，则把这条设为 primary）；
  2. 顺带把对应 UserProfile.is_verify 置 True（可用 --no-set-verify 关闭）。

用法：
    python manage.py backfill_verified_emails --dry-run   # 只预览，不写库
    python manage.py backfill_verified_emails             # 实际执行

切 mandatory 流程：先跑本命令 → 再在 .env 设 ACCOUNT_EMAIL_VERIFICATION=mandatory → 重启。
"""
import contextlib

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from allauth.account.models import EmailAddress
from user_account.models import UserProfile


class Command(BaseCommand):
    help = "把现有用户的邮箱标记为已验证（allauth EmailAddress），切 mandatory 前避免老用户被锁。"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='只预览将要做的改动，不写数据库',
        )
        parser.add_argument(
            '--no-set-verify', action='store_true',
            help='不要顺带把 UserProfile.is_verify 置 True（默认会置）',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        set_verify = not options['no_set_verify']
        User = get_user_model()

        created = verified = profiles = skipped = 0

        ctx = contextlib.nullcontext() if dry else transaction.atomic()
        with ctx:
            for user in User.objects.all().order_by('id'):
                email = (user.email or '').strip()
                if not email:
                    skipped += 1
                    self.stdout.write(f"  - {user.username}: 跳过（无邮箱）")
                    continue

                has_primary = EmailAddress.objects.filter(user=user, primary=True).exists()
                ea = EmailAddress.objects.filter(user=user, email__iexact=email).first()

                if ea is None:
                    created += 1
                    action = "新建并标记已验证"
                    if not dry:
                        EmailAddress.objects.create(
                            user=user, email=email,
                            verified=True, primary=not has_primary,
                        )
                elif not ea.verified:
                    verified += 1
                    action = "已存在 → 标记已验证"
                    if not dry:
                        ea.verified = True
                        if not has_primary:
                            ea.primary = True
                        ea.save(update_fields=['verified', 'primary'])
                else:
                    action = "已是已验证，跳过"

                if set_verify:
                    profile = UserProfile.objects.filter(user=user).first()
                    if profile is None or not profile.is_verify:
                        profiles += 1
                        if not dry:
                            profile, _ = UserProfile.objects.get_or_create(user=user)
                            profile.is_verify = True
                            profile.save(update_fields=['is_verify'])

                self.stdout.write(f"  - {user.username} <{email}>: {action}")

        prefix = "[DRY-RUN] " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}完成：EmailAddress 新建 {created}、补标记已验证 {verified}；"
            f"UserProfile.is_verify 置 True {profiles}；跳过(无邮箱) {skipped}。"
        ))
        if dry:
            self.stdout.write("（dry-run 未写库，去掉 --dry-run 实际执行）")
