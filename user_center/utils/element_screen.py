"""客户待合成序列 vs 载体元件的同源重组风险筛查。

为什么不用 BLAST：同源重组要的不是"远缘相似"，而是"一段足够长、近乎完全一致的
序列"（RecA 依赖的重组需要 ~20-50bp 以上的同源臂，效率随长度陡增）。这正好是
k-mer 精确种子 + 无 gap 双向延伸能干的事，比 BLAST 更贴需求，而且零外部依赖 ——
生产镜像是 python:3.10-slim，装 ncbi-blast+ 要多背一百多 MB 和一套建库维护。

比对基准有两个，缺一不可：
  1. 元件库里 screen_enabled 的元件 —— 抓"客户序列里混进了常见载体元件"
  2. 目标载体骨架全序列 —— 抓那些没被标注成 feature、但照样能重组的同源区段
"""
import logging
from collections import defaultdict

from django.db.models import Count, Max

from product.models import VectorElement, VectorElementOccurrence

logger = logging.getLogger(__name__)

SEED_K = 20                  # 种子长度：短于此的同源基本不驱动重组
DEFAULT_MIN_LENGTH = 30      # 报告阈值：命中至少这么长
DEFAULT_MIN_IDENTITY = 0.95  # 报告阈值：命中至少这个一致度

# X-drop 延伸参数（同 BLAST 的思路）。
# 不能用"连续错配 N 次就停"那种朴素延伸：真实同源区结束后，query 进入的随机序列
# 与 subject 仍有 ~25% 概率偶然配上，延伸会拖着多走十几到几十 bp 才停，这些噪声
# 被算进 identity，能把一段 100% 一致的命中稀释到阈值以下 —— 假阴性，最糟的失效方式。
# X-drop 记录得分最高点并回退到那里，边界落在真实同源边界上。
MATCH_SCORE = 1
MISMATCH_SCORE = -3          # 惩罚够重，随机噪声区得分迅速下坠
XDROP = 12                   # 比最高分低这么多就收手

_COMPLEMENT = str.maketrans('ACGTNacgtn', 'TGCANtgcan')
_BASE4 = str.maketrans('ACGT', '0123')

# 元件库索引缓存（进程内）。库变了就重建，靠 (条数, 最后更新时间) 判断。
_INDEX_CACHE: dict = {'version': None, 'index': None, 'elements': None}


def revcomp(seq):
    return seq.translate(_COMPLEMENT)[::-1]


def _encode(kmer):
    """把 k-mer 编码成 int（2-bit/碱基）。含 N 等非 ACGT 字符时返回 None。

    用 int 做字典键而不是 str：实测 500 条元件（505kb）的索引从 266MB 降到 25MB，
    Django worker 里常驻得起。
    """
    try:
        return int(kmer.translate(_BASE4), 4)
    except ValueError:
        return None


def _seed_stride(min_length):
    """稀疏种子步长。

    长度 >= min_length 的匹配区间里有 (min_length - SEED_K + 1) 个连续的种子起点，
    步长不超过这个数就保证至少落进一个种子 —— 不会漏报。
    """
    return max(1, min(5, min_length - SEED_K + 1))


def _index_sequences(seqs, stride):
    """seqs: [(key, sequence)] -> {encoded_kmer: [(key, pos)]}（只索引正链）。"""
    index = defaultdict(list)
    for key, seq in seqs:
        s = seq.upper()
        for i in range(0, len(s) - SEED_K + 1, stride):
            code = _encode(s[i:i + SEED_K])
            if code is not None:
                index[code].append((key, i))
    return index


def _extend_one_way(query, subject, qi, si, step):
    """从 (qi, si) 沿 step 方向做 X-drop 延伸，返回该方向上应保留的碱基数。

    回退到得分最高点，所以延伸停在真实同源边界，而不是噪声漂移停下的地方。
    """
    score = best_score = 0
    offset = best_offset = 0
    while 0 <= qi < len(query) and 0 <= si < len(subject):
        score += MATCH_SCORE if query[qi] == subject[si] else MISMATCH_SCORE
        offset += 1
        if score > best_score:
            best_score = score
            best_offset = offset
        elif best_score - score > XDROP:
            break
        qi += step
        si += step
    return best_offset


def _extend(query, subject, q_seed, s_seed):
    """从种子出发向两端无 gap 延伸，返回 (q_start, q_end, s_start, s_end, identity)。"""
    left = _extend_one_way(query, subject, q_seed - 1, s_seed - 1, -1)
    right = _extend_one_way(query, subject, q_seed + SEED_K, s_seed + SEED_K, 1)

    q_start, q_end = q_seed - left, q_seed + SEED_K + right
    s_start, s_end = s_seed - left, s_seed + SEED_K + right

    aln_q = query[q_start:q_end]
    aln_s = subject[s_start:s_end]
    if not aln_q or len(aln_q) != len(aln_s):
        return None
    identity = sum(a == b for a, b in zip(aln_q, aln_s)) / len(aln_q)
    return q_start, q_end, s_start, s_end, identity


