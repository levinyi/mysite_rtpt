import base64
from concurrent.futures import ProcessPoolExecutor
import io
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from .models import Tool
from django.contrib.auth.decorators import login_required
from tools.scripts.AnalysisSequence import DNARepeatsFinder
import pandas as pd
# Create your views here.

def tools_list(request):
    tools = Tool.objects.all()
    return render(request, 'tools/tools_list.html', {'tools': tools})

def safe_float_convert(x):
    try:
        return x.dropna().astype(float).sum()
    except ValueError:
        return 0  # 或其他适当的默认值，例如 np.nan 依情况而定
    
def expanded_rows_to_gene_table(df, gene_table):
    expanded_results = []

    for gene_id, row in df.iterrows():
        result_dict = {
            'gene_id': gene_id
        }
        
        for analysis_type, results_list in row.items():
            if results_list:
                # 假设每个结果都是一个字典，我们将使用扁平化处理
                for result in results_list:
                    for key, value in result.items():
                        column_name = f'{analysis_type}_{key}'
                        # 特殊处理 penalty_score 列，累加浮点数值
                        if 'penalty_score' in key:
                            if column_name in result_dict:
                                # 如果这是一个 penalty_score 列，我们将尝试将其转换为浮点数并将其添加到现有值上
                                try:
                                    result_dict[column_name] += float(value)
                                except ValueError:
                                    continue
                            else:
                                # 第一次遇到 penalty_score 列，我们将尝试将其转换为浮点数
                                try:
                                    result_dict[column_name] = float(value)
                                except ValueError:
                                    continue
                        # 特殊处理 seqType 列，只取第一个值
                        elif 'seqType' in key:
                            if column_name not in result_dict:
                                result_dict[column_name] = value
                        # 其他列使用字符串连接
                        else:
                            # 对于其他列，我们将使用字符串连接
                            if column_name in result_dict:
                                result_dict[column_name] += f';{value}'
                            else:
                                result_dict[column_name] = str(value)
            else:
                continue
            
        expanded_results.append(result_dict)

    expanded_df = pd.DataFrame(expanded_results)

    # merge gene_table and updated_df
    gene_table = gene_table.merge(expanded_df, on='gene_id', how='left')

    return gene_table

# 使用 ProcessPoolExecutor 来并行处理
def process_row(row_data, finder_dataset):
    index, row  = row_data
    gene_id = row['gene_id']
    return {
        'gene_id': gene_id,
        'tandem_repeats': finder_dataset.find_tandem_repeats(index=index, min_unit=3, min_copies=3),
        'inverted_repeats': finder_dataset.find_inverted_repeats(index=index, min_len=10, max_distance=10),
        'W8S8_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=8, min_S_length=8),
        'local_gc_content': finder_dataset.find_local_gc_content(index=index),
        'homopolymers': finder_dataset.find_homopolymers(index=index, min_len=7),
        'long_repeats': finder_dataset.find_dispersed_repeats(index=index, min_len=16),
        'palindromes': finder_dataset.find_palindrome_repeats(index=index)
    }

"""
"""
@login_required
def SequenceAnalyzer(request):
    if request.method == 'POST':
        # data is from a Handsontable, so it is a JSON string
        data = json.loads(request.body.decode('utf-8'))
        gene_table = data.get("genetable")
        if not gene_table:
            return JsonResponse({'status': 'error', 'message': 'No gene data provided'})
        
        # Convert the data to a DataFrame and set the column names 
        # and drop any rows with missing values and reset the index
        gene_table = pd.DataFrame(gene_table, columns=['gene_id', 'sequence']).dropna().reset_index(drop=True)
        
        # Create a DNARepeatsFinder object and run the analysis
        finder_dataset = DNARepeatsFinder(data_set=gene_table)
        

        results = {}
        for index, row in gene_table.iterrows():
            gene_id = row['gene_id']
            results[gene_id] = {
                'tandem_repeats': finder_dataset.find_tandem_repeats(index=index, min_unit=3, min_copies=3),
                'inverted_repeats': finder_dataset.find_inverted_repeats(index=index, min_len=10, max_distance=10),
                'W8S8_motifs': finder_dataset.find_WS_motifs(index=index, min_W_length=8, min_S_length=8),
                'local_gc_content': finder_dataset.find_local_gc_content(index=index),
                'homopolymers': finder_dataset.find_homopolymers(index=index, min_len=7),
                'long_repeats': finder_dataset.find_dispersed_repeats(index=index, min_len=16),
                'palindromes': finder_dataset.find_palindrome_repeats(index=index)
            }

        # Use ProcessPoolExecutor to parallelize the processing of each row
        # print("Yes, I am here")
        # results = {}
        # with ProcessPoolExecutor() as executor:
        #     tasks = [(index, row) for index, row in enumerate(gene_table.to_dict('records'))]
        #     for result in executor.map(process_row, tasks, [finder_dataset]*len(tasks)):
        #         results[result['gene_id']] = result
        # print("Yes, I am here")
        # print("results:", results)


        df = pd.DataFrame(results).T

        gene_table = expanded_rows_to_gene_table(df, gene_table)
        # add a total penalty score column
        gene_table['total_penalty_score'] = gene_table.apply(lambda row: row.filter(like='penalty_score').sum(), axis=1)
        
        request.session['gene_table'] = gene_table.to_dict(orient='records')
        return JsonResponse({'status': 'success', 'redirect_url': '/tools/sequence_analysis_detail/'})    
    return render(request, 'tools/SequenceAnalyzer.html')

@login_required
def download_gene_table(request):
    # 假设你已经在某个地方存储了需要的数据或可以快速访问/生成它
    # 从会话中获取存储的gene_table
    gene_table_data = request.session.get('gene_table')
    if not gene_table_data:
        return HttpResponse('No gene table data found in the session.', status=404)
    
    # 将数据转换为DataFrame
    df = pd.DataFrame(gene_table_data)

    # 将DataFrame转换为CSV文件
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="gene_analysis_results.csv"'
    return response


@login_required
def sequence_analysis_detail(request):
    gene_table = request.session['gene_table']
    return render(request, 'tools/sequence_detail.html', {'gene_table': gene_table})