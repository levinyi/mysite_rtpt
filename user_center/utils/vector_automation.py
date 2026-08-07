"""
载体改造自动化设计工具函数
用于解析GenBank文件、设计v5NC和v3NC序列、设计NC-PCR引物并生成改造后图谱
"""
import re
import os

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation
from Bio.SeqUtils import MeltingTemp as mt
try:
    import primer3
except ImportError:
    primer3 = None
from tools.scripts.AnalysisSequence import DNARepeatsFinder


# Cm-ccdB 片段库（按 IIS 酶切位点分类，优先级: BsaI > BsmBI > BbsI > BfuAI > PaqCI > BtgZI > NNNN）
CM_CCDB_FRAGMENTS = {
    'BsaI': {
        'sequence': "gGAGACCGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGGGTCTCa",
        'sites': ['GGTCTC', 'GAGACC'],
    },
    'BsmBI': {
        'sequence': "gGAGACGGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGCGTCTCa",
        'sites': ['CGTCTC', 'GAGACG'],
    },
    'BbsI': {
        'sequence': "gaGTCTTCGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGGAAGACat",
        'sites': ['GAAGAC', 'GTCTTC'],
    },
    'BfuAI': {
        'sequence': "cactGCAGGTGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGACCTGCagtg",
        'sites': ['ACCTGC', 'GCAGGT'],
    },
    'PaqCI': {
        'sequence': "cactGCAGGTGGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGCACCTGCagtg",
        'sites': ['CACCTGC', 'GCAGGTG'],
    },
    'BtgZI': {
        'sequence': "cactaaactaGCAGGTGGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGGCGATGagtgttactt",
        'sites': ['GCGATG', 'CATCGC'],
    },
    'NNNN': {
        'sequence': "NNNNNNGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTATACACAGCCAGTCTGCAGNNNNNN",
        'sites': [],  # 无特定位点，兜底方案
    },
}

# Cm-ccdB 片段选择优先级
CM_CCDB_PRIORITY = ['BsaI', 'BsmBI', 'BbsI', 'BfuAI', 'PaqCI', 'BtgZI']

# 所有 IIS 酶的识别序列（用于检测载体中是否含有）
ALL_IIS_SITES = {
    'BsaI':  ['GGTCTC', 'GAGACC'],
    'BsmBI': ['CGTCTC', 'GAGACG'],
    'BbsI':  ['GAAGAC', 'GTCTTC'],
    'BfuAI': ['ACCTGC', 'GCAGGT'],
    'PaqCI': ['CACCTGC', 'GCAGGTG'],
    'BtgZI': ['GCGATG', 'CATCGC'],
}


def select_cm_ccdb_fragment(vector_sequence):
    """
    根据客户载体序列中的 IIS 酶切位点，选择合适的 Cm-ccdB 片段

    优先级: BsaI > BsmBI > BbsI > BfuAI > PaqCI > BtgZI > NNNN

    Args:
        vector_sequence: 客户载体序列

    Returns:
        tuple: (enzyme_name, sequence, warning_msg)
    """
    seq_upper = vector_sequence.upper()

    for enzyme_name in CM_CCDB_PRIORITY:
        sites = ALL_IIS_SITES[enzyme_name]
        has_site = any(site in seq_upper for site in sites)
        if not has_site:
            # 载体不含该酶的位点，可以使用对应的 Cm-ccdB 片段
            return enzyme_name, CM_CCDB_FRAGMENTS[enzyme_name]['sequence'], ""

    # 所有6种酶的位点都存在，使用 NNNN 兜底片段
    return 'NNNN', CM_CCDB_FRAGMENTS['NNNN']['sequence'], "载体含有全部6种IIS酶位点，使用NNNN占位片段，需售前技术人员介入处理"


# 向后兼容：保留 CM_CCDB_SEQUENCE 作为默认值（BsaI 片段）
CM_CCDB_SEQUENCE = CM_CCDB_FRAGMENTS['BsaI']['sequence']


