import sys
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature, FeatureLocation, CompoundLocation


def modify_locations(features, start_pos, end_pos, new_seq_length):
    offset = new_seq_length - (end_pos - start_pos)
    new_features = []
    for feature in features:
        if feature.location.end <= start_pos:
            # Feature before the insertion point, no change
            new_features.append(feature)
        elif feature.location.start >= end_pos:
            # Feature after the insertion point, adjust location
            if isinstance(feature.location, CompoundLocation):
                new_parts = []
                for part in feature.location.parts:
                    new_start = part.start + offset
                    new_end = part.end + offset
                    new_parts.append(FeatureLocation(new_start, new_end, part.strand))
                feature.location = CompoundLocation(new_parts)
            else:
                new_start = feature.location.start + offset
                new_end = feature.location.end + offset
                feature.location = FeatureLocation(new_start, new_end, feature.location.strand)
            new_features.append(feature)
        else:
            # Feature overlaps with the insertion point, adjust or split feature
            new_parts = []
            if isinstance(feature.location, CompoundLocation):
                for part in feature.location.parts:
                    if part.end <= start_pos:
                        new_parts.append(part)
                    elif part.start >= end_pos:
                        new_start = part.start + offset
                        new_end = part.end + offset
                        new_parts.append(FeatureLocation(new_start, new_end, part.strand))
                    else:
                        if part.start < start_pos:
                            new_parts.append(FeatureLocation(part.start, start_pos, part.strand))
                        if part.end > end_pos:
                            new_start = start_pos + new_seq_length
                            new_parts.append(FeatureLocation(new_start, new_start + (part.end - end_pos), part.strand))
                if new_parts:
                    feature.location = CompoundLocation(new_parts)
                    new_features.append(feature)
            else:
                if feature.location.start < start_pos and feature.location.end > end_pos:
                    new_parts.append(FeatureLocation(feature.location.start, start_pos, feature.location.strand))
                    new_start = start_pos + new_seq_length
                    new_parts.append(FeatureLocation(new_start, new_start + (feature.location.end - end_pos), feature.location.strand))
                    feature.location = CompoundLocation(new_parts)
                    new_features.append(feature)
                elif feature.location.start < start_pos:
                    feature.location = FeatureLocation(feature.location.start, start_pos, feature.location.strand)
                    new_features.append(feature)
                elif feature.location.end > end_pos:
                    new_start = start_pos + new_seq_length
                    feature.location = FeatureLocation(new_start, new_start + (feature.location.end - end_pos), feature.location.strand)
                    new_features.append(feature)
    features[:] = new_features


def readGenBank(genebank_file):
    # 如果有乱码，可以尝试指定errors="ignore"
    with open(genebank_file, "r", encoding="utf-8", errors="ignore") as input_handle:
        record = SeqIO.read(input_handle, "genbank")
    return record


def addFeaturesToGeneBank(genebank_file, new_sequence, output_file, start_feature_label, end_feature_label, new_feature_name):
    record = readGenBank(genebank_file)
    new_seq_length = len(new_sequence)
    
    start_pos = None
    end_pos = None
    
    for feature in record.features:
        labels = feature.qualifiers.get("label", [])
        if start_feature_label in labels:
            start_pos = feature.location.end
        elif end_feature_label in labels:
            end_pos = feature.location.start
    
    if start_pos is None or end_pos is None:
        raise ValueError("Start or end feature not found in the GenBank file")
    
    # Replace the sequence
    record.seq = record.seq[:start_pos] + Seq(new_sequence) + record.seq[end_pos:]
    
    # Modify locations of existing features
    modify_locations(record.features, start_pos, end_pos, new_seq_length)
    
    # Add new feature
    new_feature = SeqFeature(FeatureLocation(start_pos, start_pos + new_seq_length), type="misc_feature", qualifiers={"label": new_feature_name})
    record.features.append(new_feature)
    
    # Write to the output file
    with open(output_file, "w") as output_handle:
        SeqIO.write(record, output_handle, "genbank")


