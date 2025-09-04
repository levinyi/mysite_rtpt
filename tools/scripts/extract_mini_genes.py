#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCR突变位点Mini Gene提取工具
从Excel文件中提取HGVSc和HGVSp信息，生成29个氨基酸长度的mini gene片段
"""

import pandas as pd
import re
import requests
import json
from typing import Dict, List, Tuple, Optional
import time

class MiniGeneExtractor:
    def __init__(self):
        self.ensembl_server = "https://grch37.rest.ensembl.org"  # hg19对应的Ensembl版本
        self.session = requests.Session()
        
        # 新增：frameshift左侧延展模式配置
        # 当为frameshift且提供了MT_Epitope时，允许窗口长度>29以同时包含突变前k个氨基酸与整个表位
        self.frameshift_left_extend: bool = True
        self.target_left_shared: int = 14   # 目标至少包含的突变前氨基酸数量
        self.post_epitope_extend: int = 14  # 新增：表位右侧额外延展的氨基酸数量
        self.max_window_len: int = 80       # 窗口最大长度上限（避免过长）
        # 新增：in-frame 插入优先包含模式配置
        self.insertion_include_mode: bool = True  # 对所有插入突变，尽量包含“完整插入段+左右各k”
        self.insertion_flank_k: int = 14
        
        # 氨基酸三字母到单字母的转换字典
        self.aa_three_to_one = {
            'Ala': 'A', 'Arg': 'R', 'Asn': 'N', 'Asp': 'D', 'Cys': 'C',
            'Gln': 'Q', 'Glu': 'E', 'Gly': 'G', 'His': 'H', 'Ile': 'I',
            'Leu': 'L', 'Lys': 'K', 'Met': 'M', 'Phe': 'F', 'Pro': 'P',
            'Ser': 'S', 'Thr': 'T', 'Trp': 'W', 'Tyr': 'Y', 'Val': 'V',
            'Ter': '*', 'Stop': '*'
        }

    def read_excel_data(self, file_path: str, sheet_name: str = "最后整合") -> pd.DataFrame:
        """
        读取Excel文件中的数据
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"成功读取Excel文件，共{len(df)}行数据")
            print(f"列名: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return None
    
    def three_to_one_aa(self, three_letter: str) -> str:
        """
        将三字母氨基酸缩写转换为单字母缩写
        """
        if not three_letter:
            return ''
        return self.aa_three_to_one.get(three_letter, three_letter)
    
    def check_epitope_containment(self, mini_gene_wt: str, mini_gene_mt: str, wt_epitope: str, mt_epitope: str) -> Tuple[bool, bool]:
        """
        检查epitope序列是否包含在mini gene中
        """
        wt_contains = False
        mt_contains = False
        
        if wt_epitope and isinstance(wt_epitope, str) and mini_gene_wt:
            wt_contains = wt_epitope.upper() in mini_gene_wt.upper()
        
        if mt_epitope and isinstance(mt_epitope, str) and mini_gene_mt:
            mt_contains = mt_epitope.upper() in mini_gene_mt.upper()
        
        return wt_contains, mt_contains
    
    def parse_hgvs_protein(self, hgvs_p: str) -> Optional[Dict]:
        """
        解析HGVSp格式的蛋白质变异信息
        支持格式: 
        - 替换: ENSP00000123456.1:p.Ala123Val
        - 单个删除: ENSP00000123456.1:p.Met102del
        - 范围删除: ENSP00000123456.1:p.Ala156_Ala159del
        - 移码: ENSP00000123456.1:p.Asp394GlyfsTer52
        - 插入: ENSP00000123456.1:p.Glu1599_Ala1600insThrGly...
        """
        if pd.isna(hgvs_p) or not hgvs_p:
            return None
        
        try:
            # 提取蛋白质ID和变异信息
            if ':' in hgvs_p:
                parts = hgvs_p.split(':')
                protein_id = parts[0]
                variant_part = parts[1]
            else:
                protein_id = None
                variant_part = hgvs_p
                
            # 移除p.前缀
            if variant_part.startswith('p.'):
                variant_part = variant_part[2:]
            
            # 1. 范围删除 (如: Ala156_Ala159del) - 优先匹配
            range_deletion_pattern = r'^([A-Za-z]{3})(\d+)_([A-Za-z]{3})(\d+)del$'
            match = re.match(range_deletion_pattern, variant_part)
            if match:
                start_aa, start_pos, end_aa, end_pos = match.groups()
                return {
                    'protein_id': protein_id,
                    'ref_aa': start_aa,
                    'position': int(start_pos),
                    'end_position': int(end_pos),
                    'end_aa': end_aa,
                    'alt_aa': '',
                    'type': 'deletion',
                    'deletion_type': 'range'
                }
            
            # 2. 单个氨基酸删除 (如: Met102del) - 第二优先
            single_deletion_pattern = r'^([A-Za-z]{3})(\d+)del$'
            match = re.match(single_deletion_pattern, variant_part)
            if match:
                ref_aa, position = match.groups()
                return {
                    'protein_id': protein_id,
                    'ref_aa': ref_aa,
                    'position': int(position),
                    'alt_aa': '',
                    'type': 'deletion',
                    'deletion_type': 'single'
                }
            
            # 3. 移码突变 (如: Asp394GlyfsTer52) - 第三优先
            frameshift_pattern = r'^([A-Za-z]{3})(\d+)([A-Za-z]{3})fsTer(\d+)$'
            match = re.match(frameshift_pattern, variant_part)
            if match:
                ref_aa, position, alt_aa, ter_position = match.groups()
                return {
                    'protein_id': protein_id,
                    'ref_aa': ref_aa,
                    'position': int(position),
                    'alt_aa': alt_aa,
                    'ter_position': int(ter_position),
                    'type': 'frameshift'
                }
            
            # 4. 插入突变 (如: Glu1599_Ala1600insThrGly...) - 第四优先
            insertion_pattern = r'^([A-Za-z]{3})(\d+)_([A-Za-z]{3})(\d+)ins([A-Za-z]+)$'
            match = re.match(insertion_pattern, variant_part)
            if match:
                left_aa, left_pos, right_aa, right_pos, inserted_three = match.groups()
                return {
                    'protein_id': protein_id,
                    'ref_aa': left_aa,
                    'position': int(left_pos),  # 插入发生在left_pos和right_pos之间
                    'end_position': int(right_pos),
                    'end_aa': right_aa,
                    'alt_aa': inserted_three,  # 保留三字母串，在后续处理中转换
                    'type': 'insertion'
                }
            
            # 5. 替换突变 (如: Ala123Val) - 最后匹配
            substitution_pattern = r'^([A-Za-z]{3})(\d+)([A-Za-z]{3})$'
            match = re.match(substitution_pattern, variant_part)
            if match:
                ref_aa, position, alt_aa = match.groups()
                return {
                    'protein_id': protein_id,
                    'ref_aa': ref_aa,
                    'position': int(position),
                    'alt_aa': alt_aa,
                    'type': 'substitution'
                }
            
            print(f"无法解析的HGVSp格式: {variant_part}")
            return None
            
        except Exception as e:
            print(f"解析HGVSp时出错: {e}")
            return None
    
    def parse_hgvs_coding(self, hgvs_c: str) -> Optional[Dict]:
        """
        解析HGVSc格式的编码序列变异信息
        例如: ENST00000475866.2:c.1178dup 或 c.367C>T
        """
        if pd.isna(hgvs_c) or not hgvs_c:
            return None
        try:
            transcript_id = None
            c_part = hgvs_c
            if ':' in hgvs_c:
                tid, c_part = hgvs_c.split(':', 1)
                if tid.startswith('ENST'):
                    transcript_id = tid
            # 移除c.前缀
            if c_part.startswith('c.'):
                c_part = c_part[2:]
            # 替换
            m = re.match(r'^(\d+)([ATCG])>([ATCG])$', c_part, flags=re.IGNORECASE)
            if m:
                pos, ref_nt, alt_nt = m.groups()
                return {
                    'type': 'substitution',
                    'position': int(pos),
                    'ref_nucleotide': ref_nt.upper(),
                    'alt_nucleotide': alt_nt.upper(),
                    'transcript_id': transcript_id,
                    'raw': hgvs_c
                }
            # 单碱基删除 如 c.123del 或 区间删除 如 c.123_125del
            m = re.match(r'^(\d+)del$', c_part, flags=re.IGNORECASE)
            if m:
                return {
                    'type': 'deletion',
                    'start': int(m.group(1)),
                    'end': int(m.group(1)),
                    'transcript_id': transcript_id,
                    'raw': hgvs_c
                }
            m = re.match(r'^(\d+)_(\d+)del$', c_part, flags=re.IGNORECASE)
            if m:
                s, e = m.groups()
                return {
                    'type': 'deletion',
                    'start': int(s),
                    'end': int(e),
                    'transcript_id': transcript_id,
                    'raw': hgvs_c
                }
            # 插入 如 c.123_124insAT
            m = re.match(r'^(\d+)_(\d+)ins([ATCG]+)$', c_part, flags=re.IGNORECASE)
            if m:
                s, e, ins = m.groups()
                return {
                    'type': 'insertion',
                    'start': int(s),
                    'end': int(e),
                    'sequence': ins.upper(),
                    'transcript_id': transcript_id,
                    'raw': hgvs_c
                }
            # 重复 如 c.1178dup 或 c.1178dupA
            m = re.match(r'^(\d+)dup([ATCG]+)?$', c_part, flags=re.IGNORECASE)
            if m:
                pos, seq = m.groups()
                return {
                    'type': 'duplication',
                    'position': int(pos),
                    'sequence': (seq or '').upper(),
                    'transcript_id': transcript_id,
                    'raw': hgvs_c
                }
            return None
        except Exception as e:
            print(f"解析HGVSc时出错: {e}")
            return None

    def get_protein_sequence_from_ensembl(self, gene_symbol: str, transcript_id: str = None) -> Optional[str]:
        """
        从Ensembl获取蛋白质序列
        """
        try:
            if transcript_id:
                url = f"{self.ensembl_server}/sequence/id/{transcript_id}?type=protein"
            else:
                # 先获取基因信息
                gene_url = f"{self.ensembl_server}/lookup/symbol/homo_sapiens/{gene_symbol}?expand=1"
                gene_response = self.session.get(gene_url, headers={"Content-Type": "application/json"})
                
                if gene_response.status_code != 200:
                    print(f"无法获取基因 {gene_symbol} 的信息")
                    return None
                
                gene_data = gene_response.json()
                
                # 获取canonical transcript
                canonical_transcript = None
                if 'Transcript' in gene_data:
                    for transcript in gene_data['Transcript']:
                        if transcript.get('is_canonical', 0) == 1:
                            canonical_transcript = transcript['id']
                            break
                
                if not canonical_transcript:
                    print(f"无法找到基因 {gene_symbol} 的canonical transcript")
                    return None
                
                url = f"{self.ensembl_server}/sequence/id/{canonical_transcript}?type=protein"
            
            response = self.session.get(url, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                data = response.json()
                return data.get('seq', '')
            else:
                print(f"获取蛋白质序列失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取蛋白质序列时出错: {e}")
            return None
    
    def get_cds_sequence(self, transcript_id: str) -> Optional[str]:
        """
        获取转录本的CDS序列（不含UTR），用于在核酸层面应用c.HGVS并重翻译蛋白。
        """
        try:
            if not transcript_id:
                return None
            url = f"{self.ensembl_server}/sequence/id/{transcript_id}?type=cds"
            response = self.session.get(url, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                seq = data.get('seq', '')
                return seq if seq else None
            else:
                print(f"获取CDS失败，状态码: {response.status_code} - {transcript_id}")
                return None
        except Exception as e:
            print(f"获取CDS序列时出错: {e}")
            return None

    def translate_dna(self, dna_seq: str) -> str:
        """
        将DNA序列按标准遗传密码表翻译为蛋白质序列，遇到终止密码子即停止。
        非标准碱基导致的未知密码子翻译为'X'。
        """
        if not dna_seq:
            return ''
        dna = dna_seq.upper().replace('\n', '').replace('\r', '')
        codon_table = {
            'TTT':'F','TTC':'F','TTA':'L','TTG':'L',
            'CTT':'L','CTC':'L','CTA':'L','CTG':'L',
            'ATT':'I','ATC':'I','ATA':'I','ATG':'M',
            'GTT':'V','GTC':'V','GTA':'V','GTG':'V',
            'TCT':'S','TCC':'S','TCA':'S','TCG':'S',
            'CCT':'P','CCC':'P','CCA':'P','CCG':'P',
            'ACT':'T','ACC':'T','ACA':'T','ACG':'T',
            'GCT':'A','GCC':'A','GCA':'A','GCG':'A',
            'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*',
            'CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
            'AAT':'N','AAC':'N','AAA':'K','AAG':'K',
            'GAT':'D','GAC':'D','GAA':'E','GAG':'E',
            'TGT':'C','TGC':'C','TGA':'*','TGG':'W',
            'CGT':'R','CGC':'R','CGA':'R','CGG':'R',
            'AGT':'S','AGC':'S','AGA':'R','AGG':'R',
            'GGT':'G','GGC':'G','GGA':'G','GGG':'G'
        }
        prot = []
        for i in range(0, len(dna) - 2, 3):
            codon = dna[i:i+3]
            aa = codon_table.get(codon, 'X')
            if aa == '*':
                break
            prot.append(aa)
        return ''.join(prot)

    def segment_sequence_with_gs_padding(self, sequence: str, window_size: int = 29, step_size: int = 15) -> List[Dict]:
        """
        通用分段引擎：将长序列按窗口29AA、步长15AA（重叠14AA）进行分段
        最后一段不足时用GS-repeat补齐，并标注补了多少个GS
        按二肽单位补齐，因此最后一段可能为29AA或28AA
        
        Returns:
            List[Dict]: 每个字典包含 {'sequence': str, 'tile_index': int, 'total_tiles': int, 'gs_pad_count': int}
        """
        if not sequence:
            return []
        
        segments = []
        start = 0
        tile_index = 1
        
        # 第一阶段：生成所有完整/部分片段
        while start < len(sequence):
            end = min(start + window_size, len(sequence))
            segment = sequence[start:end]
            
            # 如果是最后一段且长度不足窗口大小，需要GS补齐
            gs_pad_count = 0
            if end == len(sequence) and len(segment) < window_size:
                need_padding = window_size - len(segment)
                # 按GS（二肽）为单位补齐
                gs_pairs = need_padding // 2
                gs_pad_count = gs_pairs
                segment += "GS" * gs_pairs
                
                # 如果补齐后仍差1个AA，则最后一段为28AA（避免半个GS）
                # 这种情况下不再补齐，保持28AA
            
            segments.append({
                'sequence': segment,
                'tile_index': tile_index,
                'gs_pad_count': gs_pad_count
            })
            
            # 计算下一个起始位置
            start += step_size
            tile_index += 1
            
            # 如果当前段已经覆盖到序列末尾，停止
            if end >= len(sequence):
                break
        
        # 添加总分段数信息
        total_tiles = len(segments)
        for segment in segments:
            segment['total_tiles'] = total_tiles
        
        return segments

    def extract_mini_gene_four_columns(self, protein_seq: str, mutation_pos: int, ref_aa: str, alt_aa: str, 
                                     mutation_type: str = 'substitution', end_position: int = None, 
                                     ter_position: int = None, hgvs_c_full: str = None, 
                                     transcript_id: str = None) -> Optional[Dict]:
        """
        按新规则提取mini gene的四列数据：WT-Seq, MUT-Seq, WT-Minigene, MUT-Seq-Minigene
        
        Args:
            protein_seq: 完整蛋白质序列
            mutation_pos: 突变位置 (1-based)
            ref_aa: 参考氨基酸（三字母）
            alt_aa: 突变氨基酸（三字母）
            mutation_type: 突变类型 ('substitution', 'deletion', 'insertion', 'frameshift')
            end_position: 删除结束位置 (1-based)
            ter_position: 移码终止位置
            hgvs_c_full: 完整的HGVSc信息
            transcript_id: 转录本ID
        
        Returns:
            Dict包含四列数据和分段信息
        """
        if not protein_seq or mutation_pos <= 0:
            return None
        
        pos_0based = mutation_pos - 1
        
        # 验证原始氨基酸
        if pos_0based < len(protein_seq):
            actual_aa = protein_seq[pos_0based]
            ref_aa_single = self.three_to_one_aa(ref_aa)
            if actual_aa != ref_aa_single:
                print(f"警告: 位置{mutation_pos}的氨基酸不匹配。期望: {ref_aa}({ref_aa_single}), 实际: {actual_aa}")
        
        # 对于插入突变，原始突变位置应显示为position+1（即插入位点右侧）
        display_position = mutation_pos + 1 if mutation_type == 'insertion' else mutation_pos
        
        result = {
            'mutation_type': mutation_type,
            'mutation_position': display_position,
            'ref_aa': ref_aa,
            'alt_aa': alt_aa,
            'wt_seq': '',
            'mut_seq': '',
            'wt_minigene': [],  # 可能是单条或多条
            'mut_seq_minigene': [],  # 可能是单条或多条
            'processing_notes': []
        }
        
        if mutation_type == 'substitution':
            # 单点突变：14AA + WT中心位点AA + 14AA（总长29）
            start_pos = max(0, pos_0based - 14)
            end_pos = min(len(protein_seq), start_pos + 29)
            
            wt_seq = protein_seq[start_pos:end_pos]
            mut_seq = list(wt_seq)
            relative_pos = pos_0based - start_pos
            if 0 <= relative_pos < len(mut_seq):
                alt_aa_single = self.three_to_one_aa(alt_aa)
                mut_seq[relative_pos] = alt_aa_single
            mut_seq = ''.join(mut_seq)
            
            # 使用分段引擎生成WT和MUT的minigene（单段，必要时GS补齐）
            wt_segments = self.segment_sequence_with_gs_padding(wt_seq)
            mut_segments = self.segment_sequence_with_gs_padding(mut_seq)
            
            result.update({
                'wt_seq': wt_seq,
                'mut_seq': mut_seq,
                'wt_minigene': wt_segments,
                'mut_seq_minigene': mut_segments
            })
            
        elif mutation_type == 'deletion':
            # 缺失：确定删除区间中间AA作为WT锚点
            if end_position and end_position >= mutation_pos:
                # 范围删除
                start_del = pos_0based  # 0-based
                end_del = end_position - 1  # 0-based
                deletion_length = end_del - start_del + 1
                
                # 计算中间AA位置
                if deletion_length % 2 == 1:
                    # 奇数长度，取正中间
                    middle_pos = start_del + deletion_length // 2
                else:
                    # 偶数长度，取靠前的那个
                    middle_pos = start_del + (deletion_length - 1) // 2
            else:
                # 单个删除
                middle_pos = pos_0based
            
            # WT-Seq: Up-14AA + Middle-AA + Dn-14AA
            wt_start = max(0, middle_pos - 14)
            wt_end = min(len(protein_seq), wt_start + 29)
            wt_seq = protein_seq[wt_start:wt_end]
            
            # MUT-Seq: Up-14AA + Dn-15AA（以缺失拼接点为中心）
            # 拼接点在删除起始位置
            mut_start = max(0, pos_0based - 14)
            
            # 构造删除后的序列
            if end_position and end_position >= mutation_pos:
                deleted_seq = protein_seq[:pos_0based] + protein_seq[end_position:]
            else:
                deleted_seq = protein_seq[:pos_0based] + protein_seq[pos_0based + 1:]
            
            mut_end = min(len(deleted_seq), mut_start + 29)
            mut_seq = deleted_seq[mut_start:mut_end]
            
            # 使用分段引擎生成WT和MUT的minigene（单段，必要时GS补齐）
            wt_segments = self.segment_sequence_with_gs_padding(wt_seq)
            mut_segments = self.segment_sequence_with_gs_padding(mut_seq)
            
            result.update({
                'wt_seq': wt_seq,
                'mut_seq': mut_seq,
                'wt_minigene': wt_segments,
                'mut_seq_minigene': mut_segments
            })
            
        elif mutation_type == 'insertion':
            # 插入：WT和MUT都以插入位点右侧为锚点（position+1），这样确保从D开始构造序列
            
            # 统一锚点：以插入位点右侧为锚点（position+1）
            anchor_after = pos_0based + 1
            
            # WT-Seq: 以右侧锚点回溯取Up-14AA + Dn-15AA
            wt_start = max(0, anchor_after - 14)
            wt_end = min(len(protein_seq), wt_start + 29)
            wt_seq = protein_seq[wt_start:wt_end]
            
            # MUT-Seq: 也以右侧锚点为基准构造长序列
            inserted_three = alt_aa or ''
            inserted_one_list = []
            if inserted_three:
                for i in range(0, len(inserted_three), 3):
                    triplet = inserted_three[i:i+3]
                    inserted_one_list.append(self.three_to_one_aa(triplet))
            inserted_one = ''.join(inserted_one_list)
            
            # 构造：Up-14AA（从右侧锚点回溯） + Inserted Seq + Dn-14AA（从右侧锚点开始）
            up_part = protein_seq[max(0, anchor_after - 14):anchor_after]
            dn_part = protein_seq[anchor_after:anchor_after + 14]
            
            mut_long_seq = up_part + inserted_one + dn_part
            
            # 对长序列进行分段
            mut_segments = self.segment_sequence_with_gs_padding(mut_long_seq)
            # WT 也需要使用分段引擎以便在靠近终止位点时补齐
            wt_segments = self.segment_sequence_with_gs_padding(wt_seq)
            
            result.update({
                'wt_seq': wt_seq,
                'mut_seq': mut_long_seq,
                'wt_minigene': wt_segments,
                'mut_seq_minigene': mut_segments
            })
            
        elif mutation_type == 'frameshift':
            # 移码：WT=Up-14AA + Dn-15AA，MUT=基于CDS重翻译后分段
            
            # WT-Seq: Up-14AA + Dn-15AA（以移码起始位点为中心）
            wt_start = max(0, pos_0based - 14)
            wt_end = min(len(protein_seq), wt_start + 29)
            wt_seq = protein_seq[wt_start:wt_end]
            
            # MUT-Seq: 尝试基于CDS重翻译获得新AA序列
            mut_long_seq = None
            if hgvs_c_full and transcript_id:
                coding = self.parse_hgvs_coding(hgvs_c_full)
                if coding and coding.get('transcript_id') == transcript_id:
                    cds = self.get_cds_sequence(transcript_id)
                    if cds:
                        try:
                            cds_list = list(cds)
                            mutated_cds = None
                            
                            if coding['type'] == 'duplication':
                                n = coding['position']
                                if 1 <= n <= len(cds_list):
                                    if coding.get('sequence'):
                                        ins_seq = coding['sequence']
                                    else:
                                        ins_seq = cds_list[n-1]
                                    mutated_cds = cds[:n] + ins_seq + cds[n:]
                            elif coding['type'] == 'insertion':
                                s, e, ins_seq = coding['start'], coding['end'], coding.get('sequence', '')
                                if 1 <= s <= e <= len(cds_list):
                                    mutated_cds = cds[:s] + ins_seq + cds[e:]
                            elif coding['type'] == 'deletion':
                                s, e = coding['start'], coding['end']
                                if 1 <= s <= e <= len(cds_list):
                                    mutated_cds = cds[:s-1] + cds[e:]
                            
                            if mutated_cds:
                                mt_protein_full = self.translate_dna(mutated_cds)
                                # 构造：Up-14AA + frameshift新AA序列
                                up_part = protein_seq[max(0, pos_0based - 14):pos_0based]
                                frameshift_part = mt_protein_full[pos_0based:] if pos_0based < len(mt_protein_full) else ""
                                mut_long_seq = up_part + frameshift_part
                                
                        except Exception as e:
                            print(f"CDS重翻译失败: {e}")
                            result['processing_notes'].append(f"CDS重翻译失败: {e}")
            
            # 如果CDS重翻译失败，使用回退策略
            if not mut_long_seq:
                alt_aa_single = self.three_to_one_aa(alt_aa) if alt_aa else ''
                up_part = protein_seq[max(0, pos_0based - 14):pos_0based]
                
                if ter_position:
                    frameshift_length = min(ter_position, len(protein_seq) - pos_0based)
                    if frameshift_length > 1:
                        frameshift_part = alt_aa_single + protein_seq[pos_0based + 1:pos_0based + frameshift_length]
                    else:
                        frameshift_part = alt_aa_single
                else:
                    frameshift_part = alt_aa_single + protein_seq[pos_0based + 1:]
                
                mut_long_seq = up_part + frameshift_part
                result['processing_notes'].append("使用回退策略生成移码序列")
            
            # 对长序列进行分段
            mut_segments = self.segment_sequence_with_gs_padding(mut_long_seq)
            # WT 使用分段引擎（靠近末端时补齐）
            wt_segments = self.segment_sequence_with_gs_padding(wt_seq)
            
            result.update({
                'wt_seq': wt_seq,
                'mut_seq': mut_long_seq,
                'wt_minigene': wt_segments,
                'mut_seq_minigene': mut_segments
            })

        
        return result

    def extract_mini_gene(self, protein_seq: str, mutation_pos: int, ref_aa: str, alt_aa: str, upstream: int = 14, downstream: int = 14, mutation_type: str = 'substitution', end_position: int = None, ter_position: int = None, hgvs_c_full: str = None, transcript_id: str = None, mt_epitope: Optional[str] = None):
        """
        保持向后兼容的旧接口，内部调用新的四列方法
        """
        new_result = self.extract_mini_gene_four_columns(
            protein_seq, mutation_pos, ref_aa, alt_aa, mutation_type, 
            end_position, ter_position, hgvs_c_full, transcript_id
        )
        
        if not new_result:
            return None
        
        # 转换为旧格式（取第一条mini-gene作为代表）
        wt_minigene = new_result['wt_minigene'][0]['sequence'] if new_result['wt_minigene'] else ''
        mut_minigene = new_result['mut_seq_minigene'][0]['sequence'] if new_result['mut_seq_minigene'] else ''
        
        # 为了兼容性，保持原有字段
        pos_0based = mutation_pos - 1
        start_pos = max(0, pos_0based - upstream)
        end_pos = min(len(protein_seq), start_pos + 29)
        
        # 对于插入突变，原始突变位置应显示为position+1（即插入位点右侧）
        display_position = mutation_pos + 1 if mutation_type == 'insertion' else mutation_pos
        
        return {
            'wild_type_sequence': wt_minigene,
            'mutated_sequence': mut_minigene,
            'mini_gene_length': len(wt_minigene),
            'original_mutation_position': display_position,
            'relative_mutation_position': max(0, pos_0based - start_pos + 1),
            'start_position_in_protein': start_pos + 1,
            'end_position_in_protein': end_pos,
            'upstream_length': max(0, pos_0based - start_pos),
            'downstream_length': max(0, end_pos - pos_0based - 1),
            'mutation_type': mutation_type,
            'window_anchor': 'new_rules',
            # 新增四列数据
            'four_columns_data': new_result
        }

    def process_mutations(self, df: pd.DataFrame) -> List[Dict]:
        """
        处理所有突变数据
        """
        results = []
        
        # 查找HGVSc和HGVSp列
        hgvsc_col = 'HGVSc' if 'HGVSc' in df.columns else None
        hgvsp_col = 'HGVSp' if 'HGVSp' in df.columns else None
        gene_col = 'Gene.Name' if 'Gene.Name' in df.columns else None
        
        # 查找epitope列
        wt_epitope_col = None
        mt_epitope_col = None
        for col in df.columns:
            if 'wt' in str(col).lower() and 'epitope' in str(col).lower():
                wt_epitope_col = col
            elif 'mt' in str(col).lower() and 'epitope' in str(col).lower():
                mt_epitope_col = col
        
        # 如果没找到，尝试其他可能的列名
        if not hgvsc_col:
            for col in df.columns:
                if 'hgvsc' in str(col).lower() or 'hgvs_c' in str(col).lower():
                    hgvsc_col = col
                    break
        
        if not hgvsp_col:
            for col in df.columns:
                if 'hgvsp' in str(col).lower() or 'hgvs_p' in str(col).lower():
                    hgvsp_col = col
                    break
                    
        if not gene_col:
            for col in df.columns:
                if 'gene' in str(col).lower() or '基因' in str(col).lower():
                    gene_col = col
                    break
        
        if not hgvsc_col or not hgvsp_col:
            print("未找到HGVSc或HGVSp列")
            print(f"可用列: {list(df.columns)}")
            return results
        
        print(f"找到HGVSc列: {hgvsc_col}")
        print(f"找到HGVSp列: {hgvsp_col}")
        if gene_col:
            print(f"找到基因列: {gene_col}")
        if wt_epitope_col:
            print(f"找到WT Epitope列: {wt_epitope_col}")
        if mt_epitope_col:
            print(f"找到MT Epitope列: {mt_epitope_col}")
        
        for idx, row in df.iterrows():
            try:
                hgvs_c = row[hgvsc_col]
                hgvs_p = row[hgvsp_col]
                gene_symbol = row[gene_col] if gene_col else None
                
                # 获取epitope序列
                wt_epitope = row[wt_epitope_col] if wt_epitope_col else None
                mt_epitope = row[mt_epitope_col] if mt_epitope_col else None
                
                print(f"\n处理第 {idx + 1} 行数据:")
                print(f"HGVSc: {hgvs_c}")
                print(f"HGVSp: {hgvs_p}")
                print(f"基因: {gene_symbol}")
                if wt_epitope:
                    print(f"WT Epitope: {wt_epitope}")
                if mt_epitope:
                    print(f"MT Epitope: {mt_epitope}")
                
                # 解析蛋白质变异
                protein_variant = self.parse_hgvs_protein(hgvs_p)
                if not protein_variant:
                    print(f"无法解析HGVSp: {hgvs_p}")
                    continue
                
                # 解析编码序列变异
                coding_variant = self.parse_hgvs_coding(hgvs_c)
                
                print(f"解析的蛋白质变异: {protein_variant}")
                
                # 获取蛋白质序列
                protein_seq = None
                
                # 首先尝试使用蛋白质ID直接获取序列
                if protein_variant.get('protein_id'):
                    protein_id = protein_variant['protein_id']
                    try:
                        url = f"{self.ensembl_server}/sequence/id/{protein_id}?type=protein"
                        response = self.session.get(url, headers={"Content-Type": "application/json"})
                        if response.status_code == 200:
                            data = response.json()
                            protein_seq = data.get('seq', '')
                            print(f"通过蛋白质ID获取到序列，长度: {len(protein_seq)}")
                    except Exception as e:
                        print(f"通过蛋白质ID获取序列失败: {e}")
                
                # 如果通过蛋白质ID获取失败，尝试使用基因名称
                if not protein_seq and gene_symbol:
                    protein_seq = self.get_protein_sequence_from_ensembl(gene_symbol)
                    if protein_seq:
                        print(f"通过基因名称获取到序列，长度: {len(protein_seq)}")
                
                if protein_seq:
                    # 从HGVSc中提取转录本ID以便frameshift重翻译使用
                    transcript_id = None
                    if isinstance(hgvs_c, str) and ':' in str(hgvs_c):
                        tid = str(hgvs_c).split(':', 1)[0]
                        if tid.startswith('ENST'):
                            transcript_id = tid
                    # 提取mini gene
                    mini_gene_info = self.extract_mini_gene(
                        protein_seq, 
                        protein_variant['position'],
                        protein_variant['ref_aa'],
                        protein_variant['alt_aa'],
                        mutation_type=protein_variant['type'],
                        end_position=protein_variant.get('end_position'),
                        ter_position=protein_variant.get('ter_position'),
                        hgvs_c_full=str(hgvs_c) if hgvs_c is not None else None,
                        transcript_id=transcript_id,
                        mt_epitope=mt_epitope
                    )
                    
                    if mini_gene_info:
                        # 使用四列中的WT-Seq和MUT-Seq进行Epitope包含检查（MT改为对MUT-Seq验证）
                        four_cols = mini_gene_info.get('four_columns_data') if isinstance(mini_gene_info, dict) else None
                        wt_check_seq = four_cols.get('wt_seq', mini_gene_info['wild_type_sequence']) if four_cols else mini_gene_info['wild_type_sequence']
                        mt_check_seq = four_cols.get('mut_seq', mini_gene_info['mutated_sequence']) if four_cols else mini_gene_info['mutated_sequence']

                        # IGFN1 定向调试输出
                        if gene_symbol == 'IGFN1':
                            print(f"[IGFN1 DEBUG] 用于WT Epitope验证的WT-Seq: {wt_check_seq} (len={len(wt_check_seq)})")
                            print(f"[IGFN1 DEBUG] 用于MT Epitope验证的MUT-Seq: {mt_check_seq} (len={len(mt_check_seq)})")
                            print(f"[IGFN1 DEBUG] mutated_sequence(首个tile): {mini_gene_info.get('mutated_sequence', '')}")
                            if isinstance(mt_epitope, str):
                                print(f"[IGFN1 DEBUG] MT_Epitope: {mt_epitope} (len={len(mt_epitope)})")
                        
                        wt_contains, mt_contains = self.check_epitope_containment(
                            wt_check_seq,
                            mt_check_seq,
                            wt_epitope,
                            mt_epitope
                        )
                        
                        result = {
                            'row_index': idx + 1,
                            'gene_symbol': gene_symbol,
                            'hgvs_c': hgvs_c,
                            'hgvs_p': hgvs_p,
                            'protein_variant': protein_variant,
                            'coding_variant': coding_variant,
                            'mini_gene_info': mini_gene_info,
                            'full_protein_length': len(protein_seq),
                            'wt_epitope': wt_epitope,
                            'mt_epitope': mt_epitope,
                            'wt_epitope_contained': wt_contains,
                            'mt_epitope_contained': mt_contains
                        }
                        results.append(result)
                        print(f"成功提取mini gene WT: {mini_gene_info['wild_type_sequence']}")
                        print(f"成功提取mini gene MT: {mini_gene_info['mutated_sequence']}")
                        print(f"WT Epitope包含检查: {wt_contains}")
                        print(f"MT Epitope包含检查: {mt_contains}")
                    else:
                        print("提取mini gene失败")
                else:
                    print(f"无法获取蛋白质序列 - 基因: {gene_symbol}, 蛋白质ID: {protein_variant.get('protein_id')}")
                
                # 添加延时避免API限制
                time.sleep(0.5)
                
            except Exception as e:
                print(f"处理第 {idx + 1} 行数据时出错: {e}")
                continue
        
        return results
    
    def save_results(self, results: List[Dict], output_file: str):
        """
        保存结果到文件（新版四列输出 + 分段明细）
        - Summary工作表：每行输出四列 WT-Seq, MUT-Seq, WT-Minigene, MUT-Seq-Minigene
          对于插入/移码，MUT-Seq-Minigene 会将多条分段用" | "拼接，并在有GS补齐的分段末尾标注"(NxGS)"
        - Tiles工作表：逐条列出WT和MUT所有minigene分段，包含tile_index、total_tiles、gs_pad_count
        """
        # 准备输出数据
        summary_rows = []
        tiles_rows = []

        for result in results:
            mini_gene = result['mini_gene_info']
            four_cols = mini_gene.get('four_columns_data') if isinstance(mini_gene, dict) else None

            # 兼容：如未提供四列数据，则退回旧字段
            if not four_cols:
                wt_seq = mini_gene.get('wild_type_sequence', '')
                mut_seq = mini_gene.get('mutated_sequence', '')
                wt_minigene_seq = wt_seq
                mut_minigene_joined = mut_seq
                tiles_count = 1
            else:
                wt_seq = four_cols.get('wt_seq', '')
                mut_seq = four_cols.get('mut_seq', '')

                # WT-Minigene：单条
                wt_minigenes = four_cols.get('wt_minigene', []) or []
                if wt_minigenes:
                    _wt_seg0 = wt_minigenes[0]
                    _wt_s = _wt_seg0.get('sequence', '')
                    _wt_gs = int(_wt_seg0.get('gs_pad_count', 0) or 0)
                    wt_minigene_seq = f"{_wt_s} ({_wt_gs}xGS)" if _wt_gs > 0 else _wt_s
                else:
                    wt_minigene_seq = ''

                # MUT-Minigene：可能多条
                mut_minigenes = four_cols.get('mut_seq_minigene', []) or []
                def fmt_seg(seg):
                    s = seg.get('sequence', '')
                    gs = int(seg.get('gs_pad_count', 0) or 0)
                    return f"{s} ({gs}xGS)" if gs > 0 else s
                mut_minigene_joined = ' | '.join([fmt_seg(seg) for seg in mut_minigenes]) if mut_minigenes else ''
                tiles_count = len(mut_minigenes) if mut_minigenes else 1

            # Summary 行
            summary_rows.append({
                '行号': result['row_index'],
                '基因名称': result['gene_symbol'],
                'HGVSc': result['hgvs_c'],
                'HGVSp': result['hgvs_p'],
                '突变类型': result['protein_variant'].get('type'),
                'WT-Seq': wt_seq,
                'MUT-Seq': mut_seq,
                'WT-Minigene': wt_minigene_seq,
                'MUT-Seq-Minigene': mut_minigene_joined,
                'Tiles-Count(MUT)': tiles_count,
                'Notes': '; '.join(four_cols.get('processing_notes', [])) if four_cols else '',
                # 兼容保留的旧版统计列
                'Mini Gene长度': mini_gene.get('mini_gene_length', len(wt_minigene_seq) if isinstance(wt_minigene_seq, str) else None),
                '原始突变位置': mini_gene.get('original_mutation_position'),
                '相对突变位置': mini_gene.get('relative_mutation_position'),
                '蛋白质起始位置': mini_gene.get('start_position_in_protein'),
                '蛋白质结束位置': mini_gene.get('end_position_in_protein'),
                '上游氨基酸数': mini_gene.get('upstream_length'),
                '下游氨基酸数': mini_gene.get('downstream_length'),
                '完整蛋白质长度': result.get('full_protein_length'),
                '参考氨基酸': result['protein_variant'].get('ref_aa'),
                '突变氨基酸': result['protein_variant'].get('alt_aa'),
                'WT_Epitope': result.get('wt_epitope'),
                'MT_Epitope': result.get('mt_epitope'),
                'WT_Epitope包含在Mini_Gene中': result.get('wt_epitope_contained'),
                'MT_Epitope包含在Mini_Gene中': result.get('mt_epitope_contained')
            })

        # 保存为Excel文件（仅Summary工作表）
        summary_df = pd.DataFrame(summary_rows)
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        print(f"\n结果已保存到: {output_file}")
        print(f"Summary工作表行数: {len(summary_df)}")

        return summary_df

def main():
    # 初始化提取器
    extractor = MiniGeneExtractor()
    
    # 读取Excel文件
    excel_file = "P49YFL_T_FROZEN精细筛选60个_ver1.xlsx"
    df = extractor.read_excel_data(excel_file)
    
    if df is None:
        print("无法读取Excel文件")
        return
    
    # 处理突变数据
    print("\n开始处理突变数据...")
    results = extractor.process_mutations(df)
    
    if results:
        # 保存结果
        output_file = "mini_genes_results.xlsx"
        output_df = extractor.save_results(results, output_file)
        
        # 显示统计信息
        print(f"\n=== 处理统计 ===")
        print(f"总输入行数: {len(df)}")
        print(f"成功处理: {len(results)}")
        print(f"成功率: {len(results)/len(df)*100:.1f}%")
        
        # 显示前几个结果
        print(f"\n=== 前3个结果示例 ===")
        for i, result in enumerate(results[:3]):
            mini_gene = result['mini_gene_info']
            print(f"\n{i+1}. {result['gene_symbol']} - {result['hgvs_p']}")
            print(f"   Mini Gene WT: {mini_gene['wild_type_sequence']}")
            print(f"   Mini Gene MT: {mini_gene['mutated_sequence']}")
            print(f"   长度: {mini_gene['mini_gene_length']} AA")
            print(f"   突变位置: {mini_gene['relative_mutation_position']}")
            if result.get('wt_epitope'):
                print(f"   WT Epitope包含: {result.get('wt_epitope_contained', False)}")
            if result.get('mt_epitope'):
                print(f"   MT Epitope包含: {result.get('mt_epitope_contained', False)}")
    else:
        print("没有成功处理任何突变数据")

if __name__ == "__main__":
    main()

    def get_cds_sequence(self, transcript_id: str) -> Optional[str]:
        """
        获取转录本的CDS序列（不含UTR），用于在核酸层面应用c.HGVS并重翻译蛋白。
        """
        try:
            if not transcript_id:
                return None
            url = f"{self.ensembl_server}/sequence/id/{transcript_id}?type=cds"
            response = self.session.get(url, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                seq = data.get('seq', '')
                return seq if seq else None
            else:
                print(f"获取CDS失败，状态码: {response.status_code} - {transcript_id}")
                return None
        except Exception as e:
            print(f"获取CDS序列时出错: {e}")
            return None

    def translate_dna(self, dna_seq: str) -> str:
        """
        将DNA序列按标准遗传密码表翻译为蛋白质序列，遇到终止密码子即停止。
        非标准碱基导致的未知密码子翻译为'X'。
        """
        if not dna_seq:
            return ''
        dna = dna_seq.upper().replace('\n', '').replace('\r', '')
        codon_table = {
            'TTT':'F','TTC':'F','TTA':'L','TTG':'L',
            'CTT':'L','CTC':'L','CTA':'L','CTG':'L',
            'ATT':'I','ATC':'I','ATA':'I','ATG':'M',
            'GTT':'V','GTC':'V','GTA':'V','GTG':'V',
            'TCT':'S','TCC':'S','TCA':'S','TCG':'S',
            'CCT':'P','CCC':'P','CCA':'P','CCG':'P',
            'ACT':'T','ACC':'T','ACA':'T','ACG':'T',
            'GCT':'A','GCC':'A','GCA':'A','GCG':'A',
            'TAT':'Y','TAC':'Y','TAA':'*','TAG':'*',
            'CAT':'H','CAC':'H','CAA':'Q','CAG':'Q',
            'AAT':'N','AAC':'N','AAA':'K','AAG':'K',
            'GAT':'D','GAC':'D','GAA':'E','GAG':'E',
            'TGT':'C','TGC':'C','TGA':'*','TGG':'W',
            'CGT':'R','CGC':'R','CGA':'R','CGG':'R',
            'AGT':'S','AGC':'S','AGA':'R','AGG':'R',
            'GGT':'G','GGC':'G','GGA':'G','GGG':'G'
        }
        prot = []
        for i in range(0, len(dna) - 2, 3):
            codon = dna[i:i+3]
            aa = codon_table.get(codon, 'X')
            if aa == '*':
                break
            prot.append(aa)
        return ''.join(prot)