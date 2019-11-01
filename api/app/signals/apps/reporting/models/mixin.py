"""
Module with Django model mixin for SIA report parameters.

Reports can be parametrized based on the following:
- an interval (daily, weekly, monthly or arbitrary)
- one or more categories
- one or more areas
"""
import datetime
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError as DjangoValidationError
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

from signals.apps.signals.models import Category

MONTH = 'MONTH'
WEEK = 'WEEK'
DAY = 'DAY'
ARBITRARY = 'ARBITRARY'

# These schemas allow only one type of interval at a time (so no weekly and
# daily interval's parameters are allowed to present at once.)
CATEGORIES_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'main_slug': {'type': 'string'},
            'sub_slug': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'null'},
                ]
            },
        },
        'required': ['main_slug', 'sub_slug'],
        'additionalProperties': False,
    }
}

SCHEMAS = {
    WEEK: {
        'type': 'object',
        'properties': {
            'isoweek': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'isoyear': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'categories': CATEGORIES_SCHEMA,
            'areas': {'type': 'array'},
        },
        'required': ['isoyear', 'isoweek'],
        'additionalProperties': False,
    },
    MONTH: {
        'type': 'object',
        'properties': {
            'year': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'month': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'categories': CATEGORIES_SCHEMA,
            'areas': {'type': 'array'},
        },
        'additionalProperties': False,
        'required': ['year', 'month']
    },
    DAY: {
        'type': 'object',
        'properties': {
            'year': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'month': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'day': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
            'categories': CATEGORIES_SCHEMA,
            'areas': {'type': 'array'},
        },
        'additionalProperties': False,
        'required': ['year', 'month', 'day']
    },
    ARBITRARY: {
        'type': 'object',
        'properties': {
            # TODO: Add date-time format check, for now defer to Python validation.
            'start': {'type': 'string'},
            'end': {'type': 'string'},
            'categories': CATEGORIES_SCHEMA,
            'areas': {'type': 'array'},
        },
        'required': ['start', 'end'],
        'additionalProperties': False,
    },
}


# -- interval validation --

def get_week_interval(value):
    """
    Validate weekly interval parameters.

    Note: Raises Django ValidationError on incorrect data - this function is
    used both for validation and deriving the relevant interval.
    """
    # Data type, and presence checks
    try:
        isoweek = int(value['isoweek'])
        isoyear = int(value['isoyear'])
    except (ValueError, TypeError):
        msg = f'"isoweek" and/or "isoyear" parameters are invalid.'
        raise DjangoValidationError(msg)
    except KeyError:
        raise DjangoValidationError('Missing parameter(s) for weekly interval.')

    # Value checks
    monday = f'{isoyear} {isoweek} 1'
    try:
        begin_date = datetime.datetime.strptime(monday, '%G %V %u').date()
    except ValueError:
        msg = f'isoweek={isoweek} and/or isoyear={isoyear} parameters are invalid.'
        raise DjangoValidationError(msg)

    t_begin = datetime.datetime.combine(begin_date, datetime.datetime.min.time())
    t_end = t_begin + relativedelta(days=7)

    return t_begin, t_end


def get_month_interval(value):
    """
    Validate monthly interval parameters.

    Note: Raises Django ValidationError on incorrect data - this function is
    used both for validation and deriving the relevant interval.
    """
    # Data type, and presence checks
    try:
        month = int(value['month'])
        year = int(value['year'])
    except (ValueError, TypeError):
        msg = f'"month" and/or "year" parameters are invalid.'
        raise DjangoValidationError(msg)
    except KeyError:
        raise DjangoValidationError('Missing parameter(s) for weekly interval.')

    # Value checks
    try:
        first_of_month = datetime.date(year, month, 1)
    except ValueError:
        msg = f'month={month} and/or year={year} parameters are invalid.'
        raise DjangoValidationError(msg)
    first_of_next_month = first_of_month + relativedelta(months=1)

    t_begin = datetime.datetime.combine(first_of_month, datetime.datetime.min.time())
    t_end = datetime.datetime.combine(first_of_next_month, datetime.datetime.min.time())

    return t_begin, t_end


def get_day_interval(value):
    """
    Validate daily interval parameters.

    Note: Raises Django ValidationError on incorrect data - this function is
    used both for validation and deriving the relevant interval.
    """
    raise NotImplementedError('Daily intervals not yet supported')


def get_arbitrary_interval(value):
    """
    Validate arbitrary interval parameters.

    Note: Raises Django ValidationError on incorrect data - this function is
    used both for validation and deriving the relevant interval.
    """
    raise NotImplementedError('Arbitrary interval not yet supported')


