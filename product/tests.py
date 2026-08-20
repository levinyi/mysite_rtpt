import copy
import io
import os
import random
import re
import shutil
import tempfile

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature, SimpleLocation
from Bio.SeqRecord import SeqRecord
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import TestCase, override_settings

from product.models import Vector, VectorElement, VectorElementOccurrence, compute_seq_hash
from user_center.utils.element_extractor import commit_candidates, extract_candidates_bulk
from user_center.utils.element_screen import (
    screen_sequence, find_element_by_sequence, invalidate_index_cache, revcomp,
)
from user_center.utils.vector_automation import VectorAutomationDesigner


def _rand_seq(n, seed):
    rng = random.Random(seed)
    return ''.join(rng.choice('ACGT') for _ in range(n))


# 命中边界允许的松动量。侧翼随机碱基有 1/4 概率恰好接着 subject 继续配上，这时确实存在
# 一段更长的完全一致序列，X-drop 如实报出来是对的。但漂移必须是几个碱基级别 —— 出问题的
# 旧实现会拖出 20+ bp 噪声并把 identity 稀释掉，这个上界就是用来卡住那种情况的。
BOUNDARY_SLOP = 8


class ElementScreenTests(TestCase):
    """客户序列 vs 载体元件的同源重组风险筛查。"""

    def setUp(self):
        invalidate_index_cache()
        self.promoter_seq = _rand_seq(204, seed=11)
        self.resistance_seq = _rand_seq(861, seed=12)

        self.promoter = VectorElement.objects.create(
            name='CMV promoter', element_type='promoter', sequence=self.promoter_seq,
        )
        self.resistance = VectorElement.objects.create(
            name='AmpR', element_type='resistance', sequence=self.resistance_seq,
        )

        # 目标载体：骨架含 promoter，不含 AmpR
        backbone = _rand_seq(2000, seed=13) + self.promoter_seq + _rand_seq(2000, seed=14)
        self.vector = Vector.objects.create(vector_name='pTest', vector_map=backbone)
        VectorElementOccurrence.objects.create(
            element=self.promoter, vector=self.vector, start=2000, end=2204, strand=1,
        )

    def tearDown(self):
        invalidate_index_cache()

    def test_clean_sequence_passes(self):
        result = screen_sequence(_rand_seq(1500, seed=99), target_vector=self.vector)
        self.assertTrue(result['ok'])
        self.assertEqual(result['summary']['verdict'], 'pass')
        self.assertEqual(result['element_hits'], [])
        self.assertEqual(result['vector_hits'], [])

    def test_exact_element_found_with_exact_boundaries(self):
        """埋一段 100% 一致的元件，必须原样捞回，长度和 identity 都不能被延伸噪声稀释。

        回归测试：早期实现的延伸是"连续错配 N 次就停"。真实同源区结束后，query 进入的
        随机序列与 subject 仍有 ~25% 概率偶然配上，延伸会多拖十几到几十 bp，这些噪声被
        算进 identity，把一段 100% 一致的命中稀释到阈值以下 —— 完全一致的元件反而漏报。
        改成 X-drop（延伸时记最高分，结束后回退到最高分处）才让边界落在真实同源边界上。
        """
        planted = len(self.promoter_seq)
        query = _rand_seq(600, seed=21) + self.promoter_seq + _rand_seq(600, seed=22)
        result = screen_sequence(query, target_vector=self.vector)

        hits = [h for h in result['element_hits'] if h['name'] == 'CMV promoter']
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['identity'], 1.0)          # 旧 bug 在这里稀释成 0.947
        self.assertGreaterEqual(hits[0]['length'], planted)  # 整段都要捞回来
        self.assertLessEqual(hits[0]['length'], planted + BOUNDARY_SLOP)  # 且不许漂移
        self.assertLessEqual(hits[0]['q_start'], 600)        # 覆盖埋入区
        self.assertGreaterEqual(hits[0]['q_end'], 600 + planted)
        self.assertTrue(hits[0]['on_target_vector'])
        self.assertEqual(result['summary']['verdict'], 'risk')

    def test_exact_match_found_under_any_padding(self):
        """原 bug 只在某些侧翼序列下发作（polyA 侧翼恰好能立刻停住延伸），逐一钉死。"""
        paddings = {
            'random': _rand_seq(300, seed=31),
            'polyA': 'A' * 300,
            'polyGC': 'GC' * 150,
            'low_complexity': 'ATATAT' * 50,
        }
        planted = len(self.promoter_seq)
        for tag, pad in paddings.items():
            with self.subTest(padding=tag):
                result = screen_sequence(pad + self.promoter_seq + pad, target_vector=self.vector)
                hits = [h for h in result['element_hits'] if h['name'] == 'CMV promoter']
                self.assertEqual(len(hits), 1, f'{tag} 侧翼下漏报了元件')
                self.assertEqual(hits[0]['identity'], 1.0)
                self.assertGreaterEqual(hits[0]['length'], planted)
                self.assertLessEqual(hits[0]['length'], planted + BOUNDARY_SLOP)

    def test_reverse_complement_hit_is_found(self):
        """元件以反向互补形式混进客户序列，照样要抓到 —— 重组不挑链向。"""
        rc = revcomp(self.resistance_seq)[:400]
        query = _rand_seq(300, seed=41) + rc + _rand_seq(300, seed=42)
        result = screen_sequence(query, target_vector=self.vector)

        hits = [h for h in result['element_hits'] if h['name'] == 'AmpR']
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['strand'], -1)
        self.assertEqual(hits[0]['identity'], 1.0)
        self.assertGreaterEqual(hits[0]['length'], 400)
        self.assertLessEqual(hits[0]['length'], 400 + BOUNDARY_SLOP)
        self.assertFalse(hits[0]['on_target_vector'])

    def test_point_mutations_still_hit_above_identity_threshold(self):
        seq = list(self.resistance_seq[:300])
        for pos in (50, 130, 210):
            seq[pos] = 'A' if seq[pos] != 'A' else 'C'
        query = _rand_seq(200, seed=51) + ''.join(seq) + _rand_seq(200, seed=52)

        hits = [h for h in screen_sequence(query, target_vector=self.vector)['element_hits']
                if h['name'] == 'AmpR']
        self.assertEqual(len(hits), 1)
        self.assertGreaterEqual(hits[0]['identity'], 0.95)
        self.assertLess(hits[0]['identity'], 1.0)

    def test_unannotated_backbone_homology_is_caught(self):
        """目标载体骨架上没被标注成元件的区段同样能重组，必须报出来。"""
        segment = self.vector.vector_map[300:500]
        query = _rand_seq(400, seed=61) + segment + _rand_seq(400, seed=62)

        result = screen_sequence(query, target_vector=self.vector)
        self.assertEqual(len(result['vector_hits']), 1)
        hit = result['vector_hits'][0]
        self.assertEqual(hit['identity'], 1.0)
        self.assertGreaterEqual(hit['length'], 200)
        self.assertLessEqual(hit['length'], 200 + BOUNDARY_SLOP)

    def test_short_homology_below_threshold_is_ignored(self):
        """22bp 的偶然同源不驱动重组，报出来只会淹没真信号。"""
        query = _rand_seq(500, seed=71) + self.promoter_seq[:22] + _rand_seq(500, seed=72)
        result = screen_sequence(query, target_vector=self.vector, min_length=30)
        self.assertEqual([h for h in result['element_hits'] if h['name'] == 'CMV promoter'], [])

    def test_screen_disabled_elements_are_excluded(self):
        self.resistance.screen_enabled = False
        self.resistance.save()
        invalidate_index_cache()

        query = _rand_seq(200, seed=81) + self.resistance_seq[:300] + _rand_seq(200, seed=82)
        result = screen_sequence(query, target_vector=self.vector)
        self.assertEqual([h for h in result['element_hits'] if h['name'] == 'AmpR'], [])

    def test_index_cache_refreshes_when_library_changes(self):
        query = _rand_seq(200, seed=91) + self.promoter_seq + _rand_seq(200, seed=92)
        self.assertEqual(len(screen_sequence(query)['element_hits']), 1)

        VectorElement.objects.create(
            name='extra', element_type='other', sequence=self.promoter_seq[::-1],
        )
        # 库变了但没手动 invalidate：版本号（条数 + 最后更新时间）应当自动触发重建
        self.assertEqual(screen_sequence(query)['library_size'], 3)

    def test_screen_without_target_vector(self):
        query = _rand_seq(200, seed=101) + self.promoter_seq + _rand_seq(200, seed=102)
        result = screen_sequence(query, target_vector=None)
        self.assertTrue(result['ok'])
        self.assertEqual(len(result['element_hits']), 1)
        self.assertFalse(result['element_hits'][0]['on_target_vector'])
        self.assertEqual(result['vector_hits'], [])

    def test_sequence_too_short_is_rejected(self):
        self.assertFalse(screen_sequence('ACGT')['ok'])