def addMultipleFeaturesToGeneBank(genebank_file, output_file, new_sequences, new_feature_names, start_feature_label, end_feature_label):
    """
    :param genebank_file: 输入的GenBank文件路径
    :param new_sequences: list或tuple，包含多个待插入的DNA序列字符串
    :param new_feature_names: list或tuple，对应每个序列的特征名称
    :param output_file: 输出文件路径
    :param start_feature_label: 用于定位插入起点的特征label
    :param end_feature_label: 用于定位插入终点的特征label
    
    假设：所有新序列将在 start_feature_label 与 end_feature_label 间插入。
    """

    if len(new_sequences) != len(new_feature_names):
        raise ValueError("new_sequences 与 new_feature_names 的长度必须一致")
    
    # print("new_sequences: ", new_sequences)

    record = readGenBank(genebank_file)

    start_pos = None
    end_pos = None

    # 寻找指定label的特征位置
    for feature in record.features:
        labels = feature.qualifiers.get("label", [])
        # print("labels: ", labels)
        if start_feature_label in labels:
            # print(f"start_feature_label: {start_feature_label}")
            start_pos = feature.location.end
            # print(f"start_pos: {feature.location.start}, {feature.location.end}")
        elif end_feature_label in labels:
            # print(f"end_feature_label: {end_feature_label}")
            end_pos = feature.location.start
            # print(f"end_pos: {feature.location.start}, {feature.location.end}")
    # print(f"I found start pos and end pos here: \n compare which is bigger\nfeature: {feature}, labels: {labels}, start_pos: {start_pos}, end_pos: {end_pos}")

    if start_pos is None or end_pos is None:
        raise ValueError("无法在GenBank文件中找到指定的起始或终止特征")

    # 将多个新特征序列拼接为一个大序列
    full_new_seq = "".join([seq for seq in new_sequences if seq is not None])
    # print("full_new_seq: ", full_new_seq)
    full_new_seq_length = len(full_new_seq)

    # 替换原序列中的指定片段
    # print("Before modification:", record.seq)
    record.seq = record.seq[:start_pos] + Seq(full_new_seq) + record.seq[end_pos:]
    # print("After modification:", record.seq)

    # 调整已有特征位置
    modify_locations(record.features, start_pos, end_pos, full_new_seq_length)

    # 添加新特征
    offset = 0
    for seq, name in zip(new_sequences, new_feature_names):
        if not seq:  # 如果序列为空，跳过
            continue
        seq_len = len(seq)
        new_feature = SeqFeature(
            FeatureLocation(start_pos + offset, start_pos + offset + seq_len),
            type="misc_feature",
            qualifiers={"label": name}
        )
        record.features.append(new_feature)
        offset += seq_len

    # 输出
    with open(output_file, "w") as output_handle:
        SeqIO.write(record, output_handle, "genbank")


