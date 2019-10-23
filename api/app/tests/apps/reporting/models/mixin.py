import copy
import datetime
from unittest import TestCase

from django.core.exceptions import ValidationError as DjangoValidationError
from jsonschema import Draft7Validator as Validator  # update JSON Schema version when possible
from jsonschema.exceptions import ValidationError as JSONValidationError

from signals.apps.reporting.models.mixin import (
    ARBITRARY,
    DAY,
    MONTH,
    SCHEMAS,
    WEEK,
    get_arbitrary_interval,
    get_day_interval,
    get_interval_type,
    get_month_interval,
    get_parameters,
    get_week_interval,
    validate_parameters
)

VALID_WEEK = {
    'isoweek': 40,
    'isoyear': 2019,
    'categories': ['TBD', 'TBD'],
    'areas': ['TBD', 'TBD'],
}

VALID_MONTH = {
    'month': 12,
    'year': 2019,
    'categories': ['TBD', 'TBD'],
    'areas': ['TBD', 'TBD'],
}

VALID_DAY = {
    'day': 31,
    'month': 12,
    'year': 2019,
    'categories': ['TBD', 'TBD'],
    'areas': ['TBD', 'TBD'],
}

VALID_ARBITRARY = {
    'start': 'TBD',
    'end': 'TBD',
    'categories': ['TBD', 'TBD'],
    'areas': ['TBD', 'TBD'],
}

SHOULD_VALIDATE = [VALID_DAY, VALID_WEEK, VALID_MONTH, VALID_ARBITRARY]


class TestSchemas(TestCase):
    def test_validate_schemas(self):
        """Check that our schemas are in fact JSONSchemas."""
        for interval_type, schema in SCHEMAS.items():
            try:
                Validator.check_schema(schema)
            except JSONValidationError:
                msg = f'JSON schema assoctiated with {interval_type} interval is incorrect.'
                self.fail(msg)

    def test_should_validate(self):
        """Check that our data validates given the JSON schemas."""
        self.assertEqual(True, Validator(SCHEMAS[ARBITRARY]).is_valid(VALID_ARBITRARY))
        self.assertEqual(True, Validator(SCHEMAS[DAY]).is_valid(VALID_DAY))
        self.assertEqual(True, Validator(SCHEMAS[MONTH]).is_valid(VALID_MONTH))
        self.assertEqual(True, Validator(SCHEMAS[WEEK]).is_valid(VALID_WEEK))

    def test_should_fail_missing_parameters(self):
        """Missing parameters should cause JSONSchema validation failure."""
        validator = Validator(SCHEMAS[ARBITRARY])
        for required in ['start', 'end']:
            data = copy.deepcopy(VALID_ARBITRARY)
            del data[required]
            self.assertEqual(False, validator.is_valid(data))

        validator = Validator(SCHEMAS[DAY])
        for required in ['day', 'month', 'year']:
            data = copy.deepcopy(VALID_DAY)
            del data[required]
            self.assertEqual(False, validator.is_valid(data))

        validator = Validator(SCHEMAS[MONTH])
        for required in ['month', 'year']:
            data = copy.deepcopy(VALID_MONTH)
            del data[required]
            self.assertEqual(False, validator.is_valid(data))

        validator = Validator(SCHEMAS[WEEK])
        for required in ['isoweek', 'isoyear']:
            data = copy.deepcopy(VALID_WEEK)
            del data[required]
            self.assertEqual(False, validator.is_valid(data))

    def test_should_fail_extra_parameters(self):
        """Extra parameters should cause JSONSchema validation failure."""
        data = copy.deepcopy(VALID_ARBITRARY)
        data['isoweek'] = '21'
        self.assertEqual(False, Validator(SCHEMAS[ARBITRARY]).is_valid(data))

        data = copy.deepcopy(VALID_DAY)
        data['start'] = 'TBD'
        self.assertEqual(False, Validator(SCHEMAS[DAY]).is_valid(data))

        data = copy.deepcopy(VALID_MONTH)
        data['start'] = 'TBD'
        self.assertEqual(False, Validator(SCHEMAS[MONTH]).is_valid(data))

        data = copy.deepcopy(VALID_WEEK)
        data['start'] = 'TBD'
        self.assertEqual(False, Validator(SCHEMAS[WEEK]).is_valid(data))


