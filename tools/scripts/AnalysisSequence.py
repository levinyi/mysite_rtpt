import re


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
        return sorted(range(len(s)), key=lambda k: s[k:])

    @staticmethod
    def find_lcp(s, sa):
        """Find the longest common prefix (LCP) array for `s` using the suffix array `sa`."""
        n = len(s)
        lcp = [0] * n
        rank = [0] * n
        for i in range(n):
            rank[sa[i]] = i
        k = 0
        for i in range(n):
            if rank[i] == n - 1:  # 末尾
                k = 0
                continue
            j = sa[rank[i] + 1]
            while i + k < n and j + k < n and s[i+k] == s[j+k]:
                k += 1
            lcp[rank[i]] = k
            if k:
                k -= 1
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
    
    def calculate_local_gc_penalty_score(self, sequence, gc_content, min_GC_threshold=20, max_GC_threshold=80):
        length = len(sequence)
        return round(length * abs(min_GC_threshold - gc_content) if gc_content < min_GC_threshold else length * abs(gc_content - max_GC_threshold) / 100, 1)
    
    def calculate_tandem_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_dispersed_repeats_penalty_score(self, length, count):
        return round(((length - 15) / 2 if length > 16 else 0) * count, 1)
    
    def calculate_palindrome_repeats_penalty_score(self, length):
        return round((length - 15) / 2 if length > 15 else 0, 1)
    
    def calculate_inverted_repeats_penalty_score(self, length):
        return round((length - 10) / 2 if length > 15 else 0, 1)
    
    def calculate_WS_motifs_penalty_score(self, length, min_len=8):
        return round((length - min_len + 1) / 2 , 1)
    
    # 1) Tandem Repeats
    def find_tandem_repeats(self, index=None, min_unit=3, min_copies=3):
        s, sa, lcp = self._get_sequence_data(index)
        
        repeats = []
        n = len(sa)

        for i in range(n):
            length = lcp[i]

            # 根据长度去判断它符合什么类型的重复，
            # 如果长度大于等于最小单元长度乘以最小重复次数，那么就是tandem repeat
            if length >= min_unit * min_copies:
                start_index = sa[i]

                # 尝试所有可能的单元长度，看看是否能匹配到重复次数
                for unit_length in range(min_unit, length // min_copies + 1):
                    repeat_unit = s[start_index:start_index + unit_length]
                    if self.is_homopolymer(repeat_unit):
                        continue

                    full_seq = repeat_unit * min_copies
                    repeat_count = length // unit_length
                    actual_length = repeat_count * unit_length

                    # 检查是否有重复,确保重复次数大于等于最小重复次数，
                    # Ensure the sequence matches the exact repeated pattern and aligns with the lcp length
                    if s[start_index:start_index + actual_length]== full_seq:
                        repeats.append({
                            'seqType': 'tandem_repeats',
                            'sequence': full_seq,
                            'start': start_index,
                            'end': start_index + actual_length - 1,
                            'length': actual_length,
                            'gc_content': self.calculate_gc_content(full_seq),
                            'penalty_score': self.calculate_tandem_repeats_penalty_score(actual_length)
                        })
                        break
    
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
        # print("potential_repeats: ", potential_repeats)
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
                        'seqType': 'long_repeats',
                        'sequence': seq,
                        'positions': matches,
                        'count': len(matches),
                        'gc_content': self.calculate_gc_content(seq),
                        'length':len(seq),
                        'penalty_score': self.calculate_dispersed_repeats_penalty_score(len(seq), len(matches))
                    })

        return repeats

    # 3) Palindrome Repeats
    def find_palindrome_repeats(self, index=None, min_len=15):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        palindromes = []

        # 函数：检查两个索引上的字符是否为互补
        def is_complementary(i, j):
            complements = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
            return s[i] == complements[s[j]]

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

        return palindromes

    # 4) Inverted Repeats
    def find_inverted_repeats(self, index=None, min_len=4, max_distance=100):
        s, sa, lcp = self._get_sequence_data(index)
        
        def reverse_complement(seq):
            seq = seq.upper()
            complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
            return ''.join(complement[base] for base in reversed(seq))

        n = len(s)
        inverted_repeats = []

        for i in range(n - min_len + 1):
            for length in range(min_len, min(n - i, max_distance + min_len)):
                segment = s[i:i + length]
                rev_comp = reverse_complement(segment)

                # Check for the presence of this reverse complement within the specified distance
                # Start the search from i + length to ensure non-overlapping segments within the maximum distance
                for j in range(i + length, min(i + length + max_distance, n - length + 1)):
                    if s[j:j + length] == rev_comp:
                        inverted_repeats.append({
                            'seqType': 'inverted_repeats',
                            'sequence': segment,
                            'inverted_sequence': rev_comp,
                            'start1': i,
                            'end1': i + length - 1,
                            'start2': j,
                            'end2': j + length - 1,
                            'length': length,
                            'penalty_score': self.calculate_inverted_repeats_penalty_score(length),
                        })

        return inverted_repeats

    # 5) Homopolymers
    def find_homopolymers(self, index=None, min_len=9):
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

        return W_motifs + S_motifs

    # 7) Local GC Content by Window
    def find_local_gc_content(self, index=None, window_size=30, min_GC_content=20, max_GC_content=80):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        if n < window_size:
            # 将整个序列作为一个窗口
            gc_content = self.calculate_gc_content(s)
            if gc_content < min_GC_content or gc_content > max_GC_content:
                return [{
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
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
                    # penalty_score 
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
            else:
                gc_contents.append(gc_content)
        
        # recalculate the GC content of the merged windows, and calculate the penalty score
        for gc_content in gc_contents:
            gc_content['seqType'] = 'local_gc'
            gc_content['length'] = len(gc_content['sequence'])
            gc_content['gc_content'] = self.calculate_gc_content(gc_content['sequence'])
            gc_content['penalty_score'] = self.calculate_local_gc_penalty_score(gc_content['sequence'], gc_content['gc_content'])
        return gc_contents

