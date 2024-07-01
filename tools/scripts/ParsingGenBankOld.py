import sys
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature, FeatureLocation, CompoundLocation


def modify_locations(features, offset):
    for feature in features:
        if isinstance(feature.location, CompoundLocation):
            # 处理复合位置
            new_parts = []
            for part in feature.location.parts:
                new_start = part.start + offset
                new_end = part.end + offset
                new_parts.append(FeatureLocation(new_start, new_end, part.strand))
            feature.location = CompoundLocation(new_parts)
        else:
            # 处理单一位置
            new_start = feature.location.start + offset
            new_end = feature.location.end + offset
            feature.location = FeatureLocation(new_start, new_end, feature.location.strand)


def readGenBank(genebank_file):
    with open(genebank_file, "r") as input_handle:
        record = SeqIO.read(input_handle, "genbank")
    return record

def addFeaturesToGeneBank(genebank_file, new_sequence, output_file):
    # 步骤1：读取GenBank文件
    record = readGenBank(genebank_file)

    new_seq_length = len(new_sequence)
    record.seq = Seq(new_sequence + str(record.seq))

    # 修改特征位置
    modify_locations(record.features, new_seq_length)

    # 添加新特征
    new_feature = SeqFeature(FeatureLocation(0, new_seq_length), type="misc_feature", qualifiers={"label": "GOI"})
    record.features.insert(0, new_feature)  # 将新特征插入特征列表的开始位置

    # 步骤2：写入GenBank文件
    with open(output_file, "w") as output_handle:
        SeqIO.write(record, output_handle, "genbank")


if __name__ == "__main__":
    genebank_file = sys.argv[1] # full path
    new_sequence = sys.argv[2] # sequence
    output_file = sys.argv[3]  # full path

    addFeaturesToGeneBank(genebank_file, new_sequence, output_file)