class ElementLookupTests(TestCase):
    """元件库序列查询：库里有没有这段序列。"""

    def setUp(self):
        invalidate_index_cache()
        self.seq = _rand_seq(300, seed=201)
        self.element = VectorElement.objects.create(
            name='T7 promoter', element_type='promoter', sequence=self.seq,
        )

    def tearDown(self):
        invalidate_index_cache()

    def test_exact_lookup(self):
        result = find_element_by_sequence(self.seq)
        self.assertTrue(result['exact'])
        self.assertEqual(result['hits'][0]['element_id'], self.element.pk)

    def test_exact_lookup_ignores_whitespace_and_case(self):
        messy = f'  {self.seq[:100].lower()}\n{self.seq[100:200]}\t{self.seq[200:].lower()}  '
        result = find_element_by_sequence(messy)
        self.assertTrue(result['exact'])
        self.assertEqual(result['hits'][0]['element_id'], self.element.pk)

    def test_partial_lookup_reports_coverage(self):
        result = find_element_by_sequence(self.seq[50:200])
        self.assertFalse(result['exact'])
        self.assertEqual(len(result['hits']), 1)
        self.assertEqual(result['hits'][0]['length'], 150)
        self.assertAlmostEqual(result['hits'][0]['coverage'], 150 / 300, places=3)

    def test_unknown_sequence_returns_no_hits(self):
        result = find_element_by_sequence(_rand_seq(300, seed=999))
        self.assertFalse(result['exact'])
        self.assertEqual(result['hits'], [])


