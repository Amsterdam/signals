from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0095_SIG-2224_SIG-2234_new_categories'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reporter',
            name='is_anonymized',
        ),
        migrations.AddField(
            model_name='reporter',
            name='email_anonymized',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reporter',
            name='phone_anonymized',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='reporter',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='reporter',
            name='phone',
            field=models.CharField(blank=True, max_length=17, null=True),
        ),
    ]
