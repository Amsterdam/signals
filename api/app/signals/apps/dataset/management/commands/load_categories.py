# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
import json

from django.core.management import BaseCommand

from signals.apps.signals.models import Category


class Command(BaseCommand):
    data = None
    slugsdict = {}

    def _init_slugs_dict(self) -> None:
        if self.data is not None:
            for cat in self.data:
                self.slugsdict[cat['pk']] = cat['fields']['slug']

    def _get_parent(self, id) -> Category:
        if id in self.slugsdict:
            return self._get_cat(slug=self.slugsdict[id], parent=None)
        else:
            return None

    def _get_cat(self, slug, parent) -> Category:
        try:
            return Category.objects.get(slug=slug, parent=parent)
        except Exception as e:
            print("Failed get cat {cat} - {parent}: {err}".format(cat=slug, parent=parent, err=str(e)))
            return None

    def add_arguments(self, parser) -> None:
        parser.add_argument('data_file', type=str)

    def handle(self, *args, **options) -> None:
        self.processed_cats = set()
        with open(options['data_file']) as f:
            self.data = json.load(f)
        if self.data is not None:
            self._init_slugs_dict()
            self.stdout.write(f'Total Categories: {len(self.data)}')
            for c in self.data:
                fields = c['fields']
                parent_id = fields.pop('parent')
                if parent_id:
                    fields['parent'] = self._get_parent(parent_id)
                cat = self._get_cat(fields['slug'], fields.get('parent', None))
                if cat is not None:
                    self.stdout.write(f'Updating: {fields["slug"]}')
                    for attr, value in fields.items():
                        if hasattr(cat, attr):
                            setattr(cat, attr, value)
                    cat.save()
                else:
                    # create cat
                    cat = Category.objects.create(**fields)
                self.processed_cats.add(cat.pk)

            # set non processed cats to inactive
            inactive_cats = Category.objects.exclude(id__in=self.processed_cats).filter(is_active=True)
            self.stdout.write(f'\nInactive categories {len(inactive_cats)}')
            inactive_cats.update(**{'is_active': False})
            active_cats = Category.objects.filter(is_active=True)
            self.stdout.write(f'\nActive categories {len(active_cats)}')
            self.stdout.write('\nDone!')
