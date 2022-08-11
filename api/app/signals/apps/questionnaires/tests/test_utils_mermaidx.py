# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.questionnaires.services import QuestionGraphService
from signals.apps.questionnaires.tests.data.questionnaires import questionnaire_geluidsoverlast
from signals.apps.questionnaires.utils.mermaidx import (
    DIRECTION_DT,
    DIRECTION_LR,
    DIRECTION_RL,
    DIRECTION_TD,
    mermaidx
)


class TestUtilMermaid(TestCase):
    def test_mermaidx(self):
        questionnaire = questionnaire_geluidsoverlast()
        question_graph_service = QuestionGraphService(q_graph=questionnaire.graph)

        expected_output = '''geluidsoverlast-6-2-2["Mogen we u nu bellen?"]
geluidsoverlast-6-1["Waarom hebt u liever geen contact?"]
geluidsoverlast-6["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"] -->|Ja, u mag contact met mij opnemen| geluidsoverlast-6-1["Waarom hebt u liever geen contact?"]
geluidsoverlast-6["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"] -->|Nee, liever geen contact| geluidsoverlast-6-2-2["Mogen we u nu bellen?"]
geluidsoverlast-5["Gebeurt het vaker?"] --> geluidsoverlast-6["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"]
geluidsoverlast-4["Op welk adres hebt u overlast?"] --> geluidsoverlast-5["Gebeurt het vaker?"]
geluidsoverlast-3["Wie of wat zorgt voor deze overlast, denkt u?"] --> geluidsoverlast-4["Op welk adres hebt u overlast?"]
geluidsoverlast-2["Uw melding gaat over?"] --> geluidsoverlast-3["Wie of wat zorgt voor deze overlast, denkt u?"]
geluidsoverlast-1-2["Hoe laat?"] --> geluidsoverlast-2["Uw melding gaat over?"]
geluidsoverlast-1-1["Welke dag?"] --> geluidsoverlast-1-2["Hoe laat?"]
geluidsoverlast-1["Wanneer was het?"] -->|Eerder| geluidsoverlast-1-1["Welke dag?"]
geluidsoverlast-1["Wanneer was het?"] -->|Nu| geluidsoverlast-2["Uw melding gaat over?"]'''  # noqa: E501

        output = mermaidx(question_graph_service.nx_graph)
        self.assertEqual(f'graph TD\n\n{expected_output}', output)

        for direction in [DIRECTION_TD, DIRECTION_DT, DIRECTION_LR, DIRECTION_RL]:
            output = mermaidx(question_graph_service.nx_graph, direction=direction)
            self.assertEqual(f'graph {direction}\n\n{expected_output}', output)
