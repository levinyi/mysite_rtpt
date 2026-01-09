#!/usr/bin/env python
"""
回填购物车基因的限制性酶切位点决策数据

使用方法:
    python backfill_restriction_decisions.py
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from user_center.models import Cart, GeneInfo
from user_center.utils.sequence_processing import make_restriction_site_decision

def backfill_cart_genes(username=None):
    """
    为购物车中的基因回填决策数据

    参数:
        username: 用户名。如果为None，则处理所有购物车
    """
    if username:
        carts = Cart.objects.filter(user__username=username)
        print(f"处理用户 '{username}' 的购物车...")
    else:
        carts = Cart.objects.all()
        print("处理所有购物车...")

    total_carts = carts.count()
    print(f"找到 {total_carts} 个购物车")

    total_updated = 0
    total_skipped = 0

    for cart in carts:
        genes = cart.genes.all()
        print(f"\n用户: {cart.user.username}, 基因数量: {genes.count()}")

        # 默认使用T4克隆方法
        default_cloning_method = 'T4'

        for gene in genes:
            # 检查是否已有决策数据
            if gene.restriction_decision:
                total_skipped += 1
                continue

            # 获取序列
            seq = gene.saved_seq if gene.saved_seq else gene.original_seq
            if not seq:
                print(f"  ⚠ {gene.gene_name}: 无序列，跳过")
                total_skipped += 1
                continue

            # 如果基因关联了载体，使用载体的克隆方法
            cloning_method = default_cloning_method
            if hasattr(gene, 'vector') and gene.vector and gene.vector.cloning_method:
                cloning_method = gene.vector.cloning_method

            # 计算决策
            result = make_restriction_site_decision(seq, cloning_method)

            # 更新数据库
            gene.restriction_decision = result['decision']
            gene.restriction_process_route = result['process_route']
            gene.restriction_message = result['message']
            gene.restriction_requires_manual_review = result['requires_manual_review']
            gene.bsai_count = result['bsai_count']
            gene.bsmbi_count = result['bsmbi_count']
            gene.bsai_positions = result['bsai_positions']
            gene.bsmbi_positions = result['bsmbi_positions']
            gene.save()

            total_updated += 1

            # 显示结果
            decision_icon = "✅" if result['decision'] == 'accept' else "❌"
            route_text = f"via {result['process_route']}" if result['process_route'] else ""
            review_text = " (需人工评估)" if result['requires_manual_review'] else ""

            print(f"  {decision_icon} {gene.gene_name}: BsaI={result['bsai_count']}, BsmBI={result['bsmbi_count']} → {result['decision']} {route_text}{review_text}")

    print(f"\n{'='*80}")
    print(f"回填完成!")
    print(f"  更新: {total_updated} 个基因")
    print(f"  跳过: {total_skipped} 个基因")
    print(f"{'='*80}")


def backfill_all_genes():
    """
    为所有基因（不仅是购物车）回填决策数据
    """
    print("处理所有基因...")

    genes = GeneInfo.objects.filter(restriction_decision__isnull=True)
    total = genes.count()

    print(f"找到 {total} 个没有决策数据的基因")

    if total == 0:
        print("所有基因都已有决策数据")
        return

    # 默认使用T4克隆方法
    default_cloning_method = 'T4'

    updated = 0
    skipped = 0

    for i, gene in enumerate(genes, 1):
        # 获取序列
        seq = gene.saved_seq if gene.saved_seq else gene.original_seq
        if not seq:
            skipped += 1
            continue

        # 如果基因关联了载体，使用载体的克隆方法
        cloning_method = default_cloning_method
        if hasattr(gene, 'vector') and gene.vector and gene.vector.cloning_method:
            cloning_method = gene.vector.cloning_method

        # 计算决策
        result = make_restriction_site_decision(seq, cloning_method)

        # 更新数据库
        gene.restriction_decision = result['decision']
        gene.restriction_process_route = result['process_route']
        gene.restriction_message = result['message']
        gene.restriction_requires_manual_review = result['requires_manual_review']
        gene.bsai_count = result['bsai_count']
        gene.bsmbi_count = result['bsmbi_count']
        gene.bsai_positions = result['bsai_positions']
        gene.bsmbi_positions = result['bsmbi_positions']
        gene.save()

        updated += 1

        # 每处理100个基因显示一次进度
        if i % 100 == 0:
            print(f"  进度: {i}/{total} ({i*100//total}%)")

    print(f"\n{'='*80}")
    print(f"回填完成!")
    print(f"  更新: {updated} 个基因")
    print(f"  跳过: {skipped} 个基因")
    print(f"{'='*80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='回填限制性酶切位点决策数据')
    parser.add_argument('--user', '-u', type=str, help='只处理指定用户的购物车基因')
    parser.add_argument('--all', '-a', action='store_true', help='处理所有基因（不仅是购物车）')
    parser.add_argument('--cart-only', '-c', action='store_true', default=True, help='只处理购物车基因（默认）')

    args = parser.parse_args()

    if args.all:
        backfill_all_genes()
    else:
        backfill_cart_genes(username=args.user)
