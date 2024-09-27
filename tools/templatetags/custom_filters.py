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
def highlight_sequence_with_offset(sequence, highlights):
    """
    针对 original_seq 的高亮，位移前移 20bp
    """
    return highlight_sequence(sequence, highlights, 20)

@register.filter
def highlight_sequence_no_offset(sequence, highlights):
    """
    针对 saved_seq 的高亮，不需要位移
    """
    return highlight_sequence(sequence, highlights, 0)

def highlight_sequence(sequence, highlights, offset):
    """
    根据给定的高亮列表，将 DNA 序列的不同部分用 HTML 标签进行高亮显示
    :param sequence: 字符串，DNA 序列
    :param highlights: 列表，包含高亮信息的字典
    :param offset: 偏移量
    :return: 字符串，带 HTML 标签的高亮序列
    """
    tags = []
    if highlights is None:
        return sequence
    for highlight in highlights:
        tags.append((highlight['start'] - offset, 'start', highlight['type']))
        tags.append((highlight['end'] - offset, 'end', highlight['type']))

    tags.sort(key=lambda x: (x[0], x[1] == 'end'))

    tag_map = {
        'text-warning': ('<i class="text-warning">', '</i>'),
        'bg-danger': ('<span class="bg-danger">', '</span>')
    }

    result = []
    tag_stack = []
    last_index = 0

    def close_tag(tag_type):
        result.append(tag_map[tag_type][1])

    def open_tag(tag_type):
        result.append(tag_map[tag_type][0])

    for index, tag_type, highlight_type in tags:
        if last_index < index:
            result.append(sequence[last_index:index])

        if tag_type == 'start':
            tag_stack.append(highlight_type)
            open_tag(highlight_type)
        elif tag_type == 'end':
            temp_stack = []
            while tag_stack and tag_stack[-1] != highlight_type:
                temp_stack.append(tag_stack.pop())
                close_tag(temp_stack[-1])

            tag_stack.pop()
            close_tag(highlight_type)

            while temp_stack:
                tag_type_temp = temp_stack.pop()
                tag_stack.append(tag_type_temp)
                open_tag(tag_type_temp)

        last_index = index

    if last_index < len(sequence):
        result.append(sequence[last_index:])

    while tag_stack:
        close_tag(tag_stack.pop())

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