class VectorElementModelTests(TestCase):
    def test_save_normalizes_sequence_and_derives_hash(self):
        element = VectorElement.objects.create(name='a', sequence='  acgtacgtacgtacgtacgt \n')
        self.assertEqual(element.sequence, 'ACGTACGTACGTACGTACGT')
        self.assertEqual(element.seq_length, 20)
        self.assertEqual(element.seq_hash, compute_seq_hash('ACGTACGTACGTACGTACGT'))

    def test_seq_hash_is_unique(self):
        VectorElement.objects.create(name='first', sequence='ACGTACGTACGTACGTACGT')
        with self.assertRaises(IntegrityError):
            VectorElement.objects.create(name='second', sequence='acgtacgtacgtacgtacgt')


def _genbank_bytes(sequence, features):
    """拼一个最小可解析的 GenBank 文件。features: [(type, start, end, strand, label)]"""
    record = SeqRecord(
        Seq(sequence), id='pTest', name='pTest', description='test vector',
        annotations={'molecule_type': 'DNA', 'topology': 'circular'},
    )
    for ftype, start, end, strand, label in features:
        record.features.append(SeqFeature(
            SimpleLocation(start, end, strand=strand), type=ftype, qualifiers={'label': [label]},
        ))
    handle = io.StringIO()
    SeqIO.write(record, handle, 'genbank')
    return handle.getvalue().encode()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='rtpt-test-media-'))
