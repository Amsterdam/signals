# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
from django.core.management import BaseCommand

from signals.apps.signals.factories import CategoryFactory, ParentCategoryFactory


class Command(BaseCommand):
    default_to_create = 1
    min_to_create = 1
    max_to_create = 10

    def add_arguments(self, parser):
        parser.add_argument('--parent-slug', type=int, help='If given the child elements will be created for this '
                                                            'Parent. If used this will overrule the option'
                                                            '--parents-to-create')
        parser.add_argument('--parents-to-create', type=int, help='Total random parent Categories to create '
                                                                  f'(max {self.max_to_create}). '
                                                                  f'Default {self.default_to_create}.')
        parser.add_argument('--children-to-create', type=int, help='Total random child Categories per parent Category '
                                                                   f'to create (max {self.max_to_create}). '
                                                                   f'Default {self.default_to_create} per parent '
                                                                   'Category.')

    def handle(self, *args, **options):
        parent_slug = options.get('parent_slug', False)
        if parent_slug:
            parents_to_create = 1
            parent_options = {'slug': parent_slug, }
        else:
            parents_to_create = int(options['parents_to_create'] or self.default_to_create)
            parent_options = {}
        children_to_create = int(options['children_to_create'] or self.default_to_create)

        if not self.min_to_create <= parents_to_create <= self.max_to_create:
            self.stderr.write(f'The parents to create option must be an integer from {self.min_to_create} to '
                              f'{self.max_to_create}, {parents_to_create} given')
            return

        if not self.min_to_create <= children_to_create <= self.max_to_create:
            self.stderr.write(f'The children to create option must be an integer from {self.min_to_create} to '
                              f'{self.max_to_create}, {children_to_create} given')
            return

        parents = ParentCategoryFactory.create_batch(parents_to_create, **parent_options)
        for parent in parents:
            CategoryFactory.create_batch(children_to_create, parent=parent)
