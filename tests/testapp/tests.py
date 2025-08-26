"""Define tests for the test app."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

from django.contrib.admin.utils import flatten
from django.contrib.auth.models import User
from django.core import exceptions
from django.test import TestCase, tag
from django.urls import reverse

from admin_auto_filters import filters
from tests.testapp.admin import BASIC_USERNAME, SHORTCUT_USERNAME
from tests.testapp.models import Book, BugReport, Collection, Coupon, CouponUser, Device, Food, Member, Person, PingLog


def name(model: Any) -> str:
    """A repeatable way to get the formatted model name."""
    return model.__name__.replace('_', '').lower()


# a all of the models, and their names for convenience
MODELS = (Food, Collection, Person, Book)
MODEL_NAMES = tuple([name(model) for model in MODELS])


# a tuple of tuples with (model_name, key, val, field, pks)
# this must match data in fixture
FILTER_STRINGS = (
    (Food, 'person', '3', 'id', (3,)),
    (Food, 'people_with_this_least_fav_food', '3', 'id', (2,)),
    (Collection, 'curators', '1', 'id', (1,)),
    (Collection, 'curators', '3', 'id', ()),
    (Collection, 'book', '2357', 'id', (2,)),
    (Person, 'best_friend', '1', 'id', (2, 3)),
    (Person, 'twin', '1', 'id', (3,)),
    (Person, 'rev_twin', '3', 'id', (1,)),
    (Person, 'best_friend__best_friend', '1', 'id', (4,)),
    (Person, 'best_friend__favorite_food', '1', 'id', (4,)),
    (Person, 'siblings', '2', 'id', (1, 3, 4)),
    (Person, 'favorite_food', '3', 'id', (3, 4)),
    (Person, 'person', '3', 'id', (1,)),
    (Person, 'book', '1111', 'id', (4,)),
    (Person, 'person__favorite_food', '3', 'id', (1, 2)),
    (Person, 'collection', '1', 'id', (1, 2)),
    (Book, 'author', '2', 'isbn', (42,)),
    (Book, 'coll', '2', 'isbn', (2357,)),
    (Book, 'people_with_this_fav_book', '4', 'isbn', (1234,)),
)


class RootTestCase:
    # fixtures = ['fixture.json']  # loading from data migration 0002

    @classmethod
    def setUpTestData(cls) -> None:
        cls.basic_user = User.objects.get(username=BASIC_USERNAME)
        cls.shortcut_user = User.objects.get(username=SHORTCUT_USERNAME)

    def test_endpoint(self) -> None:
        """
        Test that custom autocomplete endpoint functions and returns proper values.
        """
        url = reverse('admin:foods_that_are_favorites')
        # Django 4.2+ AutocompleteJsonView expects app_label/model_name/field_name
        query_params = {
            'app_label': Person._meta.app_label,
            'model_name': Person._meta.model_name,
            'field_name': 'favorite_food',  # FK from Person -> Food
        }
        response = self.client.get(url + '?' + urlencode(query_params), follow=False)
        self.assertEqual(response.status_code, 200, msg=str(url))
        data = json.loads(response.content)
        texts = {item['text'] for item in data['results']}
        self.assertEqual(len(texts), 2, msg=str(texts))
        self.assertIn('SPAM', texts, msg=str(texts))
        self.assertIn('TOAST', texts, msg=str(texts))

    def test_admin_changelist_search(self) -> None:
        """
        Test that the admin changelist page loads with a search query, at a basic level.
        Need selenium tests to fully check.
        """
        for model_name in MODEL_NAMES:
            with self.subTest(model_name=model_name):
                url = reverse(f'admin:testapp_{model_name}_changelist') + '?q=a'
                response = self.client.get(url, follow=False)
                self.assertContains(
                    response,
                    '/static/custom.css',
                    html=False,
                    msg_prefix=str(url),
                )

    def test_admin_autocomplete_load_32_plus(self) -> None:
        """
        Test that the admin autocomplete endpoint loads on Django >= 3.2.
        """
        model_field_name = [
            # (Food, 'person'),
            (Collection, 'curators'),
            (Person, 'best_friend'),
            (Person, 'twin'),
            (Person, 'siblings'),
            (Person, 'favorite_food'),
            (Book, 'author'),
            (Book, 'coll'),
        ]
        for model, field_name in model_field_name:
            with self.subTest(model_name=model.__name__, field_name=field_name):
                url = reverse('admin:autocomplete')
                query_params = {
                    'app_label': model._meta.app_label,
                    'model_name': model._meta.model_name,
                    'field_name': field_name,
                }
                url = url + '?' + urlencode(query_params)
                response = self.client.get(url, follow=False)
                self.assertContains(response, '"results"')

    def test_admin_changelist_filters(self) -> None:
        """
        Test that the admin changelist page loads with filters applied, at a basic level.
        Need selenium tests to fully check.
        """
        for model, key, val, field, pks in FILTER_STRINGS:
            model_name = name(model)
            with self.subTest(model_name=model_name, key=key, val=val, field=field):
                url = reverse(f'admin:testapp_{model_name}_changelist') + f'?{key}={val}'
                response = self.client.get(url, follow=False)
                # print(response.content.decode('utf-8'))
                self.assertEqual(response.status_code, 200, msg=str(url))
                all_pks = set(flatten(list(model.objects.values_list('pk'))))
                for pk in pks:
                    self.assertContains(
                        response,
                        f'<td class="field-{field}">{pk}</td>',
                        html=True,
                        msg_prefix=str(url),
                    )
                for pk in all_pks - set(pks):
                    self.assertNotContains(
                        response,
                        f'<td class="field-{field}">{pk}</td>',
                        html=True,
                        msg_prefix=str(url),
                    )

    def test_get_queryset_for_field(self) -> None:
        """
        Test the AutocompleteFilter.get_queryset_for_field method.
        """

        class TestFilter(filters.AutocompleteFilter):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

        f = TestFilter()
        self.assertRaises(exceptions.FieldDoesNotExist, f.get_queryset_for_field, Person, 'not_a_field')
        self.assertRaises(AttributeError, f.get_queryset_for_field, Person, 'name')
        for field in ('best_friend', 'siblings', 'favorite_food', 'curated_collections', 'favorite_book', 'book'):
            with self.subTest(field=field):
                try:
                    _ = f.get_queryset_for_field(Person, field)
                except BaseException as e:
                    self.fail(str(e))
        try:
            _ = f.get_queryset_for_field(Book, 'people_with_this_fav_book')
        except BaseException as e:
            self.fail(str(e))

    def test_admin_autocomplete_custom_url_is_registered(self) -> None:
        """
        Ensure our app registers admin:admin-autocomplete automatically via AppConfig.ready().
        The endpoint should behave like the built-in admin:autocomplete and return JSON.
        """
        # Pick a known model/field pair present in admin autocomplete
        model, field_name = (Person, 'best_friend')
        url = reverse('admin:admin-autocomplete')
        query_params = {
            'app_label': model._meta.app_label,
            'model_name': model._meta.model_name,
            'field_name': field_name,
        }
        response = self.client.get(url + '?' + urlencode(query_params), follow=False)
        self.assertEqual(response.status_code, 200, msg=str(url))
        self.assertIn('"results"', response.content.decode('utf-8'))


@tag('basic')
class BasicTestCase(RootTestCase, TestCase):
    def setUp(self) -> None:
        self.client.force_login(self.basic_user)


@tag('shortcut')
class ShortcutTestCase(RootTestCase, TestCase):
    def setUp(self) -> None:
        self.client.force_login(self.shortcut_user)


class ShowcaseTests(TestCase):
    """Tests for README showcase models/filters."""

    @classmethod
    def setUpTestData(cls) -> None:
        # Auth users from fixture: bu(1), su(2) already exist.
        # Members/Devices/PingLogs
        cls.m1 = Member.objects.create(name='Alice')
        cls.m2 = Member.objects.create(name='Bob')
        cls.d1 = Device.objects.create(slug='router-1')
        cls.d2 = Device.objects.create(slug='router-2')
        cls.d1.members.add(cls.m1)
        cls.d2.members.add(cls.m2)
        cls.p1 = PingLog.objects.create(device=cls.d1, ip='10.0.0.1')
        cls.p2 = PingLog.objects.create(device=cls.d2, ip='10.0.0.2')

        # Coupons/BugReports/CouponUser
        cls.c1 = Coupon.objects.create(code='AAA111')
        cls.c2 = Coupon.objects.create(code='BBB222')
        cls.b1 = BugReport.objects.create(title='XSS', reward_coupon=cls.c1)
        cls.b2 = BugReport.objects.create(title='SQLi', reward_coupon=None)
        # Assign coupon to auth user 1 (bu)
        CouponUser.objects.create(coupon=cls.c1, user_id=1)

    def setUp(self) -> None:
        # Use a superuser from fixtures
        from django.contrib.auth.models import User

        self.client.force_login(User.objects.get(pk=1))

    def test_pinglog_filter_by_member_nested(self) -> None:
        url = reverse('admin:testapp_pinglog_changelist') + f'?device__members={self.m1.pk}'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('router-1', content)
        self.assertNotIn('router-2', content)

    def test_member_filter_by_devices_reverse_m2m(self) -> None:
        url = reverse('admin:testapp_member_changelist') + f'?devices={self.d2.pk}'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Bob', content)
        self.assertNotIn('Alice', content)

    def test_coupon_filter_by_users_through_model(self) -> None:
        # Filter coupons by users who redeemed them via CouponUser (users__user)
        url = reverse('admin:testapp_coupon_changelist') + '?users__user=1'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('AAA111', content)
        self.assertNotIn('BBB222', content)

    def test_coupon_filter_by_bugreport_reverse_fk(self) -> None:
        # Filter coupons by bug reports that rewarded them (reverse FK: bugreport)
        url = reverse('admin:testapp_coupon_changelist') + f'?bugreport={self.b1.pk}'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('AAA111', content)
        self.assertNotIn('BBB222', content)

    def test_admin_autocomplete_device_members(self) -> None:
        """Our admin-autocomplete should return Member results for Device.members."""
        url = reverse('admin:admin-autocomplete')
        params = {
            'app_label': Device._meta.app_label,
            'model_name': Device._meta.model_name,
            'field_name': 'members',
        }
        response = self.client.get(url + '?' + urlencode(params), follow=False)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        texts = {item['text'] for item in data['results']}
        self.assertIn('Alice', texts)
        self.assertIn('Bob', texts)

    def test_admin_autocomplete_coupon_users_user(self) -> None:
        """Our admin-autocomplete should return auth users via CouponUser.user relation."""
        url = reverse('admin:admin-autocomplete')
        params = {
            'app_label': 'testapp',
            'model_name': 'couponuser',
            'field_name': 'user',
        }
        response = self.client.get(url + '?' + urlencode(params), follow=False)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        texts = {item['text'] for item in data['results']}
        self.assertIn('bu', texts)
        self.assertIn('su', texts)

    def test_admin_autocomplete_coupon_bugreport_reverse(self) -> None:
        """Our admin-autocomplete should return BugReport via Coupon.bugreport reverse FK."""
        url = reverse('admin:admin-autocomplete')
        params = {
            'app_label': Coupon._meta.app_label,
            'model_name': Coupon._meta.model_name,
            'field_name': 'bugreport',
        }
        response = self.client.get(url + '?' + urlencode(params), follow=False)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        texts = {item['text'] for item in data['results']}
        self.assertIn('XSS', texts)
        self.assertIn('SQLi', texts)
