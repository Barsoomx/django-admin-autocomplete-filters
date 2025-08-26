"""Defines the models for the test app."""

from django.db import models


class Food(models.Model):
    name = models.CharField(max_length=100)

    def __repr__(self) -> str:
        return 'Food#' + str(self.pk)

    def __str__(self) -> str:
        return self.name

    def alternate_name(self) -> str:
        return str(self.name).upper()


class Collection(models.Model):
    name = models.CharField(max_length=100)
    curators = models.ManyToManyField('Person', blank=True)  # type: ignore[var-annotated]

    def __repr__(self) -> str:
        return 'Collection#' + str(self.pk)

    def __str__(self) -> str:
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=100)
    best_friend = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)  # may not be reciprocated
    twin = models.OneToOneField('self', on_delete=models.CASCADE, blank=True, null=True, related_name='rev_twin')
    siblings = models.ManyToManyField('self', blank=True)
    favorite_food = models.ForeignKey(Food, on_delete=models.CASCADE, blank=True, null=True)
    least_favorite_food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='food_is_least_fav',
        related_query_name='people_with_this_least_fav_food',
    )
    # this fails in django 5.0; for those who need it, see https://code.djangoproject.com/ticket/897#comment:51 and https://code.djangoproject.com/ticket/35056
    # i won't be touching it here, because it's such an edge case, hence the type: ignore[attr-defined]
    curated_collections = models.ManyToManyField(Collection, blank=True, db_table=Collection.curators.field.db_table)  # type: ignore[attr-defined]
    favorite_book = models.ForeignKey('Book', on_delete=models.CASCADE, blank=True, null=True, related_name='people_with_this_fav_book')

    def __repr__(self) -> str:
        return 'Person#' + str(self.pk)

    def __str__(self) -> str:
        return self.name


# Use this and curated_collections.db_table to set up reverse M2M
# See https://code.djangoproject.com/ticket/897
# noinspection PyProtectedMember
Person.curated_collections.through._meta.managed = False


class Book(models.Model):
    isbn = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    coll = models.ForeignKey(Collection, on_delete=models.CASCADE, blank=True, null=True)  # just for test purposes

    def __repr__(self) -> str:
        return 'Book#' + str(self.isbn)

    def __str__(self) -> str:
        return self.title


# Showcase models for README/tests
class Member(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


class Device(models.Model):
    slug = models.CharField(max_length=100)
    members = models.ManyToManyField(Member, related_name='devices', blank=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.slug


class PingLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='pings')
    ip = models.CharField(max_length=64, blank=True, default='')

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f'{self.device} {self.ip}'


class Coupon(models.Model):
    code = models.CharField('Code', max_length=64, unique=True, blank=True, db_index=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class BugReport(models.Model):
    title = models.CharField(max_length=1024)
    reward_coupon = models.ForeignKey(Coupon, on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class CouponUser(models.Model):
    coupon = models.ForeignKey(Coupon, related_name='users', on_delete=models.DO_NOTHING)
    user = models.ForeignKey('auth.User', null=True, related_name='coupons', on_delete=models.SET_NULL)
    redeemed_at = models.DateTimeField('Used', auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover
        return f'{self.coupon} -> {self.user}'
