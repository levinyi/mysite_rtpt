import os
import time
import pandas as pd
import sys
import re
from Bio.Seq import Seq
from Bio.Data import CodonTable


# Load codon usage data based on species
def load_codon_usage(species):
    codon_usage_file = f"/cygene4/pipeline/OEPCR/CodonUsageTable/Excel_CodonUsage_{species}.xlsx"
    codon_df = pd.read_excel(codon_usage_file, header=None)
    return  dict(zip(codon_df[0], codon_df[2]))

# Translate amino acid sequence to the corresponding nucleotide sequence using the most frequent codons
def translate_aa_to_codon(aa_seq, codon_usage):
    """Translate amino acid sequence to the corresponding nucleotide sequence using the most frequent codons."""
    standard_table = CodonTable.unambiguous_dna_by_id[1] # Consider moving this to a global if called frequently
    nucleotide_seq = ""
    for amino_acid in aa_seq:
        if amino_acid == '*':  # Handle stop codons
            nucleotide_seq += 'TGA'
            continue
        # Get condons that translate to the current amino acid
        possible_codons = [codon for codon, aa in standard_table.forward_table.items() if aa == amino_acid]
        if not possible_codons:
            print(f"Error: no codon found for amino acid {amino_acid}")
            raise ValueError(f"No codon found for amino acid {amino_acid} in {aa_seq}")
        # Choose the most frequent codon
        highest_freq_codon = max(possible_codons, key=lambda x: codon_usage.get(x, 0))
        nucleotide_seq += highest_freq_codon
    return nucleotide_seq

# Generate memo string based on GC ratios
def generate_memo(row):
    memo = "{$SAC-OptFbdSeq$[AT][AT][AT][AT][AT][AT][AT][AT];[GC][GC][GC][GC][GC][GC][GC][GC];}"
    # memo = "{$SAC-GlobalGC$min:0.4,max:0.6}"
    if pd.notna(row['LowestGCratio']) and pd.notna(row['HighestGCratio']):
        memo += "{$SAC-GlobalGC$min:" + f"{str(row['LowestGCratio'])}" + f",max:{str(row['HighestGCratio'])}"+"}"
    return memo

# Update forbidden sequences with new sequences
def update_forbidden_seqs(row):
    add_seqs = ['<BsaI>']
    # 将现有序列分割成列表，然后添加新序列，通过set去重，最后重新组合
    # df中有BsaI呢？df中有'GCCGAA'呢？,需要处理。
    # 如果 row 为空，则直接返回要添加的序列
    if pd.isna(row):
        return ';'.join(add_seqs) + ';'
    
    # 将现有序列分割成列表，然后处理带有 '[]' 的项
    existing_seqs = row.split(';')
    
    # 移除空字符串并替换 '[]' 为 '<>'
    updated_seqs = []
    for seq in existing_seqs:
        if seq.startswith('[') and seq.endswith(']'):
            updated_seqs.append('<' + seq[1:-1] + '>')
        else:
            updated_seqs.append(seq)

    # 合并现有序列和要添加的序列
    combined_seqs = updated_seqs + add_seqs
    # 利用set去重，然后转回列表保持顺序，最后组合成字符串
    unique_seqs = list(set(combined_seqs))
    
    # 返回以分号分隔的字符串
    return ';'.join(unique_seqs) + ';'

# Process sequence and return formatted amino acid and nucleotide sequences
def process_sequence(sequence, codon_usage=None):
    def optimize_dna(dna_seq):
        # 将DNA序列翻译成蛋白质序列，然后参考最常用的密码子，将蛋白质序列翻译回DNA序列，返回用[]包裹的氨基酸序列，和翻译后的DNA序列
        dna_seq_obj = Seq(dna_seq)
        aa_seq = str(dna_seq_obj.translate())
        formated_aa_seq = ''.join(f'[{aa}]' for aa in aa_seq)
        return formated_aa_seq

    def optimize_aa(aa_seq):
        # 优化逻辑是，将aa_seq中的每个氨基酸用[]包裹，和一个空字符串
        formated_aa_seq = ''.join(f'[{aa}]' for aa in aa_seq)
        optimized_seq = translate_aa_to_codon(aa_seq, codon_usage)
        return formated_aa_seq, optimized_seq

    PsNTA_CDS = []
    InitialNT_CDS = []

    # 按照[[...]]或者((...))分割序列
    mixed_segments = re.split(r'(\[\[.*?\]\]|\(\(.*?\)\))', sequence)  # Split by amino acid or DNA segments
    # 先检查是什么类型的序列：
    if len(mixed_segments) == 1:
        # 1. 普通DNA序列（不需要优化），PsNTA_CDS是原始的DNA序列，InitialNT_CDS为空。
        PsNTA_CDS.append(sequence)
        InitialNT_CDS.append("")
    elif len(mixed_segments) == 3 and mixed_segments[0] == '' and mixed_segments[2] == '' :
        if mixed_segments[1].startswith('((') and mixed_segments[1].endswith('))'):
            # 2.纯DNA序列, 需要优化： PsNTA_CDS是氨基酸序列，InitialNT_CDS是原始的DNA序列
            nt_segment = mixed_segments[1][2:-2]
            formatted_aa = optimize_dna(nt_segment)
            PsNTA_CDS.append(formatted_aa)
            InitialNT_CDS.append(nt_segment)  # 原始的DNA序列
        elif mixed_segments[1].startswith('[[') and mixed_segments[1].endswith(']]'):
            # 4.纯氨基酸序列
            aa_segment = mixed_segments[1][2:-2]
            formatted_aa, _ = optimize_aa(aa_segment)
            PsNTA_CDS.append(formatted_aa)
            InitialNT_CDS.append("")
    else:
        for segment in mixed_segments:
            if segment.startswith('[[') and segment.endswith(']]'):
                # 氨基酸序列
                aa_segment = segment[2:-2]
                formatted_aa, optimized_nt = optimize_aa(aa_segment)
                PsNTA_CDS.append(formatted_aa)
                InitialNT_CDS.append(optimized_nt)
            elif segment.startswith('((') and segment.endswith('))'):
                # 需要优化的DNA序列
                nt_segment = segment[2:-2]
                formatted_aa = optimize_dna(nt_segment)
                PsNTA_CDS.append(formatted_aa)
                InitialNT_CDS.append(nt_segment)
            else:
                # 普通DNA序列
                PsNTA_CDS.append(segment)
                InitialNT_CDS.append(segment)

    return ''.join(PsNTA_CDS), ''.join(InitialNT_CDS)

