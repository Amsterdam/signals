from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('action', models.CharField(choices=[('I', 'Inserted'),
                                                     ('U', 'Updated')], max_length=1)),
                ('when', models.DateTimeField(auto_now_add=True)),
                ('who', models.EmailField(max_length=254, null=True)),
                ('data', django_extensions.db.fields.json.JSONField(default=dict, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING,
                                                   to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'change_log',
                'ordering': ['content_type', 'object_id', '-when'],
                'index_together': {('content_type', 'object_id')},
            },
        ),
    ]
