import re
from Bio.Seq import Seq
from Bio.SeqUtils.lcc import lcc_simp
import pandas as pd


class DNARepeatsFinder:
    def __init__(self, data_set=None, sequence=None):
        '''
        够接受单个序列或者数据集
        '''
        if data_set is not None:
            self.data_set = data_set
            self.suffix_arrays = {}
            self.lcps_arrays = {}

            # 为每个序列构建后缀数组和LCP数组,预先计算每条序列的后缀数组和LCP数组
            for index, row in data_set.iterrows():
                seq = row['sequence']
                self.suffix_arrays[index] = self.build_suffix_array(seq)
                self.lcps_arrays[index] = self.find_lcp(seq, self.suffix_arrays[index])
        elif sequence is not None:
            self.s = sequence
            self.sa = self.build_suffix_array(sequence)
            self.lcp = self.find_lcp(sequence, self.sa)

    @staticmethod
    def build_suffix_array(s):
        """Build suffix array of s in O(n log n)"""
        n = len(s)
        suffixes = sorted((s[i:], i) for i in range(n))
        sa = [suffix[1] for suffix in suffixes]
        return sa

    @staticmethod
    def find_lcp(s, sa):
        """Find the longest common prefix (LCP) array for `s` using the suffix array `sa`."""
        n = len(s)
        rank = [0] * n
        lcp = [0] * n

        for i in range(n):
            rank[sa[i]] = i

        h = 0
        for i in range(n):
            if rank[i] > 0:
                j = sa[rank[i] - 1]
                while (i + h < n) and (j + h < n) and (s[i + h] == s[j + h]):
                    h += 1
                lcp[rank[i]] = h
                if h > 0:
                    h -= 1
        return lcp
    
    def _get_sequence_data(self, index=None):
        if index is not None:
            return self.data_set.loc[index, 'sequence'], self.suffix_arrays[index], self.lcps_arrays[index]
        return self.s, self.sa, self.lcp
    
    def is_homopolymer(self, unit):
        '''Check if a given DNA sequence is a homopolymer (consisting of only one type of base).'''
        return len(set(unit)) == 1
    
    def calculate_gc_content(self, sequence):
        '''
        Calculate the GC content of a DNA sequence.
        '''
        sequence = sequence.upper().replace(" ", "")
        gc_count = sequence.count('G') + sequence.count('C')
        gc_content = (gc_count / len(sequence)) * 100
        return round(gc_content, 2)

    def calculate_homopolymer_penalty_score(self, length):
        return length *10 if length > 10 else length
    
    def calculate_tandem_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_dispersed_repeats_penalty_score(self, length, count):
        return round(((length - 15) / 2 if length > 15 else 0) * count, 1)
    
    def calculate_palindrome_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_inverted_repeats_penalty_score(self, length, max_distance):
        return round((length - 10) - (max_distance-20), 1)
    
    def calculate_WS_motifs_penalty_score(self, length, min_len=8):
        return round((length - min_len + 1) / 2 , 1)
    
    def calculate_local_gc_penalty_score(self, gc_content, min_GC_threshold=None, max_GC_threshold=None):
        if min_GC_threshold is not None and gc_content < min_GC_threshold:
            penalty_score = round(abs(min_GC_threshold - gc_content + 1) / 10, 1)
        elif max_GC_threshold is not None and gc_content > max_GC_threshold:
            penalty_score = round(abs(gc_content - max_GC_threshold + 1) / 10, 1)
        else:
            # 表示不在范围内
            penalty_score = 0
        return penalty_score

    # 1) Tandem Repeats
    def find_tandem_repeats(self, index=None, min_unit=3, min_copies=3):
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)
        
        repeats_temp = []
        for i in range(n):
            for unit_length in range(min_unit, n - sa[i]):
                repeat_unit = s[sa[i]:sa[i] + unit_length]
                if self.is_homopolymer(repeat_unit):
                    continue

                repeat_count = 1
                for j in range(sa[i] + unit_length, n, unit_length):
                    if s[j:j + unit_length] == repeat_unit:
                        repeat_count += 1
                    else:
                        break

                if repeat_count >= min_copies:
                    actual_length = repeat_count * unit_length
                    repeats_temp.append({
                        'sequence': repeat_unit * repeat_count,
                        'start': sa[i],
                        'end': sa[i] + actual_length - 1,
                    })
        # 根据start位置对repeats_temp进行排序
        repeats_temp.sort(key=lambda x: x['start'])
        # 合并重复序列
        repeats = []
        for repeat in repeats_temp:
            print(repeat)
            if repeats and repeats[-1]['end'] >= repeat['start'] - 1:
                old_end = repeats[-1]['end']
                new_end = max(old_end, repeat['end'])
                repeats[-1]['end'] = new_end
                repeats[-1]['sequence'] = s[repeats[-1]['start']:new_end + 1]
            else:
                repeats.append(repeat)

        for repeat in repeats:
            repeat['length'] = len(repeat['sequence'])
            repeat['seqType'] = 'tandem_repeats'
            repeat['gc_content'] = self.calculate_gc_content(repeat['sequence'])
            repeat['penalty_score'] = self.calculate_tandem_repeats_penalty_score(repeat['length'])

        # 处理空结果，仍然返回相应的表头
        if not repeats:
            repeats = [{
                'seqType': 'tandem_repeats',
                'sequence': '',
                'start': '',
                'end': '',
                'length': '',
                'gc_content': '',
                'penalty_score': '',
            }]
        return repeats

    # 2) Dispersed Repeats
    def merge_potential_repeats(self, potential_repeats):
        # 按照序列的起始位置排序
        sorted_repeats = sorted(potential_repeats.items(), key=lambda x: x[1][0])
        merged_repeats = {}

        for seq, positions in sorted_repeats:
            merged = False
            for merged_seq in list(merged_repeats.keys()):
                merged_positions = merged_repeats[merged_seq]

                # 检查是否应该合并：如果序列的起始位置接近并且序列有重叠或接近
                if abs(positions[0] - merged_positions[-1]) <= len(seq):
                    # 合并序列：选择更长的序列保留，并合并位置
                    if len(seq) > len(merged_seq):
                        merged_repeats[seq] = merged_positions + positions
                        del merged_repeats[merged_seq]  # 删除旧的短序列
                    else:
                        merged_repeats[merged_seq].extend(positions)
                    merged_repeats[seq if len(seq) > len(merged_seq) else merged_seq] = sorted(set(merged_repeats[seq if len(seq) > len(merged_seq) else merged_seq]))  # 去重并排序
                    merged = True
                    break

            if not merged:
                merged_repeats[seq] = positions

        return merged_repeats

    def find_dispersed_repeats(self, index=None, min_len=16):
        s, sa, lcp = self._get_sequence_data(index)
        
        repeats = []
        n = len(s)
        potential_repeats = {}

        # 收集所有潜在的重复序列
        for i in range(1, n):
            length = lcp[i]
            if length >= min_len:
                start_index = sa[i]
                seq = s[start_index:start_index + length]
                if seq not in potential_repeats:
                    potential_repeats[seq] = []
                potential_repeats[seq].append(start_index)
        
        merged_repeats = self.merge_potential_repeats(potential_repeats)
        # print("merged_repeats", merged_repeats)
        # 转换为最终输出格式
        for seq, positions in merged_repeats.items():
            # 根据序列去重新找到起始位置和结束位置
            matches = [match.start() for match in re.finditer(re.escape(seq), s)]
            if len(matches) >= 2:  # 至少要有两个以上的重复位置才算分散重复
                distances = [matches[j] - matches[j - 1] for j in range(1, len(matches))]
                if all(d >= min_len for d in distances):
                    repeats.append({
                        'seqType': 'long_repeats',
                        'sequence': seq,
                        'start': matches,
                        'end': [match + len(seq) - 1 for match in matches],
                        'gc_content': self.calculate_gc_content(seq),
                        'length': len(seq),
                        'penalty_score': self.calculate_dispersed_repeats_penalty_score(len(seq), len(matches))
                    })

        # 处理空结果，仍然返回相应的表头
        if not repeats:
            repeats = [{
                'seqType': 'long_repeats',
                'sequence': '',
                'start': '',
                'end': '',
                'gc_content': '',
                'length': '',
                'penalty_score': '',
            }]
        return repeats

    # 3) Palindrome Repeats
    def find_palindrome_repeats(self, index=None, min_len=15):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        palindromes = []
        excluded_combinations = {"AT", "TA", "CG", "GC","AC", "CA", "GT", "TG"}

        def is_excluded(sequence):
            if len(set(sequence)) == 2 and sequence[:2] in excluded_combinations:
                return True
            return False
        
        # 遍历每个可能的中心点
        for center in range(n):
            # 奇数长度的回文
            start, end = center, center
            while start >= 0 and end < n and s[start] == s[end]:
                if end - start + 1 >= min_len:
                    palindromes.append({
                        'seqType': 'palindrome_repeats',
                        'sequence': s[start:end+1],
                        'start': start,
                        'end': end,
                        'length': end - start + 1,
                        'penalty_score': self.calculate_palindrome_repeats_penalty_score(end - start + 1),
                    })
                start -= 1
                end += 1
            
            # 偶数长度的回文
            start, end = center, center + 1
            while start >= 0 and end < n and s[start] == s[end]:
                if end - start + 1 >= min_len:
                    palindromes.append({
                        'seqType': 'palindrome_repeats',
                        'sequence': s[start:end+1],
                        'start': start,
                        'end': end,
                        'length': end - start + 1,
                        'penalty_score': self.calculate_palindrome_repeats_penalty_score(end - start + 1),
                    })
                start -= 1
                end += 1
        
        # 合并重复序列
        palindromes.sort(key=lambda x: x['start'])

        merged_palindromes = []
        for palindrome in palindromes:
            if merged_palindromes and merged_palindromes[-1]['end'] >= palindrome['start'] - 1:
                old_end = merged_palindromes[-1]['end']
                new_end = max(old_end, palindrome['end'])
                merged_palindromes[-1]['end'] = new_end
                merged_palindromes[-1]['sequence'] = s[merged_palindromes[-1]['start']:new_end + 1]
                merged_palindromes[-1]['length'] = new_end - merged_palindromes[-1]['start'] + 1
                merged_palindromes[-1]['gc_content'] = self.calculate_gc_content(merged_palindromes[-1]['sequence'])
                merged_palindromes[-1]['penalty_score'] = self.calculate_palindrome_repeats_penalty_score(merged_palindromes[-1]['length'])
            else:
                merged_palindromes.append(palindrome)

        # 处理空结果，仍然返回相应的表头
        if not merged_palindromes:
            merged_palindromes = [{
                'seqType': 'palindrome_repeats',
                'sequence': '',
                'start': '',
                'end': '',
                'length': '',
                'gc_content': '',
                'penalty_score': '',
            }]
        return merged_palindromes

    # 4) Inverted Repeats
    def find_inverted_repeats(self, index=None, min_len=10):
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)

        def reverse_complement(seq):
            complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
            return ''.join(complement[base] for base in reversed(seq.upper()))

        # 构建反向互补序列的索引
        rev_comp_index = {}
        for i in range(n):
            for length in range(min_len, n - i + 1):
                segment = s[i:i + length]
                rev_comp = reverse_complement(segment)
                if rev_comp not in rev_comp_index:
                    rev_comp_index[rev_comp] = []
                rev_comp_index[rev_comp].append((i, length))

        inverted_repeats = []
        # 检索可能的倒置重复
        for i in range(n - min_len + 1):
            for length in range(min_len, n - i + 1):
                segment = s[i:i + length]
                if segment in rev_comp_index:
                    for j, l in rev_comp_index[segment]:
                        if i + length <= j:  # 确保不重叠
                            distance = j - (i + length)
                            inverted_repeats.append({
                                'seqType': 'inverted_repeats',
                                'sequence': segment,
                                'inverted_sequence': segment,
                                'start1': i,
                                'end1': i + length - 1,
                                'start2': j,
                                'end2': j + l - 1,
                                'length': l,
                                'distance': distance,
                                'penalty_score': self.calculate_inverted_repeats_penalty_score(len(segment), distance),
                            })

        # 处理空结果，仍然返回相应的表头
        if not inverted_repeats:
            inverted_repeats = [{
                'seqType': 'inverted_repeats',
                'sequence': '',
                'inverted_sequence': '',
                'start1': '',
                'end1': '',
                'start2': '',
                'end2': '',
                'length': '',
                'distance': '',
                'penalty_score': '',
            }]
        return inverted_repeats

    # 5) Homopolymers
    def find_homopolymers(self, index=None, min_len=7):
        s, sa, lcp = self._get_sequence_data(index)
    
        homopolymers = []
        n = len(s)
        start = 0
        for i in range(1, n):
            if s[i] != s[i - 1]:
                length = i - start
                if length >= min_len:
                    seq = s[start:i]
                    homopolymers.append({
                        'seqType': 'homopolymers',
                        'sequence': seq,
                        'start': start,
                        'end': i - 1,
                        'length': length,
                        'penalty_score': self.calculate_homopolymer_penalty_score(length),
                    })
                start = i
        
        # 处理空结果，仍然返回相应的表头
        if not homopolymers:
            homopolymers = [{
                'seqType': 'homopolymers',
                'sequence': '',
                'start': '',
                'end': '',
                'length': '',
                'penalty_score': '',
            }]
        return homopolymers

    # 6) W8S8 Motifs
    def find_WS_motifs(self, index=None, min_W_length=8, min_S_length=8):
        s, sa, lcp = self._get_sequence_data(index)
        
        W_pattern = r'[AT]{' + str(min_W_length) + ',}'
        S_pattern = r'[GC]{' + str(min_S_length) + ',}'

        def find_motifs(pattern, motif_type):
            motifs = []
            for match in re.finditer(pattern, s):
                start, end = match.span()
                matched_sequence = s[start:end]
                matched_sequence2 = match.group(0)
                if not self.is_homopolymer(matched_sequence):
                    motifs.append({
                        'seqType': motif_type + '_motifs',
                        'motif_type': motif_type,
                        'sequence': s[start:end],
                        'start': start,
                        'end': end - 1,
                        'length': end - start,
                        'penalty_score': self.calculate_WS_motifs_penalty_score((end - start), min_len=min_S_length),
                    })
            return motifs

        W_motifs = find_motifs(W_pattern, 'W' + str(min_W_length))
        S_motifs = find_motifs(S_pattern, 'S' + str(min_S_length))

        motifs = W_motifs + S_motifs
        # 处理空结果，仍然返回相应的表头
        if not motifs:
            motifs = [{
                'seqType': 'W' + str(min_W_length) + 'S' + str(min_S_length) + '_motifs',
                'motif_type': '',
                'sequence': '',
                'start': '',
                'end': '',
                'length': '',
                'penalty_score': '',
            }]
        return motifs

    # 7) Local GC Content by Window
    def find_local_gc_content(self, index=None, window_size=30, min_GC_content=20, max_GC_content=80):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        if n < window_size:
            # 将整个序列作为一个窗口
            gc_content = self.calculate_gc_content(s)
            if gc_content < min_GC_content or gc_content > max_GC_content:
                return [{
                    'seqType': 'local_gc',
                    'length': n,
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(s, gc_content),
                }]
            return []
        
        gc_contents_temp = []

        for i in range(n - window_size + 1):
            window = s[i:i + window_size]
            gc_content = self.calculate_gc_content(window)
            
            if gc_content < min_GC_content or gc_content > max_GC_content:
                gc_contents_temp.append({
                    'sequence': window,
                    'start': i,
                    'end': i + window_size - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(gc_content, min_GC_content, max_GC_content),
                })

        # Merge overlapping windows according to the continuous sequence, 
        # do not merge windows with different regions.
        gc_contents = []
        for gc_content in gc_contents_temp:
            if gc_contents and gc_contents[-1]['end'] >= gc_content['start'] - 1:  # 表示有重叠
                # 扩展上一个窗口
                old_end = gc_contents[-1]['end']
                new_end = max(old_end, gc_content['end'])
                gc_contents[-1]['end'] = new_end
                gc_contents[-1]['sequence'] = s[gc_contents[-1]['start']:new_end + 1]
                # penalty score 要叠加
                gc_contents[-1]['penalty_score'] += gc_content['penalty_score']
            else:
                gc_contents.append(gc_content)
        # recalculate the GC content of the merged windows, and calculate the penalty score
        for gc_content in gc_contents:
            gc_content['seqType'] = 'local_gc'
            gc_content['length'] = len(gc_content['sequence'])
            gc_content['gc_content'] = self.calculate_gc_content(gc_content['sequence'])

        if not gc_contents:
            gc_contents = [{
                'seqType': 'local_gc',
                'length': '',
                'sequence': '',
                'start': '',
                'end': '',
                'gc_content': '',
                'penalty_score': '',
            }]
        return gc_contents
    
    def find_high_gc_content(self, index=None, window_size=30, max_GC_content=80):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        if n < window_size:
            gc_content = self.calculate_gc_content(s)
            if gc_content > max_GC_content:
                return [{
                    'seqType': 'highGC',
                    'length': n,
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_content), max_GC_content, max_GC_content),
                }]
            return []

        high_gc_contents_temp = []

        for i in range(n - window_size + 1):
            window = s[i:i + window_size]
            gc_content = self.calculate_gc_content(window)
            
            if gc_content > max_GC_content:
                high_gc_contents_temp.append({
                    'sequence': window,
                    'start': i,
                    'end': i + window_size - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_content), max_GC_content, max_GC_content),
                })

        high_gc_contents = self.merge_gc_windows(high_gc_contents_temp, s, 'highGC', min_GC_content=None, max_GC_content=max_GC_content)

        return high_gc_contents
    
    def find_low_gc_content(self, index=None, window_size=30, min_GC_content=20):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        if n < window_size:
            gc_content = self.calculate_gc_content(s)
            if gc_content < min_GC_content:
                return [{
                    'seqType': 'lowGC',
                    'length': n,
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_content), min_GC_content, min_GC_content),
                }]
            return []

        low_gc_contents_temp = []

        for i in range(n - window_size + 1):
            window = s[i:i + window_size]
            gc_content = self.calculate_gc_content(window)
            
            if gc_content < min_GC_content:
                low_gc_contents_temp.append({
                    'sequence': window,
                    'start': i,
                    'end': i + window_size - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_content), min_GC_content, min_GC_content),
                })

        low_gc_contents = self.merge_gc_windows(low_gc_contents_temp, s, 'lowGC', min_GC_content=min_GC_content, max_GC_content=None)

        return low_gc_contents

    def merge_gc_windows(self, gc_contents_temp, sequence, gc_type, min_GC_content=None, max_GC_content=None):
        gc_contents = []
        for gc_content in gc_contents_temp:
            if gc_contents and gc_contents[-1]['end'] >= gc_content['start'] - 1:  # 表示有重叠
                old_end = gc_contents[-1]['end']
                new_end = max(old_end, gc_content['end'])
                gc_contents[-1]['end'] = new_end
                gc_contents[-1]['sequence'] = sequence[gc_contents[-1]['start']:new_end + 1]
                gc_contents[-1]['penalty_score'] += gc_content['penalty_score']
            else:
                gc_contents.append(gc_content)

        for gc_content in gc_contents:
            gc_content['seqType'] = gc_type
            gc_content['length'] = len(gc_content['sequence'])
            gc_content['gc_content'] = self.calculate_gc_content(gc_content['sequence'])
            if gc_type == 'lowGC':
                gc_content['penalty_score'] = self.calculate_local_gc_penalty_score(float(gc_content['gc_content']), min_GC_content, max_GC_content)
            elif gc_type == 'highGC':
                gc_content['penalty_score'] = self.calculate_local_gc_penalty_score(float(gc_content['gc_content']), min_GC_content, max_GC_content)

        if not gc_contents:
            gc_contents = [{
                'seqType': gc_type,
                'length': '',
                'sequence': '',
                'start': '',
                'end': '',
                'gc_content': '',
                'penalty_score': '',
            }]
        return gc_contents

    # 8) Dinucleotide Repeats
    def find_dinucleotide_repeats(self, index=None, threshold=10):
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)
        repeats = []

        i = 0
        while i < n - 1:
            dinucleotide = s[i:i+2]
            if len(dinucleotide) < 2:
                break
            
            repeat_length = 2
            j = i + 2
            while j < n and s[j:j+2] == dinucleotide:
                repeat_length += 2
                j += 2
            
            if repeat_length >= threshold:
                sequence = dinucleotide * (repeat_length // 2)
                # 判断是否为homopolymer
                if dinucleotide[0] != dinucleotide[1]:
                    repeats.append({
                        'seqType': 'dinucleotide_repeats',
                        'sequence': sequence,
                        'start': i,
                        'end': i + repeat_length - 1,
                        'length': repeat_length,
                        'gc_content': self.calculate_gc_content(sequence),
                        'penalty_score': repeat_length // 2
                    })
            
            i += repeat_length  # 跳过已检测到的重复序列

        # 处理空结果，仍然返回相应的表头
        if not repeats:
            repeats = [{
                'seqType': 'dinucleotide_repeats',
                'sequence': '',
                'start': '',
                'end': '',
                'length': '',
                'gc_content': '',
                'penalty_score': '',
            }]
        return repeats

    # 9) lcc
    def get_lcc(self, index=None):
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)
        lcc = 0
        dna_seq = Seq(s)
        # protein_seq = dna_seq.translate()

        dna_complexity = lcc_simp(dna_seq)
        # protein_complexity = lcc_simp(protein_seq)

        return [{
            'seqType': 'LCC',
            'penalty_score': dna_complexity,
            # 'protein_complexity': protein_complexity,
        }]

    # 10) Length
    def get_length(self, index=None):
        s, sa, lcp = self._get_sequence_data(index)
        return [{
            'seqType': 'length',
            'length': len(s),
        }]



