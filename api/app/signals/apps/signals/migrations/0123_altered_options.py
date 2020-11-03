from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0122_SLA_HISTORY'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='area',
            options={'ordering': ['_type', 'code'], 'verbose_name': 'Gebied', 'verbose_name_plural': 'Gebieden'},
        ),
        migrations.AlterModelOptions(
            name='areatype',
            options={'ordering': ['code'], 'verbose_name': 'Gebiedstype', 'verbose_name_plural': 'Gebiedstypen'},
        ),
        migrations.AlterModelOptions(
            name='expression',
            options={
                'ordering': ['pk'],
                'permissions': (
                    ('sia_expression_read', 'Inzien van expressies'),
                    ('sia_expression_write', 'Wijzigen van expressies')
                ),
                'verbose_name': 'Expression'
            },
        ),
        migrations.AlterModelOptions(
            name='expressioncontext',
            options={'verbose_name': 'ExpressionContext'},
        ),
        migrations.AlterModelOptions(
            name='expressiontype',
            options={'verbose_name': 'ExpressionsType'},
        ),
    ]
