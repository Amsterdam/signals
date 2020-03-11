import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0098_sig-2193'),
    ]

    operations = [
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('SIG', 'Signal'),
                                                   ('REQ', 'Request'),
                                                   ('QUE', 'Question'),
                                                   ('COM', 'Complaint'),
                                                   ('MAI', 'Maintenance')], default='SIG', max_length=3)),
                ('created_by', models.EmailField(max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('_signal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='types',
                                              to='signals.Signal')),
            ],
            options={
                'verbose_name_plural': 'Types',
                'ordering': ('_signal', '-created_at'),
            },
        ),
    ]