def _search(query, subjects, index, min_length, min_identity):
    """query 对一组 subject 序列做筛查。

    subjects: {key: sequence}（正链）。query 的两条链都查：反链命中通过反向互补 query
    得到，再把坐标翻回原始 query 上，这样索引只需存正链。

    注意 query 侧是**逐位置**取种子（不能像建索引那样跳步）—— 稀疏只在 subject 侧
    安全，两边同时稀疏就会漏掉相位错开的匹配。
    """
    hits = []
    for strand, q in (1, query), (-1, revcomp(query)):
        for i in range(len(q) - SEED_K + 1):
            code = _encode(q[i:i + SEED_K])
            if code is None:
                continue
            for key, s_pos in index.get(code, ()):
                res = _extend(q, subjects[key], i, s_pos)
                if not res:
                    continue
                q_start, q_end, s_start, s_end, identity = res
                if q_end - q_start < min_length or identity < min_identity:
                    continue
                if strand == 1:
                    oq_start, oq_end = q_start, q_end
                else:
                    oq_start, oq_end = len(q) - q_end, len(q) - q_start
                hits.append({
                    'key': key, 'strand': strand,
                    'q_start': oq_start, 'q_end': oq_end,
                    's_start': s_start, 's_end': s_end,
                    'length': q_end - q_start,
                    'identity': round(identity, 4),
                })

    # 同一段同源会被区间内每个种子各命中一次 -> 按 (key, strand) 去冗余，保留最长的那条
    hits.sort(key=lambda h: (-h['length'], h['q_start']))
    kept = []
    for h in hits:
        if any(k['key'] == h['key'] and k['strand'] == h['strand']
               and not (h['q_end'] <= k['q_start'] or h['q_start'] >= k['q_end'])
               for k in kept):
            continue
        kept.append(h)
    return kept


def _library_version():
    agg = (VectorElement.objects
           .filter(is_active=True, screen_enabled=True)
           .aggregate(n=Count('id'), last=Max('updated_at')))
    return (agg['n'] or 0, agg['last'].isoformat() if agg['last'] else None)


def _get_library_index(min_length):
    """取（必要时重建）元件库索引。步长依赖 min_length，所以一并作为缓存键。"""
    version = _library_version() + (_seed_stride(min_length),)
    if _INDEX_CACHE['version'] == version:
        return _INDEX_CACHE['index'], _INDEX_CACHE['elements']

    elements = {
        e.pk: e for e in VectorElement.objects.filter(is_active=True, screen_enabled=True)
    }
    index = _index_sequences([(pk, e.sequence) for pk, e in elements.items()],
                             _seed_stride(min_length))
    _INDEX_CACHE.update({'version': version, 'index': index, 'elements': elements})
    logger.info("元件库索引重建：%s 条元件，%s 个 k-mer", len(elements), len(index))
    return index, elements


def _vector_backbone(vector):
    """目标载体的骨架序列。

    优先 vector_map —— 它是去掉插入区（v5NC..v3NC 之间）后的骨架，正是客户序列插进去
    之后要与之共存、可能发生重组的那部分。vector_map 为空时回退到原始图谱全序列。
    """
    if vector.vector_map and vector.vector_map.strip():
        return vector.vector_map.strip().upper()
    from user_center.utils.element_extractor import read_vector_record
    record, _ = read_vector_record(vector)
    return str(record.seq).upper() if record is not None else ''


