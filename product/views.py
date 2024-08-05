import json
import os
from pathlib import Path
from django.shortcuts import get_object_or_404, render

from mysite import settings
from .models import Species, Vector

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import pandas as pd
import re


species_dir = os.path.join(settings.MEDIA_ROOT, 'codon_usage_table')
BASE_DIR = Path(__file__).resolve().parent.parent


def vector_validation(request):
    # 只接受post请求
    # 获取用户上传的文件
    # 判断文件是否合法
    # 存入用户的数据库
    # 返回跳转页面
    if request.method == "POST":
        # 判读是否登录
        if not request.user.is_authenticated: # 未登录
            return JsonResponse({'status': 'error', 'message': 'Please login.'}, status=401)
        # 获取用户上传的文件
        file = request.FILES.get('vector_file')
        # 判断文件是否合法
        if not file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': 'Please upload the csv file.'}, status=401)
        # 使用pandas读取文件中的内容，验证vector_name，C_Gene是否正确，正确的话，Status为True，否则为False，逐条存入Vector数据库
        df = pd.read_csv(file)
        for index, row in df.iterrows():
            if not row['Vector_name'].startswith('p'):
                return JsonResponse({'status': 'error', 'message': 'Please check the vector name.'}, status=401)
            if not row['C_Gene'].startswith('IGH'):
                return JsonResponse({'status': 'error', 'message': 'Please check the C_Gene.'}, status=401)
            if not row['V_Gene'].startswith('IGH'):
                return JsonResponse({'status': 'error', 'message': 'Please check the V_Gene.'}, status=401)
            if not row['NC5'].startswith('GG'):
                return JsonResponse({'status': 'error', 'message': 'Please check the NC5.'}, status=401)
            if not row['NC3'].startswith('TT'):
                return JsonResponse({'status': 'error', 'message': 'Please check the NC3.'}, status=401)
            # 存入用户的数据库
            Vector.objects.create(
                user=request.user,
                vector_name=row['Vector_name'],
                vector_map=row['Vector_map'],
                C_Gene=row['C_Gene'],
                V_Gene=row['V_Gene'],
                NC5=row['NC5'],
                NC3=row['NC3'],
                is_ready_to_use=False,
            )
            
        
        # 存入用户的数据库
        Vector.objects.create(
            user=request.user,
            vector_name=file.name,
            vector_map=file,
            is_ready_to_use=False,
        )
        # 返回跳转页面
        return JsonResponse({'redirect_url': '/user_center/manage_vector/'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Please use POST.'}, status=401)
    

def read_codon_usage_table(file):
    codon_df = pd.read_excel(file, header=None, names=["Triplet", "Amino acid", "Fraction", "Frequency", "Number"])
    # use regex to extract species name
    pattern = r'Excel_CodonUsage_(.+)\.xlsx'
    match = re.search(pattern, file)
    species_name = match.group(1)

    aminoAcid = {}
    triplet_dict = {}
    # convert codon_df to dict
    for _, row in codon_df.iterrows():
        amino_acid = row["Amino acid"]
        triplet = row["Triplet"]
        aminoAcid.setdefault(amino_acid, []).append(row.to_dict())
        triplet_dict[triplet] = row.to_dict()

    return aminoAcid, triplet_dict, species_name


def upload_species_codon_file(request):
    if request.method == "POST":
        # 判读是否登录
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Please login.'}, status=401)
        
        species_name = request.POST.get('species_name')
        species_note = request.POST.get('species_note', '')
        species_codon_file = request.FILES.get('species_codon_file')

        species, created = Species.objects.update_or_create(
            # 如果名字相同，就更新，否则就创建
            species_name=species_name,
            defaults={'species_note': species_note, 'species_codon_file': species_codon_file}
        )

        # update js file 
        # species_dir is a global variable
        species_files = [file for file in os.listdir(species_dir) if file.endswith(".xlsx")]
        aminoAcid = {}
        triplet = {}
        for file in species_files:
            aminoacid_dict, triplet_dict, species_name = read_codon_usage_table(os.path.join(species_dir, file))
            aminoAcid[species_name] = aminoacid_dict
            triplet[species_name] = triplet_dict

        JS_file_path = os.path.join(BASE_DIR,'static', 'species')
        with open(os.path.join(JS_file_path, "amino_acid_data.js"), "w") as f:
            f.write("var aminoAcid = ")
            json.dump(aminoAcid, f, indent=4)

        with open(os.path.join(JS_file_path, "species_data.js"), "w") as f:
            f.write("var species = ")
            json.dump(triplet, f, indent=4)
        return JsonResponse({'status': 'success', 'message': 'Upload success.'})
    return render(request, '/super_manage/species_codon_manage.html')


def species_delete(request):
    if request.method == "POST":
        species_id = request.POST.get('species_id')
        
        species = get_object_or_404(Species, id=species_id)
    
        if species.species_codon_file:
            file_path = species.species_codon_file.path
            if os.path.exists(file_path):
                os.remove(file_path)
        species.delete()
        return JsonResponse({'status': 'success', 'message': 'Species deleted Successfully'})
    else:
        return JsonResponse({'status': 'failed', 'message': 'Not A Post Request.'})
