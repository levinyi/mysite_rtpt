"""从载体 GenBank 图谱里提取候选元件，供管理员挑选入库。

入库是半自动的：这里只负责"识别 + 建议"，真正写进 VectorElement 的是管理员在后台
勾选过的那些（见 super_manage.views.element_commit）。全自动会把 primer_bind、
内部标记这类噪声一起灌进库里。

支持一次解析多个载体（extract_candidates_bulk）：同一条序列在不同载体上合并成一行
候选，勾一次就把所有出现位置都登记进去 —— AmpR / pUC ori / T7 promoter 几乎每张
图谱上都有，逐个载体点的话同一条序列要重复审很多遍。
"""
import collections
import logging
import re

from Bio import SeqIO
from django.db.models.functions import Lower

from product.models import Vector, VectorElement, VectorElementOccurrence, compute_seq_hash

logger = logging.getLogger(__name__)

# GenBank feature.type -> VectorElement.element_type
FUNCTIONAL_TYPE_MAP = {
    'promoter': 'promoter',
    'terminator': 'terminator',
    'rep_origin': 'ori',
    'polyA_signal': 'polya',
    'enhancer': 'enhancer',
    'protein_bind': 'protein_bind',
    'RBS': 'rbs',
    'sig_peptide': 'signal_peptide',
    'regulatory': 'regulatory',
    'CDS': 'cds',           # 再按 label 细分出 resistance / tag
}

# 图谱上常见但不是可复用功能元件的 feature，直接丢弃（不进候选列表）
IGNORED_FEATURE_TYPES = {'source', 'primer_bind', 'gene', 'mRNA', 'STS'}

# RootPath 自己的克隆/插入位点标记，不是元件
INTERNAL_MARKER_RE = re.compile(
    r'^(iu20|id20|v5nc|v3nc|i5nc|i3nc|5nc|3nc|start|end)(\b|[-_.]|$)', re.IGNORECASE
)

# CDS 里按 label 认抗性基因（与 vector_automation.KNOWN_RESISTANCES 同源）
RESISTANCE_RE = re.compile(
    r'\b(amp|kan|cm|chlor|spec|sm|tet|hyg|blast|bsd|puro|neo|zeo|gent?|str)r?\b'
    r'|\b(bla|aph|cat|nptii|ereg)\b',
    re.IGNORECASE
)
# 常见亲和/表位标签
TAG_RE = re.compile(
    r'\b(6?x?his|his6|flag|3xflag|ha\s*tag|myc|gst|mbp|sumo|strep|avitag|v5\s*tag|s\s*tag)\b',
    re.IGNORECASE
)

MIN_ELEMENT_LENGTH = 15   # 短于此长度的片段做同源比对没有意义

# misc_feature 归到 'other'：这类里混着真元件（WPRE / MCS / IRES）和噪声，
# 所以照样列成候选，但前端默认不勾选，交给管理员判断。
MISC_TYPE = 'other'


def _labels_of(feature):
    q = feature.qualifiers or {}
    return q.get('label', []) + q.get('gene', []) + q.get('note', [])


def _primary_label(feature):
    for key in ('label', 'gene', 'product', 'note'):
        vals = (feature.qualifiers or {}).get(key)
        if vals and str(vals[0]).strip():
            return str(vals[0]).strip()
    return ''


def _is_internal_marker(feature):
    return any(INTERNAL_MARKER_RE.match((lab or '').strip()) for lab in _labels_of(feature))


def _suggest_type(feature, label):
    gb_type = feature.type
    if gb_type == 'CDS':
        if RESISTANCE_RE.search(label):
            return 'resistance'
        if TAG_RE.search(label):
            return 'tag'
        return 'cds'
    return FUNCTIONAL_TYPE_MAP.get(gb_type, MISC_TYPE)


