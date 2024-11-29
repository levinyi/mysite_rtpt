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
    with open(genebank_file, "r") as input_handle:
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


if __name__ == "__main__":
    genebank_file = sys.argv[1] # full path
    new_sequence = sys.argv[2] # sequence
    output_file = sys.argv[3]  # full path
    start_feature_label = sys.argv[4] # start feature label
    end_feature_label = sys.argv[5] # end feature label
    new_feature_name = sys.argv[6] # new feature name

    addFeaturesToGeneBank(genebank_file, new_sequence, output_file, start_feature_label, end_feature_label, new_feature_name)
