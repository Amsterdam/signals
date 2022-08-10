# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from unittest import skip

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
    @skip('When running this test, the questions in the graph do not always have the expected id\'s')
    def test_mermaidx(self):
        questionnaire = questionnaire_geluidsoverlast()
        question_graph_service = QuestionGraphService(q_graph=questionnaire.graph)

        expected_output = '''10["Mogen we u nu bellen?"]
9["Waarom hebt u liever geen contact?"]
8["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"] -->|Ja, u mag contact met mij opnemen| 9["Waarom hebt u liever geen contact?"]
8["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"] -->|Nee, liever geen contact| 10["Mogen we u nu bellen?"]
7["Gebeurt het vaker?"] --> 8["Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)"]
6["Op welk adres hebt u overlast?"] --> 7["Gebeurt het vaker?"]
5["Wie of wat zorgt voor deze overlast, denkt u?"] --> 6["Op welk adres hebt u overlast?"]
4["Uw melding gaat over?"] --> 5["Wie of wat zorgt voor deze overlast, denkt u?"]
3["Hoe laat?"] --> 4["Uw melding gaat over?"]
2["Welke dag?"] --> 3["Hoe laat?"]
1["Wanneer was het?"] -->|Eerder| 2["Welke dag?"]
1["Wanneer was het?"] -->|Nu| 4["Uw melding gaat over?"]'''  # noqa: E501

        output = mermaidx(question_graph_service.nx_graph)
        self.assertEqual(f'graph TD\n\n{expected_output}', output)

        for direction in [DIRECTION_TD, DIRECTION_DT, DIRECTION_LR, DIRECTION_RL]:
            output = mermaidx(question_graph_service.nx_graph, direction=direction)
            self.assertEqual(f'graph {direction}\n\n{expected_output}', output)