def read_vector_record(vector):
    """读出载体的 GenBank record。

    优先用客户/公司上传的原始图谱 vector_file —— vector_gb 是我们改造后生成的，
    里面掺了 Cm-ccdB、引物等设计产物，不该被当成"这个载体本来的元件"。
    """
    for field_name in ('vector_file', 'vector_gb'):
        f = getattr(vector, field_name, None)
        if not f:
            continue
        try:
            path = f.path
        except ValueError:
            continue
        for encoding in ('utf-8', 'gbk', 'latin-1'):
            try:
                with open(path, 'r', encoding=encoding, errors='strict') as handle:
                    return SeqIO.read(handle, 'genbank'), field_name
            except (UnicodeDecodeError, LookupError):
                continue
            except (ValueError, OSError) as exc:
                logger.warning("解析 %s (vector=%s) 失败: %s", field_name, vector.pk, exc)
                break
    return None, None


def _scan_features(record, vector_pk):
    """扫一张图谱上的 feature，产出候选原料。纯解析，不查库。

    返回 (candidates, skipped)。candidates 里还没有 dedup 判定 —— 那部分要查库，
    批量解析时统一做一次，避免每个 feature 查两遍。
    """
    candidates = []
    skipped = {'internal_marker': 0, 'ignored_type': 0, 'too_short': 0}

    for idx, feature in enumerate(record.features):
        if feature.type in IGNORED_FEATURE_TYPES:
            skipped['ignored_type'] += 1
            continue
        if _is_internal_marker(feature):
            skipped['internal_marker'] += 1
            continue

        try:
            seq = str(feature.extract(record.seq)).upper()
        except Exception as exc:  # 坐标越界 / 畸形 location
            logger.warning("提取 feature #%s (vector=%s) 序列失败: %s", idx, vector_pk, exc)
            continue

        if len(seq) < MIN_ELEMENT_LENGTH:
            skipped['too_short'] += 1
            continue

        label = _primary_label(feature) or f'{feature.type}_{idx}'
        candidates.append({
            'index': idx,
            'label': label,
            'genbank_feature_type': feature.type,
            'suggested_type': _suggest_type(feature, label),
            'sequence': seq,
            'length': len(seq),
            'start': int(feature.location.start),
            'end': int(feature.location.end),
            'strand': int(feature.location.strand or 1),
            'seq_hash': compute_seq_hash(seq),
        })

    return candidates, skipped


def _lookup_existing(seq_hashes, labels):
    """一次性查出这批候选在库里的对应情况。

    返回 (hash -> VectorElement, 已被占用的小写名集合)。
    """
    by_hash = {
        e.seq_hash: e
        for e in VectorElement.objects.filter(seq_hash__in=seq_hashes)
    }
    # 用 Lower() 而不是 name__in，免得依赖数据库的 collation 大小写敏感性
    taken_names = set(
        VectorElement.objects
        .annotate(lower_name=Lower('name'))
        .filter(lower_name__in={(lab or '').lower() for lab in labels})
        .values_list('lower_name', flat=True)
    )
    return by_hash, taken_names


def _dedup_state(seq_hash, label, by_hash, taken_names, registered):
    """判定一条候选相对元件库的状态。

      new         —— 库里没有这条序列
      exists      —— 序列已在库中（同 seq_hash），且它在相关载体上的出现都已登记
      exists_new_occurrence —— 序列已在库中，但还有载体上的出现没登记
      name_clash  —— 库里有同名元件但序列不同（同名不同序，需要人工确认）
    """
    if seq_hash in by_hash:
        return 'exists' if registered else 'exists_new_occurrence'
    if label.lower() in taken_names:
        return 'name_clash'
    return 'new'


def _most_common(values):
    """取出现次数最多的值，并列时取先出现的那个。"""
    return collections.Counter(values).most_common(1)[0][0]


