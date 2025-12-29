"""
载体改造自动化设计工具函数
用于解析GenBank文件、设计v5NC和v3NC序列、设计NC-PCR引物并生成改造后图谱
"""
import re
import os
import hashlib
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


# Cm-ccdB固定序列
CM_CCDB_SEQUENCE = "GGCAGgagaccGCGGCCGCATTAGGCACCCCAGGCTTTACACTTTATGCTTCCGGCTCGTATAATGTGTGGATTTTGAGTTAGGATCCGTCGAGATTTTCAGGAGCTAAGGAAGCTAAAATGGAGAAAAAAATCACTGGATATACCACCGTTGATATATCCCAATGGCATCGTAAAGAACATTTTGAGGCATTTCAGTCAGTTGCTCAATGTACCTATAACCAGACCGTTCAGCTGGATATTACGGCCTTTTTAAAGACCGTAAAGAAAAATAAGCACAAGTTTTATCCGGCCTTTATTCACATTCTTGCCCGCCTGATGAATGCTCATCCGGAATTCCGTATGGCAATGAAAGACGGTGAGCTGGTGATATGGGATAGTGTTCACCCTTGTTACACCGTTTTCCATGAGCAAACTGAAACGTTTTCATCGCTCTGGAGTGAATACCACGACGATTTCCGGCAGTTTCTACACATATATTCGCAAGATGTGGCGTGTTACGGTGAAAACCTGGCCTATTTCCCTAAAGGGTTTATTGAGAATATGTTTTTCGTATCAGCCAATCCCTGGGTGAGTTTCACCAGTTTTGATTTAAACGTGGCCAATATGGACAACTTCTTCGCCCCCGTTTTCACCATGGGCAAATATTATACGCAAGGCGACAAGGTGCTGATGCCGCTGGCGATTCAGGTTCATCATGCCGTCTGTGATGGCTTCCATGTCGGCAGAATGCTTAATGAATTACAACAGTACTGCGATGAGTGGCAGGGCGGGGCGTAAACGCCGCGTGGATCCGGCTTACTAAAAGCCAGATAACAGTATGCGTATTTGCGCGCTGATTTTTGCGGTATAAGAATATATACTGATATGTATACCCGAAGTATGTCAAAAAGAGGTATGCTATGAAGCAGCGTATTACAGTGACAGTTGACAGCGACAGCTATCAGTTGCTCAAGGCATATATGATGTCAATATCTCCGGTCTGGTAAGCACAACCATGCAGAATGAAGCCCGTCGTCTGCGTGCCGAACGCTGGAAAGCGGAAAATCAGGAAGGGATGGCTGAGGTCGCCCGGTTTATTGAAATGAACGGCTCTTTTGCTGACGAGAACAGGGGCTGGTGAAATGCAGTTTAAGGTTTACACCTATAAAAGAGAGAGCCGTTATCGTCTGTTTGTGGATGTACAGAGTGATATTATTGACACGCCCGGGCGACGGATGGTGATCCCCCTGGCCAGTGCACGTCTGCTGTCAGATAAAGTCTCCCGTGAACTTTACCCGGTGGTGCATATCGGGGATGAAAGCTGGCGCATGATGACCACCGATATGGCCAGTGTGCCGGTTTCCGTTATCGGGGAAGAAGTGGCTGATCTCAGCCACCGCGAAAATGACATCAAAAACGCCATTAACCTGATGTTCTGGGGAATATAAATGTCAGGCTCCCTTAT"


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
            iu20_seq = str(self.record.seq[self.iu20_location.start:self.iu20_location.end])
            id20_seq = str(self.record.seq[self.id20_location.start:self.id20_location.end])

            return {
                'sequence': str(self.record.seq),
                'iu20_location': (int(self.iu20_location.start), int(self.iu20_location.end)),
                'id20_location': (int(self.id20_location.start), int(self.id20_location.end)),
                'iu20_seq': iu20_seq,
                'id20_seq': id20_seq,
                'record_name': self.record.name,
                'record_description': self.record.description
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
            max_length: 最大允许重复长度
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
    def count_gc_in_window(sequence, window_size=12, threshold=11):
        """
        检查序列中是否有连续window_size bp内包含threshold个或更多G/C

        Args:
            sequence: DNA序列
            window_size: 窗口大小
            threshold: G/C数量阈值

        Returns:
            bool: True如果存在违规窗口
        """
        sequence = sequence.upper()
        for i in range(len(sequence) - window_size + 1):
            window = sequence[i:i + window_size]
            gc_count = window.count('G') + window.count('C')
            if gc_count >= threshold:
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

    def check_long_repeat_penalty(self, sequence, insert_position, range_bp=2000, max_penalty=28):
        """
        检查插入位点上下游指定范围内的Long repeat罚分

        Args:
            sequence: 完整载体序列
            insert_position: 插入位点位置
            range_bp: 检查范围（上下游各range_bp/2）
            max_penalty: 最大允许罚分

        Returns:
            tuple: (is_valid, penalty_score)
        """
        # 提取检查区域序列
        start = max(0, insert_position - range_bp // 2)
        end = min(len(sequence), insert_position + range_bp // 2)
        check_seq = sequence[start:end]

        # 使用DNARepeatsFinder查找分散重复
        finder = DNARepeatsFinder(sequence=check_seq)
        long_repeats = finder.find_dispersed_repeats(min_len=16)

        # 计算总罚分
        total_penalty = sum(repeat.get('penalty_score', 0) for repeat in long_repeats)

        return total_penalty <= max_penalty, total_penalty

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
        if self.count_gc_in_window(sequence, 12, 11):
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

    def design_gibson_method(self, parsed_data):
        """
        设计Gibson克隆方法

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']

        # 检查插入位点的Long repeat罚分
        insert_position = (iu20_end + id20_start) // 2
        is_valid, penalty = self.check_long_repeat_penalty(sequence, insert_position)
        if not is_valid:
            self.errors.append(f"Gibson方法: 插入位点上下游2000bp内Long repeat罚分({penalty})超过28分")
            return None

        # 设计v5NC和v3NC（初始尝试：至少30bp）
        min_nc_length = 30
        max_attempts = 100

        for attempt in range(max_attempts):
            # v5NC: 从iU20末端往前取min_nc_length bp
            v5nc_start = iu20_end - min_nc_length - attempt
            v5nc_end = iu20_end - attempt
            v5nc = sequence[v5nc_start:v5nc_end]

            # v3NC: 从iD20起始往后取min_nc_length bp
            v3nc_start = id20_start + attempt
            v3nc_end = id20_start + min_nc_length + attempt
            v3nc = sequence[v3nc_start:v3nc_end]

            # 检查v5NC
            tm_v5nc = self.calculate_tm_simple(v5nc)
            gc_v5nc = self.calculate_gc_content(v5nc)

            # 检查v3NC
            tm_v3nc = self.calculate_tm_simple(v3nc)
            gc_v3nc = self.calculate_gc_content(v3nc)

            # 验证所有条件
            if (tm_v5nc >= 48 and tm_v3nc >= 48 and
                20 < gc_v5nc < 80 and 20 < gc_v3nc < 80 and
                not self.has_homopolymer(v5nc, max_length=7, bases='GC') and
                not self.has_homopolymer(v3nc, max_length=7, bases='GC') and
                not self.count_gc_in_window(v5nc, 12, 11) and
                not self.count_gc_in_window(v3nc, 12, 11)):

                # 记录移位信息
                i5nc = sequence[iu20_end - attempt:iu20_end] if attempt > 0 else ''
                i3nc = sequence[id20_start:id20_start + attempt] if attempt > 0 else ''

                return {
                    'method': 'Gibson',
                    'v5nc': v5nc,
                    'v3nc': v3nc,
                    'v5nc_location': (v5nc_start, v5nc_end),
                    'v3nc_location': (v3nc_start, v3nc_end),
                    'i5nc': i5nc,
                    'i3nc': i3nc,
                    'tm_v5nc': tm_v5nc,
                    'tm_v3nc': tm_v3nc,
                    'gc_v5nc': gc_v5nc,
                    'gc_v3nc': gc_v3nc
                }

        self.errors.append("Gibson方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    def design_goldengate_method(self, parsed_data):
        """
        设计Golden Gate克隆方法

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        iu20_seq = parsed_data['iu20_seq']
        id20_seq = parsed_data['id20_seq']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']

        # 检查是否同时含有BsaI和BsmBI位点
        bsai_sites = ['GGTCTC', 'GAGACC']  # BsaI识别序列及其反向互补
        bsmbi_sites = ['CGTCTC', 'GAGACG']  # BsmBI识别序列及其反向互补

        has_bsai = any(site in sequence.upper() for site in bsai_sites)
        has_bsmbi = any(site in sequence.upper() for site in bsmbi_sites)

        if has_bsai and has_bsmbi:
            self.errors.append("GoldenGate方法: 载体同时含有BsaI和BsmBI位点，无法使用")
            return None

        # v5NC是iU20的最后4bp，v3NC是iD20的最开始4bp
        v5nc = iu20_seq[-4:]
        v3nc = id20_seq[:4]

        # 尝试移位直到找到满足条件的序列
        max_shift = 20
        for shift in range(max_shift):
            # 检查v5NC是否为回文序列
            if self.is_palindrome(v5nc):
                # v5NC往前移动1bp
                v5nc = sequence[iu20_end - 4 - shift - 1:iu20_end - shift - 1]
                continue

            # 检查v3NC是否为回文序列
            if self.is_palindrome(v3nc):
                # v3NC往后移动1bp
                v3nc = sequence[id20_start + shift + 1:id20_start + 4 + shift + 1]
                continue

            # 检查是否会相互错搭
            if self.check_cross_pairing(v5nc, v3nc):
                # 两个都移动
                v5nc = sequence[iu20_end - 4 - shift - 1:iu20_end - shift - 1]
                v3nc = sequence[id20_start + shift + 1:id20_start + 4 + shift + 1]
                continue

            # 找到满足条件的序列
            i5nc = sequence[iu20_end - shift:iu20_end] if shift > 0 else ''
            i3nc = sequence[id20_start:id20_start + shift] if shift > 0 else ''

            return {
                'method': 'GoldenGate',
                'v5nc': v5nc,
                'v3nc': v3nc,
                'v5nc_location': (iu20_end - 4 - shift, iu20_end - shift),
                'v3nc_location': (id20_start + shift, id20_start + 4 + shift),
                'i5nc': i5nc,
                'i3nc': i3nc
            }

        self.errors.append("GoldenGate方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    def design_t4_method(self, parsed_data):
        """
        设计T4克隆方法（要求与GG完全相同）

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        sequence = parsed_data['sequence']
        iu20_seq = parsed_data['iu20_seq']
        id20_seq = parsed_data['id20_seq']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']

        # v5NC是iU20的最后4bp，v3NC是iD20的最开始4bp
        v5nc = iu20_seq[-4:]
        v3nc = id20_seq[:4]

        # 尝试移位直到找到满足条件的序列
        max_shift = 20
        for shift in range(max_shift):
            # 检查v5NC是否为回文序列
            if self.is_palindrome(v5nc):
                # v5NC往前移动1bp
                v5nc = sequence[iu20_end - 4 - shift - 1:iu20_end - shift - 1]
                continue

            # 检查v3NC是否为回文序列
            if self.is_palindrome(v3nc):
                # v3NC往后移动1bp
                v3nc = sequence[id20_start + shift + 1:id20_start + 4 + shift + 1]
                continue

            # 检查是否会相互错搭
            if self.check_cross_pairing(v5nc, v3nc):
                # 两个都移动
                v5nc = sequence[iu20_end - 4 - shift - 1:iu20_end - shift - 1]
                v3nc = sequence[id20_start + shift + 1:id20_start + 4 + shift + 1]
                continue

            # 找到满足条件的序列
            i5nc = sequence[iu20_end - shift:iu20_end] if shift > 0 else ''
            i3nc = sequence[id20_start:id20_start + shift] if shift > 0 else ''

            return {
                'method': 'T4',
                'v5nc': v5nc,
                'v3nc': v3nc,
                'v5nc_location': (iu20_end - 4 - shift, iu20_end - shift),
                'v3nc_location': (id20_start + shift, id20_start + 4 + shift),
                'i5nc': i5nc,
                'i3nc': i3nc
            }

        self.errors.append("T4方法: 无法找到满足条件的v5NC和v3NC序列")
        return None

    def select_cloning_method(self, parsed_data):
        """
        按优先级选择克隆方法

        Args:
            parsed_data: 解析后的GenBank数据

        Returns:
            dict: 设计结果或None
        """
        # 按优先级尝试：Gibson > GoldenGate > T4
        methods = [
            ('Gibson', self.design_gibson_method),
            ('GoldenGate', self.design_goldengate_method),
            ('T4', self.design_t4_method)
        ]

        for method_name, design_func in methods:
            result = design_func(parsed_data)
            if result:
                return result

        return None

    def design_nc_pcr_primers(self, design_result, parsed_data, vector_code=None, target_tm=60):
        """
        设计NC-PCR引物（仅Gibson方法需要）

        Args:
            design_result: 克隆方法设计结果
            parsed_data: 解析后的GenBank数据
            target_tm: 目标Tm值（默认60℃）

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

        v5_len = original_v5_end - original_v5_start
        v3_len = original_v3_end - original_v3_start

        def attempt_design(v5_start, v3_start):
            v5_end = v5_start + v5_len
            v3_start_adj = v3_start
            v3_end = v3_start_adj + v3_len
            if v5_start < 0 or v3_end > len(sequence) or v5_end > parsed_data['iu20_location'][1]:
                return None
            if v3_start_adj < parsed_data['id20_location'][0]:
                return None

            v5_seq = sequence[v5_start:v5_end]
            v3_seq = sequence[v3_start_adj:v3_end]

            if not self._validate_gibson_arm(v5_seq) or not self._validate_gibson_arm(v3_seq):
                return None

            forward = None
            forward_fallback = None
            max_forward_len = min(max_primer_len, v5_len)
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
            max_reverse_len = min(max_primer_len, v3_len)
            for length in range(min_primer_len, max_reverse_len + 1):
                template_start = v3_end - length
                if template_start < 0:
                    continue
                if template_start < v3_start_adj:
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

            return forward, reverse, (v5_start, v5_end), (v3_start_adj, v3_end), hetero_dg

        for shift5 in range(0, max_boundary_shift + 1):
            new_v5_start = max(0, original_v5_start - shift5)
            for shift3 in range(0, max_boundary_shift + 1):
                new_v3_start = original_v3_start + shift3
                attempt = attempt_design(new_v5_start, new_v3_start)
                if attempt:
                    forward, reverse, v5_loc, v3_loc, hetero_dg = attempt
                    design_result['v5nc_location'] = v5_loc
                    design_result['v3nc_location'] = v3_loc
                    design_result['v5nc'] = sequence[v5_loc[0]:v5_loc[1]]
                    design_result['v3nc'] = sequence[v3_loc[0]:v3_loc[1]]
                    self._update_shift_records(design_result, parsed_data, sequence)

                    forward['name'] = self.generate_primer_name(vector_code, '5OL', f"{v5_loc[0]}-{v5_loc[1]}")
                    reverse['name'] = self.generate_primer_name(vector_code, '3OLrc', f"{v3_loc[0]}-{v3_loc[1]}")

                    return {
                        'forward': forward,
                        'reverse': reverse,
                        'heterodimer_dg': hetero_dg
                    }

        self.errors.append("NC-PCR引物设计失败：无法在允许边界内找到满足T97=60℃的引物")
        return None

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

    def generate_modified_genbank(self, design_result, parsed_data, primer_result, output_path, vector_name):
        """
        生成改造后的GenBank文件

        Args:
            design_result: 克隆方法设计结果
            parsed_data: 解析后的GenBank数据
            primer_result: 引物设计结果（可能为None）
            output_path: 输出文件路径
            vector_name: 载体名称

        Returns:
            str: 输出文件路径
        """
        sequence = parsed_data['sequence']
        iu20_start, iu20_end = parsed_data['iu20_location']
        id20_start, id20_end = parsed_data['id20_location']
        v5nc_start, v5nc_end = design_result['v5nc_location']
        v3nc_start, v3nc_end = design_result['v3nc_location']

        # 构建改造后序列：移除v5NC和v3NC之间的序列，插入Cm-ccdB
        modified_seq = sequence[:v5nc_end] + CM_CCDB_SEQUENCE + sequence[v3nc_start:]

        # 创建新的SeqRecord
        modified_record = SeqRecord(
            Seq(modified_seq),
            id=vector_name,
            name=vector_name,
            description=f"Modified vector - {design_result['method']} method",
            annotations={"molecule_type": "DNA"}
        )

        # 添加features
        # 1. iU20
        iu20_feature = SeqFeature(
            FeatureLocation(iu20_start, iu20_end),
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

        # 3. Cm-ccdB（插入在v5nc_end位置）
        cm_ccdb_start = v5nc_end
        cm_ccdb_end = v5nc_end + len(CM_CCDB_SEQUENCE)
        cm_ccdb_feature = SeqFeature(
            FeatureLocation(cm_ccdb_start, cm_ccdb_end),
            type="CDS",
            qualifiers={'label': ['Cm-ccdB'], 'note': ['Chloramphenicol resistance and ccdB']}
        )
        modified_record.features.append(cm_ccdb_feature)

        # 4. v3NC（位置需要调整）
        v3nc_new_start = cm_ccdb_end
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

        # 5. iD20（位置需要调整）
        id20_offset = len(modified_seq) - len(sequence)
        id20_new_start = id20_start + id20_offset
        id20_new_end = id20_end + id20_offset
        id20_feature = SeqFeature(
            FeatureLocation(id20_new_start, id20_new_end),
            type="misc_feature",
            qualifiers={'label': ['iD20']}
        )
        modified_record.features.append(id20_feature)

        # 写入GenBank文件
        SeqIO.write(modified_record, output_path, "genbank")

        return output_path

    def extract_resistance_from_filename(self, filename):
        """
        从文件名中提取抗性信息
        例如: pCVaXXX(Amp)-xxxxxxxxxxxx.gb -> Amp

        Args:
            filename: 文件名

        Returns:
            str: 抗性信息，如果未找到则返回None
        """
        pattern = r'\(([^)]+)\)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
        return None

    def extract_vector_code_from_filename(self, filename):
        """
        从文件名中提取载体编号
        例如: pCVa123(Amp)-xxxxxxxxxxxx.gb -> pCVa123

        Args:
            filename: 文件名

        Returns:
            str: 载体编号
        """
        pattern = r'(pCVa\w+)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
        return 'pCVa001'  # 默认值

    def extract_filename_suffix(self, filename):
        """
        提取文件名中的描述部分（pCVaXXX(抗性)-xxxx.gb -> xxxx）
        """
        base = os.path.basename(filename)
        if '-' in base:
            suffix = base.split('-', 1)[1]
        else:
            suffix = os.path.splitext(base)[0]
        suffix = os.path.splitext(suffix)[0].strip()
        return suffix or 'Modified'

    @staticmethod
    def generate_primer_name(vector_code, suffix, token):
        """
        生成符合要求的引物名称
        """
        code = vector_code or 'Vector'
        digest = hashlib.md5(f"{code}-{suffix}-{token}".encode()).hexdigest()
        number = int(digest[:6], 16) % 10000
        return f"YHY{number:04d}-{code}M1-{suffix}"
