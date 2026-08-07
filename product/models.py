import hashlib
import re
from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils import timezone


def compute_seq_hash(sequence):
    """元件去重键：大写序列的 sha1。"""
    return hashlib.sha1((sequence or '').strip().upper().encode()).hexdigest()


class VectorFileStorage(FileSystemStorage):
    """
    自定义存储类，保留文件名中的括号。
    Django 默认的 get_valid_name 会去掉括号等特殊字符，
    但载体文件名中的括号包含抗性信息（如 pCVa999(Kan)-xxx.gb），必须保留。
    """
    def get_valid_name(self, name):
        # 只去掉真正危险的字符（路径分隔符、空字节等），保留括号
        name = name.replace('\x00', '')
        # 去掉路径中的目录遍历
        name = re.sub(r'[/\\]', '', name)
        # 去掉首尾空格
        name = name.strip()
        return name


vector_storage = VectorFileStorage()


# Create your models here.
def user_directory_path(instance, filename):
    # 文件将被上传到 MEDIA_ROOT/user_<id>/vector_file/<filename>
    if not instance.user:
        return f'user/vector_file/{filename}'
    else:
        return 'user_{0}/vector_file/{1}'.format(instance.user.id, filename)

class Vector(models.Model):
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE, null=True, blank=True)
    # on_delete=models.SET_NULL,这里有bug，设置成SET_NULL后，如果user被删除了，那么这个vector的user就会变成null, 就会变成公司的vector了，就会展示在公司的vector列表里面，这是不对的
    # 直接设置成CASCADE吧，这样user被删除了，这个vector也会被删除，这样就不会出现这个问题了

    vector_id = models.CharField(verbose_name="Vector_ID", max_length=200, null=True, blank=True)
    vector_name = models.CharField(verbose_name="Vector_name", max_length=200)
    vector_map = models.TextField(verbose_name="Vector_Seq", blank=True, default='')  # 这里的vector_map是指序列，不是图片
    NC5 = models.TextField(verbose_name="v5NC", blank=True, default='')
    NC3 = models.TextField(verbose_name="v3NC", blank=True, default='')
    iu20 = models.TextField(verbose_name="iu20", null=True, blank=True)
    id20 = models.TextField(verbose_name="id20", null=True, blank=True)
    i5NC = models.TextField(verbose_name="i5NC", null=True, blank=True, help_text="v5NC移位碱基")
    i3NC = models.TextField(verbose_name="i3NC", null=True, blank=True, help_text="v3NC移位碱基")
    vector_file = models.FileField(verbose_name="用户上传的vector文件", upload_to=user_directory_path, storage=vector_storage, null=True, blank=True)
    vector_png = models.ImageField(verbose_name="改造后的Vector_png", upload_to=user_directory_path, null=True, blank=True)

    vector_gb = models.FileField(verbose_name="genebank file", upload_to=user_directory_path, storage=vector_storage, null=True, blank=True)

    # 载体改造自动化设计相关字段
    cloning_method = models.CharField(verbose_name="克隆方法", max_length=50, null=True, blank=True, help_text="Gibson/GoldenGate/T4")
    # 改造 / 不改造是载体级属性：同一条客户质粒若两种都要，就建两条 Vector 记录。
    # 不改造(False)：只把 v5NC/v3NC/引物标注到图谱上，iU20–iD20 之间的序列保持原样，
    # 骨架靠酶切或外向 PCR 获得（散单常用）。目前仅支持 Gibson。
    modify_vector = models.BooleanField(
        verbose_name="是否改造载体", default=True,
        help_text="True=改造(iU20–iD20 之间替换为 Cm-ccdB)；False=不改造，仅标注设计结果，质粒序列不变")
    antibiotic_resistance = models.CharField(verbose_name="抗性", max_length=50, null=True, blank=True, help_text="Amp/Kan/Chlor/etc")
    design_status = models.CharField(verbose_name="设计状态", max_length=50, null=True, blank=True, default='Pending', help_text="Pending/Processing/Completed/Failed")
    design_error = models.TextField(verbose_name="设计错误信息", null=True, blank=True)
    primer_forward = models.TextField(verbose_name="正向引物序列", null=True, blank=True)
    primer_reverse = models.TextField(verbose_name="反向引物序列", null=True, blank=True)
    primer_forward_tm = models.FloatField(verbose_name="正向引物Tm", null=True, blank=True)
    primer_reverse_tm = models.FloatField(verbose_name="反向引物Tm", null=True, blank=True)
    colony_pcr_primers = models.TextField(verbose_name="菌落PCR引物(5对, JSON)", null=True, blank=True)
    # 骨架 PCR 引物：只在不改造模式下设计。与 NC-PCR 的 5OL/3OLrc 相向不同，这一对是"外向"的
    # ——正向锚在 v3NC 起点向右、反向锚在 v5NC 终点向左，绕质粒一圈扩出线性化骨架（不含 iU20–iD20 之间）。
    backbone_primer_forward = models.TextField(verbose_name="骨架PCR正向引物", null=True, blank=True,
                                               help_text="外向引物，锚在 v3NC 起点向右")
    backbone_primer_reverse = models.TextField(verbose_name="骨架PCR反向引物", null=True, blank=True,
                                               help_text="外向引物，锚在 v5NC 终点向左")
    backbone_primer_forward_tm = models.FloatField(verbose_name="骨架PCR正向引物Tm", null=True, blank=True)
    backbone_primer_reverse_tm = models.FloatField(verbose_name="骨架PCR反向引物Tm", null=True, blank=True)

    create_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255, default='Received')

    # 可见性与归属解耦：
    #   user=None  + is_public=True  -> 公司公开载体（客户目录可见）
    #   user=None  + is_public=False -> 公司内部载体（仅后台/管理员可见）
    #   user=客户  + is_public=False -> 客户私有载体（仅该客户可见）
    # 归属由“上传者身份”决定：管理员上传 -> user=None（公司）；客户上传 -> user=客户。
    is_public = models.BooleanField(default=False, verbose_name="是否对客户公开")

    def is_company_vector(self):
        return self.user is None

    def is_visible_to_customers(self):
        """是否出现在客户目录里（公司公开载体）。"""
        return self.is_public

    def __str__(self):
        return self.vector_name