def addAnalysisFeaturesAndFragments(genebank_file, output_file, new_sequences, new_feature_names,
                                     start_feature_label, end_feature_label,
                                     analysis_results=None, fragments_data=None, gene_start_pos_in_insert=0):
    """
    扩展的GenBank特征标注函数，除了添加基本特征外，还会标注：
    1. 序列评估特征（long repeats, homopolymers, hairpins等）
    2. Fragments（切割的片段）

    :param genebank_file: 输入的GenBank文件路径
    :param output_file: 输出文件路径
    :param new_sequences: list或tuple，包含多个待插入的DNA序列字符串
    :param new_feature_names: list或tuple，对应每个序列的特征名称
    :param start_feature_label: 用于定位插入起点的特征label
    :param end_feature_label: 用于定位插入终点的特征label
    :param analysis_results: dict，序列分析结果（包含各种penalty score和位置信息）
    :param fragments_data: dict，片段数据（如果序列被切割）
    :param gene_start_pos_in_insert: int, 基因序列在插入序列中的起始位置（相对于i5nc后的位置）
    """

    if len(new_sequences) != len(new_feature_names):
        raise ValueError("new_sequences 与 new_feature_names 的长度必须一致")

    record = readGenBank(genebank_file)

    start_pos = None
    end_pos = None

    # 寻找指定label的特征位置
    for feature in record.features:
        labels = feature.qualifiers.get("label", [])
        if start_feature_label in labels:
            start_pos = feature.location.end
        elif end_feature_label in labels:
            end_pos = feature.location.start

    if start_pos is None or end_pos is None:
        raise ValueError("无法在GenBank文件中找到指定的起始或终止特征")

    # 将多个新特征序列拼接为一个大序列
    full_new_seq = "".join([seq for seq in new_sequences if seq is not None])
    full_new_seq_length = len(full_new_seq)

    # 替换原序列中的指定片段
    record.seq = record.seq[:start_pos] + Seq(full_new_seq) + record.seq[end_pos:]

    # 调整已有特征位置
    modify_locations(record.features, start_pos, end_pos, full_new_seq_length)

    # 添加基本特征（i5NC, gene, i3NC）
    offset = 0
    for seq, name in zip(new_sequences, new_feature_names):
        if not seq:  # 如果序列为空，跳过
            continue
        seq_len = len(seq)
        new_feature = SeqFeature(
            FeatureLocation(start_pos + offset, start_pos + offset + seq_len),
            type="misc_feature",
            qualifiers={"label": name}
        )
        record.features.append(new_feature)
        offset += seq_len

    # 添加序列评估特征标注
    if analysis_results:
        import re
        if not isinstance(analysis_results, dict):
            try:
                import json
                analysis_results = json.loads(analysis_results)
            except Exception:
                analysis_results = {}
        gene_start_in_vector = start_pos + gene_start_pos_in_insert

        # 定义需要标注的特征类型及其对应的feature type
        feature_types_mapping = {
            'LongRepeats': 'repeat_region',
            'Homopolymers': 'repeat_region',
            'W12S12Motifs': 'misc_feature',
            'HighGC': 'misc_feature',
            'LowGC': 'misc_feature',
            'DoubleNT': 'repeat_region',
            'TandemRepeats': 'repeat_region',
            'PalindromeRepeats': 'repeat_region',
            'InvertedRepeats': 'repeat_region'
        }
        key_aliases = {
            'HighGC': ['highGC'],
            'LowGC': ['lowGC'],
            'DoubleNT': ['doubleNT'],
        }

        def get_analysis_data(results, key):
            if key in results:
                return results.get(key)
            for alias in key_aliases.get(key, []):
                if alias in results:
                    return results.get(alias)
            return None

        def extract_numbers(text, key):
            matches = re.findall(rf'{key}:\s*(?:\[(.*?)\]|(\d+))', text)
            numbers = []
            for list_part, single_part in matches:
                if list_part:
                    numbers.extend([int(n) for n in re.findall(r'\d+', list_part)])
                elif single_part:
                    numbers.append(int(single_part))
            return numbers

        def iter_ranges(item):
            if not isinstance(item, dict):
                return []
            starts = item.get('start')
            ends = item.get('end')
            length = item.get('length')

            if isinstance(starts, list):
                if isinstance(ends, list) and ends:
                    count = min(len(starts), len(ends))
                    return [(int(starts[i]), int(ends[i])) for i in range(count)]
                if length is not None:
                    return [(int(s), int(s) + int(length) - 1) for s in starts]
                return []

            if starts is None:
                return []

            try:
                start_val = int(starts)
            except (TypeError, ValueError):
                return []

            end_val = None
            if ends is not None:
                try:
                    end_val = int(ends)
                except (TypeError, ValueError):
                    end_val = None
            if end_val is None and length is not None:
                try:
                    end_val = start_val + int(length) - 1
                except (TypeError, ValueError):
                    end_val = None
            if end_val is None:
                return []
            return [(start_val, end_val)]

        def format_penalty(penalty_score):
            try:
                return f"{float(penalty_score):.2f}"
            except (TypeError, ValueError):
                return None

        for analysis_type, feature_type in feature_types_mapping.items():
            annotation_data = get_analysis_data(analysis_results, analysis_type)
            if not annotation_data:
                continue

            if analysis_type == 'InvertedRepeats':
                items = annotation_data if isinstance(annotation_data, list) else [annotation_data]
                if isinstance(annotation_data, str):
                    stem1_starts = extract_numbers(annotation_data, 'stem1_start')
                    stem1_ends = extract_numbers(annotation_data, 'stem1_end')
                    stem2_starts = extract_numbers(annotation_data, 'stem2_start')
                    stem2_ends = extract_numbers(annotation_data, 'stem2_end')
                    items = []
                    for s1_start, s1_end, s2_start, s2_end in zip(stem1_starts, stem1_ends, stem2_starts, stem2_ends):
                        items.append({
                            'stem1_start': s1_start,
                            'stem1_end': s1_end,
                            'stem2_start': s2_start,
                            'stem2_end': s2_end,
                        })

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    try:
                        s1_start = int(item.get('stem1_start'))
                        s1_end = int(item.get('stem1_end'))
                        s2_start = int(item.get('stem2_start'))
                        s2_end = int(item.get('stem2_end'))
                    except (TypeError, ValueError):
                        continue

                    stem1_start_abs = gene_start_in_vector + s1_start
                    stem1_end_abs = gene_start_in_vector + s1_end
                    stem2_start_abs = gene_start_in_vector + s2_start
                    stem2_end_abs = gene_start_in_vector + s2_end

                    penalty_str = format_penalty(item.get('penalty_score'))
                    repeat_type = item.get('type')
                    note_suffix = f" ({repeat_type})" if repeat_type else ""
                    penalty_suffix = f", penalty: {penalty_str}" if penalty_str else ""

                    stem1_feature = SeqFeature(
                        FeatureLocation(stem1_start_abs, stem1_end_abs),
                        type=feature_type,
                        qualifiers={
                            "label": f"{analysis_type}_stem1",
                            "note": f"Inverted repeat stem1 at {s1_start}-{s1_end}{note_suffix}{penalty_suffix}"
                        }
                    )
                    record.features.append(stem1_feature)

                    stem2_feature = SeqFeature(
                        FeatureLocation(stem2_start_abs, stem2_end_abs),
                        type=feature_type,
                        qualifiers={
                            "label": f"{analysis_type}_stem2",
                            "note": f"Inverted repeat stem2 at {s2_start}-{s2_end}{note_suffix}{penalty_suffix}"
                        }
                    )
                    record.features.append(stem2_feature)
                continue

            if isinstance(annotation_data, str):
                starts = extract_numbers(annotation_data, 'start')
                ends = extract_numbers(annotation_data, 'end')
                items = [{'start': s, 'end': e} for s, e in zip(starts, ends)]
            else:
                items = annotation_data if isinstance(annotation_data, list) else [annotation_data]

            for item in items:
                for start_rel, end_rel in iter_ranges(item):
                    start_abs = gene_start_in_vector + int(start_rel)
                    end_abs = gene_start_in_vector + int(end_rel)

                    penalty_score = None
                    if isinstance(item, dict):
                        penalty_score = item.get('penalty_score')
                    if penalty_score is None:
                        penalty_score = analysis_results.get(f'{analysis_type}_penalty_score', 0)
                    penalty_str = format_penalty(penalty_score)
                    penalty_suffix = f" (penalty: {penalty_str})" if penalty_str else ""

                    feature = SeqFeature(
                        FeatureLocation(start_abs, end_abs),
                        type=feature_type,
                        qualifiers={
                            "label": analysis_type,
                            "note": f"{analysis_type} at {start_rel}-{end_rel}{penalty_suffix}"
                        }
                    )
                    record.features.append(feature)

    # 添加Fragment特征标注
    if fragments_data and fragments_data.get('need_fragmentation'):
        gene_start_in_vector = start_pos + gene_start_pos_in_insert
        fragments = fragments_data.get('fragments', [])

        for frag in fragments:
            frag_start_rel = frag.get('start', 0)
            frag_end_rel = frag.get('end', 0)
            frag_index = frag.get('index', 0)
            frag_penalty = frag.get('penalty_score', 0)
            adapter_left = frag.get('adapter_left', '')
            adapter_right = frag.get('adapter_right', '')

            # 计算在载体中的绝对位置
            frag_start_abs = gene_start_in_vector + frag_start_rel
            frag_end_abs = gene_start_in_vector + frag_end_rel

            # 添加Fragment特征
            frag_feature = SeqFeature(
                FeatureLocation(frag_start_abs, frag_end_abs),
                type="CDS",
                qualifiers={
                    "label": f"Fragment_{frag_index}",
                    "note": f"Fragment {frag_index}: {frag_start_rel}-{frag_end_rel} bp, penalty={frag_penalty:.2f}, adapters={adapter_left}/{adapter_right}"
                }
            )
            record.features.append(frag_feature)

    # 输出
    with open(output_file, "w") as output_handle:
        SeqIO.write(record, output_handle, "genbank")


