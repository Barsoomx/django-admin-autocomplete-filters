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
from tests.testapp.models import Book, Collection, Food, Person


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
