"""
user_center模块的Celery异步任务
"""
import os
from celery import shared_task
from django.core.files import File
from django.core.files.base import ContentFile
from product.models import Vector
from user_center.utils.vector_automation import VectorAutomationDesigner


@shared_task
def async_vector_automation_design(vector_id):
    """
    异步执行载体改造自动化设计任务

    Args:
        vector_id: Vector对象的ID

    Returns:
        dict: 设计结果
    """
    try:
        vector = Vector.objects.get(pk=vector_id)

        # 更新状态为Processing
        vector.design_status = 'Processing'
        vector.save()

        # 获取上传的GenBank文件路径
        genbank_file_path = vector.vector_file.path

        # 初始化设计器
        designer = VectorAutomationDesigner(genbank_file_path)

        # 1. 解析GenBank文件
        parsed_data = designer.parse_genbank()
        if not parsed_data:
            vector.design_status = 'Failed'
            vector.design_error = '; '.join(designer.errors)
            vector.save()
            return {'status': 'error', 'errors': designer.errors}

        # 保存iU20和iD20序列
        vector.iu20 = parsed_data['iu20_seq']
        vector.id20 = parsed_data['id20_seq']

        # 2. 选择克隆方法并设计v5NC和v3NC
        design_result = designer.select_cloning_method(parsed_data)
        if not design_result:
            vector.design_status = 'Failed'
            vector.design_error = '没有找到可用的克隆方法。' + '; '.join(designer.errors)
            vector.save()
            return {'status': 'error', 'errors': designer.errors}

        # 保存设计结果
        vector.cloning_method = design_result['method']
        vector.NC5 = design_result['v5nc']
        vector.NC3 = design_result['v3nc']
        vector.i5NC = design_result.get('i5nc', '')
        vector.i3NC = design_result.get('i3nc', '')

        # 3. 设计NC-PCR引物（仅Gibson方法）
        primer_result = None
        if design_result['method'] == 'Gibson':
            primer_result = designer.design_nc_pcr_primers(design_result, parsed_data)
            if primer_result:
                vector.primer_forward = primer_result['forward']['sequence']
                vector.primer_reverse = primer_result['reverse']['sequence']
                vector.primer_forward_tm = primer_result['forward']['tm']
                vector.primer_reverse_tm = primer_result['reverse']['tm']
            else:
                # 引物设计失败，但不影响整体流程
                vector.design_error = '引物设计失败：' + '; '.join(designer.errors)

        # 4. 生成改造后GenBank文件
        # 从文件名提取信息
        original_filename = os.path.basename(genbank_file_path)
        resistance = designer.extract_resistance_from_filename(original_filename)
        vector_code = designer.extract_vector_code_from_filename(original_filename)

        # 构建输出文件名
        if resistance:
            output_filename = f"{vector_code}M1({resistance})-Modified-M1.gb"
        else:
            output_filename = f"{vector_code}M1-Modified-M1.gb"
            vector.design_error = (vector.design_error or '') + ' 未在文件名中找到抗性信息;'

        # 生成临时输出路径
        output_dir = os.path.dirname(genbank_file_path)
        output_path = os.path.join(output_dir, output_filename)

        # 生成GenBank文件
        designer.generate_modified_genbank(
            design_result,
            parsed_data,
            primer_result,
            output_path,
            output_filename.replace('.gb', '')
        )

        # 保存到vector_gb字段
        with open(output_path, 'rb') as f:
            vector.vector_gb.save(output_filename, File(f), save=False)

        # 保存载体序列（without v5NC/v3NC之间的序列）
        v5nc_end = design_result['v5nc_location'][1]
        v3nc_start = design_result['v3nc_location'][0]
        vector_without_insert = parsed_data['sequence'][:v5nc_end] + parsed_data['sequence'][v3nc_start:]
        vector.vector_map = vector_without_insert

        # 更新状态为Completed
        vector.design_status = 'Completed'
        vector.save()

        return {
            'status': 'success',
            'method': design_result['method'],
            'v5nc': design_result['v5nc'],
            'v3nc': design_result['v3nc'],
            'i5nc': design_result.get('i5nc', ''),
            'i3nc': design_result.get('i3nc', ''),
            'primer_forward': vector.primer_forward,
            'primer_reverse': vector.primer_reverse,
            'output_file': output_filename
        }

    except Vector.DoesNotExist:
        return {'status': 'error', 'errors': ['Vector对象不存在']}
    except Exception as e:
        # 捕获所有异常
        try:
            vector = Vector.objects.get(pk=vector_id)
            vector.design_status = 'Failed'
            vector.design_error = f'系统错误: {str(e)}'
            vector.save()
        except:
            pass

        return {'status': 'error', 'errors': [f'系统错误: {str(e)}']}