if __name__ == "__main__":
    # test addFeaturesToGeneBank
    # genebank_file = sys.argv[1] # full path
    # new_sequence = sys.argv[2] # sequence
    # output_file = sys.argv[3]  # full path
    # start_feature_label = sys.argv[4] # start feature label
    # end_feature_label = sys.argv[5] # end feature label
    # new_feature_name = sys.argv[6] # new feature name
    # addFeaturesToGeneBank(genebank_file, new_sequence, output_file, start_feature_label, end_feature_label, new_feature_name)

    # test addMultipleFeaturesToGeneBank
    genebank_file = sys.argv[1]
    output_file = sys.argv[2]
    # 假设传入参数时，多个新序列和特征名用分隔符分隔，如 seq1,seq2,seq3 ...
    new_sequences = sys.argv[3].split(",")  # 例如：ATGCGA,CGT... 
    new_feature_names = sys.argv[4].split(",")
    start_feature_label = sys.argv[5]
    end_feature_label = sys.argv[6]
    print("genbank_file: ", genebank_file)
    print("new_sequences: ", new_sequences)
    print("new_feature_names: ", new_feature_names)
    print("output_file: ", output_file)
    print("start_feature_label: ", start_feature_label)
    print("end_feature_label: ", end_feature_label)

    addMultipleFeaturesToGeneBank(genebank_file, output_file, new_sequences, new_feature_names, start_feature_label, end_feature_label)
