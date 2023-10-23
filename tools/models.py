from django.db import models


class Tool(models.Model):
    """小工具管理"""
    name_alias = models.CharField(verbose_name="tool alias", max_length=64, blank=True)
    tool_name = models.CharField(verbose_name="tool name", max_length=64)
    tool_desc = models.TextField(verbose_name="description")
    tool_freq = models.SmallIntegerField(verbose_name="Use frequency",)
    tool_icon = models.ImageField(upload_to="static/img/tools_icon", blank=True)