class ElementBulkExtractTests(TestCase):
    """批量解析多个载体，把同一条序列合并成一行候选。"""

    def setUp(self):
        invalidate_index_cache()
        self.promoter = _rand_seq(120, seed=21)     # 两个载体共有
        self.ampr = _rand_seq(300, seed=22)         # 两个载体共有，但叫法不同
        self.only_a = _rand_seq(200, seed=23)       # 只在 A 上

        self.vector_a = self._make_vector('pA', _rand_seq(500, seed=24), [
            ('promoter', self.promoter, 'T7 promoter'),
            ('CDS', self.ampr, 'AmpR'),
            ('CDS', self.only_a, 'GFP'),
        ])
        self.vector_b = self._make_vector('pB', _rand_seq(500, seed=25), [
            ('promoter', self.promoter, 'T7 promoter'),
            ('CDS', self.ampr, 'bla'),
        ])

    def tearDown(self):
        invalidate_index_cache()

    def _make_vector(self, name, filler, parts, user=None):
        """把 parts 依次拼进 filler 之后，生成一个带图谱的载体。"""
        sequence = filler
        features = []
        for ftype, seq, label in parts:
            features.append((ftype, len(sequence), len(sequence) + len(seq), 1, label))
            sequence += seq
        vector = Vector.objects.create(vector_name=name, user=user)
        vector.vector_file.save(f'{name}.gb', ContentFile(_genbank_bytes(sequence, features)))
        return vector

    def _candidate(self, result, name):
        return next(c for c in result['candidates'] if c['label'] == name)

    def _selection(self, candidate):
        """按前端的方式把一条候选转成 commit 用的 selection。"""
        return {
            'sequence': candidate['sequence'],
            'name': candidate['label'],
            'element_type': candidate['suggested_type'],
            'genbank_feature_type': candidate['genbank_feature_type'],
            'aliases': candidate['aliases'],
            'occurrences': [{
                'vector_id': o['vector_id'], 'start': o['start'], 'end': o['end'],
                'strand': o['strand'], 'label_in_vector': o['label'],
            } for o in candidate['occurrences']],
        }

    def test_shared_sequence_merges_into_one_row(self):
        result = extract_candidates_bulk([self.vector_a, self.vector_b])

        self.assertEqual(result['stats']['rows_before_merge'], 5)
        self.assertEqual(result['stats']['rows_after_merge'], 3)

        shared = self._candidate(result, 'T7 promoter')
        self.assertEqual(shared['vector_count'], 2)
        self.assertEqual({o['vector_id'] for o in shared['occurrences']},
                         {self.vector_a.pk, self.vector_b.pk})

        # 只在一个载体上的元件不受影响
        self.assertEqual(self._candidate(result, 'GFP')['vector_count'], 1)

    def test_differing_labels_become_aliases(self):
        result = extract_candidates_bulk([self.vector_a, self.vector_b])
        # AmpR / bla 是同一条序列的两个叫法，各出现一次，取先出现的 AmpR 作主名
        merged = self._candidate(result, 'AmpR')
        self.assertEqual(merged['vector_count'], 2)
        self.assertEqual(merged['aliases'], ['bla'])

    def test_commit_registers_occurrence_on_every_vector(self):
        result = extract_candidates_bulk([self.vector_a, self.vector_b])
        stats = commit_candidates([self._selection(self._candidate(result, 'AmpR'))])

        self.assertEqual((stats['created'], stats['occurrences']), (1, 2))
        element = VectorElement.objects.get(seq_hash=compute_seq_hash(self.ampr))
        self.assertEqual(
            set(element.occurrences.values_list('vector_id', flat=True)),
            {self.vector_a.pk, self.vector_b.pk},
        )
        # 两张图谱上的叫法都收进了别名
        self.assertIn('bla', element.aliases)

    def test_recommit_is_idempotent(self):
        result = extract_candidates_bulk([self.vector_a, self.vector_b])
        selections = [self._selection(c) for c in result['candidates']]
        commit_candidates(selections)

        again = commit_candidates(selections)
        self.assertEqual(again['created'], 0)
        self.assertEqual(again['occurrences'], 0)
        self.assertEqual(VectorElementOccurrence.objects.count(), 5)

    def test_committed_elements_show_as_exists_on_reparse(self):
        result = extract_candidates_bulk([self.vector_a, self.vector_b])
        commit_candidates([self._selection(c) for c in result['candidates']])

        reparsed = extract_candidates_bulk([self.vector_a, self.vector_b])
        self.assertTrue(all(c['dedup'] == 'exists' for c in reparsed['candidates']))
        self.assertFalse(any(c['default_checked'] for c in reparsed['candidates']))
        self.assertTrue(all(o['registered'] for c in reparsed['candidates']
                            for o in c['occurrences']))

    def test_partially_registered_sequence_is_flagged_for_the_missing_vector(self):
        """序列已入库、但还有载体没登记过 —— 这行要留着可勾选。"""
        result = extract_candidates_bulk([self.vector_a])
        commit_candidates([self._selection(self._candidate(result, 'T7 promoter'))])

        both = extract_candidates_bulk([self.vector_a, self.vector_b])
        promoter = self._candidate(both, 'T7 promoter')
        self.assertEqual(promoter['dedup'], 'exists_new_occurrence')
        self.assertTrue(promoter['default_checked'])
        registered = {o['vector_id']: o['registered'] for o in promoter['occurrences']}
        self.assertEqual(registered, {self.vector_a.pk: True, self.vector_b.pk: False})

    def test_unreadable_vector_is_reported_without_killing_the_batch(self):
        broken = Vector.objects.create(vector_name='pNoMap')   # 没有任何图谱文件
        result = extract_candidates_bulk([self.vector_a, broken, self.vector_b])

        self.assertEqual(result['stats']['vectors_ok'], 2)
        self.assertEqual([e['vector_name'] for e in result['errors']], ['pNoMap'])
        self.assertEqual(result['stats']['rows_after_merge'], 3)

    def test_company_vector_wins_as_source_of_a_shared_element(self):
        """同一条序列既长在客户载体又长在公司载体上，算公司的通用元件。"""
        customer = User.objects.create_user('cust', password='x')
        vector_c = self._make_vector('pCustomer', _rand_seq(400, seed=26),
                                     [('promoter', self.promoter, 'T7 promoter')], user=customer)

        result = extract_candidates_bulk([vector_c, self.vector_a])
        commit_candidates([self._selection(self._candidate(result, 'T7 promoter'))])

        element = VectorElement.objects.get(seq_hash=compute_seq_hash(self.promoter))
        self.assertEqual(element.source_kind, 'company')
        self.assertEqual(element.source_vector_id, self.vector_a.pk)

    def test_selection_without_usable_occurrence_is_skipped(self):
        stats = commit_candidates([{
            'sequence': self.promoter, 'name': 'T7 promoter', 'element_type': 'promoter',
            'occurrences': [{'vector_id': 99999, 'start': 0, 'end': 120, 'strand': 1}],
        }])
        self.assertEqual(stats['skipped'], 1)
        self.assertEqual(VectorElement.objects.count(), 0)


