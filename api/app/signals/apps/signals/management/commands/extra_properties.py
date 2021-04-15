# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import json
import os
from timeit import default_timer as timer

from django.core.management import BaseCommand
from jsonschema import ValidationError, validate

from signals.apps.signals.models import CategoryAssignment, Signal

lookup_dict = {
    "extra_afval": {
        "category_url": "/signals/v1/public/terms/categories/afval"
    },
    "extra_auto_scooter_bromfietswrak": {
        "category_url": "/signals/v1/public/terms/categories/overlast-in-de-openbare-ruimte/sub_categories/auto-scooter-bromfietswrak"  # noqa
    },
    "extra_bedrijven_horeca_adres": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_caution": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_installaties": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-installaties"  # noqa
    },
    "extra_bedrijven_horeca_muziek_direct_naast": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_evenement": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_evenement_einde": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_caution": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_installaties": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-installaties"  # noqa
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_ja": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_ja_nietnu": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_muziek": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_nee": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_muziek_geluidmeting_overige": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/overig-horecabedrijven"  # noqa
    },
    "extra_bedrijven_horeca_muziek_ramen_dicht": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_ramen_dicht_onderneming": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_muziek_ramen_dicht_onderneming_lang": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/geluidsoverlast-muziek"  # noqa
    },
    "extra_bedrijven_horeca_naam": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_personen": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/overlast-door-bezoekers-niet-op-terras"  # noqa
    },
    "extra_bedrijven_horeca_stank": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/stankoverlast"
    },
    "extra_bedrijven_horeca_stank_oorzaak": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/stankoverlast"
    },
    "extra_bedrijven_horeca_stank_ramen": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/stankoverlast"
    },
    "extra_bedrijven_horeca_stank_weer": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/stankoverlast"
    },
    "extra_bedrijven_horeca_terrassen": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca/sub_categories/overlast-terrassen"  # noqa
    },
    "extra_bedrijven_horeca_tijdstippen": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_vaker": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_bedrijven_horeca_wat": {
        "category_url": "/signals/v1/public/terms/categories/overlast-bedrijven-en-horeca"
    },
    "extra_boten_geluid_meer": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-geluid"  # noqa
    },
    "extra_boten_gezonken_meer": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-gezonken-boot"  # noqa
    },
    "extra_boten_snelheid_meer": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen"  # noqa
    },
    "extra_boten_snelheid_naamboot": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen"  # noqa
    },
    "extra_boten_snelheid_rederij": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen"  # noqa
    },
    "extra_boten_snelheid_rondvaartboot": {
        "category_url": "/signals/v1/public/terms/categories/overlast-op-het-water/sub_categories/overlast-op-het-water-snel-varen"  # noqa
    },
    "extra_brug": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/brug"
    },
    "extra_container_kind": {
        "category_url": "/signals/v1/public/terms/categories/afval"
    },
    "extra_container_number": {
        "category_url": "/signals/v1/public/terms/categories/afval"
    },
    "extra_dieren_text": {
        "category_url": "/signals/v1/public/terms/categories/overlast-van-dieren"
    },
    "extra_fietsrek_aanvraag": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/fietsrek-nietje"  # noqa
    },
    "extra_fietsrek_aanvragen": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/fietsrek-nietje"  # noqa
    },
    "extra_fietswrak": {
        "category_url": "/signals/v1/public/terms/categories/overlast-in-de-openbare-ruimte/sub_categories/fietswrak"
    },
    "extra_kerstverlichting": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair"
    },
    "extra_klok": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_klok_gevaar": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_klok_niet_op_kaart": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_klok_niet_op_kaart_nummer": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_klok_nummer": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_klok_probleem": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/klok"
    },
    "extra_onderhoud_stoep_straat_en_fietspad": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair"
    },
    "extra_parkeeroverlast": {
        "category_url": "/signals/v1/public/terms/categories/overlast-in-de-openbare-ruimte/sub_categories/parkeeroverlast"  # noqa
    },
    "extra_straatverlichting": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_gevaar": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_niet_op_kaart": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_niet_op_kaart_nummer": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_nummer": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_probleem": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_straatverlichting_hoeveel": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/lantaarnpaal-straatverlichting"  # noqa
    },
    "extra_verkeerslicht": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_gevaar": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_nummer": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_probleem_bus_tram": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_probleem_fiets_auto": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_probleem_voetganger": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_rijrichting": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_verkeerslicht_welk": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/verkeerslicht"
    },
    "extra_wegen_gladheid": {
        "category_url": "/signals/v1/public/terms/categories/wegen-verkeer-straatmeubilair/sub_categories/gladheid"
    },
    "extra_wonen_leegstand_activiteit_in_woning": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_leegstand_iemand_aanwezig": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_leegstand_naam_eigenaar": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_leegstand_naam_persoon": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_leegstand_periode": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_leegstand_woning_gebruik": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_aantal_personen": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_adres_huurder": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_bewoners_familie": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_huurder_woont": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_iemand_aanwezig": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_naam_bewoners": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_naam_huurder": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_onderhuur_woon_periode": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_aantal_mensen": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_bewoning": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_footer": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_hoe_vaak": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_link_advertentie": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_naam_bewoner": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_online_aangeboden": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_toeristen_aanwezig": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_bellen_of_formulier": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_vakantieverhuur_wanneer": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_aantal_personen": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_adres_huurder": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_bewoners_familie": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_eigenaar": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_iemand_aanwezig": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_samenwonen": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_vermoeden": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woningdelen_wisselende_bewoners": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_bewoner": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_direct_gevaar": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_direct_gevaar_alert": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_direct_gevaar_ja": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_geen_contact": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_gemeld_bij_eigenaar": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_namens_bewoner": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_toestemming_contact": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "extra_wonen_woonkwaliteit_toestemming_contact_ja": {
        "category_url": "/signals/v1/public/terms/categories/wonen"
    },
    "wonen_overig": {
        "category_url": "/signals/v1/public/terms/categories/wonen/sub_categories/wonen-overig"
    },
    "extra_personen_overig": {
        "category_url": "/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen"
    },
    "extra_personen_overig_vaker": {
        "category_url": "/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen"
    },
    "extra_personen_overig_vaker_momenten": {
        "category_url": "/signals/v1/public/terms/categories/overlast-van-en-door-personen-of-groepen"
    },
}


