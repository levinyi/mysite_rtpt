import json
import re
import sys
from Bio.Seq import Seq
from Bio.SeqUtils.lcc import lcc_simp
from Bio.SeqUtils import gc_fraction as GC
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

    @staticmethod
    def gc_percent(seq):
        """Return GC percentage with two decimal places."""
        return round(GC(seq) * 100, 2)

    def calculate_homopolymer_penalty_score(self, length):
        # 保留 1 位小数
        return round((length * 10) if length > 10 else float(length), 1)
    
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
        if min_GC_threshold is not None and gc_content <= min_GC_threshold:
            penalty_score = round(abs(min_GC_threshold - gc_content + 1) /10, 1)
        elif max_GC_threshold is not None and gc_content >= max_GC_threshold:
            penalty_score = round(abs(gc_content - max_GC_threshold + 1) /10, 1)
        else:
            # 表示不在范围内
            penalty_score = 0
        return penalty_score

    # 1) Tandem Repeats
    def find_tandem_repeats(self, index=None, min_unit=3, min_copies=4, max_mismatch=1):
        """
        查找串联重复序列
        参数:
            min_unit: 最小重复单元长度，默认3
            min_copies: 最小重复次数，默认4
            max_mismatch: 允许的最大错配数，默认1（考虑中间 mismatch 的情况）
        罚分规则: (total_length - 15) / 2 if length > 15 else 0
        """
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)

        repeats_temp = []
        checked_positions = set()  # 避免重复检查

        # 🔧 完全重写：正确的串联重复检测逻辑
        # 遍历序列的每个位置（不使用suffix array的方式，直接遍历）
        MAX_UNIT_LENGTH = 50

        for start_pos in range(n):
            if start_pos in checked_positions:
                continue

            # 尝试不同的重复单元长度
            for unit_length in range(min_unit, min(MAX_UNIT_LENGTH, (n - start_pos) // min_copies + 1)):
                repeat_unit = s[start_pos:start_pos + unit_length]

                # 跳过同聚物（由其他算法处理）
                if self.is_homopolymer(repeat_unit):
                    continue

                # 检查从当前位置开始，这个单元重复了多少次
                repeat_count = 0
                total_mismatches = 0
                pos = start_pos

                while pos + unit_length <= n:
                    current_segment = s[pos:pos + unit_length]
                    # 计算错配数
                    mismatches = sum(1 for k in range(unit_length) if current_segment[k] != repeat_unit[k])

                    if mismatches <= max_mismatch:
                        repeat_count += 1
                        total_mismatches += mismatches
                        pos += unit_length
                    else:
                        break

                # 如果找到了足够的重复
                if repeat_count >= min_copies:
                    actual_length = repeat_count * unit_length

                    # 🔧 修复：添加身份阈值检查，避免假阳性
                    # 计算总体身份百分比（匹配碱基数/总碱基数）
                    total_bases = actual_length
                    matching_bases = total_bases - total_mismatches
                    identity_percent = matching_bases / total_bases if total_bases > 0 else 0

                    # 要求至少85%的身份（即最多15%错配率）
                    # 这确保检测到的是真正的串联重复，而不是随机相似序列
                    # 真正的串联重复应该是大部分copy完美匹配，只有少数突变
                    # 例如：18bp重复，最多允许2个错配 (88.9% identity) ✓
                    #       18bp重复，3个错配 (83.3% identity) ✗ 太多突变
                    MIN_IDENTITY = 0.85

                    if identity_percent < MIN_IDENTITY:
                        # 身份太低，不是真正的串联重复，跳过
                        continue

                    end_pos = start_pos + actual_length - 1

                    repeats_temp.append({
                        'sequence': s[start_pos:start_pos + actual_length],
                        'start': start_pos,
                        'end': end_pos,
                        'mismatches': total_mismatches,
                        'unit': repeat_unit,
                        'unit_length': unit_length,
                    })

                    # 标记这些位置已检查，避免重复
                    for p in range(start_pos, start_pos + actual_length):
                        checked_positions.add(p)

                    # 找到一个重复后，跳出unit_length循环
                    break

        # 根据start位置对repeats_temp进行排序
        repeats_temp.sort(key=lambda x: x['start'])

        # 🔧 修复：改进合并逻辑，只合并相同重复单元的重复
        repeats = []
        for repeat in repeats_temp:
            if repeats and repeats[-1]['end'] >= repeat['start'] - 1:
                # 检查重复单元是否相同
                if repeats[-1].get('unit') == repeat.get('unit'):
                    # 相同重复单元，可以合并
                    old_end = repeats[-1]['end']
                    new_end = max(old_end, repeat['end'])
                    repeats[-1]['end'] = new_end
                    repeats[-1]['sequence'] = s[repeats[-1]['start']:new_end + 1]
                else:
                    # 不同重复单元，选择更长的保留
                    if repeat['end'] - repeat['start'] > repeats[-1]['end'] - repeats[-1]['start']:
                        repeats[-1] = repeat
            else:
                repeats.append(repeat)

        for repeat in repeats:
            repeat['length'] = len(repeat['sequence'])
            repeat['gc_content'] = self.gc_percent(repeat['sequence'])
            repeat['penalty_score'] = self.calculate_tandem_repeats_penalty_score(repeat['length'])
            # 🔧 修复：清理临时字段
            repeat.pop('unit', None)
            repeat.pop('unit_length', None)

        # 🔧 过滤：只保留长度>15bp的串联重复（因为≤15bp的罚分都是0，不需要报告）
        repeats = [r for r in repeats if r['length'] > 15]

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
        # 转换为最终输出格式
        for seq, positions in merged_repeats.items():
            # 根据序列去重新找到起始位置和结束位置
            matches = [match.start() for match in re.finditer(re.escape(seq), s)]
            if len(matches) >= 2:  # 至少要有两个以上的重复位置才算分散重复
                distances = [matches[j] - matches[j - 1] for j in range(1, len(matches))]
                if all(d >= min_len for d in distances):
                    repeats.append({
                        'sequence': seq,
                        'start': matches,
                        'end': [match + len(seq) - 1 for match in matches],
                        'gc_content': self.gc_percent(seq),
                        'length': len(seq),
                        'penalty_score': self.calculate_dispersed_repeats_penalty_score(len(seq), len(matches))
                    })
        return repeats

    # 3) Palindrome Repeats
    def find_palindrome_repeats(self, index=None, min_len=15):
        """
        查找DNA回文序列（Palindromic Sequences）

        DNA回文定义：序列等于其反向互补序列
        例如：
        - ATCGAT → 反向互补 ATCGAT (相同，是DNA回文)
        - GAATTC → 反向互补 GAATTC (EcoRI限制性位点)
        - CGGGGGC → 反向互补 GCCCCCG (不同，不是DNA回文)

        注意：这不是字符串回文！字符串回文如 "ABCBA"，但DNA回文基于碱基互补配对。

        参数:
            min_len: 最小回文长度，默认15 (必须是偶数)
        排除规则: 排除两个碱基交替组合的 repeats（如 ATATATAT），长度≥8
        罚分规则: (length - 15) / 2 if length > 15 else 0
        """
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        palindromes = []
        excluded_combinations = {"AT", "TA", "CG", "GC", "AC", "CA", "GT", "TG"}

        # 🔧 修复：DNA回文必须是偶数长度，确保 min_len 是偶数
        if min_len % 2 != 0:
            min_len += 1  # 如果是奇数，调整为下一个偶数

        def is_excluded(sequence):
            """
            检查是否应该排除：
            - 长度≥8
            - 只包含两种碱基
            - 这两种碱基交替出现（如 ATATAT 或 CGCGCG）
            """
            if len(sequence) < 8:
                return False

            unique_bases = set(sequence)
            if len(unique_bases) != 2:
                return False

            # 检查前两个字符的组合是否在排除列表中
            if sequence[:2] not in excluded_combinations:
                return False

            # 检查是否为交替模式
            pattern = sequence[:2]
            expected = (pattern * (len(sequence) // 2 + 1))[:len(sequence)]
            return sequence == expected

        def reverse_complement(seq):
            """计算反向互补序列"""
            complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
            return ''.join(complement[base] for base in reversed(seq.upper()))

        def is_dna_palindrome(seq):
            """检查是否是DNA回文（序列 == 反向互补）"""
            return seq == reverse_complement(seq)

        # 遍历所有可能的子序列，查找DNA回文
        # DNA回文必须是偶数长度（因为序列必须等于其反向互补）
        for start in range(n - min_len + 1):
            # 只检查偶数长度的序列
            for length in range(min_len, min(n - start + 1, 200), 2):  # 限制最大长度200以提高效率
                end = start + length - 1
                seq = s[start:end + 1]

                # 检查是否是DNA回文
                if is_dna_palindrome(seq):
                    # 应用排除规则
                    if not is_excluded(seq):
                        palindromes.append({
                            'sequence': seq,
                            'start': start,
                            'end': end,
                            'length': length,
                            'gc_content': self.gc_percent(seq),
                            'penalty_score': self.calculate_palindrome_repeats_penalty_score(length),
                        })

        # 过滤重叠的回文，保留较长的
        filtered_palindromes = self._filter_overlapping_palindromes(palindromes)

        # 按起始位置排序
        filtered_palindromes.sort(key=lambda x: x['start'])

        return filtered_palindromes

    def _filter_overlapping_palindromes(self, palindromes):
        """
        过滤重叠的回文序列，保留较长的
        策略：如果两个回文重叠超过50%，只保留较长的
        """
        if not palindromes:
            return []

        # 按长度降序排序
        sorted_palindromes = sorted(palindromes, key=lambda x: x['length'], reverse=True)

        selected = []
        for candidate in sorted_palindromes:
            # 检查是否与已选择的回文显著重叠
            is_overlapping = False

            for selected_item in selected:
                overlap = self._calculate_overlap(
                    candidate['start'], candidate['end'],
                    selected_item['start'], selected_item['end']
                )

                # 计算重叠比例
                candidate_len = candidate['end'] - candidate['start'] + 1
                overlap_ratio = overlap / candidate_len if candidate_len > 0 else 0

                # 如果重叠超过50%，认为显著重叠
                if overlap_ratio > 0.5:
                    is_overlapping = True
                    break

            if not is_overlapping:
                selected.append(candidate)

        return selected

    # 4) Inverted Repeats (包含 Hairpin 和 Inverted Repeats)
    def find_inverted_repeats(self, index=None, min_stem_len=10):
        """
        查找倒置重复序列（包括 hairpin 和 inverted repeats）
        参数:
            min_stem_len: 最小 stem 长度，默认10

        分类和罚分规则:
        1. Hairpin: Stem >= 10, loop 4-8 bp
           罚分: stem_length - 9

        2. Inverted Repeats: Stem >= 16, loop >= 8 or <= 3
           罚分: ((stem_length - 15) / 2) * count
        """
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)

        def reverse_complement(seq):
            complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
            return ''.join(complement[base] for base in reversed(seq.upper()))

        hairpins = []
        inverted_repeats = []

        # 统计相同 stem 序列出现的次数（用于 inverted repeats 的 count）
        stem_counts = {}

        # 遍历序列查找所有可能的倒置重复
        for i in range(n):
            max_stem = min(n - i, 100)  # 限制最大 stem 长度以提高效率

            for stem_len in range(min_stem_len, max_stem):
                stem1 = s[i:i + stem_len]
                stem1_rc = reverse_complement(stem1)

                # 在 stem1 之后查找其反向互补序列
                search_start = i + stem_len

                # 使用字符串查找方法寻找反向互补序列
                pos = search_start
                while pos < n:
                    idx = s.find(stem1_rc, pos)
                    if idx == -1:
                        break

                    # 计算 loop 长度
                    loop_length = idx - (i + stem_len)

                    if loop_length < 0:  # 重叠的情况，跳过
                        pos = idx + 1
                        continue

                    stem2_end = idx + stem_len

                    # 分类为 hairpin 或 inverted repeats
                    if stem_len >= 10 and 4 <= loop_length <= 8:
                        # Hairpin 结构
                        penalty = stem_len - 9
                        hairpins.append({
                            'type': 'hairpin',
                            'stem_sequence': stem1,
                            'stem_length': stem_len,
                            'stem1_start': i,
                            'stem1_end': i + stem_len - 1,
                            'stem2_start': idx,
                            'stem2_end': stem2_end - 1,
                            'loop_sequence': s[i + stem_len:idx],
                            'loop_length': loop_length,
                            'full_sequence': s[i:stem2_end],
                            'penalty_score': round(penalty, 1),
                        })

                    elif stem_len >= 16 and (loop_length >= 8 or loop_length <= 3):
                        # Inverted Repeats 结构
                        # 统计这个 stem 序列的出现次数
                        stem_key = (stem1, stem_len)
                        if stem_key not in stem_counts:
                            stem_counts[stem_key] = []
                        stem_counts[stem_key].append({
                            'stem1_start': i,
                            'stem1_end': i + stem_len - 1,
                            'stem2_start': idx,
                            'stem2_end': stem2_end - 1,
                            'loop_length': loop_length,
                            'loop_sequence': s[i + stem_len:idx],
                            'full_sequence': s[i:stem2_end],
                        })

                    pos = idx + 1

        # 处理 inverted repeats，计算每个 stem 的 count 和罚分
        for (stem_seq, stem_len), occurrences in stem_counts.items():
            count = len(occurrences)
            base_penalty = (stem_len - 15) / 2 if stem_len > 15 else 0
            total_penalty = base_penalty * count

            for occ in occurrences:
                inverted_repeats.append({
                    'type': 'inverted_repeat',
                    'stem_sequence': stem_seq,
                    'stem_length': stem_len,
                    'stem1_start': occ['stem1_start'],
                    'stem1_end': occ['stem1_end'],
                    'stem2_start': occ['stem2_start'],
                    'stem2_end': occ['stem2_end'],
                    'loop_sequence': occ['loop_sequence'],
                    'loop_length': occ['loop_length'],
                    'full_sequence': occ['full_sequence'],
                    'count': count,
                    'penalty_score': round(total_penalty, 1),
                })

        # 合并 hairpins 和 inverted_repeats
        all_results = hairpins + inverted_repeats

        # 过滤重叠的结构，保留最显著的
        filtered_results = self._filter_overlapping_inverted_repeats(all_results)

        # 按起始位置排序
        filtered_results.sort(key=lambda x: x['stem1_start'])

        return filtered_results

    def _filter_overlapping_inverted_repeats(self, results):
        """
        过滤重叠的倒置重复结构，保留最显著的
        策略：
        1. 优先保留 stem 更长的结构
        2. 对于相同起始位置的结构，只保留最长的
        3. 对于显著重叠（>50% overlap）的结构，保留更高分的
        """
        if not results:
            return []

        # 按 stem_length 降序排序（优先保留长的）, 然后按 penalty_score 降序
        sorted_results = sorted(results,
                               key=lambda x: (x['stem_length'], x['penalty_score']),
                               reverse=True)

        selected = []

        for candidate in sorted_results:
            # 检查是否与已选择的结构显著重叠
            is_overlapping = False

            for selected_item in selected:
                if self._has_significant_overlap(candidate, selected_item):
                    is_overlapping = True
                    break

            if not is_overlapping:
                selected.append(candidate)

        return selected

    def _has_significant_overlap(self, struct1, struct2):
        """
        检查两个倒置重复结构是否显著重叠
        判断标准：
        - 如果 stem1 区域重叠超过50%，认为显著重叠
        - 或者 stem2 区域重叠超过50%，认为显著重叠
        """
        # 计算 stem1 的重叠
        stem1_overlap = self._calculate_overlap(
            struct1['stem1_start'], struct1['stem1_end'],
            struct2['stem1_start'], struct2['stem1_end']
        )

        # 计算 stem2 的重叠
        stem2_overlap = self._calculate_overlap(
            struct1['stem2_start'], struct1['stem2_end'],
            struct2['stem2_start'], struct2['stem2_end']
        )

        # 计算重叠比例
        len1 = struct1['stem1_end'] - struct1['stem1_start'] + 1
        len2 = struct2['stem1_end'] - struct2['stem1_start'] + 1

        stem1_overlap_ratio = stem1_overlap / min(len1, len2) if min(len1, len2) > 0 else 0
        stem2_overlap_ratio = stem2_overlap / min(len1, len2) if min(len1, len2) > 0 else 0

        # 如果任一区域重叠超过50%，认为显著重叠
        return stem1_overlap_ratio > 0.5 or stem2_overlap_ratio > 0.5

    def _calculate_overlap(self, start1, end1, start2, end2):
        """计算两个区间的重叠长度"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        return max(0, overlap_end - overlap_start + 1)

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
        return motifs

    # 7) Local GC Content by Window
    def find_high_gc_content(self, index=None, window_size=30, max_GC_content=80):
        s, sa, lcp = self._get_sequence_data(index)
        # print(f"Sequence: {s}")  # 输出序列

        n = len(s)
        if n < window_size:
            gc_raw = GC(s) * 100
            gc_content = round(gc_raw, 2)
            # print(f"GC Content for entire sequence: {gc_content}")  # 输出整个序列的GC含量
            if gc_raw >= max_GC_content:
                penalty_score = self.calculate_local_gc_penalty_score(float(gc_raw), max_GC_content, max_GC_content)
                # print(f"Penalty Score for entire sequence: {penalty_score}")  # 输出惩罚分数
                return [{
                    'length': n,
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
                    'penalty_score': penalty_score,
                }]
            return []

        high_gc_contents_temp = []

        for i in range(n - window_size + 1):
            window = s[i:i + window_size]
            gc_raw = GC(window) * 100
            gc_content = round(gc_raw, 2)
            if gc_raw >= max_GC_content:
                penalty_score = self.calculate_local_gc_penalty_score(float(gc_raw), max_GC_content, max_GC_content)
                # print(f"Window {i}-{i + window_size - 1}: {window}, GC Content: {gc_content} Penalty Score for window {i}-{i + window_size - 1}: {penalty_score}")
                high_gc_contents_temp.append({
                    'sequence': window,
                    'start': i,
                    'end': i + window_size - 1,
                    'gc_content': gc_content,
                    'penalty_score': penalty_score,
                })

        high_gc_contents = self.merge_gc_windows(high_gc_contents_temp, s, 'highGC', min_GC_content=None, max_GC_content=max_GC_content)
        # print(f"Merged High GC Contents: {high_gc_contents}")  # 输出合并后的高GC窗口

        return high_gc_contents
    
    def find_low_gc_content(self, index=None, window_size=30, min_GC_content=20):
        s, sa, lcp = self._get_sequence_data(index)

        n = len(s)
        if n < window_size:
            # 将整个序列作为一个窗口
            gc_raw = GC(s)*100
            gc_content = round(gc_raw, 2)
            if gc_raw <= min_GC_content:
                return [{
                    'length': n,
                    'sequence': s,
                    'start': 0,
                    'end': n - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_raw), min_GC_content, min_GC_content),
                }]
            return []

        low_gc_contents_temp = []

        for i in range(n - window_size + 1):
            window = s[i:i + window_size]
            gc_raw = GC(window)*100
            gc_content = round(gc_raw, 2)
            if gc_raw < min_GC_content:
                low_gc_contents_temp.append({
                    'sequence': window,
                    'start': i,
                    'end': i + window_size - 1,
                    'gc_content': gc_content,
                    'penalty_score': self.calculate_local_gc_penalty_score(float(gc_raw), min_GC_content, min_GC_content),
                })

        low_gc_contents = self.merge_gc_windows(low_gc_contents_temp, s, 'lowGC', min_GC_content=min_GC_content, max_GC_content=None)

        return low_gc_contents

    def merge_gc_windows(self, gc_contents_temp, sequence, gc_type, min_GC_content=None, max_GC_content=None):
        """原始合并逻辑：只要区间重叠或相邻就合并。"""
        gc_contents = []
        for gc_content in gc_contents_temp:
            if gc_contents and gc_contents[-1]['end'] >= gc_content['start'] - 1:  # 表示有重叠或相邻
                old_end = gc_contents[-1]['end']
                new_end = max(old_end, gc_content['end'])
                gc_contents[-1]['end'] = new_end
                gc_contents[-1]['sequence'] = sequence[gc_contents[-1]['start']:new_end + 1]
                gc_contents[-1]['penalty_score'] += gc_content['penalty_score']  # 累加惩罚分数
            else:
                gc_contents.append(gc_content)

        for gc_content in gc_contents:
            gc_content['seqType'] = gc_type
            gc_content['length'] = len(gc_content['sequence'])
            gc_content['gc_content'] = self.gc_percent(gc_content['sequence'])
            # 保留 1 位小数的显示效果
            gc_content['penalty_score'] = round(float(gc_content.get('penalty_score', 0)), 1)
        return gc_contents

    # 8) Dinucleotide Repeats
    def find_dinucleotide_repeats(self, index=None, threshold=12):
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
                        # 'seqType': 'dinucleotide_repeats',
                        'sequence': sequence,
                        'start': i,
                        'end': i + repeat_length - 1,
                        'length': repeat_length,
                        'gc_content': self.gc_percent(sequence),
                        'penalty_score': round(repeat_length / 2, 1)
                    })
            
            i += repeat_length  # 跳过已检测到的重复序列
        return repeats

    # 9) lcc
    def get_lcc(self, index=None):
        s, sa, lcp = self._get_sequence_data(index)
        n = len(s)
        lcc = 0
        dna_seq = Seq(s)
        dna_complexity = lcc_simp(dna_seq)

        return f'{dna_complexity:.2f}'


def convert_gene_table_to_RepeatsFinder_Format(gene_table, long_repeats_min_len=16, homopolymers_min_len=7,
                                               min_w_length=12, min_s_length=12, window_size=30,
                                               min_gc_content=20, max_gc_content=80,
                                               tandem_min_unit=3, tandem_min_copies=4, tandem_max_mismatch=1,
                                               palindrome_min_len=15, inverted_min_stem_len=10):
    """
    将基因表格转换为 RepeatsFinder 格式

    新增参数:
        tandem_min_unit: Tandem Repeats 最小单元长度，默认3
        tandem_min_copies: Tandem Repeats 最小重复次数，默认4
        tandem_max_mismatch: Tandem Repeats 最大错配数，默认1
        palindrome_min_len: Palindrome Repeats 最小长度，默认15
        inverted_min_stem_len: Inverted Repeats 最小 stem 长度，默认10
    """
    finder_dataset = DNARepeatsFinder(data_set=gene_table)

    results = {}
    for index, row in gene_table.iterrows():
        gene_id = row['gene_id']
        results[gene_id] = {
            'LongRepeats': finder_dataset.find_dispersed_repeats(index=index, min_len=long_repeats_min_len),
            'Homopolymers': finder_dataset.find_homopolymers(index=index, min_len=homopolymers_min_len),
            'W12S12Motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=min_w_length, min_S_length=min_s_length),
            'highGC': finder_dataset.find_high_gc_content(index=index, window_size=window_size, max_GC_content=max_gc_content),
            'lowGC': finder_dataset.find_low_gc_content(index=index, window_size=window_size, min_GC_content=min_gc_content),
            # 'LCC': finder_dataset.get_lcc(index=index),
            'doubleNT': finder_dataset.find_dinucleotide_repeats(index=index, threshold=12),
            # ========== 新增三个分析方法 ==========
            'TandemRepeats': finder_dataset.find_tandem_repeats(index=index, min_unit=tandem_min_unit,
                                                                min_copies=tandem_min_copies,
                                                                max_mismatch=tandem_max_mismatch),
            'PalindromeRepeats': finder_dataset.find_palindrome_repeats(index=index, min_len=palindrome_min_len),
            'InvertedRepeats': finder_dataset.find_inverted_repeats(index=index, min_stem_len=inverted_min_stem_len),
            # ====================================
            'length': len(finder_dataset._get_sequence_data(index)[0])
        }

    # print(json.dumps(results, indent=4))
    return results


# 格式化函数：将特征信息合并为字符串
def format_feature_data(feature_data, keys):
    if not feature_data:
        return ""
    values = []
    if isinstance(feature_data, list):  # 处理多个对象的情况
        for item in feature_data:
            parts = []
            for key in keys:
                parts.append(f"{key}: {item.get(key, '')}")
            values.append(" | ".join(parts))
    else:
        for key in keys:
            if isinstance(feature_data[key], list):
                values.append(f"{key}: {', '.join(map(str, feature_data[key]))}")
            else:
                values.append(f"{key}: {feature_data[key]}")
    return "; ".join(values)


def calculate_total_penalty_score(feature_list):
    # 定义函数来计算每个特征的总 penalty score
    total = sum(float(item.get('penalty_score', 0)) for item in feature_list)
    return round(total, 1)

# --- 新增：统计各特征总长度 ---
def calculate_total_feature_length(feature_list):
    """
    计算一个特征列表的总长度。
    - 若 item["start"] 是列表，则 repeats = len(item["start"])；
      否则 repeats = 1。
    - 总长度 = repeats × item["length"]（缺失时按 0）。
    """
    total_len = 0
    for item in feature_list:
        base_len = item.get("length", 0) or 0

        starts = item.get("start", [])
        repeats = len(starts) if isinstance(starts, list) and starts else 1

        total_len += base_len * repeats

    return total_len

# 数据处理函数，返回处理后的 DataFrame
def process_gene_table_results(data):
    records = []
    for gene, details in data.items():
        # 1) 各特征惩罚分
        long_repeats_penalty = calculate_total_penalty_score(details.get("LongRepeats", []))
        homopolymers_penalty = calculate_total_penalty_score(details.get("Homopolymers", []))
        w12s12motifs_penalty = calculate_total_penalty_score(details.get("W12S12Motifs", []))
        highGC_penalty = calculate_total_penalty_score(details.get("highGC", []))
        lowGC_penalty = calculate_total_penalty_score(details.get("lowGC", []))
        doubleNT_penalty = calculate_total_penalty_score(details.get("doubleNT", []))
        # ========== 新增三个特征的惩罚分 ==========
        tandem_repeats_penalty = calculate_total_penalty_score(details.get("TandemRepeats", []))
        palindrome_repeats_penalty = calculate_total_penalty_score(details.get("PalindromeRepeats", []))
        inverted_repeats_penalty = calculate_total_penalty_score(details.get("InvertedRepeats", []))

        # 2) 各特征总长度
        long_repeats_len = calculate_total_feature_length(details.get("LongRepeats", []))
        homopolymers_len = calculate_total_feature_length(details.get("Homopolymers", []))
        w12s12motifs_len = calculate_total_feature_length(details.get("W12S12Motifs", []))
        highGC_len = calculate_total_feature_length(details.get("highGC", []))
        lowGC_len = calculate_total_feature_length(details.get("lowGC", []))
        doubleNT_len = calculate_total_feature_length(details.get("doubleNT", []))
        # ========== 新增三个特征的总长度 ==========
        tandem_repeats_len = calculate_total_feature_length(details.get("TandemRepeats", []))
        palindrome_repeats_len = calculate_total_feature_length(details.get("PalindromeRepeats", []))
        # InvertedRepeats 长度计算需要特殊处理（stem1 + loop + stem2）
        inverted_repeats_len = sum(
            item.get('stem_length', 0) * 2 + item.get('loop_length', 0)
            for item in details.get("InvertedRepeats", [])
        )

        record = {
            "GeneName": gene,
            "Total_Length": details.get("length"),
            # "LCC": details.get("LCC"),
            "LongRepeats": format_feature_data(details.get("LongRepeats", []), ["sequence", "start", "end", "length", "gc_content"]),
            "LongRepeats_penalty_score": long_repeats_penalty,
            "Homopolymers": format_feature_data(details.get("Homopolymers", []), ["sequence", "start", "end", "length"]),
            "Homopolymers_penalty_score": homopolymers_penalty,
            "W12S12Motifs": format_feature_data(details.get("W12S12Motifs", []), ["sequence", "start", "end", "length"]),
            "W12S12Motifs_penalty_score": w12s12motifs_penalty,
            "HighGC": format_feature_data(details.get("highGC", []), ["sequence", "start", "end", "length", "gc_content"]),
            "HighGC_penalty_score": highGC_penalty,
            "LowGC": format_feature_data(details.get("lowGC", []), ["sequence", "start", "end", "length", "gc_content"]),
            "LowGC_penalty_score": lowGC_penalty,
            "DoubleNT": format_feature_data(details.get("doubleNT", []), ["sequence", "start", "end", "length", "gc_content"]),
            "DoubleNT_penalty_score": doubleNT_penalty,
            # ========== 新增三个特征 ==========
            "TandemRepeats": format_feature_data(details.get("TandemRepeats", []), ["sequence", "start", "end", "length", "gc_content"]),
            "TandemRepeats_penalty_score": tandem_repeats_penalty,
            "PalindromeRepeats": format_feature_data(details.get("PalindromeRepeats", []), ["sequence", "start", "end", "length", "gc_content"]),
            "PalindromeRepeats_penalty_score": palindrome_repeats_penalty,
            "InvertedRepeats": format_feature_data(details.get("InvertedRepeats", []),
                                                    ["type", "stem_sequence", "stem_length", "stem1_start", "stem1_end",
                                                     "stem2_start", "stem2_end", "loop_length", "loop_sequence"]),
            "InvertedRepeats_penalty_score": inverted_repeats_penalty,
            # ====================================
            # ------------- ★ 新增的总长度列 ★ -------------
            "LongRepeats_total_length": long_repeats_len,
            "Homopolymers_total_length": homopolymers_len,
            "W12S12Motifs_total_length": w12s12motifs_len,
            "HighGC_total_length": highGC_len,
            "LowGC_total_length": lowGC_len,
            "DoubleNT_total_length": doubleNT_len,
            # ========== 新增三个特征的总长度 ==========
            "TandemRepeats_total_length": tandem_repeats_len,
            "PalindromeRepeats_total_length": palindrome_repeats_len,
            "InvertedRepeats_total_length": inverted_repeats_len,
            # ====================================
        }
        records.append(record)

    # 转换为 DataFrame
    df = pd.DataFrame(records)

    return df

if __name__ == '__main__':
    input_file = sys.argv[1]
    if input_file.endswith('.xlsx'):
        gene_table = pd.read_excel(input_file)
    elif input_file.endswith('.csv'):
        gene_table = pd.read_csv(input_file)
    else:
        raise ValueError("Invalid file format. Please provide a .csv or .xlsx file")
    
    # gene_table['gene_id'] = gene_table['GeneName']
    # gene_table['sequence'] = gene_table['FullSeqREAL']

    data = convert_gene_table_to_RepeatsFinder_Format(gene_table)
    print(data)
    # 处理数据并获取结果 DataFrame
    result_df = process_gene_table_results(data)
    print(result_df[['GeneName', 'Total_Length', 'LongRepeats_total_length', 'LongRepeats',]])
    # 合并原始表格
    # df = gene_table.merge(result_df, on='gene_id', how='left')
    # # 删除不需要的列
    # df.drop(['gene_id', 'sequence'], axis=1, inplace=True)
    # # 保存结果
    # output_file = input_file.replace('.xlsx', '_output.txt').replace('.csv', '_output.txt')
