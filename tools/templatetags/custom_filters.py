import re
from django import template
import os
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def basename(path):
    if not isinstance(path, str):
        path = str(path)
    return os.path.basename(path)


@register.filter
def codon_split(gene_seq, frameshift):
    start_idx = frameshift
    codons = [gene_seq[i:i+3] for i in range(start_idx, len(gene_seq), 3)]
    return codons

@register.filter
def check_status(gene_list, status):
    '''检查全部为Saved状态时，返回True，否则返回False'''
    for gene in gene_list:
        if gene.status != status:
            return False
    return True

@register.filter(name='get_previous')
def get_previous(value, arg):
    # used in shopping cart html
    return value[arg - 1] if arg > 0 else None


@register.filter
def highlight_sequence(sequence, highlights):
    """
    根据给定的高亮列表，将 DNA 序列的不同部分用 HTML 标签进行高亮显示
    :param sequence: 字符串，DNA 序列
    :param highlights: 列表，包含高亮信息的字典
    :return: 字符串，带 HTML 标签的高亮序列
    """
    # print("sequence: ", sequence)
    # print("highlights: ", highlights)
    # print("I'm in template tags")
    # 初始化所有的标记点
    tags = []
    if highlights is None:
        return sequence
    # 为每个标签类型标记起始和结束位置
    for highlight in highlights:
        tags.append((highlight['start'], 'start', highlight['type']))
        tags.append((highlight['end'], 'end', highlight['type']))

    # 将标记点按位置排序，位置相同的点按起止顺序排序
    tags.sort(key=lambda x: (x[0], x[1] == 'end'))

    # 定义标签的 HTML 映射
    tag_map = {
        'text-warning': ('<i class="text-warning">', '</i>'),
        'bg-danger': ('<span class="bg-danger">', '</span>')
    }

    # 结果列表
    result = []
    tag_stack = []
    last_index = 0

    def close_tag(tag_type):
        """关闭指定类型的标签"""
        close_tag_str = tag_map[tag_type][1]
        result.append(close_tag_str)

    def open_tag(tag_type):
        """打开指定类型的标签"""
        open_tag_str = tag_map[tag_type][0]
        result.append(open_tag_str)

    # 遍历标记点，将它们插入到结果列表中
    for index, tag_type, highlight_type in tags:
        if last_index < index:
            result.append(sequence[last_index:index])

        if tag_type == 'start':
            # 如果有重叠的标签，确保嵌套顺序
            tag_stack.append(highlight_type)
            open_tag(highlight_type)
        elif tag_type == 'end':
            # 关闭所有正在进行的标签，直到找到当前结束标签对应的开始标签
            temp_stack = []
            while tag_stack and tag_stack[-1] != highlight_type:
                temp_stack.append(tag_stack.pop())
                close_tag(temp_stack[-1])

            # 关闭当前的结束标签
            tag_stack.pop()
            close_tag(highlight_type)

            # 按相反顺序重新打开之前临时关闭的标签
            while temp_stack:
                tag_type_temp = temp_stack.pop()
                tag_stack.append(tag_type_temp)
                open_tag(tag_type_temp)

        last_index = index

    # 添加最后剩余的字符串
    if last_index < len(sequence):
        result.append(sequence[last_index:])

    # 关闭所有剩余的标签
    while tag_stack:
        close_tag(tag_stack.pop())

    # print("".join(result))
    return ''.join(result)

@register.filter
def percentage_of(value, total):
    """计算某个值占总数的百分比"""
    try:
        return (value / total) * 100
    except (ZeroDivisionError, TypeError):
        return 0

@register.filter
def filter_status(gene_list, status):
    """统计指定状态的基因数量"""
    return len([gene for gene in gene_list if gene.status == status])

@register.filter
def minus_gene(a,b):
    """减去两个值"""
    try:
        return int(a) - int(b)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def base_length(seq):
    # print(seq)
    '''计算序列长度，去除掉开头的小写的序列，去除掉末尾的小写的长度，去掉空格，最后计算长度'''
    seq = re.sub(r'^[a-z]+', '', seq)  # 去掉开头的小写序列
    seq = re.sub(r'[a-z]+$', '', seq)
    return len(seq.replace(' ', ''))  # 去掉空格计算长度