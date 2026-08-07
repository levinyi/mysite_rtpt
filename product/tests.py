import io
import random
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