class VectorNoModifyDesignTests(TestCase):
    """不改造模式：只把 v5NC/v3NC/引物标注到图谱上，质粒序列一个碱基都不动。

    对照改造模式（把 iU20–iD20 之间换成 Cm-ccdB）跑同一条载体，验证两者的差别
    只在中间区，以及下游 ParsingGenBank 依赖的 [iU20.end, iD20.start) 区间仍然对得上。
    """

    IU20 = (1000, 1020)
    ID20 = (1500, 1520)
    SPANNING = (900, 1600)   # 横跨 iU20–iD20，改造模式下会被丢弃

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # seed=1 的随机序列能过 Gibson 的全部闸门（长重复、回文/发卡、GC、同聚物）
        rng = random.Random(1)
        cls.sequence = ''.join(rng.choice('ACGT') for _ in range(3000))
        record = SeqRecord(
            Seq(cls.sequence), id='pCVaTEST', name='pCVaTEST',
            description='synthetic test vector', annotations={'molecule_type': 'DNA'},
        )
        record.features = [
            SeqFeature(SimpleLocation(*cls.IU20), type='misc_feature', qualifiers={'label': ['iU20']}),
            SeqFeature(SimpleLocation(*cls.ID20), type='misc_feature', qualifiers={'label': ['iD20']}),
            SeqFeature(SimpleLocation(200, 400), type='misc_feature', qualifiers={'label': ['upstream_elem']}),
            SeqFeature(SimpleLocation(*cls.SPANNING), type='misc_feature', qualifiers={'label': ['spanning_elem']}),
            SeqFeature(SimpleLocation(2000, 2300), type='misc_feature', qualifiers={'label': ['downstream_elem']}),
        ]
        cls._tmpdir = tempfile.mkdtemp()
        cls.gb_path = os.path.join(cls._tmpdir, 'pCVaTEST.gb')
        with open(cls.gb_path, 'w') as handle:
            SeqIO.write(record, handle, 'genbank')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)
        super().tearDownClass()

    def _design(self, modify):
        """跑完整一条设计链路，返回 (设计结果, 输出图谱 record, 骨架引物)。"""
        designer = VectorAutomationDesigner(self.gb_path)
        parsed = designer.parse_genbank()
        self.assertIsNotNone(parsed, f'解析失败: {designer.errors}')
        design_result = designer.select_cloning_method(parsed, forced_method='Gibson')
        self.assertIsNotNone(design_result, f'Gibson 设计失败: {designer.errors}')

        # 不改造模式下质粒没变，编号不进位，版本位留空
        variant = 'M1' if modify else ''
        primers = designer.design_nc_pcr_primers(
            design_result, parsed, vector_code='pCVaTEST', variant=variant)
        backbone = None if modify else designer.design_backbone_pcr_primers(
            design_result, parsed, vector_code='pCVaTEST')

        out_path = os.path.join(self._tmpdir, f"out_{'M1' if modify else 'plain'}.gb")
        designer.generate_modified_genbank(
            design_result, parsed, primers, out_path, f'pCVaTEST{variant}',
            colony_primers=None, modify=modify, backbone_primers=backbone,
        )
        return design_result, SeqIO.read(out_path, 'genbank'), backbone

    @staticmethod
    def _labels(record):
        found = {}
        for feature in record.features:
            for label in feature.qualifiers.get('label', []):
                found.setdefault(label, []).append(
                    (int(feature.location.start), int(feature.location.end)))
        return found

    def test_not_modified_output_keeps_the_original_sequence(self):
        _, record, _ = self._design(modify=False)
        self.assertEqual(str(record.seq).upper(), self.sequence.upper())

    def test_not_modified_output_has_no_cm_ccdb(self):
        _, record, _ = self._design(modify=False)
        self.assertFalse([lbl for lbl in self._labels(record) if lbl.startswith('Cm-ccdB')])

    def test_modified_output_inserts_cm_ccdb_and_grows(self):
        # 回归保护：改造模式的行为不能被不改造模式的改动带偏
        design_result, record, _ = self._design(modify=True)
        cm_labels = [lbl for lbl in self._labels(record) if lbl.startswith('Cm-ccdB')]
        self.assertEqual(len(cm_labels), 1)
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]
        cm_start, cm_end = self._labels(record)[cm_labels[0]][0]
        self.assertEqual(cm_start, v5nc_end)
        expected_len = len(self.sequence) - (v3nc_start - v5nc_end) + (cm_end - cm_start)
        self.assertEqual(len(record.seq), expected_len)

    def test_feature_spanning_the_insert_survives_only_when_not_modified(self):
        _, annotated, _ = self._design(modify=False)
        _, modified, _ = self._design(modify=True)
        self.assertEqual(self._labels(annotated).get('spanning_elem'), [self.SPANNING])
        self.assertIsNone(self._labels(modified).get('spanning_elem'))
        # 插入点之前的 feature 两种模式下都原位保留
        self.assertEqual(self._labels(annotated).get('upstream_elem'), [(200, 400)])
        self.assertEqual(self._labels(modified).get('upstream_elem'), [(200, 400)])

    def test_downstream_replacement_window_matches_the_design(self):
        # 下游 ParsingGenBank 取 [iU20.end, iD20.start) 整段替换成 [i5NC, gene, i3NC]，
        # 所以这两个坐标必须紧贴 v5NC 末端和 v3NC 起点，否则会切错地方
        for modify in (True, False):
            with self.subTest(modify=modify):
                design_result, record, _ = self._design(modify)
                labels = self._labels(record)
                iu20_end = labels['iU20'][0][1]
                id20_start = labels['iD20'][0][0]
                v3nc_start = labels['v3NC'][0][0]
                self.assertEqual(iu20_end, design_result['v5nc_location'][1])
                self.assertEqual(id20_start, v3nc_start)

    def test_not_modified_replacement_window_is_the_customers_own_sequence(self):
        design_result, record, _ = self._design(modify=False)
        labels = self._labels(record)
        window = str(record.seq)[labels['iU20'][0][1]:labels['iD20'][0][0]].upper()
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]
        self.assertEqual(window, self.sequence[v5nc_end:v3nc_start].upper())

    def test_backbone_primers_are_outward_facing(self):
        design_result, _, backbone = self._design(modify=False)
        self.assertIsNotNone(backbone, '骨架引物应设计成功')
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]
        forward = backbone['forward']
        reverse = backbone['reverse']
        # 正向 5' 端紧贴 v3NC 起点、向右；反向 5' 端紧贴 v5NC 末端、向左 —— 两条背对背
        self.assertEqual(forward['template_start'], v3nc_start)
        self.assertEqual(forward['sequence'],
                         self.sequence[v3nc_start:v3nc_start + forward['length']])
        self.assertEqual(reverse['template_end'], v5nc_end)
        self.assertEqual(
            reverse['sequence'],
            str(Seq(self.sequence[v5nc_end - reverse['length']:v5nc_end]).reverse_complement()).upper(),
        )

    def test_backbone_primers_are_annotated_on_the_map(self):
        _, record, backbone = self._design(modify=False)
        labels = self._labels(record)
        self.assertIn(backbone['forward']['name'], labels)
        self.assertIn(backbone['reverse']['name'], labels)
        strands = {
            tuple(f.qualifiers.get('label', [''])): f.location.strand
            for f in record.features if f.type == 'primer_bind'
        }
        self.assertEqual(strands[(backbone['forward']['name'],)], 1)
        self.assertEqual(strands[(backbone['reverse']['name'],)], -1)

    def test_modified_mode_designs_no_backbone_primers(self):
        _, record, backbone = self._design(modify=True)
        self.assertIsNone(backbone)
        self.assertFalse([lbl for lbl in self._labels(record) if 'BB' in lbl])

    def test_primer_names_carry_the_map_variant(self):
        designer = VectorAutomationDesigner(self.gb_path)
        self.assertTrue(
            designer.generate_primer_name('pCVa001', '5OL', '0-30').endswith('pCVa001M1-5OL'))
        # 不改造：引物名里只能出现原编号，加版本号就等于指向另一条质粒
        self.assertTrue(
            designer.generate_primer_name('pCVa001', '5OL', '0-30', variant='')
            .endswith('pCVa001-5OL'))

    def test_backbone_primer_names_keep_the_original_vector_code(self):
        _, _, backbone = self._design(modify=False)
        self.assertEqual(backbone['forward']['name'].split('-')[1], 'pCVaTEST')
        self.assertEqual(backbone['reverse']['name'].split('-')[1], 'pCVaTEST')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='vec_task_test_'))
