"""
一次性 / 抛弃型邮箱域名黑名单（精选），用于注册时拦截机器人批量注册。

- 触发本次事件的 immenseignite.info 已收录。
- 可在 settings.DISPOSABLE_EMAIL_DOMAINS_EXTRA（list/可迭代）追加更多域名，
  无需改代码、无需重建镜像（改 settings 即可）。
- 子域名也会命中父域名（如 x.mailinator.com -> mailinator.com）。
- 匹配不区分大小写。
"""
from django.conf import settings

# 精选常见一次性邮箱域名（覆盖绝大多数批量注册脚本所用服务）。
# 漏网的由「强制邮箱验证 mandatory」兜底——拿不到验证邮件 = 账号不可用。
_BLOCKLIST = {
    # —— 本次攻击源 ——
    'immenseignite.info',
    # —— 常见一次性 / 抛弃型邮箱 ——
    '10minutemail.com', '10minutemail.net', '20minutemail.com', '33mail.com',
    '1secmail.com', '1secmail.net', '1secmail.org',
    'mailinator.com', 'mailinator.net', 'mailinator.org',
    'guerrillamail.com', 'guerrillamail.info', 'guerrillamail.net',
    'guerrillamail.org', 'guerrillamail.biz', 'guerrillamailblock.com',
    'sharklasers.com', 'grr.la', 'spam4.me',
    'temp-mail.org', 'temp-mail.io', 'tempmail.com', 'tempmailo.com',
    'tempr.email', 'tempail.com', 'tempemail.com', 'tmpmail.org', 'tmpmail.net',
    'tmpeml.com', 'minuteinbox.com', 'mailpoof.com', 'moakt.com',
    'throwawaymail.com', 'getnada.com', 'nada.email', 'getairmail.com',
    'maildrop.cc', 'dispostable.com', 'discard.email', 'discardmail.com',
    'yopmail.com', 'yopmail.net', 'yopmail.fr',
    'mailnesia.com', 'trashmail.com', 'trashmail.de', 'trash-mail.com',
    'mytemp.email', 'fakeinbox.com', 'fakemailgenerator.com', 'fakemail.net',
    'mohmal.com', 'emailondeck.com', 'emailfake.com', 'mailcatch.com',
    'tempinbox.com', 'inboxbear.com', 'inboxkitten.com', 'mailtemp.info',
    'spambog.com', 'spambox.us', 'mintemail.com', 'mailexpire.com',
    'mt2015.com', 'mailforspam.com', 'spamgourmet.com', 'mailsac.com',
    'mailde.de', 'einrot.com', 'cuvox.de', 'dayrep.com', 'fleckens.hu',
    'gustr.com', 'jourrapide.com', 'rhyta.com', 'superrito.com',
    'teleworm.us', 'armyspy.com', 'mvrht.com', 'mvrht.net', 'tafmail.com',
    'wegwerfmail.de', 'wegwerfmail.net', 'mailnull.com', 'incognitomail.org',
    'burnermail.io', 'anonbox.net', 'mailcuk.com', 'luxusmail.org',
    'kzccv.com', 'qiott.com', 'wwjmp.com', 'esiix.com', 'xojxe.com', 'yoggm.com',
    'altmails.com',
}


def _extra():
    extra = getattr(settings, 'DISPOSABLE_EMAIL_DOMAINS_EXTRA', None) or []
    return {
        str(d).strip().lower().lstrip('@').rstrip('.')
        for d in extra if str(d).strip()
    }


def is_disposable_domain(domain):
    """域名（不含 @）是否属于一次性邮箱黑名单（含子域名匹配）。"""
    domain = (domain or '').strip().lower().rstrip('.')
    if not domain:
        return False
    blocklist = _BLOCKLIST | _extra()
    if domain in blocklist:
        return True
    # 子域名命中父域名：a.b.mailinator.com -> mailinator.com
    parts = domain.split('.')
    for i in range(1, len(parts) - 1):
        if '.'.join(parts[i:]) in blocklist:
            return True
    return False


def is_disposable_email(email):
    """完整邮箱地址是否为一次性 / 抛弃型邮箱。"""
    email = (email or '').strip().lower()
    if '@' not in email:
        return False
    return is_disposable_domain(email.rsplit('@', 1)[-1])
