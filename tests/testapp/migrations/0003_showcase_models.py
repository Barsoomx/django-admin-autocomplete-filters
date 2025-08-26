"""Add showcase models for nested autocomplete filters."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('testapp', '0002_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=100)),
                ('members', models.ManyToManyField(blank=True, related_name='devices', to='testapp.member')),
            ],
        ),
        migrations.CreateModel(
            name='PingLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(blank=True, default='', max_length=64)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pings', to='testapp.device')),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, blank=True, max_length=64, unique=True, verbose_name='Code')),
            ],
        ),
        migrations.CreateModel(
            name='BugReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1024)),
                (
                    'reward_coupon',
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='testapp.coupon'),
                ),
            ],
        ),
        migrations.CreateModel(
            name='CouponUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('redeemed_at', models.DateTimeField(auto_now_add=True, verbose_name='Used')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='users', to='testapp.coupon')),
                (
                    'user',
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coupons', to='auth.user'),
                ),
            ],
        ),
    ]