class VectorDesignTaskTests(TestCase):
    """跑完整的 Celery 任务体（同步调用），确认两种模式落库的字段和产物文件都对。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        rng = random.Random(1)
        cls.sequence = ''.join(rng.choice('ACGT') for _ in range(3000))
        record = SeqRecord(
            Seq(cls.sequence), id='pCVa777', name='pCVa777',
            description='synthetic test vector', annotations={'molecule_type': 'DNA'},
        )
        record.features = [
            SeqFeature(SimpleLocation(1000, 1020), type='misc_feature', qualifiers={'label': ['iU20']}),
            SeqFeature(SimpleLocation(1500, 1520), type='misc_feature', qualifiers={'label': ['iD20']}),
        ]
        buf = io.StringIO()
        SeqIO.write(record, buf, 'genbank')
        cls.gb_bytes = buf.getvalue().encode()

    def _make_vector(self):
        vector = Vector.objects.create(vector_name='pCVa777 test')
        vector.vector_file.save('pCVa777(Kan)-test.gb', ContentFile(self.gb_bytes), save=True)
        return vector

    def test_task_not_modified_keeps_the_vector_id_and_adds_backbone_primers(self):
        from user_center.tasks import async_vector_automation_design

        vector = self._make_vector()
        result = async_vector_automation_design(vector.id, modify=False)
        self.assertEqual(result['status'], 'success', result)
        self.assertEqual(result['method'], 'Gibson')
        self.assertIs(result['modify_vector'], False)

        vector.refresh_from_db()
        self.assertIs(vector.modify_vector, False)
        self.assertEqual(vector.design_status, 'Completed')

        # 质粒没改，编号不能进位：VectorID、图谱文件名、引物名里都只能是 pCVa777
        self.assertEqual(vector.vector_id, 'pCVa777(Kan)')
        gb_name = os.path.basename(vector.vector_gb.name)
        self.assertTrue(gb_name.startswith('pCVa777(Kan)-'), gb_name)
        self.assertNotIn('M1', gb_name)
        self.assertNotIn('A1', gb_name)
        # 和客户上传的原件同目录，靠 -Annotated 区分，否则会被 Django 追加随机后缀
        self.assertTrue(gb_name.endswith('-Annotated.gb'), gb_name)
        self.assertNotEqual(gb_name, os.path.basename(vector.vector_file.name))
        for field in (vector.primer_forward, vector.primer_reverse,
                      vector.backbone_primer_forward, vector.backbone_primer_reverse):
            self.assertIn('-pCVa777-', field.split('::')[0])

        self.assertTrue(vector.backbone_primer_forward)
        self.assertTrue(vector.backbone_primer_reverse)
        self.assertIsNotNone(vector.backbone_primer_forward_tm)

        # 产物图谱的序列必须与客户原质粒完全一致
        record = SeqIO.read(vector.vector_gb.path, 'genbank')
        self.assertEqual(str(record.seq).upper(), self.sequence.upper())

        # vector_map 存的是骨架，与是否改造无关
        self.assertEqual(vector.vector_map.upper(),
                         (self.sequence[:1020] + self.sequence[1500:]).upper())

    def test_task_modified_writes_m1_file_and_no_backbone_primers(self):
        from user_center.tasks import async_vector_automation_design

        vector = self._make_vector()
        result = async_vector_automation_design(vector.id, forced_method='Gibson', modify=True)
        self.assertEqual(result['status'], 'success', result)
        self.assertIs(result['modify_vector'], True)

        vector.refresh_from_db()
        self.assertIs(vector.modify_vector, True)
        self.assertIn('M1(Kan)', os.path.basename(vector.vector_gb.name))
        self.assertNotIn('-Annotated', os.path.basename(vector.vector_gb.name))
        self.assertIsNone(vector.backbone_primer_forward)

        record = SeqIO.read(vector.vector_gb.path, 'genbank')
        self.assertNotEqual(str(record.seq).upper(), self.sequence.upper())
        self.assertGreater(len(record.seq), len(self.sequence))

        # 骨架序列与不改造模式一致
        self.assertEqual(vector.vector_map.upper(),
                         (self.sequence[:1020] + self.sequence[1500:]).upper())

    def test_task_defaults_to_modify_for_backward_compatibility(self):
        from user_center.tasks import async_vector_automation_design

        vector = self._make_vector()
        async_vector_automation_design(vector.id)
        vector.refresh_from_db()
        self.assertIs(vector.modify_vector, True)
        self.assertIn('M1', os.path.basename(vector.vector_gb.name))


class VectorColonyPrimerTests(TestCase):
    """菌落PCR引物：图谱上只标 best 那一对；没有原始图谱的老载体按骨架补设计。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 与 VectorNoModifyDesignTests 同一条 seed=1 序列：能过 Gibson 的全部闸门
        cls.sequence = _rand_seq(3000, 1)
        record = SeqRecord(
            Seq(cls.sequence), id='pCVaTEST', name='pCVaTEST',
            description='synthetic test vector', annotations={'molecule_type': 'DNA'},
        )
        record.features = [
            SeqFeature(SimpleLocation(1000, 1020), type='misc_feature', qualifiers={'label': ['iU20']}),
            SeqFeature(SimpleLocation(1500, 1520), type='misc_feature', qualifiers={'label': ['iD20']}),
        ]
        cls._tmpdir = tempfile.mkdtemp()
        cls.gb_path = os.path.join(cls._tmpdir, 'pCVaTEST.gb')
        with open(cls.gb_path, 'w') as handle:
            SeqIO.write(record, handle, 'genbank')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)
        super().tearDownClass()

    def _design_with_colony(self, colony_primers=None):
        """跑完整链路生成图谱；colony_primers 不传时现设计一套。"""
        designer = VectorAutomationDesigner(self.gb_path)
        parsed = designer.parse_genbank()
        self.assertIsNotNone(parsed, f'解析失败: {designer.errors}')
        design_result = designer.select_cloning_method(parsed, forced_method='Gibson')
        self.assertIsNotNone(design_result, f'Gibson 设计失败: {designer.errors}')
        primers = designer.design_nc_pcr_primers(design_result, parsed, vector_code='pCVaTEST')
        if colony_primers is None:
            colony_primers = designer.design_colony_pcr_primers(
                parsed, design_result, vector_code='pCVaTEST')
            self.assertTrue(colony_primers, f'菌落PCR设计失败: {designer.errors}')

        out_path = os.path.join(self._tmpdir, 'out_colony.gb')
        designer.generate_modified_genbank(
            design_result, parsed, primers, out_path, 'pCVaTESTM1',
            colony_primers=colony_primers, modify=True,
        )
        return colony_primers, SeqIO.read(out_path, 'genbank')

    @staticmethod
    def _colony_pair_indices(record):
        """图谱上标了哪几对菌落PCR引物（取引物名尾巴上的 CPF{n}/CPR{n}）。"""
        found = set()
        for feature in record.features:
            if feature.type != 'primer_bind':
                continue
            for label in feature.qualifiers.get('label', []):
                match = re.search(r'-CP[FR](\d+)$', label)
                if match:
                    found.add(int(match.group(1)))
        return found

    def test_map_only_annotates_the_best_colony_pair(self):
        colony_primers, record = self._design_with_colony()
        self.assertGreater(len(colony_primers), 1, '要有多对引物这条测试才有意义')
        best = [pair['index'] for pair in colony_primers if pair.get('is_best')]
        self.assertEqual(len(best), 1)
        self.assertEqual(self._colony_pair_indices(record), set(best))

    def test_map_falls_back_to_the_first_pair_for_legacy_json(self):
        colony_primers, _ = self._design_with_colony()
        legacy = copy.deepcopy(colony_primers)  # 旧数据没有 is_best 字段
        for pair in legacy:
            pair.pop('is_best', None)
        _, record = self._design_with_colony(colony_primers=legacy)
        self.assertEqual(self._colony_pair_indices(record), {1})

    def test_backbone_design_puts_the_flanks_on_the_backbone(self):
        backbone = self.sequence[:2000]
        nc5, nc3 = self.sequence[2000:2024], self.sequence[2024:2048]
        pairs, errors = VectorAutomationDesigner.design_colony_pcr_primers_from_backbone(
            backbone, nc5, nc3, vector_code='pCVaTEST')
        self.assertTrue(pairs, errors)
        self.assertEqual(len([pair for pair in pairs if pair['is_best']]), 1)

        circle = (backbone + nc5 + nc3).upper()
        for pair in pairs:
            forward, reverse = pair['forward'], pair['reverse']
            upstream, downstream = pair['upstream_seq'], pair['downstream_seq']
            # 正向引物落在骨架尾巴（v5NC 上游），反向引物落在骨架开头（v3NC 下游）
            self.assertEqual(upstream, backbone[len(backbone) - len(upstream):].upper())
            self.assertTrue(upstream.startswith(forward['sequence']))
            self.assertEqual(downstream, backbone[:len(downstream)].upper())
            self.assertTrue(downstream.endswith(
                VectorAutomationDesigner.reverse_complement(reverse['sequence'])))
            # 反向引物取自骨架副本，坐标折回环内后仍能取回同一条模板
            self.assertEqual(circle[reverse['template_start']:reverse['template_end']],
                             VectorAutomationDesigner.reverse_complement(reverse['sequence']))

    def test_backbone_primer_names_have_no_version_suffix(self):
        pairs, _ = VectorAutomationDesigner.design_colony_pcr_primers_from_backbone(
            self.sequence[:2000], self.sequence[2000:2024], self.sequence[2024:2048],
            vector_code='pCVaTEST')
        # 没改造过质粒，编号必须沿用原 VectorID，不能进位成 pCVaTESTM1
        self.assertTrue(pairs)
        self.assertEqual(pairs[0]['forward']['name'], 'OJYxxx-pCVaTEST-CPF1')

    def test_backbone_design_rejects_a_map_that_still_contains_the_ncs(self):
        # 自动化设计写的 vector_map 含 v5NC/v3NC，是另一套格式，直接拼会把两段重复一次
        pairs, errors = VectorAutomationDesigner.design_colony_pcr_primers_from_backbone(
            self.sequence, self.sequence[100:124], self.sequence[200:224])
        self.assertIsNone(pairs)
        self.assertTrue(errors)

    def test_backbone_design_needs_the_backbone_and_both_ncs(self):
        pairs, errors = VectorAutomationDesigner.design_colony_pcr_primers_from_backbone(
            '', 'ACGT', 'ACGT')
        self.assertIsNone(pairs)
        self.assertTrue(errors)