def convert_gene_table_to_RepeatsFinder_Format(gene_table):
    def expanded_rows_to_gene_table(df, gene_table):
        expanded_results = []
        all_columns = set()
        gene_analysis_types = []

        # 首先收集所有可能的列名
        for _, row in df.iterrows():
            for analysis_type, results_list in row.items():
                if analysis_type not in gene_analysis_types:
                    gene_analysis_types.append(analysis_type)
                if results_list:
                    for result in results_list:
                        for key, value in result.items():
                            column_name = f'{analysis_type}_{key}'
                            all_columns.add(column_name)

        # 按照检测类型和键的字母顺序排序列名
        gene_analysis_types = list(set(gene_analysis_types))  # 去除重复项
        sorted_columns = ['gene_id'] + sorted(all_columns, key=lambda x: (gene_analysis_types.index(x.split('_')[0]), x.split('_')[1]))

        # 初始化每个 result_dict，并确保所有可能的列名都在字典中
        for gene_id, row in df.iterrows():
            result_dict = {col: '' for col in sorted_columns}
            result_dict['gene_id'] = gene_id
            
            for analysis_type, results_list in row.items():
                if results_list:
                    for result in results_list:
                        for key, value in result.items():
                            column_name = f'{analysis_type}_{key}'
                            if 'penalty_score' in key:
                                if value == '':
                                    continue  # 跳过空值
                                if result_dict[column_name] != '':
                                    try:
                                        result_dict[column_name] += float(value)
                                    except ValueError:
                                        print(f'Error: {value} is not a valid float')
                                else:
                                    try:
                                        result_dict[column_name] = float(value)
                                    except ValueError:
                                        print(f'Error: {value} is not a valid float')
                            elif 'seqType' in key:
                                if value == '':
                                    continue
                                result_dict[column_name] = value
                            else:
                                if result_dict[column_name] != '':
                                    result_dict[column_name] += f';{value}'
                                else:
                                    result_dict[column_name] = str(value)
                else:
                    continue
                
            expanded_results.append(result_dict)

        expanded_df = pd.DataFrame(expanded_results)
        # 将所有带有penalty_score的列，求和赋值给total_penalty_score列
        penalty_columns = [col for col in expanded_df.columns if 'penalty_score' in col]
        expanded_df[penalty_columns] = expanded_df[penalty_columns].apply(pd.to_numeric, errors='coerce')
        expanded_df['total_penalty_score'] = expanded_df[penalty_columns].fillna(0).sum(axis=1).round(0).astype(int)

        gene_table = gene_table.merge(expanded_df, on='gene_id', how='left')

        return gene_table
    
    # Remove rows with None
    finder_dataset = DNARepeatsFinder(data_set=gene_table)

    results = {}
    for index, row in gene_table.iterrows():
        gene_id = row['gene_id']
        results[gene_id] = {
            # 'tandem_repeats': finder_dataset.find_tandem_repeats(index=index, min_unit=3, min_copies=3),
            'LongRepeats': finder_dataset.find_dispersed_repeats(index=index, min_len=16),
            # 'palindromes': finder_dataset.find_palindrome_repeats(index=index, min_len=15),
            # 'inverted_repeats': finder_dataset.find_inverted_repeats(index=index, min_len=10),
            'Homopolymers': finder_dataset.find_homopolymers(index=index, min_len=7),
            'W12S12Motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=12, min_S_length=12),
            'highGC': finder_dataset.find_high_gc_content(index=index, window_size=30, max_GC_content=80),
            'lowGC': finder_dataset.find_low_gc_content(index=index, window_size=30, min_GC_content=20),
            'LCC': finder_dataset.get_lcc(index=index),
            'doubleNT': finder_dataset.find_dinucleotide_repeats(index=index, threshold=12),
            'length': finder_dataset.get_length(index=index),
        }
    #将结果列表转换为DataFrame， 处理长度不一致问题
    df = pd.DataFrame(results).T
    
    gene_table = expanded_rows_to_gene_table(df, gene_table)

    return gene_table