class Command(BaseCommand):
    dry_run = False
    schema = signal_id = None

    def add_arguments(self, parser):
        """
        Add arguments
        """
        parser.add_argument('--dry-run', action='store_true', help='Will not store anything in the database')
        parser.add_argument('--signal-id', type=int, help='The Signal that needs to be analyzed and/or fixed')

    def _pre_handle(self, **options):
        """
        Setup
        """
        self.dry_run = options['dry_run']
        self.signal_id = int(options['signal_id']) if options['signal_id'] else None

        # JSON Schema to validate the JSON Blob
        filename = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'api', 'json_schema', 'extra_properties.json'
        )
        with open(filename) as f:
            self.schema = json.load(f)

    def handle(self, *args, **options):
        """
        Run the management command
        """
        start = timer()
        self._pre_handle(**options)

        signals_qs = self._get_queryset()
        for signal in signals_qs.all():
            self.stdout.write(f'\nAnalyzing extra properties for Signal #{signal.id}')
            if self._validate(signal.extra_properties):
                self.stdout.write('- Extra properties seem OK no need to try and fix them')
                continue

            self.stdout.write('- Extra properties needs to be fixed')
            self._fix_extra_properties(signal)
            self.stdout.write('\n')

        stop = timer()
        self.stdout.write(f'Time: {stop - start:.2f} second(s)')
        self.stdout.write('Done!')

    def _get_queryset(self):
        """
        Returns the filtered Signals QuerySet
        """
        if self.signal_id:
            # Analyze/Fix the extra_properties of a specific Signal
            return Signal.objects.filter(id=self.signal_id)
        else:
            # Will select all extra_properties where the category_url is an empty string
            # Equivalent to the SQL where statement: WHERE s.extra_properties @> '[{"category_url": ""}]'::jsonb
            return Signal.objects.filter(extra_properties__contains=[{'category_url': ''}]).order_by('created_at')

    def _validate_json_schema(self, extra_properties):
        """
        Validate the extra_properties against the JSON schema
        """
        try:
            validate(instance=extra_properties, schema=self.schema)
        except ValidationError as e:
            self.stdout.write(f'- JSON Schema validation error, {e}')
            return False
        return True

    def _validate_category_url(self, extra_property):
        """
        Check if the extra_property has a "category_url" and that it is not empty
        """
        return 'category_url' in extra_property and extra_property['category_url'] != ''

    def _validate(self, extra_properties):
        """
        Will run all validation checks on the extra_properties of a Signal
        """
        return all([self._validate_json_schema(extra_properties)] +
                   [self._validate_category_url(extra_property) for extra_property in extra_properties])

    def _fix_category_url(self, extra_property, first_category_assignment_url):
        """
        Will try to set the correct category url for the extra property
        """
        if self._validate_category_url(extra_property):
            self.stdout.write(f'- Category URL already set to {extra_property["category_url"]}')
        else:
            if extra_property['id'] not in lookup_dict:
                self.stdout.write(f'- Category URL not found for extra property with id {extra_property["id"]}')
                return extra_property

            category_url = lookup_dict[extra_property['id']]['category_url']
            if 'sub_categories' not in lookup_dict[extra_property['id']]['category_url'] \
                    and first_category_assignment_url.startswith(category_url):
                # The first assigned category is a child of the category found so use the category url
                category_url = first_category_assignment_url

            extra_property['category_url'] = category_url
            self.stdout.write(f'- Category URL set to {extra_property["category_url"]}')
        return extra_property

    def _fix_extra_properties(self, signal):
        """
        Check and fix the extra properties of a Signal
        """
        extra_properties = []

        first_category_assignment = CategoryAssignment.objects.filter(_signal_id=signal.id).order_by('created_at')[0]
        for extra_property in signal.extra_properties:
            first_category_assignment_url = first_category_assignment.category.get_absolute_url()
            extra_properties.append(self._fix_category_url(extra_property, first_category_assignment_url))

        # Validate the extra properties before storing
        self._validate_json_schema(extra_properties)

        signal.extra_properties = extra_properties
        self.stdout.write(f'- Fixed extra properties: {json.dumps(extra_properties, indent=4, sort_keys=True)}')

        if not self.dry_run:
            signal.save()
            self.stdout.write('- Saved extra properties!')
        else:
            self.stdout.write('- Dry run enabled, not storing the changes in the database')