def extract_candidates_bulk(vectors):
    """一次解析多个载体，把同一条序列合并成一行候选。

    合并键是 seq_hash —— 同一段序列在不同图谱上可能叫 AmpR / bla / ampicillin
    resistance，那是一条元件的多个别名，不是三条元件。合并后的每行带 occurrences，
    勾一次即可把它在所有涉及载体上的出现位置一起登记。
    """
    parsed = []
    errors = []
    for vector in vectors:
        record, source_field = read_vector_record(vector)
        if record is None:
            errors.append({
                'vector_id': vector.pk,
                'vector_name': vector.vector_name or f'#{vector.pk}',
                'error': '无法读取 GenBank 图谱（vector_file / vector_gb 都不可解析）',
            })
            continue
        raw, skipped = _scan_features(record, vector.pk)
        parsed.append((vector, source_field, len(record.seq), raw, skipped))

    all_candidates = [c for _, _, _, raw, _ in parsed for c in raw]
    by_hash, taken_names = _lookup_existing(
        [c['seq_hash'] for c in all_candidates], [c['label'] for c in all_candidates])

    # 已登记的 (载体, 序列) 组合，用来判断哪些出现位置还缺
    registered = set(
        VectorElementOccurrence.objects
        .filter(vector__in=[v for v, _, _, _, _ in parsed])
        .values_list('vector_id', 'element__seq_hash')
    )

    merged = collections.OrderedDict()
    for vector, source_field, _length, raw, _skipped in parsed:
        for c in raw:
            row = merged.setdefault(c['seq_hash'], {
                'seq_hash': c['seq_hash'],
                'sequence': c['sequence'],
                'length': c['length'],
                'labels': [],
                'types': [],
                'gb_types': [],
                'sources': set(),
                'occurrences': [],
            })
            row['labels'].append(c['label'])
            row['types'].append(c['suggested_type'])
            row['gb_types'].append(c['genbank_feature_type'])
            row['sources'].add(source_field)
            row['occurrences'].append({
                'vector_id': vector.pk,
                'vector_name': vector.vector_name or f'#{vector.pk}',
                'vector_code': vector.vector_id or '',
                'start': c['start'],
                'end': c['end'],
                'strand': c['strand'],
                'label': c['label'],
                'registered': (vector.pk, c['seq_hash']) in registered,
            })

    candidates = []
    for row in merged.values():
        existing = by_hash.get(row['seq_hash'])
        # 名字取各图谱上最常见的叫法，其余进别名
        name = _most_common(row['labels'])
        aliases = [lab for lab in dict.fromkeys(row['labels']) if lab != name]
        suggested = _most_common(row['types'])
        all_registered = all(occ['registered'] for occ in row['occurrences'])
        dedup = _dedup_state(row['seq_hash'], name, by_hash, taken_names,
                             registered=all_registered)
        candidates.append({
            'seq_hash': row['seq_hash'],
            'label': name,
            'aliases': aliases,
            'genbank_feature_type': _most_common(row['gb_types']),
            'suggested_type': suggested,
            'sequence': row['sequence'],
            'length': row['length'],
            'dedup': dedup,
            'existing_id': existing.pk if existing else None,
            'existing_name': existing.name if existing else '',
            'default_checked': dedup in ('new', 'exists_new_occurrence') and suggested != MISC_TYPE,
            'occurrences': sorted(row['occurrences'], key=lambda o: (o['vector_name'], o['start'])),
            'vector_count': len({occ['vector_id'] for occ in row['occurrences']}),
        })

    # 出现载体多的排前面：跨载体复用的通常就是 AmpR/ori 这类真元件，先审它们最划算
    candidates.sort(key=lambda c: (-c['vector_count'], c['label'].lower()))

    total_rows = len(all_candidates)
    return {
        'ok': True,
        'candidates': candidates,
        'errors': errors,
        'vectors': [{
            'id': v.pk,
            'name': v.vector_name or f'#{v.pk}',
            'code': v.vector_id or '',
            'owner': v.user.username if v.user else '公司',
            'source_field': source_field,
            'record_length': record_length,
            'candidate_count': len(raw),
        } for v, source_field, record_length, raw, _ in parsed],
        'from_vector_gb': sorted(
            v.vector_name or f'#{v.pk}'
            for v, source_field, _, _, _ in parsed if source_field == 'vector_gb'
        ),
        'skipped': {
            key: sum(sk[key] for _, _, _, _, sk in parsed)
            for key in ('internal_marker', 'ignored_type', 'too_short')
        },
        'stats': {
            'vectors_ok': len(parsed),
            'vectors_failed': len(errors),
            'rows_before_merge': total_rows,
            'rows_after_merge': len(candidates),
        },
    }


