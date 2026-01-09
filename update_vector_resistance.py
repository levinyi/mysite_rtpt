#!/usr/bin/env python
"""
更新现有载体的抗性信息
根据载体名称自动识别抗性类型
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from product.models import Vector

# 常见载体抗性映射表
VECTOR_RESISTANCE_MAP = {
    # pET系列 - 多数为Amp
    'pET': 'Amp',
    'pGEX': 'Amp',
    'pMAL': 'Amp',

    # pET-28系列 - Kan抗性
    'pET-28': 'Kan',
    'pET28': 'Kan',

    # pcDNA系列 - Amp
    'pcDNA': 'Amp',

    # pPIC系列 - Zeocin
    'pPIC': 'Zeocin',

    # pESC系列 - 根据具体型号
    'pESC-URA': 'URA',  # 酵母营养选择标记
    'pESC-LEU': 'LEU',
    'pESC-TRP': 'TRP',
    'pESC-HIS': 'HIS',

    # Golden Gate载体
    'pGZ1704': 'Kan',
    'pGZ1705': 'Amp',

    # 其他常见载体
    'pUC': 'Amp',
    'pBR322': 'Amp',
    'pACYC': 'Chlor',  # Chloramphenicol
}

def get_resistance_from_name(vector_name):
    """
    根据载体名称推断抗性

    Args:
        vector_name: 载体名称

    Returns:
        抗性类型字符串，如果无法推断则返回None
    """
    if not vector_name:
        return None

    # 直接匹配
    for key, resistance in VECTOR_RESISTANCE_MAP.items():
        if key.lower() in vector_name.lower():
            return resistance

    # 根据常见命名规则推断
    name_lower = vector_name.lower()

    # Kan抗性的特征
    if 'kan' in name_lower or 'kanamycin' in name_lower:
        return 'Kan'

    # Amp抗性的特征
    if 'amp' in name_lower or 'ampicillin' in name_lower:
        return 'Amp'

    # Chlor抗性的特征
    if 'chlor' in name_lower or 'cm' in name_lower:
        return 'Chlor'

    # Zeocin抗性
    if 'zeo' in name_lower or 'zeocin' in name_lower:
        return 'Zeocin'

    # Hygromycin抗性
    if 'hyg' in name_lower or 'hygromycin' in name_lower:
        return 'Hygromycin'

    return None

def update_vector_resistance():
    """
    批量更新载体抗性信息
    """
    vectors = Vector.objects.all()
    total = vectors.count()
    updated = 0
    skipped = 0
    manual_review = []

    print(f"开始更新 {total} 个载体的抗性信息...\n")

    for vector in vectors:
        # 如果已经有抗性信息，跳过
        if vector.antibiotic_resistance:
            skipped += 1
            continue

        # 推断抗性
        resistance = get_resistance_from_name(vector.vector_name)

        if resistance:
            vector.antibiotic_resistance = resistance
            vector.save(update_fields=['antibiotic_resistance'])
            updated += 1
            print(f"✓ {vector.id:4d} | {vector.vector_name:30s} → {resistance}")
        else:
            manual_review.append((vector.id, vector.vector_name))
            print(f"? {vector.id:4d} | {vector.vector_name:30s} → 需要人工确认")

    print("\n" + "="*80)
    print(f"更新完成！")
    print(f"  总载体数: {total}")
    print(f"  已有抗性: {skipped}")
    print(f"  自动更新: {updated}")
    print(f"  需人工确认: {len(manual_review)}")

    if manual_review:
        print("\n需要人工确认的载体:")
        for vid, vname in manual_review:
            print(f"  ID {vid}: {vname}")
        print("\n请手动更新这些载体的抗性信息:")
        print("  python manage.py shell")
        print("  >>> from product.models import Vector")
        print("  >>> v = Vector.objects.get(id=载体ID)")
        print("  >>> v.antibiotic_resistance = '抗性类型'")
        print("  >>> v.save()")

if __name__ == '__main__':
    update_vector_resistance()