def screen_sequence(sequence, target_vector=None,
                    min_length=DEFAULT_MIN_LENGTH, min_identity=DEFAULT_MIN_IDENTITY):
    """筛查一条客户序列。

    返回 element_hits（命中元件库）+ vector_hits（命中目标载体骨架但没被标注成元件的
    同源区段）。命中的元件如果本来就长在目标载体上，标 on_target_vector —— 那是最高危的：
    客户序列要连的就是这个载体，同源臂现成的。
    """
    query = ''.join((sequence or '').split()).upper()
    if len(query) < SEED_K:
        return {'ok': False, 'error': f'序列过短（至少需要 {SEED_K} bp）'}

    min_length = max(int(min_length), SEED_K)
    min_identity = float(min_identity)

    index, elements = _get_library_index(min_length)
    stride = _seed_stride(min_length)

    element_hits = []
    if elements:
        subjects = {pk: e.sequence for pk, e in elements.items()}
        on_target = set()
        if target_vector is not None:
            on_target = set(
                VectorElementOccurrence.objects
                .filter(vector=target_vector, element_id__in=subjects.keys())
                .values_list('element_id', flat=True)
            )
        for h in _search(query, subjects, index, min_length, min_identity):
            e = elements[h['key']]
            element_hits.append({
                'element_id': e.pk,
                'name': e.name,
                'element_type': e.element_type,
                'element_type_display': e.get_element_type_display(),
                'source_vector_name': e.source_vector_name or '',
                'risk_level': e.risk_level,
                'on_target_vector': e.pk in on_target,
                'q_start': h['q_start'], 'q_end': h['q_end'],
                'e_start': h['s_start'], 'e_end': h['s_end'],
                'length': h['length'], 'identity': h['identity'], 'strand': h['strand'],
            })

    vector_hits = []
    if target_vector is not None:
        backbone = _vector_backbone(target_vector)
        if backbone:
            v_index = _index_sequences([('v', backbone)], stride)
            for h in _search(query, {'v': backbone}, v_index, min_length, min_identity):
                vector_hits.append({
                    'q_start': h['q_start'], 'q_end': h['q_end'],
                    'v_start': h['s_start'], 'v_end': h['s_end'],
                    'length': h['length'], 'identity': h['identity'], 'strand': h['strand'],
                })

    element_hits.sort(key=lambda h: (not h['on_target_vector'], -h['length']))
    vector_hits.sort(key=lambda h: -h['length'])

    longest = max([h['length'] for h in element_hits + vector_hits], default=0)
    if any(h['on_target_vector'] for h in element_hits) or longest >= 100:
        verdict = 'risk'
    elif element_hits or vector_hits:
        verdict = 'warn'
    else:
        verdict = 'pass'

    return {
        'ok': True,
        'query_length': len(query),
        'params': {'min_length': min_length, 'min_identity': min_identity, 'seed_k': SEED_K},
        'library_size': len(elements),
        'target_vector': target_vector.vector_name if target_vector else None,
        'element_hits': element_hits,
        'vector_hits': vector_hits,
        'summary': {
            'n_element_hits': len(element_hits),
            'n_on_target': sum(1 for h in element_hits if h['on_target_vector']),
            'n_vector_hits': len(vector_hits),
            'longest_hit': longest,
            'verdict': verdict,
        },
    }


def find_element_by_sequence(sequence, min_length=DEFAULT_MIN_LENGTH,
                             min_identity=DEFAULT_MIN_IDENTITY):
    """「库里有没有这段序列」—— 元件库页面的序列查询。

    与 screen_sequence 的区别：这里查的是**全部**启用元件（不只是 screen_enabled 的），
    而且先做一次精确 hash 比对，命中就直接返回，省掉建索引。
    """
    from product.models import compute_seq_hash

    query = ''.join((sequence or '').split()).upper()
    if not query:
        return {'ok': False, 'error': '请输入序列'}

    exact = VectorElement.objects.filter(seq_hash=compute_seq_hash(query)).first()
    if exact:
        return {
            'ok': True, 'exact': True, 'query_length': len(query),
            'hits': [{
                'element_id': exact.pk, 'name': exact.name,
                'element_type': exact.element_type,
                'element_type_display': exact.get_element_type_display(),
                'source_vector_name': exact.source_vector_name or '',
                'length': exact.seq_length, 'identity': 1.0, 'strand': 1,
                'q_start': 0, 'q_end': len(query),
                'e_start': 0, 'e_end': exact.seq_length,
                'coverage': 1.0,
            }],
        }

    if len(query) < SEED_K:
        return {'ok': False, 'error': f'非精确查询至少需要 {SEED_K} bp'}

    min_length = max(int(min_length), SEED_K)
    elements = {e.pk: e for e in VectorElement.objects.filter(is_active=True)}
    if not elements:
        return {'ok': True, 'exact': False, 'query_length': len(query), 'hits': []}

    subjects = {pk: e.sequence for pk, e in elements.items()}
    stride = _seed_stride(min_length)
    index = _index_sequences(list(subjects.items()), stride)

    hits = []
    for h in _search(query, subjects, index, min_length, min_identity):
        e = elements[h['key']]
        hits.append({
            'element_id': e.pk, 'name': e.name,
            'element_type': e.element_type,
            'element_type_display': e.get_element_type_display(),
            'source_vector_name': e.source_vector_name or '',
            'q_start': h['q_start'], 'q_end': h['q_end'],
            'e_start': h['s_start'], 'e_end': h['s_end'],
            'length': h['length'], 'identity': h['identity'], 'strand': h['strand'],
            'coverage': round(h['length'] / e.seq_length, 4) if e.seq_length else 0,
        })
    return {'ok': True, 'exact': False, 'query_length': len(query), 'hits': hits}


def invalidate_index_cache():
    _INDEX_CACHE.update({'version': None, 'index': None, 'elements': None})
