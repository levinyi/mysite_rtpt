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
    full_new_seq = "".join(new_sequences)
    full_new_seq_length = len(full_new_seq)

    # 替换原序列中的指定片段
    record.seq = record.seq[:start_pos] + Seq(full_new_seq) + record.seq[end_pos:]

    # 调整已有特征位置
    modify_locations(record.features, start_pos, end_pos, full_new_seq_length)

    # 添加新特征
    offset = 0
    for seq, name in zip(new_sequences, new_feature_names):
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
