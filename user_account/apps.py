from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_account'

    def ready(self):
        # 在应用就绪时， 导入信号， 以便在信号触发时， 执行信号处理函数
        import user_account.signals
