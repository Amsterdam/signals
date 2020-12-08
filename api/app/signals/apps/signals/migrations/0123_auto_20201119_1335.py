from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0122_SLA_HISTORY'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expression',
            options={'permissions': (('sia_expression_read', 'Inzien van expressies'),
                                     ('sia_expression_write', 'Wijzigen van expressies')),
                     'verbose_name': 'Expression'},
        ),
        migrations.AlterModelOptions(
            name='expressioncontext',
            options={'verbose_name': 'ExpressionContext'},
        ),
        migrations.AlterModelOptions(
            name='expressiontype',
            options={'verbose_name': 'ExpressionsType'},
        ),
        migrations.AlterModelOptions(
            name='servicelevelobjective',
            options={'ordering': ('category', '-created_at')},
        ),
    ]
