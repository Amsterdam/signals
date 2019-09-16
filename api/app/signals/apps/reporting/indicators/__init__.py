from signals.apps.reporting.indicators.n_melding_nieuw import NMeldingNieuw
from signals.apps.reporting.indicators.n_melding_open import NMeldingOpen
from signals.apps.reporting.indicators.categorie_naam import CategorieNaam
from signals.apps.reporting.indicators.n_melding_gesloten import NMeldingGesloten
from signals.apps.reporting.indicators.p_melding_tevreden import PMeldingTevreden
from signals.apps.reporting.indicators.n_melding_nieuw_anoniem import MMeldingNieuwAnoniem
from signals.apps.reporting.indicators.n_melding_nieuw_niet_anoniem import MMeldingNieuwNietAnoniem
from signals.apps.reporting.indicators.hoofd_categorie_naam import HoofdCategorieNaam
from signals.apps.reporting.indicators.p_melding_intake_in_12h import PMeldingIntakeIn12H
from signals.apps.reporting.indicators.p_melding_gesloten_binnen_termijn import PMeldingGeslotenBinnenTermijn
from signals.apps.reporting.indicators.n_melding_open_3sla import NMeldingOpen3SLA
from signals.apps.reporting.indicators.n_melding_open_1sla import NMeldingOpen1SLA
from signals.apps.reporting.indicators.n_melding_open_binnen_termijn import NMeldingOpenBinnenTermijn


def derive_routes(indicators):
    routes = {}

    for indicator in indicators:
        routes[indicator.code] = indicator
    return routes


INDICATOR_ROUTES = derive_routes([
    NMeldingNieuw,
    NMeldingOpen,
    CategorieNaam,
    NMeldingGesloten,
    PMeldingTevreden,
    MMeldingNieuwAnoniem,
    MMeldingNieuwNietAnoniem,
    HoofdCategorieNaam,
    PMeldingIntakeIn12H,
    PMeldingGeslotenBinnenTermijn,
    NMeldingOpen3SLA,
    NMeldingOpen1SLA,
    NMeldingOpenBinnenTermijn,
])