class VectorElement(models.Model):
    """质粒元件库：一条记录 = 一段有生物学功能的序列（启动子 / 抗性基因 / 复制起点 …）。

    元件由管理员从载体图谱（GenBank features）里挑选入库，也可手工录入。
    序列一律按功能链方向存（feature.extract 已处理负链），所以同一元件在不同载体上
    哪怕标注在负链，入库后也是同一条序列、同一个 seq_hash —— 去重靠 seq_hash。
    """

    ELEMENT_TYPES = [
        ('promoter', '启动子'),
        ('terminator', '终止子'),
        ('ori', '复制起点'),
        ('resistance', '抗性基因'),
        ('cds', '编码序列'),
        ('tag', '标签'),
        ('signal_peptide', '信号肽'),
        ('polya', 'polyA 信号'),
        ('enhancer', '增强子'),
        ('protein_bind', '蛋白结合位点'),
        ('rbs', '核糖体结合位点'),
        ('regulatory', '调控元件'),
        ('other', '其他'),
    ]
    RISK_LEVELS = [('high', '高'), ('medium', '中'), ('low', '低')]
    SOURCE_KINDS = [('company', '公司载体'), ('customer', '客户载体'), ('manual', '手工录入')]

    name = models.CharField(verbose_name="元件名", max_length=200)
    element_type = models.CharField(verbose_name="元件类型", max_length=32, choices=ELEMENT_TYPES, default='other')
    sequence = models.TextField(verbose_name="元件序列")
    seq_length = models.IntegerField(verbose_name="序列长度", default=0)
    seq_hash = models.CharField(verbose_name="序列指纹", max_length=40, unique=True, db_index=True,
                                help_text="sha1(大写序列)，元件去重的唯一键")
    aliases = models.JSONField(verbose_name="别名", default=list, blank=True,
                               help_text="同一元件在不同图谱上的其他叫法")
    description = models.TextField(verbose_name="备注", blank=True, default='')

    source_vector = models.ForeignKey('Vector', verbose_name="来源载体", on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='contributed_elements')
    source_vector_name = models.CharField(verbose_name="来源载体名(快照)", max_length=200, blank=True, default='',
                                          help_text="来源载体被删掉后仍能追溯出处")
    source_kind = models.CharField(verbose_name="来源类型", max_length=16, choices=SOURCE_KINDS, default='company')
    genbank_feature_type = models.CharField(verbose_name="GenBank 原始 feature 类型", max_length=64, blank=True, default='')

    # 重组风险筛查：客户待合成序列会与这些元件比对，命中说明连载体时可能发生同源重组
    screen_enabled = models.BooleanField(verbose_name="纳入重组风险筛查", default=True)
    risk_level = models.CharField(verbose_name="风险等级", max_length=8, choices=RISK_LEVELS, default='medium')

    is_active = models.BooleanField(verbose_name="启用", default=True)
    created_by = models.ForeignKey(User, verbose_name="录入人", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "质粒元件"
        verbose_name_plural = "质粒元件库"
        ordering = ['element_type', 'name']
        indexes = [
            models.Index(fields=['element_type', 'is_active']),
            models.Index(fields=['screen_enabled', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_element_type_display()}, {self.seq_length}bp)"

    def save(self, *args, **kwargs):
        self.sequence = (self.sequence or '').strip().upper()
        self.seq_length = len(self.sequence)
        self.seq_hash = compute_seq_hash(self.sequence)
        super().save(*args, **kwargs)


class VectorElementOccurrence(models.Model):
    """元件在某个载体上的一次出现（位置 + 链向）。

    元件与载体是多对多：一个元件（如 AmpR）出现在很多载体上，一个载体也含很多元件。
    有了这张表，"某质粒有哪些关键元件" 和 "某元件出现在哪些质粒上" 都能直接查。
    """

    element = models.ForeignKey(VectorElement, on_delete=models.CASCADE, related_name='occurrences')
    vector = models.ForeignKey('Vector', on_delete=models.CASCADE, related_name='element_occurrences')
    start = models.IntegerField(verbose_name="起始位置", help_text="0-based，闭区间起点")
    end = models.IntegerField(verbose_name="结束位置", help_text="0-based，开区间终点")
    strand = models.SmallIntegerField(verbose_name="链向", default=1, help_text="1 正链 / -1 负链")
    label_in_vector = models.CharField(verbose_name="该图谱上的原始标注", max_length=200, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "元件出现记录"
        verbose_name_plural = "元件出现记录"
        unique_together = ('element', 'vector', 'start', 'end')
        ordering = ['vector_id', 'start']

    def __str__(self):
        return f"{self.element.name} @ {self.vector.vector_name} [{self.start}-{self.end}]"


class GeneSynEnzymeCutSite(models.Model):
    enzyme_name = models.CharField(verbose_name="酶切位点", max_length=256)
    enzyme_seq = models.CharField(verbose_name="酶切序列", max_length=256)
    usescope = models.CharField(verbose_name="使用范围", max_length=256)

class Species(models.Model):
    species_name = models.CharField(verbose_name="物种名称", max_length=256)
    species_note = models.CharField(verbose_name="物种备注", max_length=256, blank=True, null=True)

    species_codon_file = models.FileField(verbose_name="codon文件", upload_to='codon_usage_table/', blank=True, null=True)

    def __str__(self):
        return self.species_name