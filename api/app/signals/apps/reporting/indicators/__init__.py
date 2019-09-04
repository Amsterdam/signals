from signals.apps.reporting.indicators.n_melding_nieuw import NMeldingNieuw
from signals.apps.reporting.indicators.n_melding_open import NMeldingOpen
from signals.apps.reporting.indicators.categorie_naam import CategorieNaam
from signals.apps.reporting.indicators.n_melding_gesloten import NMeldingGesloten
from signals.apps.reporting.indicators.p_melding_tevreden import PMeldingTevreden
from signals.apps.reporting.indicators.n_melding_nieuw_anoniem import MMeldingNieuwAnoniem
from signals.apps.reporting.indicators.n_melding_nieuw_niet_anoniem import MMeldingNieuwNietAnoniem


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
])
