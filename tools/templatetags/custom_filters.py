from django import template
import os

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