class VectorAutomationDesigner:
    """载体改造自动化设计类"""

    def __init__(self, genbank_file_path):
        """
        初始化设计器

        Args:
            genbank_file_path: GenBank文件路径
        """
        self.genbank_file_path = genbank_file_path
        self.record = None
        self.iu20_location = None
        self.id20_location = None
        self.errors = []

    def parse_genbank(self):
        """
        解析GenBank文件，提取iU20和iD20位置

        Returns:
            dict: 包含解析结果的字典，如果失败则返回None
        """
        try:
            try:
                with open(self.genbank_file_path, "r", encoding="utf-8") as handle:
                    self.record = SeqIO.read(handle, "genbank")
            except UnicodeDecodeError:
                with open(self.genbank_file_path, "r", encoding="latin-1") as handle:
                    self.record = SeqIO.read(handle, "genbank")

            # 查找iU20和iD20 feature
            for feature in self.record.features:
                if feature.type == "misc_feature" or feature.type == "primer_bind":
                    # 检查qualifiers中是否包含iU20或iD20标记
                    if 'label' in feature.qualifiers:
                        label = feature.qualifiers['label'][0]
                        if 'iU20' in label or 'iu20' in label.lower():
                            self.iu20_location = feature.location
                        elif 'iD20' in label or 'id20' in label.lower():
                            self.id20_location = feature.location
                    elif 'note' in feature.qualifiers:
                        note = feature.qualifiers['note'][0]
                        if 'iU20' in note or 'iu20' in note.lower():
                            self.iu20_location = feature.location
                        elif 'iD20' in note or 'id20' in note.lower():
                            self.id20_location = feature.location

            # 验证是否找到iU20和iD20
            if not self.iu20_location or not self.id20_location:
                self.errors.append("未检测到iU20或iD20位置，该文件不可用")
                return None

            # 提取序列
            # 1) feature序列：考虑strand，extract会返回正向/反向互补序列
            iu20_seq_feature = str(self.iu20_location.extract(self.record.seq))
            id20_seq_feature = str(self.id20_location.extract(self.record.seq))
            # 2) forward序列：始终使用正向链上的序列，用于展示/拼接
            iu20_seq = str(self.record.seq[int(self.iu20_location.start):int(self.iu20_location.end)])
            id20_seq = str(self.record.seq[int(self.id20_location.start):int(self.id20_location.end)])

            # 记录strand信息
            iu20_strand = self.iu20_location.strand if self.iu20_location.strand else 1
            id20_strand = self.id20_location.strand if self.id20_location.strand else 1

            return {
                'sequence': str(self.record.seq),
                'iu20_location': (int(self.iu20_location.start), int(self.iu20_location.end)),
                'id20_location': (int(self.id20_location.start), int(self.id20_location.end)),
                'iu20_seq': iu20_seq,
                'id20_seq': id20_seq,
                'iu20_seq_feature': iu20_seq_feature,
                'id20_seq_feature': id20_seq_feature,
                'iu20_strand': iu20_strand,
                'id20_strand': id20_strand,
                'record_name': self.record.name,
                'record_description': self.record.description,
                'original_features': self.record.features,
                'original_annotations': self.record.annotations,
            }

        except Exception as e:
            self.errors.append(f"解析GenBank文件失败: {str(e)}")
            return None

    @staticmethod
    def calculate_tm_simple(sequence):
        """
        简单Tm值计算（快速公式: 2*A/T + 4*G/C）

        Args:
            sequence: DNA序列

        Returns:
            float: Tm值（℃）
        """
        sequence = sequence.upper()
        at_count = sequence.count('A') + sequence.count('T')
        gc_count = sequence.count('G') + sequence.count('C')
        return 2 * at_count + 4 * gc_count

    @staticmethod
    def calculate_tm_t97(sequence, salt_conc=100, mg_conc=3.4, k_conc=0, tris_conc=0, dntp_conc=0, saltcorr=7):
        """
        计算引物T97值（97%分子结合时的温度）
        默认采用Biopython MeltingTemp的Nearest Neighbor算法，参数可调

        Args:
            sequence: DNA序列
            salt_conc: 单价阳离子浓度 (mM)
            mg_conc: Mg2+浓度 (mM)
            k_conc: K+浓度 (mM)
            tris_conc: Tris浓度 (mM)
            dntp_conc: dNTP浓度 (mM)
            saltcorr: Salt correction model id

        Returns:
            float: T97值（℃）
        """
        sequence = sequence.upper()
        if len(sequence) < 2:
            return 0.0
        try:
            tm = mt.Tm_NN(
                sequence,
                Na=salt_conc,
                K=k_conc,
                Tris=tris_conc,
                Mg=mg_conc,
                dNTPs=dntp_conc,
                saltcorr=saltcorr
            )
        except Exception:
            tm = mt.Tm_Wallace(sequence)

        return round(tm, 2)

    @staticmethod
    def calculate_gc_content(sequence):
        """计算GC含量（百分比）"""
        sequence = sequence.upper()
        gc_count = sequence.count('G') + sequence.count('C')
        return (gc_count / len(sequence)) * 100 if len(sequence) > 0 else 0

    @staticmethod
    def has_homopolymer(sequence, max_length=7, bases='GC'):
        """
        检查序列是否包含超过指定长度的单碱基重复

        Args:
            sequence: DNA序列
            max_length: 最大允许重复长度（允许 max_length 个，不允许 max_length+1 个）
            bases: 检查的碱基类型（默认GC）

        Returns:
            bool: True如果存在超过max_length的重复
        """
        sequence = sequence.upper()
        for base in bases:
            pattern = base * (max_length + 1)
            if pattern in sequence:
                return True
        return False

    @staticmethod
    def max_homopolymer_run(sequence):
        """返回序列中最长单碱基连续重复（homopolymer）的长度。

        例如 'ATAAAAAAGC' -> 6（6 连 A）。空序列返回 0。
        用于菌落PCR引物质量打分：连续 run 越长越差。
        """
        sequence = sequence.upper()
        if not sequence:
            return 0
        max_run = 1
        cur = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i - 1]:
                cur += 1
                if cur > max_run:
                    max_run = cur
            else:
                cur = 1
        return max_run

    @staticmethod
    def has_gc_enrichment(sequence, window=12, max_count=10):
        """
        检查序列是否存在 GC 富集：任意 window bp 窗口内 G 或 C 的数量超过 max_count

        Args:
            sequence: DNA序列
            window: 滑窗大小（默认12）
            max_count: 允许的最大 G 或 C 数量（默认10，即不允许11个）

        Returns:
            bool: True 如果存在 GC 富集
        """
        sequence = sequence.upper()
        if len(sequence) < window:
            return False
        for i in range(len(sequence) - window + 1):
            win = sequence[i:i + window]
            if win.count('G') > max_count or win.count('C') > max_count:
                return True
        return False

    @staticmethod
    def reverse_complement(sequence):
        """返回反向互补序列"""
        complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
        return ''.join(complement[base] for base in reversed(sequence.upper()))

    @staticmethod
    def is_palindrome(sequence):
        """检查序列是否为回文序列（DNA回文：序列等于其反向互补）"""
        return sequence.upper() == VectorAutomationDesigner.reverse_complement(sequence)

    @staticmethod
    def check_cross_pairing(seq1, seq2):
        """
        检查两个序列是否会相互错搭
        包括seq1, seq2, seq1的反向互补, seq2的反向互补
        如果任意两个序列在每个位置比较时有3个或4个碱基相同，则认为会错搭

        Args:
            seq1: 第一个序列
            seq2: 第二个序列

        Returns:
            bool: True如果会错搭
        """
        seq1 = seq1.upper()
        seq2 = seq2.upper()
        seq1_rc = VectorAutomationDesigner.reverse_complement(seq1)
        seq2_rc = VectorAutomationDesigner.reverse_complement(seq2)

        sequences = [seq1, seq2, seq1_rc, seq2_rc]

        # 检查所有序列对
        for i in range(len(sequences)):
            for j in range(i + 1, len(sequences)):
                s1, s2 = sequences[i], sequences[j]
                # 如果长度不同，只比较较短长度
                min_len = min(len(s1), len(s2))
                matches = sum(1 for k in range(min_len) if s1[k] == s2[k])
                if matches >= 3:  # 3个或4个碱基相同
                    return True

        return False

    def check_long_repeat_penalty(self, sequence, insert_position, iu20_end, id20_start,
                                   range_bp=2000, max_penalty=14):
        """
        检查插入位点上下游指定范围内的Long repeat罚分

        新规则:
        - 阈值为14分
        - 若罚分>14，检查repeat是否都在insert同一侧（全在iU20之前或全在iD20之后）
        - 同一侧的repeat可以接受；分散在两侧的不可接受

        Args:
            sequence: 完整载体序列
            insert_position: 插入位点位置
            iu20_end: iU20 结束位置（0-based exclusive）
            id20_start: iD20 起始位置（0-based）
            range_bp: 检查范围（上下游各range_bp/2）
            max_penalty: 最大允许罚分（默认14）

        Returns:
            tuple: (is_valid, total_penalty, detail_msg)
        """
        check_start = max(0, insert_position - range_bp // 2)
        check_end = min(len(sequence), insert_position + range_bp // 2)
        check_seq = sequence[check_start:check_end]

        finder = DNARepeatsFinder(sequence=check_seq)
        long_repeats = finder.find_dispersed_repeats(min_len=16)

        total_penalty = sum(repeat.get('penalty_score', 0) for repeat in long_repeats)

        if total_penalty <= max_penalty:
            return True, total_penalty, ""

        # 罚分>14，检查repeat是否都在同一侧
        # repeat 的 positions 是相对于 check_seq 的，需要转换为相对于原序列的位置
        for repeat in long_repeats:
            positions = repeat.get('start', [])
            if not isinstance(positions, list):
                positions = [positions]
            # 转换为原序列坐标
            abs_positions = [p + check_start for p in positions]

            # 检查是否分散在 insert 两侧
            has_upstream = any(p < iu20_end for p in abs_positions)
            has_downstream = any(p >= id20_start for p in abs_positions)

            if has_upstream and has_downstream:
                return False, total_penalty, f"Long repeat序列分散在insert两侧(罚分{total_penalty:.1f}>14)"

        # 所有 repeat 都在同一侧，可以接受
        return True, total_penalty, ""

    def _validate_gibson_arm(self, sequence):
        """验证Gibson臂是否符合基本要求"""
        if len(sequence) < 30:
            return False
        tm_val = self.calculate_tm_simple(sequence)
        gc_val = self.calculate_gc_content(sequence)
        if tm_val < 48 or not (20 < gc_val < 80):
            return False
        if self.has_homopolymer(sequence, max_length=7, bases='GC'):
            return False
        return True

    def _update_shift_records(self, design_result, parsed_data, sequence):
        """根据当前位置重新计算i5NC/i3NC"""
        iu20_end = parsed_data['iu20_location'][1]
        id20_start = parsed_data['id20_location'][0]
        v5_end = design_result['v5nc_location'][1]
        v3_start = design_result['v3nc_location'][0]

        design_result['i5nc'] = sequence[v5_end:iu20_end] if v5_end < iu20_end else ''
        design_result['i3nc'] = sequence[id20_start:v3_start] if v3_start > id20_start else ''

    def _check_tandem_repeats_near_insert(self, sequence, iu20_start, iu20_end, id20_start, id20_end, flank_bp=30):
        """
        检查 insert 上游和下游各 flank_bp 范围内是否有 tandem repeats 罚分
        上游区域: [iu20_start - flank_bp, iu20_start)  即 iU20 上游
        下游区域: [id20_end, id20_end + flank_bp)  即 iD20 下游
        注意：不包含 iU20/iD20 本身和 insert 内部

        Returns:
            tuple: (has_tandem, penalty, detail_msg)
        """
        total_penalty = 0
        details = []

        # 上游: iU20 起始位置往前 flank_bp（不含 iU20 本身）
        upstream_start = max(0, iu20_start - flank_bp)
        upstream_seq = sequence[upstream_start:iu20_start]
        if len(upstream_seq) >= 12:  # 序列太短没有检测意义
            finder_up = DNARepeatsFinder(sequence=upstream_seq)
            tandem_up = finder_up.find_tandem_repeats(min_unit=3, min_copies=4, max_mismatch=1)
            penalty_up = sum(r.get('penalty_score', 0) for r in tandem_up)
            if penalty_up > 0:
                total_penalty += penalty_up
                details.append(f"上游{flank_bp}bp内tandem repeats罚分{penalty_up:.1f}")

        # 下游: iD20 结束位置往后 flank_bp（不含 iD20 本身）
        downstream_end = min(len(sequence), id20_end + flank_bp)
        downstream_seq = sequence[id20_end:downstream_end]
        if len(downstream_seq) >= 12:
            finder_down = DNARepeatsFinder(sequence=downstream_seq)
            tandem_down = finder_down.find_tandem_repeats(min_unit=3, min_copies=4, max_mismatch=1)
            penalty_down = sum(r.get('penalty_score', 0) for r in tandem_down)
            if penalty_down > 0:
                total_penalty += penalty_down
                details.append(f"下游{flank_bp}bp内tandem repeats罚分{penalty_down:.1f}")

        if total_penalty > 0:
            return True, total_penalty, f"insert附近存在tandem repeats({'; '.join(details)})"
        return False, 0, ""

    def design_gibson_method(self, parsed_data):
        """
        设计Gibson克隆方法

        规则:
        1. 插入位点±1000bp内Long repeat罚分≤14；若>14但repeat全在同一侧可接受
        2. insert上下游各100bp内不能有Palindrome或InvertedRepeat（回文/发卡结构）
        3. v5NC/v3NC各≥30bp，Tm≥48℃，20<GC%<80，
           不能有超过连续7bp的homopolymer G或C，连续12bp内不能有11个G或C
        4. v5NC/v3NC内不能有tandem repeats（影响引物设计）

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']

        # 1. 检查 Long repeat 罚分（阈值14，支持同侧判断）
        insert_position = (iu20_end + id20_start) // 2
        is_valid, penalty, detail = self.check_long_repeat_penalty(
            sequence, insert_position, iu20_end=iu20_end, id20_start=id20_start,
            max_penalty=14
        )
        if not is_valid:
            self.errors.append(f"Gibson方法: {detail}")
            return None

        # 2. 检查 insert 上下游各100bp内的 Palindrome 和 Inverted Repeats（回文/发卡结构）
        flank_bp = 100
        for region_name, region_start, region_end in [
            ('上游', max(0, iu20_start - flank_bp), iu20_start),
            ('下游', id20_end, min(len(sequence), id20_end + flank_bp)),
        ]:
            region_seq = sequence[region_start:region_end]
            if len(region_seq) < 15:
                continue
            finder = DNARepeatsFinder(sequence=region_seq)
            palindromes = finder.find_palindrome_repeats(min_len=15)
            inverted = finder.find_inverted_repeats(min_stem_len=10)
            palindrome_penalty = sum(r.get('penalty_score', 0) for r in palindromes)
            inverted_penalty = sum(r.get('penalty_score', 0) for r in inverted)
            if palindrome_penalty > 0 or inverted_penalty > 0:
                details = []
                if palindrome_penalty > 0:
                    details.append(f"Palindrome罚分{palindrome_penalty:.1f}")
                if inverted_penalty > 0:
                    details.append(f"InvertedRepeat罚分{inverted_penalty:.1f}")
                self.errors.append(f"Gibson方法: insert{region_name}{flank_bp}bp内存在回文/发卡结构({', '.join(details)})")
                return None

        # 3. 设计 v5NC 和 v3NC
        min_nc_length = 30
        max_attempts = 100
        iu20_length = iu20_end - iu20_start
        id20_length = id20_end - id20_start

        for attempt in range(max_attempts):
            v5nc_end = iu20_end
            v5nc_length = max(min_nc_length, iu20_length) + attempt
            v5nc_start = iu20_end - v5nc_length
            if v5nc_start < 0:
                break
            v5nc = sequence[v5nc_start:v5nc_end]

            v3nc_start = id20_start
            v3nc_length = max(min_nc_length, id20_length) + attempt
            v3nc_end = id20_start + v3nc_length
            if v3nc_end > len(sequence):
                break
            v3nc = sequence[v3nc_start:v3nc_end]

            tm_v5nc = self.calculate_tm_simple(v5nc)
            gc_v5nc = self.calculate_gc_content(v5nc)
            tm_v3nc = self.calculate_tm_simple(v3nc)
            gc_v3nc = self.calculate_gc_content(v3nc)

            if (tm_v5nc >= 48 and tm_v3nc >= 48 and
                20 < gc_v5nc < 80 and 20 < gc_v3nc < 80 and
                not self.has_homopolymer(v5nc, max_length=7, bases='GC') and
                not self.has_homopolymer(v3nc, max_length=7, bases='GC') and
                not self.has_gc_enrichment(v5nc, window=12, max_count=10) and
                not self.has_gc_enrichment(v3nc, window=12, max_count=10)):

                # 3. 检查候选 v5NC/v3NC 内的 tandem repeats（影响引物设计）
                has_tandem = False
                for nc_seq, nc_name in [(v5nc, 'v5NC'), (v3nc, 'v3NC')]:
                    if len(nc_seq) >= 12:
                        finder = DNARepeatsFinder(sequence=nc_seq)
                        tandem = finder.find_tandem_repeats(min_unit=3, min_copies=4, max_mismatch=1)
                        if sum(r.get('penalty_score', 0) for r in tandem) > 0:
                            has_tandem = True
                            break
                if has_tandem:
                    continue

                return {
                    'method': 'Gibson',
                    'v5nc': v5nc,
                    'v3nc': v3nc,
                    'v5nc_location': (v5nc_start, v5nc_end),
                    'v3nc_location': (v3nc_start, v3nc_end),
                    'i5nc': '',
                    'i3nc': '',
                    'tm_v5nc': tm_v5nc,
                    'tm_v3nc': tm_v3nc,
                    'gc_v5nc': gc_v5nc,
                    'gc_v3nc': gc_v3nc
                }

        self.errors.append("Gibson方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    def _design_gg_t4_vnc(self, sequence, iu20_end, id20_start, method_name):
        """
        GG 和 T4 共用的 v5NC/v3NC 设计逻辑（移位法）

        规则:
        - v5NC = iU20 末端 4bp，v3NC = iD20 起始 4bp
        - 若 v5NC 是回文，v5NC 整体向5'移动1bp（4bp窗口平移），多出的碱基作为 i5NC
        - 若 v3NC 是回文，v3NC 整体向3'移动1bp（4bp窗口平移），多出的碱基作为 i3NC
        - 若 v5NC/v3NC 会错搭，两者分别移动1bp
        - 移位的碱基会作为 i5NC/i3NC 补回客户序列，避免缺失

        Args:
            sequence: 完整载体序列
            iu20_end: iU20 结束位置（0-based exclusive）
            id20_start: iD20 起始位置（0-based）
            method_name: 'GoldenGate' 或 'T4'

        Returns:
            dict: 设计结果或 None
        """
        v5_shift = 0  # v5NC 向5'方向移动的碱基数
        v3_shift = 0  # v3NC 向3'方向移动的碱基数
        max_shift = 20

        for _ in range(max_shift * 2):
            # v5NC: 4bp窗口，从 [iu20_end-4-v5_shift, iu20_end-v5_shift)
            v5nc_start = iu20_end - 4 - v5_shift
            v5nc_end = iu20_end - v5_shift
            if v5nc_start < 0:
                break
            v5nc = sequence[v5nc_start:v5nc_end]

            # v3NC: 4bp窗口，从 [id20_start+v3_shift, id20_start+4+v3_shift)
            v3nc_start = id20_start + v3_shift
            v3nc_end = id20_start + 4 + v3_shift
            if v3nc_end > len(sequence):
                break
            v3nc = sequence[v3nc_start:v3nc_end]

            # 检查回文
            is_v5_palindrome = self.is_palindrome(v5nc)
            is_v3_palindrome = self.is_palindrome(v3nc)

            if is_v5_palindrome:
                v5_shift += 1
                if v5_shift >= max_shift:
                    break
                continue

            if is_v3_palindrome:
                v3_shift += 1
                if v3_shift >= max_shift:
                    break
                continue

            # 检查错搭
            if self.check_cross_pairing(v5nc, v3nc):
                v5_shift += 1
                v3_shift += 1
                if v5_shift >= max_shift or v3_shift >= max_shift:
                    break
                continue

            # 找到满足条件的序列
            # i5NC: v5NC 移位后露出的碱基（原来被 v5NC 覆盖，现在需要补回客户序列）
            # 即 [iu20_end - v5_shift, iu20_end) 这段序列
            i5nc = sequence[iu20_end - v5_shift:iu20_end] if v5_shift > 0 else ''
            # i3NC: v3NC 移位后露出的碱基
            # 即 [id20_start, id20_start + v3_shift) 这段序列
            i3nc = sequence[id20_start:id20_start + v3_shift] if v3_shift > 0 else ''

            return {
                'method': method_name,
                'v5nc': v5nc,
                'v3nc': v3nc,
                'v5nc_location': (v5nc_start, v5nc_end),
                'v3nc_location': (v3nc_start, v3nc_end),
                'i5nc': i5nc,
                'i3nc': i3nc
            }

        return None

    def design_goldengate_method(self, parsed_data):
        """
        设计Golden Gate克隆方法

        规则:
        1. 载体不能同时含有 BsaI 和 BsmBI 位点
        2. v5NC/v3NC 各4bp，使用移位法避免回文和错搭

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        _, iu20_end = parsed_data['iu20_location']
        id20_start, _ = parsed_data['id20_location']

        # 检查是否同时含有BsaI和BsmBI位点
        bsai_sites = ['GGTCTC', 'GAGACC']
        bsmbi_sites = ['CGTCTC', 'GAGACG']

        has_bsai = any(site in sequence.upper() for site in bsai_sites)
        has_bsmbi = any(site in sequence.upper() for site in bsmbi_sites)

        if has_bsai and has_bsmbi:
            self.errors.append("GoldenGate方法: 载体同时含有BsaI和BsmBI位点，无法使用")
            return None

        result = self._design_gg_t4_vnc(sequence, iu20_end, id20_start, 'GoldenGate')
        if result:
            return result

        self.errors.append("GoldenGate方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    # T4 方法需要检查的 IIS 酶（BsaI/BsmBI 之外的备选）
    T4_IIS_ENZYMES = {
        'BbsI':  ['GAAGAC', 'GTCTTC'],
        'BfuAI': ['ACCTGC', 'GCAGGT'],
        'PaqCI': ['CACCTGC', 'GCAGGTG'],
        'BtgZI': ['GCGATG', 'CATCGC'],
    }

    def design_t4_method(self, parsed_data):
        """
        设计T4克隆方法

        规则:
        1. 载体至少不含 BbsI/BfuAI/PaqCI/BtgZI 中的一种；若4种都有则转人工
        2. v5NC/v3NC 设计规则与 GG 的(2)(3)(4)完全相同

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        _, iu20_end = parsed_data['iu20_location']
        id20_start, _ = parsed_data['id20_location']

        # 检查 T4 可用的 IIS 酶
        seq_upper = sequence.upper()
        available_enzymes = []
        for enzyme_name, sites in self.T4_IIS_ENZYMES.items():
            has_site = any(site in seq_upper for site in sites)
            if not has_site:
                available_enzymes.append(enzyme_name)

        if not available_enzymes:
            present = ', '.join(self.T4_IIS_ENZYMES.keys())
            self.errors.append(f"T4方法: 载体含有全部4种IIS酶位点({present})，无可用IIS酶，需转人工处理")
            return None

        result = self._design_gg_t4_vnc(sequence, iu20_end, id20_start, 'T4')
        if result:
            result['available_iis_enzymes'] = available_enzymes
            return result

        self.errors.append("T4方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    def select_cloning_method(self, parsed_data, forced_method=None):
        """
        按优先级选择克隆方法，或使用指定的克隆方法

        Args:
            parsed_data: 解析后的GenBank数据
            forced_method: 指定克隆方法（'Gibson'/'GoldenGate'/'T4'），为None时自动选择

        Returns:
            dict: 设计结果或None
        """
        methods = {
            'Gibson': self.design_gibson_method,
            'GoldenGate': self.design_goldengate_method,
            'T4': self.design_t4_method,
        }

        if forced_method and forced_method in methods:
            result = methods[forced_method](parsed_data)
            if not result:
                self.errors.append(f"指定的{forced_method}方法不适用于该载体")
            return result

        # 自动选择：按优先级尝试 Gibson > GoldenGate > T4
        for method_name in ['Gibson', 'GoldenGate', 'T4']:
            result = methods[method_name](parsed_data)
            if result:
                return result

        return None

    def design_nc_pcr_primers(self, design_result, parsed_data, vector_code=None, target_tm=60, variant='M1'):
        """
        设计NC-PCR引物（仅Gibson方法需要）

        Args:
            design_result: 克隆方法设计结果
            parsed_data: 解析后的GenBank数据
            target_tm: 目标Tm值（默认60℃）
            variant: 引物名里的图谱版本号（改造 'M1' / 不改造 'A1'）

        Returns:
            dict: 引物设计结果或None
        """
        if design_result['method'] != 'Gibson':
            return None

        sequence = parsed_data['sequence']
        original_v5_start, original_v5_end = design_result['v5nc_location']
        original_v3_start, original_v3_end = design_result['v3nc_location']

        min_primer_len = 16
        max_primer_len = 35
        tm_tolerance = 2  # T97值容差（用于fallback）
        max_boundary_shift = 10
        hairpin_tm_limit = 40
        dimer_dg_limit = 11

        def attempt_design(v5_start, v5_end, v3_start, v3_end):
            if v5_start < 0 or v3_end > len(sequence) or v5_end > parsed_data['iu20_location'][1]:
                return None
            if v3_start < parsed_data['id20_location'][0]:
                return None

            v5_seq = sequence[v5_start:v5_end]
            v3_seq = sequence[v3_start:v3_end]

            if not self._validate_gibson_arm(v5_seq) or not self._validate_gibson_arm(v3_seq):
                return None

            cur_v5_len = v5_end - v5_start
            cur_v3_len = v3_end - v3_start

            forward = None
            forward_fallback = None
            max_forward_len = min(max_primer_len, cur_v5_len)
            for length in range(min_primer_len, max_forward_len + 1):
                if v5_start + length > len(sequence):
                    break
                primer_seq = sequence[v5_start:v5_start + length]
                tm = self.calculate_tm_t97(primer_seq)
                hairpin_tm = self.calculate_hairpin_tm(primer_seq)
                if hairpin_tm is not None and hairpin_tm >= hairpin_tm_limit:
                    continue
                homodimer_dg = self.calculate_dimer_dg(primer_seq)
                if homodimer_dg is not None and abs(homodimer_dg) >= dimer_dg_limit:
                    continue
                if tm >= target_tm:
                    forward = {
                        'sequence': primer_seq,
                        'tm': tm,
                        'length': length,
                        'hairpin_tm': hairpin_tm,
                        'homodimer_dg': homodimer_dg
                    }
                    break
                elif tm >= target_tm - tm_tolerance:
                    forward_fallback = {
                        'sequence': primer_seq,
                        'tm': tm,
                        'length': length,
                        'hairpin_tm': hairpin_tm,
                        'homodimer_dg': homodimer_dg
                    }

            if not forward and forward_fallback:
                forward = forward_fallback

            reverse = None
            reverse_fallback = None
            max_reverse_len = min(max_primer_len, cur_v3_len)
            for length in range(min_primer_len, max_reverse_len + 1):
                template_start = v3_end - length
                if template_start < 0:
                    continue
                if template_start < v3_start:
                    continue
                template = sequence[template_start:v3_end]
                primer_seq = self.reverse_complement(template)
                tm = self.calculate_tm_t97(primer_seq)
                hairpin_tm = self.calculate_hairpin_tm(primer_seq)
                if hairpin_tm is not None and hairpin_tm >= hairpin_tm_limit:
                    continue
                homodimer_dg = self.calculate_dimer_dg(primer_seq)
                if homodimer_dg is not None and abs(homodimer_dg) >= dimer_dg_limit:
                    continue
                if tm >= target_tm:
                    reverse = {
                        'sequence': primer_seq,
                        'tm': tm,
                        'length': length,
                        'hairpin_tm': hairpin_tm,
                        'homodimer_dg': homodimer_dg
                    }
                    break
                elif tm >= target_tm - tm_tolerance:
                    reverse_fallback = {
                        'sequence': primer_seq,
                        'tm': tm,
                        'length': length,
                        'hairpin_tm': hairpin_tm,
                        'homodimer_dg': homodimer_dg
                    }

            if not reverse and reverse_fallback:
                reverse = reverse_fallback

            if not forward or not reverse:
                return None

            hetero_dg = self.calculate_dimer_dg(forward['sequence'], reverse['sequence'])
            if hetero_dg is not None and abs(hetero_dg) >= dimer_dg_limit:
                return None

            return forward, reverse, (v5_start, v5_end), (v3_start, v3_end), hetero_dg

        for shift5 in range(0, max_boundary_shift + 1):
            # v5NC向左扩展：起点左移，终点不变（保持与iU20末端对齐）
            new_v5_start = max(0, original_v5_start - shift5)
            new_v5_end = original_v5_end
            for shift3 in range(0, max_boundary_shift + 1):
                # v3NC向右扩展：起点不变（保持与iD20起点对齐），终点右移
                new_v3_start = original_v3_start
                new_v3_end = original_v3_end + shift3
                attempt = attempt_design(new_v5_start, new_v5_end, new_v3_start, new_v3_end)
                if attempt:
                    forward, reverse, v5_loc, v3_loc, hetero_dg = attempt
                    design_result['v5nc_location'] = v5_loc
                    design_result['v3nc_location'] = v3_loc
                    design_result['v5nc'] = sequence[v5_loc[0]:v5_loc[1]]
                    design_result['v3nc'] = sequence[v3_loc[0]:v3_loc[1]]
                    self._update_shift_records(design_result, parsed_data, sequence)

                    forward['name'] = self.generate_primer_name(vector_code, '5OL', f"{v5_loc[0]}-{v5_loc[1]}", variant=variant)
                    reverse['name'] = self.generate_primer_name(vector_code, '3OLrc', f"{v3_loc[0]}-{v3_loc[1]}", variant=variant)

                    return {
                        'forward': forward,
                        'reverse': reverse,
                        'heterodimer_dg': hetero_dg
                    }

        self.errors.append("NC-PCR引物设计失败：无法在允许边界内找到满足T97=60℃的引物")
        return None

    def design_backbone_pcr_primers(self, design_result, parsed_data, vector_code=None, target_tm=60):
        """
        设计骨架PCR引物（外向的一对，仅"不改造"模式使用）

        与 NC-PCR 的 5OL/3OLrc 相向不同，这一对是"外向"的：
        - 正向 3BB   ：5'端锚在 v3NC 起点，沿正链向右，绕质粒一圈
        - 反向 5BBrc ：5'端锚在 v5NC 终点，沿负链向左
        两者背对背，产物 = 线性化骨架，两端正好落在 v3NC 起点和 v5NC 终点，
        不含 iU20–iD20 之间那段——正是 Gibson 装基因所需要的骨架。

        引物 5'端必须精确锚在接口上（只允许长度变化，锚点不动），否则 Gibson 接缝会错位。
        本方法不修改 design_result 的边界（与 design_nc_pcr_primers 不同）。

        Args:
            design_result: 克隆方法设计结果（只读）
            parsed_data: 解析后的GenBank数据
            vector_code: 用于引物命名
            target_tm: 目标T97值（默认60℃）

        Returns:
            dict: {'forward': ..., 'reverse': ..., 'heterodimer_dg': ...}，失败返回 None
        """
        sequence = parsed_data['sequence']
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]

        min_primer_len = 16
        max_primer_len = 35
        tm_tolerance = 2
        hairpin_tm_limit = 40
        dimer_dg_limit = 11

        def pick(build_primer, max_len):
            """长度从短到长扫，取第一个 T97 达标的；都不达标则退到 T97≥58 的最长候选。"""
            fallback = None
            for length in range(min_primer_len, max_len + 1):
                primer_seq = build_primer(length)
                if not primer_seq or len(primer_seq) != length:
                    continue
                hairpin_tm = self.calculate_hairpin_tm(primer_seq)
                if hairpin_tm is not None and hairpin_tm >= hairpin_tm_limit:
                    continue
                homodimer_dg = self.calculate_dimer_dg(primer_seq)
                if homodimer_dg is not None and abs(homodimer_dg) >= dimer_dg_limit:
                    continue
                tm = self.calculate_tm_t97(primer_seq)
                candidate = {
                    'sequence': primer_seq,
                    'tm': tm,
                    'length': length,
                    'hairpin_tm': hairpin_tm,
                    'homodimer_dg': homodimer_dg,
                }
                if tm >= target_tm:
                    return candidate
                if tm >= target_tm - tm_tolerance:
                    fallback = candidate
            return fallback

        # 正向：锚点 v3nc_start，向右延伸（可越过 v3NC 终点，退火区更长只是更稳）
        forward = pick(
            lambda length: sequence[v3nc_start:v3nc_start + length],
            min(max_primer_len, len(sequence) - v3nc_start),
        )
        # 反向：锚点 v5nc_end，向左延伸（可越过 v5NC 起点）
        reverse = pick(
            lambda length: self.reverse_complement(sequence[v5nc_end - length:v5nc_end]),
            min(max_primer_len, v5nc_end),
        )

        if not forward or not reverse:
            self.errors.append("骨架PCR引物设计失败：无法在接口处找到满足T97=60℃的外向引物")
            return None

        hetero_dg = self.calculate_dimer_dg(forward['sequence'], reverse['sequence'])
        if hetero_dg is not None and abs(hetero_dg) >= dimer_dg_limit:
            self.errors.append("骨架PCR引物设计失败：正反向引物间存在明显二聚体")
            return None

        forward['template_start'] = v3nc_start
        forward['template_end'] = v3nc_start + forward['length']
        forward['name'] = self.generate_primer_name(
            vector_code, '3BB', f"{forward['template_start']}-{forward['template_end']}", variant='A1')

        reverse['template_start'] = v5nc_end - reverse['length']
        reverse['template_end'] = v5nc_end
        reverse['name'] = self.generate_primer_name(
            vector_code, '5BBrc', f"{reverse['template_start']}-{reverse['template_end']}", variant='A1')

        return {'forward': forward, 'reverse': reverse, 'heterodimer_dg': hetero_dg}

    def _check_colony_primer_quality(self, primer_seq, target_tm=60, tm_tolerance=2,
                                      hairpin_tm_limit=40, dimer_dg_limit=11):
        """菌落PCR引物质量检查：Tm/GC/同源聚体/GC富集/发卡/自二聚体。"""
        if len(primer_seq) < 16:
            return None
        gc = self.calculate_gc_content(primer_seq)
        if gc < 40 or gc > 60:
            return None
        if self.has_homopolymer(primer_seq, max_length=7, bases='GC'):
            return None
        if self.has_homopolymer(primer_seq, max_length=7, bases='AT'):
            return None
        if self.has_gc_enrichment(primer_seq, window=12, max_count=10):
            return None
        tm = self.calculate_tm_t97(primer_seq)
        if tm < target_tm - tm_tolerance or tm > target_tm + 5:
            return None
        hairpin_tm = self.calculate_hairpin_tm(primer_seq)
        if hairpin_tm is not None and hairpin_tm >= hairpin_tm_limit:
            return None
        homodimer_dg = self.calculate_dimer_dg(primer_seq)
        if homodimer_dg is not None and abs(homodimer_dg) >= dimer_dg_limit:
            return None
        return {'tm': tm, 'gc': gc, 'hairpin_tm': hairpin_tm, 'homodimer_dg': homodimer_dg}

    @staticmethod
    def find_start_reference(parsed_data):
        """在 GenBank features 中查找 "Start" 参考点（用于计算 Start_pos）。

        匹配规则：把 feature 的 label/note 归一化（转小写、去掉点/下划线/空格等
        非字母数字字符）后，等于 'start'，或以 'startpos' 结尾——可兼容
        Start / Start.pos / Start_pos / Trim.ref.Start.pos 等写法。

        返回该 feature 的 0-based 起始坐标；找不到返回 None
        （调用方据此回退到 v5NC 起点——部分载体本就没有 Start 标记）。
        """
        features = parsed_data.get('original_features') or []
        for feature in features:
            qualifiers = getattr(feature, 'qualifiers', {}) or {}
            labels = qualifiers.get('label', []) + qualifiers.get('note', [])
            for lab in labels:
                norm = re.sub(r'[^a-z0-9]', '', (lab or '').lower())
                if norm == 'start' or norm.endswith('startpos'):
                    try:
                        return int(feature.location.start)
                    except (TypeError, ValueError, AttributeError):
                        continue
        return None

    def _colony_primer_penalty(self, primer):
        """菌落PCR 单条引物质量罚分，分值越低越好。

        主导项是 homopolymer 连续重复（用户反馈：6 连 A 的引物不应判为 best），
        其次是 GC 偏离 50%、Tm 偏离 60、发卡、自二聚体、3' GC clamp。
        """
        seq = (primer.get('sequence') or '').upper()
        if not seq:
            return 999.0
        penalty = 0.0

        # 1) 单碱基连续重复：>=4 起罚，二次增长（4→2, 5→8, 6→18, 7→32），主导项
        run = self.max_homopolymer_run(seq)
        if run >= 4:
            penalty += (run - 3) ** 2 * 2.0

        # 2) GC 含量偏离 50%
        gc = primer.get('gc')
        if gc is None:
            gc = self.calculate_gc_content(seq)
        penalty += abs(gc - 50) * 0.3

        # 3) Tm 偏离 target(60)
        tm = primer.get('tm')
        if tm is not None:
            penalty += abs(tm - 60) * 0.5

        # 4) 发卡 Tm（>30℃ 起罚）
        hairpin_tm = primer.get('hairpin_tm')
        if hairpin_tm is not None:
            penalty += max(0.0, hairpin_tm - 30) * 0.2

        # 5) 自二聚体 |ΔG|（>5 起罚）
        homodimer_dg = primer.get('homodimer_dg')
        if homodimer_dg is not None:
            penalty += max(0.0, abs(homodimer_dg) - 5) * 0.3

        # 6) 3' GC clamp：末位非 G/C 略罚
        if seq[-1] not in 'GC':
            penalty += 1.0

        return penalty

    def _score_colony_pair(self, pair):
        """整对引物质量罚分（正向+反向+异源二聚体），越低越好。"""
        score = self._colony_primer_penalty(pair.get('forward') or {})
        score += self._colony_primer_penalty(pair.get('reverse') or {})
        hetero = pair.get('heterodimer_dg')
        if hetero is not None:
            score += max(0.0, abs(hetero) - 5) * 0.3
        return round(score, 2)

    def design_colony_pcr_primers(self, parsed_data, design_result, vector_code=None,
                                   num_pairs=5, target_tm=60,
                                   min_dist=50, max_dist=500,
                                   min_primer_len=18, max_primer_len=25,
                                   candidate_limit=40, dimer_dg_limit=11,
                                   start_ref=None, variant='M1'):
        """
        设计菌落PCR引物（5对），适用于所有克隆方法。

        规则:
        - 正向引物模板位于 v5NC 上游 [min_dist, max_dist) bp 区间，3'端越靠近 v5NC start 越好
        - 反向引物模板位于 v3NC 下游 [min_dist, max_dist) bp 区间，3'端越靠近 v3NC end 越好
        - 长度 18-25bp，T97 60℃ ±2，GC 40-60，无≥7连G/C或A/T，无12bp窗口>10个G/C
        - Hairpin Tm < 40℃，自/异源二聚体 |ΔG| < 11 kcal/mol
        - 贪心配对，依次外推：第1对扩增子最短，后续逐步增大

        Args:
            parsed_data: 解析后的GenBank数据
            design_result: 克隆方法设计结果（含 v5nc/v3nc 位置）
            vector_code: 用于引物命名
            num_pairs: 引物对数（默认5）

        Returns:
            list[dict] | None: 5对引物列表；失败返回 None
        """
        sequence = parsed_data['sequence']
        v5nc_start, v5nc_end = design_result['v5nc_location']
        v3nc_start, v3nc_end = design_result['v3nc_location']

        # === Forward 候选池: 距 v5NC start 越近越好 ===
        # 用 stride 收集：找到一个就跳过它占用的范围，候选池里天然非重叠
        forward_candidates = []
        fwd_window_low = max(0, v5nc_start - max_dist)
        fwd_window_high = max(0, v5nc_start - min_dist)
        primer_end = fwd_window_high
        while primer_end > fwd_window_low and len(forward_candidates) < candidate_limit:
            best_for_pos = None
            for length in range(min_primer_len, max_primer_len + 1):
                primer_start = primer_end - length
                if primer_start < fwd_window_low:
                    continue
                primer_seq = sequence[primer_start:primer_end].upper()
                quality = self._check_colony_primer_quality(
                    primer_seq, target_tm=target_tm, dimer_dg_limit=dimer_dg_limit
                )
                if not quality:
                    continue
                tm_diff = abs(quality['tm'] - target_tm)
                if best_for_pos is None or tm_diff < best_for_pos['tm_diff']:
                    best_for_pos = {
                        'sequence': primer_seq,
                        'start': primer_start,
                        'end': primer_end,
                        'length': length,
                        'tm': quality['tm'],
                        'gc': quality['gc'],
                        'hairpin_tm': quality['hairpin_tm'],
                        'homodimer_dg': quality['homodimer_dg'],
                        'distance': v5nc_start - primer_end,
                        'tm_diff': tm_diff,
                    }
            if best_for_pos:
                forward_candidates.append(best_for_pos)
                primer_end = best_for_pos['start']  # 跳过本引物长度，保证非重叠
            else:
                primer_end -= 1

        # === Reverse 候选池: 距 v3NC end 越近越好 ===
        reverse_candidates = []
        rev_window_low = min(len(sequence), v3nc_end + min_dist)
        rev_window_high = min(len(sequence), v3nc_end + max_dist)
        template_start = rev_window_low
        while template_start < rev_window_high and len(reverse_candidates) < candidate_limit:
            best_for_pos = None
            for length in range(min_primer_len, max_primer_len + 1):
                template_end = template_start + length
                if template_end > rev_window_high:
                    continue
                template_seq = sequence[template_start:template_end].upper()
                primer_seq = self.reverse_complement(template_seq)
                quality = self._check_colony_primer_quality(
                    primer_seq, target_tm=target_tm, dimer_dg_limit=dimer_dg_limit
                )
                if not quality:
                    continue
                tm_diff = abs(quality['tm'] - target_tm)
                if best_for_pos is None or tm_diff < best_for_pos['tm_diff']:
                    best_for_pos = {
                        'sequence': primer_seq,
                        'template_start': template_start,
                        'template_end': template_end,
                        'length': length,
                        'tm': quality['tm'],
                        'gc': quality['gc'],
                        'hairpin_tm': quality['hairpin_tm'],
                        'homodimer_dg': quality['homodimer_dg'],
                        'distance': template_start - v3nc_end,
                        'tm_diff': tm_diff,
                    }
            if best_for_pos:
                reverse_candidates.append(best_for_pos)
                template_start = best_for_pos['template_end']  # 跳过本引物长度
            else:
                template_start += 1

        if not forward_candidates or not reverse_candidates:
            self.errors.append("菌落PCR引物设计失败：v5NC上游或v3NC下游候选区间内无合格引物")
            return None

        # === 贪心配对依次外推 ===
        pairs = []
        used_reverse_idx = set()
        for f in forward_candidates:
            if len(pairs) >= num_pairs:
                break
            # 与已选 forward 区间不重叠
            overlap = any(
                not (f['end'] <= p['forward']['start'] or f['start'] >= p['forward']['end'])
                for p in pairs
            )
            if overlap:
                continue

            for r_idx, r in enumerate(reverse_candidates):
                if r_idx in used_reverse_idx:
                    continue
                overlap_r = any(
                    not (r['template_end'] <= p['reverse']['template_start']
                         or r['template_start'] >= p['reverse']['template_end'])
                    for p in pairs
                )
                if overlap_r:
                    continue
                hetero_dg = self.calculate_dimer_dg(f['sequence'], r['sequence'])
                if hetero_dg is not None and abs(hetero_dg) >= dimer_dg_limit:
                    continue

                pair_idx = len(pairs) + 1
                f_name = self.generate_primer_name(vector_code, f"CPF{pair_idx}", f"{f['start']}-{f['end']}", prefix='OJYxxx', variant=variant)
                r_name = self.generate_primer_name(vector_code, f"CPR{pair_idx}", f"{r['template_start']}-{r['template_end']}", prefix='OJYxxx', variant=variant)
                amplicon_length = r['template_end'] - f['start']

                pairs.append({
                    'index': pair_idx,
                    'forward': {
                        'name': f_name,
                        'sequence': f['sequence'],
                        'start': f['start'],
                        'end': f['end'],
                        'length': f['length'],
                        'tm': f['tm'],
                        'gc': round(f['gc'], 1),
                        'hairpin_tm': f['hairpin_tm'],
                        'homodimer_dg': f['homodimer_dg'],
                        'distance': f['distance'],
                    },
                    'reverse': {
                        'name': r_name,
                        'sequence': r['sequence'],
                        'template_start': r['template_start'],
                        'template_end': r['template_end'],
                        'length': r['length'],
                        'tm': r['tm'],
                        'gc': round(r['gc'], 1),
                        'hairpin_tm': r['hairpin_tm'],
                        'homodimer_dg': r['homodimer_dg'],
                        'distance': r['distance'],
                    },
                    'amplicon_length': amplicon_length,
                    'heterodimer_dg': hetero_dg,
                    'insert_start_pos': v5nc_end,  # 插入位点起始（v5NC end，原始坐标）
                })
                used_reverse_idx.add(r_idx)
                break

        if not pairs:
            self.errors.append("菌落PCR引物设计失败：候选引物无法两两配对（异源二聚体或区间冲突）")
            return None
        if len(pairs) < num_pairs:
            self.errors.append(
                f"菌落PCR引物设计：仅找到 {len(pairs)}/{num_pairs} 对合格引物"
            )

        # === 计算下载表所需字段 + 重新评估 best ===
        # Start 参考点：优先用 GenBank 上的 "Start" 特征（如 Trim.ref.Start.pos）；
        # 图谱没标 Start 时回退到 v5NC 起点（部分载体本就没有 Start 标记）。
        if start_ref is None:
            start_ref = self.find_start_reference(parsed_data)
        if start_ref is None:
            start_ref = v5nc_start

        for pair in pairs:
            f = pair['forward']
            r = pair['reverse']
            fwd_start = f['start']
            rev_far_end = r['template_end']  # 反向引物 5' 起始对应的基因组坐标

            # upstream: 正向引物 5' 起始 → v5NC 起点之间的序列
            upstream_seq = sequence[fwd_start:v5nc_start].upper()
            # downstream: v3NC 末尾 → 反向引物（远端）之间的序列
            downstream_seq = sequence[v3nc_end:rev_far_end].upper()

            pair['upstream_seq'] = upstream_seq
            pair['downstream_seq'] = downstream_seq
            # upstream+downstream：合并长度（不是序列拼接）
            pair['combined_flank_length'] = len(upstream_seq) + len(downstream_seq)
            # Start_pos：正向引物 5' 起始到 Start 参考点的相对距离
            pair['start_pos'] = start_ref - fwd_start
            # 质量罚分，越低越好
            pair['score'] = self._score_colony_pair(pair)

        # best = 质量罚分最低者；同分时取扩增子较短（index 较小）的一对
        best_pair = min(pairs, key=lambda p: (p['score'], p['index']))
        for pair in pairs:
            pair['is_best'] = (pair is best_pair)

        return pairs

    @staticmethod
    def calculate_hairpin_tm(sequence, stem_length=4, max_stem=6):
        """计算序列中可能形成的hairpin的最高Tm"""
        sequence = sequence.upper()
        n = len(sequence)
        max_tm = None

        for sl in range(stem_length, max_stem + 1):
            for i in range(n - sl * 2):
                for j in range(i + sl, n - sl + 1):
                    stem1 = sequence[i:i + sl]
                    stem2 = sequence[j:j + sl]
                    stem2_rc = VectorAutomationDesigner.reverse_complement(stem2)

                    if stem1 == stem2_rc:
                        stem_tm = VectorAutomationDesigner.calculate_tm_t97(stem1)
                        if max_tm is None or stem_tm > max_tm:
                            max_tm = stem_tm
        return max_tm

    @staticmethod
    def has_simple_hairpin(sequence, stem_length=4, tm_threshold=40):
        hairpin_tm = VectorAutomationDesigner.calculate_hairpin_tm(sequence, stem_length)
        return hairpin_tm is not None and hairpin_tm >= tm_threshold

    @staticmethod
    def calculate_dimer_dg(primer1, primer2=None, mv_conc=100, dv_conc=3.4, dntp_conc=0, dna_conc=0.25):
        """使用primer3计算引物自/互二聚体ΔG"""
        if primer3 is None:
            return None
        try:
            if primer2:
                result = primer3.calcHeterodimer(
                    primer1,
                    primer2,
                    mv_conc=mv_conc,
                    dv_conc=dv_conc,
                    dntp_conc=dntp_conc,
                    dna_conc=dna_conc
                )
            else:
                result = primer3.calcHomodimer(
                    primer1,
                    mv_conc=mv_conc,
                    dv_conc=dv_conc,
                    dntp_conc=dntp_conc,
                    dna_conc=dna_conc
                )
            if result is None:
                return None
            # primer3返回单位为cal/mol, 转为kcal/mol
            return result.dg / 1000.0
        except Exception:
            return None

    @staticmethod
    def has_primer_dimer(primer, dg_limit=11):
        """判断单个引物是否存在明显自二聚体"""
        dg = VectorAutomationDesigner.calculate_dimer_dg(primer)
        if dg is None:
            return False
        return abs(dg) >= dg_limit

    @staticmethod
    def check_primer_interaction(primer1, primer2, dg_limit=11):
        """
        检查两个引物是否会相互配对（使用primer3 ΔG）
        """
        dg = VectorAutomationDesigner.calculate_dimer_dg(primer1, primer2)
        if dg is None:
            return False
        return abs(dg) >= dg_limit

    def generate_modified_genbank(self, design_result, parsed_data, primer_result, output_path, vector_name,
                                   colony_primers=None, modify=True, backbone_primers=None):
        """
        生成设计后的GenBank文件

        两种模式：
        - modify=True（改造）：把 [v5nc_end, v3nc_start) 换成 Cm-ccdB，下游坐标整体平移，
          跨插入区的原 feature 丢弃。
        - modify=False（不改造）：序列一个碱基都不动，offset=0，原 feature 全部原位保留
          （包括跨 iU20–iD20 的那些），只把 v5NC/v3NC/引物标注上去，不加 Cm-ccdB。

        两种模式都把 iU20 的 end 对齐到 v5nc_end、iD20 的 start 对齐到 v3NC 的新起点，
        因为下游 ParsingGenBank.addAnalysisFeaturesAndFragments 就是靠这两个坐标
        取出 [iU20.end, iD20.start) 整段替换成 [i5NC, gene, i3NC] 的——错位就会切错地方。

        Args:
            design_result: 克隆方法设计结果
            parsed_data: 解析后的GenBank数据
            primer_result: NC-PCR 引物设计结果（可能为None）
            output_path: 输出文件路径
            vector_name: 载体名称
            colony_primers: 菌落PCR引物列表（可选，5对）
            modify: 是否改造载体（False 时只标注不改序列）
            backbone_primers: 骨架PCR外向引物（仅不改造模式，可能为None）

        Returns:
            str: 输出文件路径
        """
        sequence = parsed_data['sequence']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']
        v5nc_start, v5nc_end = design_result['v5nc_location']
        v3nc_start, v3nc_end = design_result['v3nc_location']

        cm_ccdb_enzyme = None
        cm_ccdb_seq = ''
        cm_ccdb_warning = ''

        if modify:
            # 选择合适的 Cm-ccdB 片段
            cm_ccdb_enzyme, cm_ccdb_seq, cm_ccdb_warning = select_cm_ccdb_fragment(sequence)
            if cm_ccdb_warning:
                # 记录警告但不阻止生成（NNNN 片段仍然可以生成文件）
                design_result['cm_ccdb_warning'] = cm_ccdb_warning

            design_result['cm_ccdb_enzyme'] = cm_ccdb_enzyme

            # 构建改造后序列：移除v5NC和v3NC之间的序列，插入Cm-ccdB
            modified_seq = sequence[:v5nc_end] + cm_ccdb_seq + sequence[v3nc_start:]
            # 位移量：插入区域后的所有坐标需要偏移
            offset = len(cm_ccdb_seq) - (v3nc_start - v5nc_end)
            # v3NC 被推到 Cm-ccdB 之后
            v3nc_new_start = v5nc_end + len(cm_ccdb_seq)
            description = f"Modified vector - {design_result['method']} method"
        else:
            # 不改造：序列原样输出
            modified_seq = sequence
            offset = 0
            v3nc_new_start = v3nc_start
            description = f"Annotated vector (not modified) - {design_result['method']} method"

        # 创建新的SeqRecord，保留原始注释信息
        original_annotations = parsed_data.get('original_annotations', {})
        original_annotations['molecule_type'] = original_annotations.get('molecule_type', 'DNA')
        modified_record = SeqRecord(
            Seq(modified_seq),
            id=vector_name,
            name=vector_name,
            description=description,
            annotations=original_annotations
        )

        # ===== 保留客户原图谱的 features（平移坐标）=====
        original_features = parsed_data.get('original_features', [])

        for feat in original_features:
            # 跳过 iU20/iD20，后面单独添加
            feat_labels = feat.qualifiers.get('label', [])
            if any(l.lower() in {'iu20', 'id20'} for l in feat_labels):
                continue

            if not modify:
                # 不改造：序列长度没变，原 feature 全部原位保留——包括跨 iU20–iD20 的那些
                # （这些在改造模式下会被丢弃，因为它们覆盖的序列已经不存在了）
                modified_record.features.append(feat)
                continue

            try:
                feat_start = int(feat.location.start)
                feat_end = int(feat.location.end)
            except Exception:
                continue

            if feat_end <= v5nc_end:
                # feature 完全在插入点之前：位置不变
                modified_record.features.append(feat)
            elif feat_start >= v3nc_start:
                # feature 完全在插入点之后：平移 offset
                new_start = feat_start + offset
                new_end = feat_end + offset
                new_feat = SeqFeature(
                    FeatureLocation(new_start, new_end, strand=feat.location.strand),
                    type=feat.type,
                    qualifiers=feat.qualifiers
                )
                modified_record.features.append(new_feat)
            # 跨越插入区域的 feature 直接跳过（已被改造替换的区域）

        # ===== 添加改造相关的新 features =====
        iu20_strand = parsed_data.get('iu20_strand', 1)
        id20_strand = parsed_data.get('id20_strand', 1)

        # 1. iU20（GG/T4回文移位时，下边界需与v5NC下边界对齐）
        iu20_effective_end = min(iu20_end, v5nc_end)
        iu20_feature = SeqFeature(
            FeatureLocation(iu20_start, iu20_effective_end, strand=iu20_strand),
            type="misc_feature",
            qualifiers={'label': ['iU20']}
        )
        modified_record.features.append(iu20_feature)

        # 2. v5NC
        v5nc_feature = SeqFeature(
            FeatureLocation(v5nc_start, v5nc_end),
            type="misc_feature",
            qualifiers={'label': ['v5NC']}
        )
        modified_record.features.append(v5nc_feature)

        # 3. Cm-ccdB（插入在v5nc_end位置）；不改造模式下没有这个 feature
        if modify:
            cm_ccdb_label = f"Cm-ccdB_{cm_ccdb_enzyme}"
            cm_ccdb_note = f"Chloramphenicol resistance and ccdB ({cm_ccdb_enzyme} sites)"
            if cm_ccdb_warning:
                cm_ccdb_note += f" WARNING: {cm_ccdb_warning}"
            cm_ccdb_feature = SeqFeature(
                FeatureLocation(v5nc_end, v3nc_new_start),
                type="CDS",
                qualifiers={'label': [cm_ccdb_label], 'note': [cm_ccdb_note]}
            )
            modified_record.features.append(cm_ccdb_feature)

        # 4. v3NC（改造模式下被推到 Cm-ccdB 之后；不改造模式下就是原位）
        v3nc_new_end = v3nc_new_start + (v3nc_end - v3nc_start)
        v3nc_feature = SeqFeature(
            FeatureLocation(v3nc_new_start, v3nc_new_end),
            type="misc_feature",
            qualifiers={'label': ['v3NC']}
        )
        modified_record.features.append(v3nc_feature)

        # 4.1 NC-PCR primers (Gibson only)
        if primer_result:
            forward = primer_result.get('forward')
            reverse = primer_result.get('reverse')

            if forward and forward.get('sequence'):
                forward_seq = forward['sequence']
                forward_start = v5nc_start
                forward_end = forward_start + len(forward_seq)
                forward_label = forward.get('name') or 'Forward Primer'
                forward_notes = [f"Sequence: {forward_seq}"]
                if forward.get('tm') is not None:
                    forward_notes.append(f"T97: {forward['tm']}C")
                forward_feature = SeqFeature(
                    FeatureLocation(forward_start, forward_end, strand=1),
                    type="primer_bind",
                    qualifiers={'label': [forward_label], 'note': forward_notes}
                )
                modified_record.features.append(forward_feature)

            if reverse and reverse.get('sequence'):
                reverse_seq = reverse['sequence']
                reverse_end = v3nc_end
                reverse_start = reverse_end - len(reverse_seq)
                v3nc_offset = v3nc_new_start - v3nc_start
                reverse_start += v3nc_offset
                reverse_end += v3nc_offset
                reverse_label = reverse.get('name') or 'Reverse Primer'
                reverse_notes = [f"Sequence: {reverse_seq}"]
                if reverse.get('tm') is not None:
                    reverse_notes.append(f"T97: {reverse['tm']}C")
                reverse_feature = SeqFeature(
                    FeatureLocation(reverse_start, reverse_end, strand=-1),
                    type="primer_bind",
                    qualifiers={'label': [reverse_label], 'note': reverse_notes}
                )
                modified_record.features.append(reverse_feature)

        # 4.15 骨架PCR引物（外向，仅不改造模式）——两条背对背，产物即线性化骨架
        if backbone_primers:
            bb_forward = backbone_primers.get('forward') or {}
            bb_reverse = backbone_primers.get('reverse') or {}
            v3nc_offset = v3nc_new_start - v3nc_start

            if bb_forward.get('sequence') and bb_forward.get('template_start') is not None:
                # 正向锚在 v3NC 起点，随 v3NC 一起平移（不改造时 offset 为 0）
                bb_f_start = bb_forward['template_start'] + v3nc_offset
                bb_f_end = bb_forward['template_end'] + v3nc_offset
                bb_f_notes = [f"Sequence: {bb_forward['sequence']}", "Backbone PCR (outward)"]
                if bb_forward.get('tm') is not None:
                    bb_f_notes.append(f"T97: {bb_forward['tm']}C")
                modified_record.features.append(SeqFeature(
                    FeatureLocation(bb_f_start, bb_f_end, strand=1),
                    type="primer_bind",
                    qualifiers={'label': [bb_forward.get('name') or 'Backbone-F'], 'note': bb_f_notes}
                ))

            if bb_reverse.get('sequence') and bb_reverse.get('template_start') is not None:
                # 反向锚在 v5NC 终点，位于插入点之前，坐标不变
                bb_r_notes = [f"Sequence: {bb_reverse['sequence']}", "Backbone PCR (outward)"]
                if bb_reverse.get('tm') is not None:
                    bb_r_notes.append(f"T97: {bb_reverse['tm']}C")
                modified_record.features.append(SeqFeature(
                    FeatureLocation(bb_reverse['template_start'], bb_reverse['template_end'], strand=-1),
                    type="primer_bind",
                    qualifiers={'label': [bb_reverse.get('name') or 'Backbone-R'], 'note': bb_r_notes}
                ))

        # 4.2 Colony PCR primers (5对，对所有克隆方法都适用)
        if colony_primers:
            for pair in colony_primers:
                fwd = pair.get('forward') or {}
                rev = pair.get('reverse') or {}
                pair_idx = pair.get('index')

                fwd_seq = fwd.get('sequence')
                if fwd_seq and fwd.get('start') is not None:
                    # 正向引物在 v5NC 上游，坐标不变
                    fwd_start = fwd['start']
                    fwd_end = fwd['end']
                    fwd_label = fwd.get('name') or f'ColonyPCR-F-{pair_idx}'
                    fwd_notes = [f"Sequence: {fwd_seq}", f"Pair {pair_idx} (Colony PCR)"]
                    if fwd.get('tm') is not None:
                        fwd_notes.append(f"T97: {fwd['tm']}C")
                    if fwd.get('distance') is not None:
                        fwd_notes.append(f"Distance to v5NC: {fwd['distance']} bp")
                    modified_record.features.append(SeqFeature(
                        FeatureLocation(fwd_start, fwd_end, strand=1),
                        type="primer_bind",
                        qualifiers={'label': [fwd_label], 'note': fwd_notes}
                    ))

                rev_seq = rev.get('sequence')
                if rev_seq and rev.get('template_start') is not None:
                    # 反向引物模板在 v3NC 下游，需平移 offset
                    new_rev_start = rev['template_start'] + offset
                    new_rev_end = rev['template_end'] + offset
                    rev_label = rev.get('name') or f'ColonyPCR-R-{pair_idx}'
                    rev_notes = [f"Sequence: {rev_seq}", f"Pair {pair_idx} (Colony PCR)"]
                    if rev.get('tm') is not None:
                        rev_notes.append(f"T97: {rev['tm']}C")
                    if rev.get('distance') is not None:
                        rev_notes.append(f"Distance to v3NC: {rev['distance']} bp")
                    if pair.get('amplicon_length') is not None:
                        rev_notes.append(f"Amplicon: {pair['amplicon_length']} bp")
                    modified_record.features.append(SeqFeature(
                        FeatureLocation(new_rev_start, new_rev_end, strand=-1),
                        type="primer_bind",
                        qualifiers={'label': [rev_label], 'note': rev_notes}
                    ))

        # 5. iD20（位置需要调整）
        id20_new_start = v3nc_new_start + max(0, id20_start - v3nc_start)
        id20_new_end = v3nc_new_start + (id20_end - v3nc_start)
        id20_feature = SeqFeature(
            FeatureLocation(id20_new_start, id20_new_end, strand=id20_strand),
            type="misc_feature",
            qualifiers={'label': ['iD20']}
        )
        modified_record.features.append(id20_feature)

        # 写入GenBank文件
        SeqIO.write(modified_record, output_path, "genbank")

        return output_path

    # 已知的抗性标记列表，用于从无括号文件名中识别抗性
    KNOWN_RESISTANCES = ['Amp', 'Kan', 'Cm', 'Spec', 'Tet', 'Hyg', 'Blast', 'Puro', 'Neo', 'Zeo', 'Gen']

    def extract_resistance_from_filename(self, filename):
        """
        从文件名中提取抗性信息
        支持两种格式:
        - 有括号: pCVa999(Kan)-xxx.gb -> Kan
        - 无括号(Django去掉括号后): pCVa999Kan-xxx.gb -> Kan

        Args:
            filename: 文件名

        Returns:
            str: 抗性信息，如果未找到则返回None
        """
        # 优先匹配有括号的格式
        match = re.search(r'\(([^)]+)\)', filename)
        if match:
            return match.group(1)

        # 回退：从 pCVa + 数字 后面提取已知抗性标记
        match = re.search(r'pCVa\d+([A-Za-z]+)', filename)
        if match:
            suffix = match.group(1)
            for resistance in self.KNOWN_RESISTANCES:
                if suffix.startswith(resistance):
                    return resistance

        return None

    def extract_vector_code_from_filename(self, filename):
        """
        从文件名中提取载体编号（仅数字部分）
        支持两种格式:
        - 有括号: pCVa123(Amp)-xxx.gb -> pCVa123
        - 无括号: pCVa123Amp-xxx.gb -> pCVa123

        Args:
            filename: 文件名

        Returns:
            str: 载体编号
        """
        # 只匹配 pCVa + 数字部分，不把抗性吞进去
        match = re.search(r'(pCVa\d+)', filename)
        if match:
            return match.group(1)
        return 'pCVa001'  # 默认值

    def extract_filename_suffix(self, filename):
        """
        提取文件名中的描述部分
        支持两种格式:
        - 有括号: pCVa999(Kan)-Test-pET-28a.gb -> Test-pET-28a
        - 无括号: pCVa999Kan-Test-pET-28a.gb -> Test-pET-28a
        """
        base = os.path.basename(filename)
        if '-' in base:
            suffix = base.split('-', 1)[1]
        else:
            suffix = os.path.splitext(base)[0]
        suffix = os.path.splitext(suffix)[0].strip()
        return suffix or 'Modified'

    @staticmethod
    def generate_primer_name(vector_code, suffix, token, prefix='YHYxxxx', variant='M1'):
        """
        生成引物名称，编号用 xxxx 占位，待人工从引物总表分配唯一编号后替换。
        NC-PCR 默认前缀 YHYxxxx；菌落 PCR 传 prefix='OJYxxx'。
        variant 跟随图谱版本号：改造版 'M1'，不改造版 'A1'。
        """
        code = vector_code or 'Vector'
        return f"{prefix}-{code}{variant}-{suffix}"
