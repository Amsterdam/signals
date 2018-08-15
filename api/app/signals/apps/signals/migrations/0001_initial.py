# Generated by Django 2.0.7 on 2018-07-19 12:40

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Buurt',
            fields=[
                ('ogc_fid', models.IntegerField(primary_key=True, serialize=False)),
                ('id', models.CharField(max_length=14)),
                ('vollcode', models.CharField(max_length=4)),
                ('naam', models.CharField(max_length=40)),
            ],
            options={
                'db_table': 'buurt_simple',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False,
                                        verbose_name='ID')),
                ('main', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('sub', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('department', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('priority', models.IntegerField(null=True)),
                ('ml_priority', models.IntegerField(null=True)),
                ('ml_cat', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('ml_prob', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('ml_cat_all', django.contrib.postgres.fields.ArrayField(
                    base_field=models.TextField(blank=True, max_length=50), null=True, size=None)),
                ('ml_cat_all_prob', django.contrib.postgres.fields.ArrayField(
                    base_field=models.IntegerField(), null=True, size=None)),
                ('ml_sub_cat', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('ml_sub_prob', models.CharField(blank=True, default='', max_length=500,
                                                 null=True)),
                ('ml_sub_all', django.contrib.postgres.fields.ArrayField(
                    base_field=models.TextField(blank=True, max_length=50), null=True, size=None)),
                ('ml_sub_all_prob', django.contrib.postgres.fields.ArrayField(
                    base_field=models.IntegerField(), null=True, size=None)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('extra_properties', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False,
                                        verbose_name='ID')),
                ('geometrie', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('stadsdeel', models.CharField(choices=[
                    ('A', 'Centrum'),
                    ('B', 'Westpoort'),
                    ('E', 'West'),
                    ('M', 'Oost'),
                    ('N', 'Noord'),
                    ('T', 'Zuidoost'),
                    ('K', 'Zuid'),
                    ('F', 'Nieuw-West')],
                    max_length=1, null=True)),
                ('buurt_code', models.CharField(max_length=4, null=True)),
                ('address', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('address_text', models.CharField(editable=False, max_length=256, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('extra_properties', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Reporter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False,
                                        verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=17)),
                ('remove_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('extra_properties', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False,
                                        verbose_name='ID')),
                ('signal_id', models.UUIDField(db_index=True, default=uuid.uuid4)),
                ('source', models.CharField(default='public-api', max_length=128)),
                ('text', models.CharField(max_length=1000)),
                ('text_extra', models.CharField(blank=True, default='', max_length=1000)),
                ('incident_date_start', models.DateTimeField()),
                ('incident_date_end', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('operational_date', models.DateTimeField(null=True)),
                ('expire_date', models.DateTimeField(null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/%Y/%m/%d/')),
                ('upload', django.contrib.postgres.fields.ArrayField(
                    base_field=models.FileField(upload_to='uploads/%Y/%m/%d/'),
                    null=True,
                    size=None)),
                ('extra_properties', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('category', models.OneToOneField(null=True,
                                                  on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='signal',
                                                  to='signals.Category')),
                ('location', models.OneToOneField(null=True,
                                                  on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='signal',
                                                  to='signals.Location')),
                ('reporter', models.OneToOneField(null=True,
                                                  on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='signal',
                                                  to='signals.Reporter')),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False,
                                        verbose_name='ID')),
                ('text', models.CharField(default='', max_length=1000)),
                ('user', models.EmailField(max_length=254, null=True)),
                ('target_api', models.CharField(default='', max_length=250)),
                ('state', models.CharField(blank=True, choices=[
                    ('m', 'Gemeld'),
                    ('i', 'In afwachting van behandeling'),
                    ('b', 'In behandeling'),
                    ('o', 'Afgehandeld'),
                    ('h', 'On hold'),
                    ('a', 'Geannuleerd')
                ], default='m', help_text='Melding status', max_length=1)),
                ('extern', models.BooleanField(default=False,
                                               help_text='Wel of niet status extern weergeven')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('extra_properties', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('_signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='states',
                                              to='signals.Signal')),
            ],
            options={
                'verbose_name_plural': 'States',
                'get_latest_by': 'datetime',
            },
        ),
        migrations.AddField(
            model_name='signal',
            name='status',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                       related_name='signal', to='signals.Status'),
        ),
        migrations.AddField(
            model_name='reporter',
            name='_signal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='reporters', to='signals.Signal'),
        ),
        migrations.AddField(
            model_name='location',
            name='_signal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='signals', to='signals.Signal'),
        ),
        migrations.AddField(
            model_name='category',
            name='_signal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    related_name='categories', to='signals.Signal'),
        ),
    ]
