from django.db import migrations


def _SIG_2192(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')

    permissions_to_change = (
        ('sia_can_view_all_categories', 'Bekijk all categorieën (overschrijft categorie rechten van afdeling)'),  # noqa
        ('sia_category_read', 'Inzien van categorieën'),
        ('sia_category_write', 'Wijzigen van categorieën'),
        ('sia_department_read', 'Inzien van afdeling instellingen'),
        ('sia_department_write', 'Wijzigen van afdeling instellingen'),
        ('sia_read', 'Leesrechten algemeen'),
        ('sia_write', 'Schrijfrechten algemeen'),
        ('sia_split', 'Splitsen van een melding'),
        ('sia_signal_create_initial', 'Melding aanmaken'),
        ('sia_signal_create_note', 'Notitie toevoegen bij een melding'),
        ('sia_signal_change_status', 'Wijzigen van status van een melding'),
        ('sia_signal_change_category', 'Wijzigen van categorie van een melding'),
        ('sia_signal_export', 'Meldingen exporteren'),
        ('sia_signal_report', 'Rapportage beheren'),
        ('push_to_sigmax', 'Doorsturen van een melding (THOR)'),
        ('sia_statusmessagetemplate_write', 'Wijzingen van standaardteksten'),
    )

    for codename, name in permissions_to_change:
        try:
            permission = Permission.objects.get(codename=codename)
            permission.name = name
            permission.save()
        except Permission.DoesNotExist:
            # Test suite fails if we do not catch these exceptions
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0103_category_changes_sig-2456'),
    ]

    operations = [
        migrations.RunPython(_SIG_2192, None),  # No reverse possible
        # migrations.AlterModelOptions(
        #     name='category',
        #     options={
        #         'ordering': (
        #             'name',
        #         ),
        #         'permissions': (
        #             ('sia_can_view_all_categories', 'Bekijk all categorieën (overschrijft categorie rechten van afdeling)'),  # noqa
        #             ('sia_category_read', 'Inzien van categorieën'),
        #             ('sia_category_write', 'Wijzigen van categorieën')
        #         ),
        #         'verbose_name_plural': 'Categories'
        #     },
        # ),
        # migrations.AlterModelOptions(
        #     name='department',
        #     options={
        #         'ordering': (
        #             'name',
        #         ),
        #         'permissions': (
        #             ('sia_department_read', 'Inzien van afdeling instellingen'),
        #             ('sia_department_write', 'Wijzigen van afdeling instellingen')
        #         )
        #     },
        # ),
        # migrations.AlterModelOptions(
        #     name='signal',
        #     options={
        #         'ordering': (
        #             'created_at',
        #         ),
        #         'permissions': (
        #             ('sia_read', 'Leesrechten algemeen'),
        #             ('sia_write', 'Schrijfrechten algemeen'),
        #             ('sia_split', 'Splitsen van een melding'),
        #             ('sia_signal_create_initial', 'Melding aanmaken'),
        #             ('sia_signal_create_note', 'Notitie toevoegen bij een melding'),
        #             ('sia_signal_change_status', 'Wijzigen van status van een melding'),
        #             ('sia_signal_change_category', 'Wijzigen van categorie van een melding'),
        #             ('sia_signal_export', 'Meldingen exporteren'),
        #             ('sia_signal_report', 'Rapportage beheren')
        #         )
        #     },
        # ),
        # migrations.AlterModelOptions(
        #     name='status',
        #     options={
        #         'get_latest_by': 'datetime',
        #         'ordering': (
        #             'created_at',
        #         ),
        #         'permissions': (
        #             ('push_to_sigmax', 'Doorsturen van een melding (THOR)'),
        #         ),
        #         'verbose_name_plural': 'Statuses'
        #     },
        # ),
        # migrations.AlterModelOptions(
        #     name='statusmessagetemplate',
        #     options={
        #         'ordering': (
        #             'category',
        #             'state',
        #             'order'
        #         ),
        #         'permissions': (
        #             ('sia_statusmessagetemplate_write', 'Wijzingen van standaardteksten'),
        #         ),
        #         'verbose_name': 'Standaard afmeldtekst',
        #         'verbose_name_plural': 'Standaard afmeldteksten'
        #     },
        # ),
    ]
