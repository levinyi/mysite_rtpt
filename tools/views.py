import base64
import io, os
import json
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import BadRequest
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

def upload_file(file_name, project_path):
    # 去掉文件名中的空格,[],()
    file_name_name = file_name.name.replace(" ", "").replace('[',"").replace(']',"")  
    file_name_name = file_name_name.replace("(","").replace(")","")
    file_path = os.path.join(project_path, file_name_name)  # result_path to project_path. Changed by dsy 20230612.
    os.makedirs(project_path, exist_ok=True)
    with open(file_path, 'wb+') as f:
        for chunk in file_name.chunks():
            f.write(chunk)
    return file_path

def GenePlateExplorer(request):
    if request.method == 'GET':
        return render(request, 'tools/tools_GenePlate_Explorer.html')
    elif request.method == 'POST':
        project_name = request.POST.get("project_name")

        temp_dir = 'media/temp/'

        # 将用户上传的文件保存到 temp_dir 目录下
        temp_file1 = request.FILES["file_name1"]
        file1_path = upload_file(temp_file1, temp_dir)
        temp_file2 = request.FILES["file_name2"]
        file2_path = upload_file(temp_file2, temp_dir)
        temp_file3 = request.FILES["file_name3"]
        file3_path = upload_file(temp_file3, temp_dir)

        context = {
            'project_name': project_name,
            'file1': file1_path,
            'file2': file2_path,
            'file3': file3_path,
        }
        return render(request, 'tools/tools_GenePlate_Explorer_detail.html', context)

def plate_view(request):
    try:
        data = json.loads(request.body)
        file1 = data['file1']
        file2 = data['file2']
        file3 = data['file3']
    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'status': 'error', 'message': f"Missing or invalid data: {str(e)}"}, status=400)

    def process_5p30_file(file):
        try:
            df = pd.read_csv(file, sep='\t')
            df['GeneID'] = 'G' + df['IntraPRJSN'].astype(str).str.zfill(4)
            df = df[['Plate', 'WellPos', 'GeneID', 'FullSeqREAL_Credit']]
            df = df.assign(FullSeqREAL_Credit=df['FullSeqREAL_Credit'].str.split(';')).explode('FullSeqREAL_Credit').reset_index(drop=True)
            df['subplate'] = 'R' + (df.groupby(['Plate', 'WellPos']).cumcount() + 1).astype(str)
            df['FullSeqREAL_Credit_Copy'] = df['FullSeqREAL_Credit']
            return df
        except FileNotFoundError:
            raise BadRequest(f"File not found: {file}")
        except pd.errors.ParserError:
            raise BadRequest(f"Error parsing file: {file}")
        except KeyError as e:
            raise BadRequest(f"Missing expected column: {e.args[0]}")
        except Exception as e:
            raise BadRequest(f"Unexpected error processing file {file}: {str(e)}")
    
    def process_3p30_file(file):
        try:
            df = pd.read_csv(file, sep='\t')
            df['Mfg_ID'] = '[' + df['PRJID'] + '][G' + df['IntraPRJSN'].astype(str).str.zfill(4) + ']'
            return df[['Mfg_ID', 'GeneName']]
        except FileNotFoundError:
            raise BadRequest(f"File not found: {file}")
        except pd.errors.ParserError:
            raise BadRequest(f"Error parsing file: {file}")
        except KeyError as e:
            raise BadRequest(f"Missing expected column: {e.args[0]}")
        except Exception as e:
            raise BadRequest(f"Unexpected error processing file {file}: {str(e)}")
    
    def process_mtp_file(file):
        try:
            return pd.read_csv(file, sep='\t')
        except FileNotFoundError:
            raise BadRequest(f"File not found: {file}")
        except pd.errors.ParserError:
            raise BadRequest(f"Error parsing file: {file}")
        except Exception as e:
            raise BadRequest(f"Unexpected error processing file {file}: {str(e)}")

    try:
        df5 = process_5p30_file(file1)
        df3 = process_3p30_file(file2)
        mtp_df = process_mtp_file(file3)
    except BadRequest as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    try:
        df_merge = pd.merge(df3, df5, left_on='Mfg_ID', right_on="FullSeqREAL_Credit", how='outer')
        df_merge = pd.merge(df_merge, mtp_df, left_on='GeneName', right_on='WF3_Synthon_GeneName', how='left')
    except KeyError as e:
        return JsonResponse({'status': 'error', 'message': f"Error during merge: Missing expected column: {e.args[0]}"}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Unexpected error during merge: {str(e)}"}, status=500)

    all_data = {'plates': {}, 'subplates': {}, 'missing_data': {}, 'extra_data': []}

    for _, row in df_merge.iterrows():
        plate_id = row['Plate']
        well_pos = row['WellPos']
        gene_id = row['GeneID']
        subplate = row['subplate']
        fullseq = row['FullSeqREAL_Credit']
        FullSeqREAL_Credit = row['FullSeqREAL_Credit_Copy']
        gene_name = row['GeneName']
        wf3_synthon_gene_name = row['WF3_Synthon_GeneName']
        wf3_mfg_id = row['WF3_Mfg_ID']

        if pd.notna(plate_id) and pd.notna(well_pos) and pd.notna(gene_id):
            all_data['plates'].setdefault(plate_id, {'well_positions': {}})['well_positions'][well_pos] = {
                'gene_id': gene_id,
                'gene_name': gene_name,
                'fullseq': fullseq,
                'hover_info': FullSeqREAL_Credit,
                'wf3_synthon_gene_name': wf3_synthon_gene_name if pd.notna(wf3_synthon_gene_name) else '',
                'wf3_mfg_id': wf3_mfg_id if pd.notna(wf3_mfg_id) else ''
            }

        if pd.notna(plate_id) and pd.notna(subplate) and pd.notna(well_pos) and pd.notna(fullseq):
            all_data['subplates'].setdefault(plate_id, {}).setdefault(subplate, {})[well_pos] = fullseq

        if pd.isna(plate_id) and gene_name not in all_data['extra_data']:
            all_data['extra_data'].append(gene_name)

        if pd.isna(wf3_mfg_id):
            all_data['missing_data'].setdefault(plate_id, {}).setdefault(subplate, []).append(well_pos)

    return JsonResponse({'status': 'success', 'all_data': all_data})

