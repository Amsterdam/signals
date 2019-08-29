from django.test import TestCase

from signals.apps.reporting.models import ReportDefinition, ReportIndicator
from signals.apps.reporting.indicators import INDICATOR_ROUTES


class TestReportCreation(TestCase):
    def test_report_creation_all_indicators(self):
        """Test that all indicators can be added to a report."""
        new_report = ReportDefinition(
            name='Standaard wekelijks rapport',
            description='Iedere week de belangrijkste indicatoren',
            interval=ReportDefinition.WEEK,
            category=ReportDefinition.CATEGORY_SUB,
            area=ReportDefinition.AREA_ALL,
        )
        new_report.save()

        for key in INDICATOR_ROUTES.keys():
            ri = ReportIndicator(report=new_report, code=key)
            ri.save()

    def test_creation_and_derivation_simple_report(self):
        """Test that a simple report can be created and indicators derived."""
        new_report = ReportDefinition(
            name='Standaard wekelijks rapport',
            description='Iedere week de belangrijkste indicatoren',
            interval=ReportDefinition.WEEK,
            category=ReportDefinition.CATEGORY_SUB,
            area=ReportDefinition.AREA_ALL,
        )
        new_report.save()

        for key in ['N_MELDING_NIEUW', 'N_MELDING_OPEN']:
            ri = ReportIndicator(report=new_report, code=key)
            ri.save()

        new_report.derive(isoweek=20, isoyear=2019)