def get_interval_type(value):
    """
    Determine intended interval parametrization using JSON Schema.
    """
    # Note: we raise a Django validation error if the data does not match one
    # of interval JSON Schemas.
    for interval_type, schema in SCHEMAS.items():
        try:
            validate(instance=value, schema=schema)
        except JSONSchemaValidationError:
            continue
        else:
            return interval_type
    else:
        msg = 'Export parameters do not match schema.'
        raise DjangoValidationError(msg)


INTERVAL_DERIVATIONS = {
    DAY: get_day_interval,
    WEEK: get_week_interval,
    MONTH: get_month_interval,
    ARBITRARY: get_arbitrary_interval,
}


def _build_category_indexes():
    # Create an dictionary of (main_slug, sub_slug) to category_id, to check
    # whether the requested (main_slug, sub_slug) actually exist in SIA.
    # Do the same for main_slug to sub categories to deal with (main_slug, '*').

    # Note: Assumes number of Categories is small, and can be loaded into
    # memory at once.
    all_categories = list(Category.objects.all())
    id_to_category = {cat.id: cat for cat in all_categories}

    slugs_to_category_id = {}
    main_slug_to_category_ids = defaultdict(set)

    for cat in all_categories:
        if cat.parent_id is None:
            slugs_to_category_id[(cat.slug, None)] = cat.id  # for (main_slug, None)
        else:
            main_cat = id_to_category[cat.parent_id]
            slugs_to_category_id[(main_cat.slug, cat.slug)] = cat.id  # for (main_slug, sub_slug)
            main_slug_to_category_ids[main_cat.slug].add(cat.id)  # for (main_slug, '*')

    return id_to_category, slugs_to_category_id, main_slug_to_category_ids


def get_categories(value):
    """
    Get a Category queryset for requested categories parameter.
    """
    if 'categories' not in value:
        return Category.objects.all()

    # Build indexes to check (main_slug, sub_slug) pairs against
    id_to_category, slugs_to_category_id, main_slug_to_category_ids = _build_category_indexes()

    # We want to return a queryset of matching categories, we do so with a
    # id__in ORM query. Loop below checks all requested (main_slug, sub_slug)
    # pairs for validity even if it starts with ('*', '*').
    matching_category_ids = set()
    for entry in value['categories']:
        main_slug = entry['main_slug']
        sub_slug = entry['sub_slug']

        if main_slug == '*' and sub_slug == '*':
            matching_category_ids |= set(id_to_category.keys())
        elif main_slug != '*' and sub_slug == '*':
            ids = main_slug_to_category_ids.get(main_slug, None)
            if ids is None:
                msg = f"No matching categories for ({main_slug}, '*')."
                raise DjangoValidationError(msg)
            matching_category_ids |= ids
        else:
            _id = slugs_to_category_id.get((main_slug, sub_slug), None)
            if _id is None:
                msg = f'No matching categories for ({main_slug}, {sub_slug}).'
                raise DjangoValidationError(msg)
            matching_category_ids.add(_id)

    # Return a queryset of matching IDs (so that filtering for allowed
    # categories is easy down the line).
    for x in matching_category_ids:
        assert type(x) == int
    return Category.objects.filter(id__in=matching_category_ids)


def get_parameters(value):
    """
    Derive export parameters. Raises Django ValidationError on invalid inputs.

    Note: is used to validate export parameters, hence the use of Django
    ValidationErrors.
    """
    # Make sure that schemas and derivation functions match:
    assert not set(SCHEMAS.keys()) - set(INTERVAL_DERIVATIONS.keys())

    # Validate JSONSchema and determine which interval type we have.
    # Note get_interval_type may raise a Django ValidationError.
    interval_type = get_interval_type(value)

    # Validate precise inputs per type of interval, derive interval.
    # Note get_interval_type may raise a Django ValidationError.
    t_begin, t_end = INTERVAL_DERIVATIONS[interval_type](value)

    # Note: support for categories and areas is not yet implemented. Hence the
    # empty queryset for Category and empty list for the, as yet un-implemented,
    # areas. Excpectation is that the latter will be a Django model as well.
    categories = get_categories(value)
    areas = []
    return t_begin, t_end, categories, areas


def validate_parameters(value):
    """
    Validate given export parameters.

    Note: internally calls the parameter derivation function and ignores its
    return value.
    """
    get_parameters(value)


class ExportParametersMixin(models.Model):
    """
    Model mixin for SIA data export and report parameters.
    """
    class Meta:
        abstract = True

    export_parameters = JSONField(validators=[validate_parameters])

    def get_parameters(self):
        """
        Derive export parameters t_begin, t_end, categories, areas.
        """
        return get_parameters(self.report_params)
