import sys
import pandas as pd
sys.path.append("/cygene4/dushiyi/mysite_rtpt/tools/scripts/")
sys.path.append("/cygene4/dushiyi/mysite_rtpt/user_center/")
from scripts.AnalysisSequence import DNARepeatsFinder
from user_center.views import convert_gene_table_to_RepeatsFinder_Format


if __name__ == "__main__":
    # Test
    gene_file = sys.argv[1]
    if gene_file.endswith(".xlsx"):
        gene_table = pd.read_excel(gene_file)
    else:
        gene_table = pd.read_csv(gene_file, sep="\t")
    gene_table['sequence'] = gene_table['FullSeqREAL']
    gene_table['gene_id'] = gene_table['WF3_Mfg_ID']

    print(gene_table)
    updated_df = convert_gene_table_to_RepeatsFinder_Format(gene_table)

    output_file = gene_file.split(".")[0] + "_updated.txt"
    updated_df.to_csv(output_file, sep="\t", index=False)