class TestParameterDerivation(TestCase):
    def test_get_arbitrary_interval(self):
        # support is not yet implemented
        with self.assertRaises(NotImplementedError):
            get_arbitrary_interval(VALID_ARBITRARY)

    def test_get_week_interval(self):
        """Check parameter handling for weekly intervals"""
        midnight = datetime.datetime.min.time()

        valid_data = {'isoweek': 40, 'isoyear': 2019}
        t_begin, t_end = get_week_interval(valid_data)

        self.assertEqual(t_begin, datetime.datetime.combine(datetime.date(2019, 9, 30), midnight))
        self.assertEqual(t_end, datetime.datetime.combine(datetime.date(2019, 10, 7), midnight))

        invalid_data = {'isoweek': 60, 'isoyear': 2019}
        with self.assertRaises(DjangoValidationError):
            get_week_interval(invalid_data)

    def test_get_month_interval(self):
        """Check parameter handling for weekly intervals"""
        midnight = datetime.datetime.min.time()

        valid_data = {'year': 2019, 'month': 12}
        t_begin, t_end = get_month_interval(valid_data)

        self.assertEqual(t_begin, datetime.datetime.combine(datetime.date(2019, 12, 1), midnight))
        self.assertEqual(t_end, datetime.datetime.combine(datetime.date(2020, 1, 1), midnight))

        invalid_data = {'year': 2019, 'month': 13}
        with self.assertRaises(DjangoValidationError):
            get_week_interval(invalid_data)

    def test_get_day_interval(self):
        # support is not yet implemented
        with self.assertRaises(NotImplementedError):
            get_day_interval(VALID_DAY)

    def test_get_categories(self):
        pass  # support is not yet implemented

    def test_get_areas(self):
        pass  # support is not yet implemented

    def test_get_interval_type(self):
        """Check that using the schemas the correct interval is identified."""
        self.assertEqual(get_interval_type(VALID_ARBITRARY), ARBITRARY)
        self.assertEqual(get_interval_type(VALID_DAY), DAY)
        self.assertEqual(get_interval_type(VALID_MONTH), MONTH)
        self.assertEqual(get_interval_type(VALID_WEEK), WEEK)

    def test_get_parameters_interval_derivation(self):
        midnight = datetime.datetime.min.time()

        # As before in test_get_<something>_interval test functions.
        valid_data = {'isoweek': 40, 'isoyear': 2019}
        t_begin, t_end, categories, areas = get_parameters(valid_data)

        self.assertEqual(t_begin, datetime.datetime.combine(datetime.date(2019, 9, 30), midnight))
        self.assertEqual(t_end, datetime.datetime.combine(datetime.date(2019, 10, 7), midnight))

        invalid_data = {'isoweek': 60, 'isoyear': 2019}
        with self.assertRaises(DjangoValidationError):
            get_parameters(invalid_data)

        # --
        midnight = datetime.datetime.min.time()

        valid_data = {'year': 2019, 'month': 12}
        t_begin, t_end, categories, areas = get_parameters(valid_data)

        self.assertEqual(t_begin, datetime.datetime.combine(datetime.date(2019, 12, 1), midnight))
        self.assertEqual(t_end, datetime.datetime.combine(datetime.date(2020, 1, 1), midnight))

        invalid_data = {'year': 2019, 'month': 13}
        with self.assertRaises(DjangoValidationError):
            get_parameters(invalid_data)

        # -- Check intervals that are to be implemented in future (they raise NotImplementedError)

        valid_data_day = {'day': 31, 'month': 12, 'year': 2019}
        with self.assertRaises(NotImplementedError):
            get_parameters(valid_data_day)

        valid_data_arbitrary = {'start': 'TBD', 'end': 'TBD'}
        with self.assertRaises(NotImplementedError):
            get_parameters(valid_data_arbitrary)

    def test_validate_parameters_raise_django_validation_error(self):
        try:
            validate_parameters(VALID_WEEK)
        except DjangoValidationError:
            self.fail('Field validator fails on valid parameters.')

        invalid_data = copy.deepcopy(VALID_WEEK)
        del invalid_data['isoweek']
        with self.assertRaises(DjangoValidationError):
            validate_parameters(invalid_data)
