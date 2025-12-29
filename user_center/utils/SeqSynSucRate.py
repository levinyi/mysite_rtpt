import pandas as pd, re, math, numpy as np, os
import sys

# ---------- constants ----------
PRIMARY = {
    'LongRepeats': 0.998976679,
    'Homopolymers': 0.999381548,
    'W12S12Motifs': 0.996537999,
    'HighGC': 0.999716263,
    'LowGC': 0.999942378,
}
SECONDARY = {
    'LongRepeats': 0.999488209,
    'Homopolymers': 0.999690726,
    'W12S12Motifs': 0.998267499,
    'HighGC': 0.999858121,
    'LowGC': 0.999971189,
}
P0 = 0.99998363
FEATURES = list(PRIMARY.keys())

# ---------- helpers ----------
def parse_intervals(cell: str):
    """Extract (start,end) tuples from the annotation cell."""
    if not isinstance(cell, str):
        return []
    starts = []
    ends = []
    start_chunks = re.findall(r'start:\s*(\[[^\]]+\]|[0-9]+)', cell)
    end_chunks = re.findall(r'end:\s*(\[[^\]]+\]|[0-9]+)', cell)
    for ch in start_chunks:
        starts.extend([int(n) for n in re.findall(r'\d+', ch)])
    for ch in end_chunks:
        ends.extend([int(n) for n in re.findall(r'\d+', ch)])
    intervals = []
    for s, e in zip(starts, ends):
        if e < s:
            s, e = e, s
        intervals.append((s, e))
    return intervals

def per_base_success(row):
    seq = row['sequence']
    if not isinstance(seq, str):
        return np.nan
    L = len(seq)
    # build coverage map
    cover = [[] for _ in range(L)]
    scores = {f: row.get(f + '_penalty_score', 0.0) or 0.0 for f in FEATURES}
    for f in FEATURES:
        for s, e in parse_intervals(row.get(f, np.nan)):
            for i in range(max(0, s - 1), min(L, e)):
                cover[i].append(f)

    logp = 0.0
    for feats in cover:
        if not feats:
            p = P0
        else:
            max_score = max(scores[f] for f in feats)
            main = [f for f in feats if scores[f] == max_score]
            p = 1.0
            for f in main:
                p *= PRIMARY[f]
            for f in feats:
                if f not in main:
                    p *= SECONDARY[f]
        logp += math.log(p)
    return math.exp(logp)


df = pd.read_csv(sys.argv[1])
df['TotalSuccessRate'] = df.apply(per_base_success, axis=1)

out_path = os.path.join(sys.argv[2], sys.argv[1] + '_with_success.csv')
df.to_csv(out_path, index=False)