def commit_candidates(selections, user=None):
    """把管理员勾选的候选写进元件库。

    selections: [{sequence, name, element_type, genbank_feature_type, description,
                  screen_enabled, risk_level, aliases,
                  occurrences: [{vector_id, start, end, strand, label_in_vector}]}]

    一条 selection = 一条元件序列 + 它在若干载体上的出现位置。序列已在库中的不新建
    元件，只补 Occurrence，并把这次的叫法并进 aliases —— 同一个 AmpR 在不同图谱上叫
    AmpR / bla / ampicillin resistance，是一条元件的多个别名，不是三条元件。
    """
    vector_ids = {
        occ.get('vector_id')
        for sel in selections for occ in (sel.get('occurrences') or [])
        if occ.get('vector_id')
    }
    vectors = Vector.objects.in_bulk(vector_ids)

    created, linked, skipped, occurrences = 0, 0, 0, 0

    for sel in selections:
        seq = (sel.get('sequence') or '').strip().upper()
        name = (sel.get('name') or '').strip()
        occs = [o for o in (sel.get('occurrences') or []) if vectors.get(o.get('vector_id'))]
        if not seq or not name or len(seq) < MIN_ELEMENT_LENGTH or not occs:
            skipped += 1
            continue

        # 同一条序列可能同时长在公司载体和客户载体上，这种属于通用元件，来源记公司的那个
        source_vector = next(
            (vectors[o['vector_id']] for o in occs if not vectors[o['vector_id']].user_id),
            vectors[occs[0]['vector_id']],
        )
        # 这批图谱上出现过的所有叫法，主名之外的都是别名
        seen_names = [name] + [
            (o.get('label_in_vector') or '').strip() for o in occs
        ] + list(sel.get('aliases') or [])

        seq_hash = compute_seq_hash(seq)
        element = VectorElement.objects.filter(seq_hash=seq_hash).first()

        if element is None:
            element = VectorElement.objects.create(
                name=name,
                element_type=sel.get('element_type') or 'other',
                sequence=seq,
                description=(sel.get('description') or '').strip(),
                source_vector=source_vector,
                source_vector_name=source_vector.vector_name or '',
                source_kind='customer' if source_vector.user_id else 'company',
                genbank_feature_type=sel.get('genbank_feature_type') or '',
                screen_enabled=bool(sel.get('screen_enabled', True)),
                risk_level=sel.get('risk_level') or 'medium',
                created_by=user if (user and user.is_authenticated) else None,
            )
            created += 1
        else:
            linked += 1

        _merge_aliases(element, seen_names)

        for occ in occs:
            _, is_new = VectorElementOccurrence.objects.get_or_create(
                element=element,
                vector=vectors[occ['vector_id']],
                start=int(occ.get('start') or 0),
                end=int(occ.get('end') or len(seq)),
                defaults={
                    'strand': int(occ.get('strand') or 1),
                    'label_in_vector': (occ.get('label_in_vector') or name)[:200],
                },
            )
            if is_new:
                occurrences += 1

    return {'created': created, 'linked': linked, 'skipped': skipped,
            'occurrences': occurrences}


def _merge_aliases(element, names):
    """把这批图谱上出现过的其他叫法并进元件别名。"""
    aliases = list(element.aliases or [])
    known = {element.name.lower()} | {a.lower() for a in aliases}
    for name in names:
        name = (name or '').strip()
        if name and name.lower() not in known:
            aliases.append(name)
            known.add(name.lower())
    if aliases != list(element.aliases or []):
        element.aliases = aliases
        element.save(update_fields=['aliases', 'updated_at'])
