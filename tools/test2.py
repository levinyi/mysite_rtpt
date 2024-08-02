import re
from Bio.Seq import Seq
from Bio.SeqUtils.lcc import lcc_simp

class DNARepeatsFinder:
    def __init__(self, data_set=None, sequence=None):
        '''
        可以接受单个序列或者数据集
        '''
        self.data_set = data_set
        self.sequence = sequence

        if data_set is not None:
            self.suffix_arrays = {}
            self.lcps_arrays = {}

            # 为每个序列构建后缀数组和LCP数组
            for index, row in data_set.iterrows():
                seq = row['sequence']
                self.suffix_arrays[index], self.lcps_arrays[index] = self.build_suffix_array(seq)
        elif sequence is not None:
            self.suffix_array, self.lcp_array = self.build_suffix_array(sequence)

    @staticmethod
    def build_suffix_array(s):
        """Build suffix array of s in O(n log n)"""
        n = len(s)
        sa = []
        rk = []
        char_to_int = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
        for i in range(n):
            rk.append(char_to_int[s[i]])  # 初始化排名，基于首字母
            sa.append(i)  # 初始化后缀数组

        length = 0  # 当前排序长度
        sig = 4  # 字符集大小，初始为4

        while True:
            p = []
            for i in range(n - length, n):
                p.append(i)
            for i in range(n):
                if sa[i] >= length:
                    p.append(sa[i] - length)

            cnt = [0] * sig
            for i in range(n):
                cnt[rk[i]] += 1
            for i in range(1, sig):
                cnt[i] += cnt[i - 1]
            for i in range(n - 1, -1, -1):
                cnt[rk[p[i]]] -= 1
                sa[cnt[rk[p[i]]]] = p[i]

            def equal(i, j, length):
                if rk[i] != rk[j]:
                    return False
                if i + length >= n and j + length >= n:
                    return True
                if i + length < n and j + length < n:
                    return rk[i + length] == rk[j + length]
                return False

            sig = -1
            tmp = [None] * n
            for i in range(n):
                if i == 0 or not equal(sa[i], sa[i - 1], length):
                    sig += 1
                tmp[sa[i]] = sig
            rk = tmp
            sig += 1
            if sig == n:
                break
            length = length << 1 if length > 0 else 1

        # 计算height数组
        k = 0
        height = [0] * n
        for i in range(n):
            if rk[i] > 0:
                j = sa[rk[i] - 1]
                while i + k < n and j + k < n and s[i + k] == s[j + k]:
                    k += 1
                height[rk[i]] = k
                if k > 0:
                    k -= 1  # 保证下一次的公共前缀至少是k-1
        return sa, height
    
    def find_most_frequent_longest_repeated_substring(self, s):
        sa, height = self.build_suffix_array(s)
        n = len(s)
        
        # 初始化
        longest_len = 0
        substr_counts = {}
        max_count = 0
        result_substring = ""
        
        # 遍历 height 数组
        for i in range(1, n):
            lcp_length = height[i]
            if lcp_length > longest_len:
                longest_len = lcp_length
                substr = s[sa[i]:sa[i] + lcp_length]
                substr_counts = {substr: 1}
                max_count = 1
                result_substring = substr
            elif lcp_length == longest_len and lcp_length > 0:
                substr = s[sa[i]:sa[i] + lcp_length]
                if substr in substr_counts:
                    substr_counts[substr] += 1
                else:
                    substr_counts[substr] = 1
                if substr_counts[substr] > max_count:
                    max_count = substr_counts[substr]
                    result_substring = substr
        
        return result_substring, max_count

    def _get_sequence_data(self, index=None):
        if index is not None:
            return self.data_set.loc[index, 'sequence'], self.suffix_arrays[index], self.lcps_arrays[index]
        return self.sequence, self.suffix_array, self.lcp_array

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
        return length * 10 if length > 10 else length
    
    def calculate_tandem_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_dispersed_repeats_penalty_score(self, length, count):
        return round(((length - 15) / 2 if length > 15 else 0) * count, 1)
    
    def calculate_palindrome_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_inverted_repeats_penalty_score(self, length, max_distance):
        return round((length - 10) - (max_distance - 20), 1)
    
    def calculate_WS_motifs_penalty_score(self, length, min_len=8):
        return round((length - min_len + 1) / 2, 1)
    
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
        
        # 按序列长度排序，处理潜在重复
        sorted_repeats = sorted(potential_repeats.items(), key=lambda x: -len(x[0]))
        merged_repeats = {}

        for seq, positions in sorted_repeats:
            if not any(seq in long_seq for long_seq in merged_repeats):
                merged_repeats[seq] = positions

        # 转换为最终输出格式
        for seq, positions in merged_repeats.items():
            escaped_seq = re.escape(seq)
            matches = [m.start() for m in re.finditer(escaped_seq, s)]
            if len(matches) >= 2:
                distances = [matches[j] - matches[j - 1] for j in range(1, len(matches))]
                if all(d >= min_len for d in distances):
                    repeats.append({
                        'seqType': 'dispersed_repeats',
                        'sequence': seq,
                        'positions': matches,
                        'count': len(matches),
                        'gc_content': self.calculate_gc_content(seq),
                        'length': len(seq),
                        'penalty_score': self.calculate_dispersed_repeats_penalty_score(len(seq), len(matches))
                    })

        # 处理空结果，仍然返回相应的表头
        if not repeats:
            repeats = [{
                'seqType': 'dispersed_repeats',
                'sequence': '',
                'positions': '',
                'count': '',
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

        # 合并重叠窗口
        gc_contents = []
        for gc_content in gc_contents_temp:
            if gc_contents and gc_contents[-1]['end'] >= gc_content['start'] - 1:
                old_end = gc_contents[-1]['end']
                new_end = max(old_end, gc_content['end'])
                gc_contents[-1]['end'] = new_end
                gc_contents[-1]['sequence'] = s[gc_contents[-1]['start']:new_end + 1]
                gc_contents[-1]['penalty_score'] += gc_content['penalty_score']
            else:
                gc_contents.append(gc_content)

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
            if gc_contents and gc_contents[-1]['end'] >= gc_content['start'] - 1:
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
        
def main():
    sequence = "ACCGGGTCATTGGGGTCAGGTTACTCCGGGTCATTGGGGTCAGGTGTCACCGGGTCATTGGGGTCAGGCTCTATGTT"
    sequence = sequence.upper()
    finder = DNARepeatsFinder(sequence=sequence)
    result_substring, count = finder.find_most_frequent_longest_repeated_substring(sequence)
    print("Most Frequent Longest Repeated Substring:", result_substring)
    print("Count:", count)
    print(finder.find_dispersed_repeats())

if __name__ == "__main__":
    main()
