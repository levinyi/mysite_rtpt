import sys
import pandas as pd
sys.path.append("/cygene4/dushiyi/mysite_rtpt/tools/scripts/")
from scripts.AnalysisSequence import DNARepeatsFinder


def expanded_rows_to_gene_table(df, gene_table):
    expanded_results = []
    all_columns = set()

    # 首先收集所有可能的列名
    for _, row in df.iterrows():
        for analysis_type, results_list in row.items():
            if results_list:
                for result in results_list:
                    for key, value in result.items():
                        column_name = f'{analysis_type}_{key}'
                        all_columns.add(column_name)

    # 初始化每个 result_dict，并确保所有可能的列名都在字典中
    for gene_id, row in df.iterrows():
        result_dict = {col: '' for col in all_columns}
        result_dict['gene_id'] = gene_id
        
        for analysis_type, results_list in row.items():
            if results_list:
                for result in results_list:
                    for key, value in result.items():
                        column_name = f'{analysis_type}_{key}'
                        if 'penalty_score' in key:
                            if value == '':
                                continue  # 跳过空值
                            if result_dict[column_name] != '':
                                try:
                                    result_dict[column_name] += float(value)
                                except ValueError:
                                    print(f'Error: {value} is not a valid float')
                            else:
                                try:
                                    result_dict[column_name] = float(value)
                                except ValueError:
                                    print(f'Error: {value} is not a valid float')
                        elif 'seqType' in key:
                            if column_name not in result_dict:
                                result_dict[column_name] = value
                        else:
                            if result_dict[column_name] != '':
                                result_dict[column_name] += f';{value}'
                            else:
                                result_dict[column_name] = str(value)
            else:
                continue
            
        expanded_results.append(result_dict)

    expanded_df = pd.DataFrame(expanded_results)

    gene_table = gene_table.merge(expanded_df, on='gene_id', how='left')

    return gene_table


def analyze_sequences(gene_table):
    # Remove rows with None
    gene_table = gene_table.dropna().reset_index(drop=True)


    finder_dataset = DNARepeatsFinder(data_set=gene_table)

    results = {}
    for index, row in gene_table.iterrows():
        gene_id = row['WF3_Mfg_ID']
        results[gene_id] = {
            # 'tandem_repeats': finder_dataset.find_tandem_repeats(index=index, min_unit=3, min_copies=3),
            'long_repeats': finder_dataset.find_dispersed_repeats(index=index, min_len=16),
            # 'palindromes': finder_dataset.find_palindrome_repeats(index=index, min_len=15),
            # # 'inverted_repeats': finder_dataset.find_inverted_repeats(index=index, min_len=10),
            'homopolymers': finder_dataset.find_homopolymers(index=index, min_len=7),
            # 'W8S8_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=8, min_S_length=8),
            'W12S12_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=12, min_S_length=12),
            # 'W16S16_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=16, min_S_length=16),
            # 'W20S20_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=20, min_S_length=20),
            'local_gc_content': finder_dataset.find_local_gc_content(index=index, window_size=30, min_GC_content=20, max_GC_content=80),
            # 'lcc_simp': finder_dataset.get_lcc(index=index),
        }

    #将结果列表转换为DataFrame， 处理长度不一致问题
    df = pd.DataFrame(results).T
    
    gene_table = expanded_rows_to_gene_table(df, gene_table)

    return gene_table

if __name__ == "__main__":
    # Test
    gene_file = sys.argv[1]
    gene_table = pd.read_csv(gene_file, sep="\t")
    gene_table['sequence'] = gene_table['FullSeqREAL']
    gene_table['gene_id'] = gene_table['WF3_Mfg_ID']

    updated_df = analyze_sequences(gene_table)

    output_file = gene_file.split(".")[0] + "_updated.txt"
    updated_df.to_csv(output_file, sep="\t", index=False)
