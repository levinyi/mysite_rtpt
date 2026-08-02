"""前台载体可见性测试。

背景：内部员工（SecondaryAdminGroup）会用自己的账号在前台替客户上传骨架质粒
（pCVaxxx），再用同一个账号替客户下单。载体归属改造后管理员上传的载体归公司
（user=None + is_public=False），如果前台列表只按 user=request.user 过滤，上传完
就会从前台彻底消失——既不在 My Vectors，也不在 RootPath Vectors，更没法下单。
这组测试锁住修复后的可见性规则。
"""
import json

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from product.models import Vector


class WorkspaceVectorVisibilityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('yeyanzhen_test', password='x')
        self.staff.groups.add(Group.objects.create(name='SecondaryAdminGroup'))
        self.customer = User.objects.create_user('customer_test', password='x')
        self.other_customer = User.objects.create_user('other_test', password='x')

        self.company_internal = Vector.objects.create(
            vector_name='pCVa393(Amp)_human_IgG1', user=None, is_public=False, status='ReadyToUse')
        self.company_public = Vector.objects.create(
            vector_name='pGZ1687(Kan)-common', user=None, is_public=True, status='ReadyToUse')
        self.customer_own = Vector.objects.create(
            vector_name='pMine', user=self.customer, is_public=False, status='ReadyToUse')

    def _my_vector_names(self, user):
        self.client.force_login(user)
        resp = self.client.get(reverse('user_center:customer_vector_data_api'))
        self.assertEqual(resp.status_code, 200)
        return {v['vector_name'] for v in json.loads(resp.content)['data']}

    def _rootpath_vector_names(self, user):
        self.client.force_login(user)
        resp = self.client.get(reverse('user_center:rootpath_vector_data_api'))
        self.assertEqual(resp.status_code, 200)
        return {v['vector_name'] for v in json.loads(resp.content)['data']}

    def test_staff_sees_company_internal_vectors_in_my_vectors(self):
        """回归：管理员代传的公司内部载体必须留在他自己的 My Vectors 里。"""
        self.assertIn(self.company_internal.vector_name, self._my_vector_names(self.staff))

    def test_public_company_vectors_not_duplicated_in_staff_my_vectors(self):
        """已公开的公司载体在 RootPath Vectors 那张表里，不重复进 My Vectors。"""
        self.assertNotIn(self.company_public.vector_name, self._my_vector_names(self.staff))
        self.assertIn(self.company_public.vector_name, self._rootpath_vector_names(self.staff))

    def test_customer_sees_only_own_vectors(self):
        self.assertEqual(self._my_vector_names(self.customer), {self.customer_own.vector_name})

    def test_customer_cannot_see_company_internal_vector(self):
        """公司内部载体（含别的客户寄来的质粒）不能出现在客户目录里。"""
        self.assertNotIn(self.company_internal.vector_name, self._rootpath_vector_names(self.customer))
        self.assertNotIn(self.company_internal.vector_name, self._my_vector_names(self.other_customer))

    def test_staff_upload_is_owned_by_company_but_still_visible(self):
        """管理员上传 -> 归公司；同时必须还能在自己的前台列表里看到。"""
        self.client.force_login(self.staff)
        self.client.post(reverse('user_center:vector_upload'), {'vector_name': 'pCVa999(Amp)-new'})

        created = Vector.objects.get(vector_name='pCVa999(Amp)-new')
        self.assertIsNone(created.user)
        self.assertFalse(created.is_public)
        self.assertIn('pCVa999(Amp)-new', self._my_vector_names(self.staff))

    def test_customer_upload_is_owned_by_customer(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('user_center:vector_upload'), {'vector_name': 'pCust001'})

        created = Vector.objects.get(vector_name='pCust001')
        self.assertEqual(created.user, self.customer)
        self.assertFalse(created.is_public)

    def test_staff_can_delete_company_vector_from_front_end(self):
        """列表里看得到，操作就得点得动，否则只会报 'Vector not found'。"""
        self.client.force_login(self.staff)
        resp = self.client.post(reverse('user_center:vector_delete'),
                                {'vector_id': self.company_internal.id})
        self.assertEqual(json.loads(resp.content)['status'], 'success')
        self.assertFalse(Vector.objects.filter(id=self.company_internal.id).exists())

    def test_customer_cannot_delete_company_vector(self):
        self.client.force_login(self.customer)
        resp = self.client.post(reverse('user_center:vector_delete'),
                                {'vector_id': self.company_internal.id})
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Vector.objects.filter(id=self.company_internal.id).exists())

    def test_order_page_lists_company_internal_vectors_for_staff(self):
        """替客户下单要能选到代传的载体：内部载体进 Your Vectors，公开的进 RootPath Vectors。"""
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('user_center:order_create'))
        self.assertEqual(resp.status_code, 200)

        own = {v.vector_name for v in resp.context['customer_vectors']}
        company = {v.vector_name for v in resp.context['company_vectors']}
        self.assertIn(self.company_internal.vector_name, own)
        self.assertIn(self.company_public.vector_name, company)
