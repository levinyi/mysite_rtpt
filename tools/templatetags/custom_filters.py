from django import template
import os

register = template.Library()

@register.filter
def basename(path):
    return os.path.basename(path)


@register.filter
def codon_split(gene_seq, frameshift):
    start_idx = frameshift
    codons = [gene_seq[i:i+3] for i in range(start_idx, len(gene_seq), 3)]
    return codons