# Main processing function
def process_dataframe(input_file, column_names, optimization_method):
    df = pd.read_excel(input_file, skiprows=5, names=column_names)
    df.dropna(subset=['GeneName'], inplace=True)
    df.replace({'\n': ''}, regex=True, inplace=True)  # Remove newline characters.
    df['SeqAA'] = df['SeqAA'].str.upper()

    codon_usage_cache = {}
    def get_codon_usage(species):
        if species not in codon_usage_cache:
            codon_usage_cache[species] = load_codon_usage(species)
        return codon_usage_cache[species]

    # 为每行生成InitialNT_CDS和PsNTA_CDS两列
    df[['PsNTA_CDS', 'InitialNT_CDS']] = df.apply(
        lambda row: process_sequence(row['SeqAA'], get_codon_usage(row['Species'])), axis=1
    ).apply(pd.Series)

    # Common processing for all data
    df['Name'] = df['GeneName']
    df['Seq5NC'] = df['v5NC'].fillna('')
    df['Seq3NC'] = df['v3NC'].fillna('')
    df['Len5PBS'] = df['Seq5NC'].apply(len)
    df['Len3PBS'] = df['Seq3NC'].apply(len)
    df['ForbiddenSeqs'] = df['ForbiddenSeqs'].apply(update_forbidden_seqs)
    df['DoNotBindPrimers'] = ""
    df['AltNC_Combo'] = ""
    if optimization_method == 0:
        # forbidden_seq_Only
        df['Memo'] = ""
    else:
        df['Memo'] = df.apply(lambda row: generate_memo(row), axis=1)

    return df

def GeneToSACFlv1(df, optimization_method):
    df.dropna(subset=['GeneName'], inplace=True)
    df.replace({'\n': ''}, regex=True, inplace=True)  # Remove newline characters.
    df['SeqAA'] = df['SeqAA'].str.upper()

    codon_usage_cache = {}
    def get_codon_usage(species):
        if species not in codon_usage_cache:
            codon_usage_cache[species] = load_codon_usage(species)
        return codon_usage_cache[species]

    # 为每行生成InitialNT_CDS和PsNTA_CDS两列
    df[['PsNTA_CDS', 'InitialNT_CDS']] = df.apply(
        lambda row: process_sequence(row['SeqAA'], get_codon_usage(row['Species'])), axis=1
    ).apply(pd.Series)

    # Common processing for all data
    df['Name'] = df['GeneName']
    df['Seq5NC'] = df['v5NC'].fillna('')
    df['Seq3NC'] = df['v3NC'].fillna('')
    df['Len5PBS'] = df['Seq5NC'].apply(len)
    df['Len3PBS'] = df['Seq3NC'].apply(len)
    df['ForbiddenSeqs'] = df['ForbiddenSeqs'].apply(update_forbidden_seqs)
    df['DoNotBindPrimers'] = ""
    df['AltNC_Combo'] = ""
    if optimization_method == 0:
        # forbidden_seq_Only
        df['Memo'] = ""
    else:
        df['Memo'] = df.apply(lambda row: generate_memo(row), axis=1)

    return df

if __name__ == "__main__":
    input_file = sys.argv[1]   # Input file 
    output_path = sys.argv[2]  # Output path
    optimization_method = int(sys.argv[3])  # 0: forbidden_seq_Only, 1: NoFoldingCheck, 2:LongGene_Relax
    column_names = ["GeneName", "SeqAA", "Species", "ForbiddenSeqs", "LowestGCratio", "HighestGCratio", "Vector_ID", "v5NC", "v3NC", "备注"]
    
    # main function
    # df = process_dataframe(input_file, column_names, optimization_method)
    df = pd.read_excel(input_file, skiprows=5, names=column_names)
    # df.dropna(subset=['GeneName'], inplace=True)
    # df.replace({'\n': ''}, regex=True, inplace=True)  # Remove newline characters.
    # df['SeqAA'] = df['SeqAA'].str.upper()
    df = GeneToSACFlv1(df, optimization_method)


    # Save to file or further processing
    selected_columns = df[["Name","Seq5NC","PsNTA_CDS","Seq3NC","Len5PBS","Len3PBS","DoNotBindPrimers","ForbiddenSeqs","Species","AltNC_Combo","InitialNT_CDS","Memo"]]
    _date = time.strftime("%Y%m%d_%H%M%S")
    _date2 = time.strftime("%Y%m%d")
    
    output_file = os.path.join(output_path, f"_SACfIv1_FLCoOp_[R{_date2[2:]}01]_{_date}.txt")
    selected_columns.to_csv(output_file, sep="\t", header=True, index=False)