# sequence = "ATGGTTTCCTGTGCAGCAaGTCTCtAAGATAAAGCGCTGCGTAGCATGTATCGTGTGCTGAAACCAGGTGGTCGTCTGCTGGTGCTGGAATTTAGCAAACCGATTATTGAACCGCTGAGCAAAGCGTATGATGCGTATAGCTTTCATGTCCTGCCGCGTATTGGTAGCCTGGTGGCGAACGATGCGGATAGCTATCGTTATCTGGCGGAAAGCATTCGTATGCATCCGGATCAGGATACCCTGAAAGCGATGATGCAGGATGCGGGCTTTGAAAGCGTGGACTACTATAACCTGACAGCTGGCGTTGTCGCCCTGCACCGCGGCTATAAGTTCGGGTCTGGTGGCAGCCATCATCATCATCATCATCATCATTGAGATCCGGCTGCTAACGATGGGTTGAGGATGGTTacccggaaccacatggagattacttgttgtaggagggaggacactatggaaatcaatacacacgcaacaagcatggagacacacatcaacggTAGCTGATCCTTGTCGCATGGTCGACGATTGATGCAcccaccatcgccaacTCGGGAATTCGGATTGGA"
# sequence = "ATGGTTTCCTGTGCAGCAaGTCTCtCAGTCACTATTCTTGATGGCAAGCAATATTCTGGCAACATTTGACATAAAGAAGAAGATTGCTGCTGATGGTACTATTCTGGAACCTTCTATTGAGTGGACTGGATCAATGGCCATGTGAAAGCTTGGTACCGCGGCTAGCTAAGATCCGCTCTGATGGGTTGAGGATGGTTaacacccacgagcggatcggcatcaactttagccccgaatgtattgagagcatcaatactagggactgcacaatcaactggcatgaaaacaacgctagggatcatatgtccgaagcaggactcgaggccagcaatgctaccagggccctcatcagcactatttgggctagcatgtgccatagcactcggtgtaagtggattacacattgcgagagaaccgccatcaacttcgcctgcaccagcatcaacacccacgaggacatcagcacccggatcaccatcaacttcacccacgagatcaatTTGCAACGTACCTGGACTTGGTCGACGATTGATGCAaacaaccggtgtgAATCGTTGCCATCTTGCC"
# sequence = "TGCTGTCTTGTCCAACGTaGTCTCtAACTGTGTTCAGAAGGGCCAGAAATGCCAAGGACTCAGGGGAGGGACCGGGTCATTGGGGTCAGGTTACTCCGGGTCATTGGGGTCAGGTGTCACCGGGTCATTGGGGTCAGGCTCTATGTTTGCTTTGATGTGTATCCTATGTCCAGTATGAAATAAAAACTGCCTCCTTCCACATTGAGAGACTTGGTCGACGATTGATGCAgagattacctcctgccatcggatctttacatttcgcgcatccagctaAACATGGACTCCTTGCGT"
# sequence = "ACGTACGTACGTACGTACGTACGTACACACACACACACACACGTGTGTGTGT"
# sequence = "CTCTAGTTAGGCTTCCGGGATAACCGATTGCGGAGACAGCTTCTTGGCGGACGTGCACAGATAACTTCGTATAATGTACATTATACGAAGTTATTCTTTGAAAAGATAATGTATGATTATGCTTTCACTCATATTTATACAGAAACTTGATGTTTTCTTTCGAGTATATACAAGGTGATTACATGTACGTTTGAAGTACAACTCTAGATTTTGTAGTGCCCTCTTGGGCTAGCGGTAAAGGTGCGCATTTTTTCACACCCTACAATGTTCTGTTCAAAAGATTTTGGTCAAACGCTGTAGAAGTGAAAGTTGGTGCGCATGTTTCGGCGTTCGAAACTTCTCCGCAGTGAAAGATAAATGATCCCAACCGTTGTGACCTTCCAGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCAAACAAGCGCAAGTGGTTTAGTGGTAAAATCCAACGTTGCCATCGTTGGGCCCCCGGTTCGATTCCGGGCTTGCGCACGAGTTTGTAACACTCTGCAGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCAAACAAGCGCAAGTGGTTTAGTGGTAAAATCCAACGTTGCCATCGTTGGGCCCCCGGTTCGATTCCGGGCTTGCGCACAAAAGGTTTAGAATTTCCAGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCTTTTGCGCAAGTGGTTTAGTGGTAAAATCCAACGTTGCCATCGTTGGGCCCCCGGTTCGATTCCGGGCTTGCGCAAGAAGGGCTTGGTTTCGAAAGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCAAACAAGCGCAAGTGGTTTAGTGGTAAAATCCAACGTTGCCATCGTTGGGCCCCCGGTTCGATTCCGGGCTTGCGCAAATGTCCTCCCCTTGGTGGGGTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGCAAACAATTTATTTTTTGTCACTATTGTTATGTAAAATGCCACCTCTGACAGTATGGAACGCAAACTTCTGTCTAGTGGATAACAGAATTTTTCTATGGCCAATTTAATAACTTCGTATAATGTACATTATACGAAGTTATAGTTAGTTTGTTTAAACAACAAACTTTTTTCATTTCTTTTGTTTCCCCTTCTCTTCTTTTAGTTAGTTTGTTTAAACAACAAACTATAGTATTGTCGTTTGGGTGGCTTCATTTAGACGGTACTGCATCTTAAATAATATGAATG"
# sequence = sequence.upper()
# finder = DNARepeatsFinder(sequence=sequence)
# # print(finder.find_dinucleotide_repeats())
# print(finder.find_dispersed_repeats())

