# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
import uuid

from signals.apps.questionnaires.factories import (
    ChoiceFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory
)
from signals.apps.questionnaires.models import Questionnaire


def questionnaire_geluidsoverlast():
    """
    Questionnaire based on the "geluidsoverlast" category.
    """
    # sketch:
    #       q1
    #     /    \
    #    |    q1_1
    #    |     |
    #    |    q1_2
    #     \    /
    #       q2
    #        |
    #       q3
    #        |
    #       q4
    #        |
    #       q5
    #        |
    #       q6
    #     /    \
    #  q6_1   q6_2

    # Create questionnaire
    q_uuid = uuid.UUID('5483355b-358d-4bc2-9f4d-0e69c48b1d69')
    try:
        questionnaire = Questionnaire.objects.get(uuid=q_uuid)
        return questionnaire
    except Questionnaire.DoesNotExist:
        # Create the questionnaire
        pass

    questionnaire = QuestionnaireFactory.create(uuid=q_uuid,
                                                name='Test questionnaire ("geluidsoverlast")',
                                                description='Based upon the "geluidsoverlast" category',
                                                graph=None,
                                                flow=Questionnaire.EXTRA_PROPERTIES)

    # Create all questions needed
    q1 = QuestionFactory(label='Wanneer was het?',
                         short_label='Wanneer was het?',
                         retrieval_key='geluidsoverlast-1',
                         field_type='choice')
    q1_o1 = ChoiceFactory(question=q1, display='Nu', payload='nu')
    q1_o2 = ChoiceFactory(question=q1, display='Eerder', payload='eerder')

    q1_1 = QuestionFactory(label='Welke dag?',
                           short_label='Welke dag?',
                           retrieval_key='geluidsoverlast-1-1',
                           field_type='date',)

    q1_2 = QuestionFactory(label='Hoe laat?',
                           short_label='Hoe laat?',
                           retrieval_key='geluidsoverlast-1-2',
                           field_type='time',)

    q2 = QuestionFactory(label='Uw melding gaat over?',
                         short_label='Uw melding gaat over?',
                         retrieval_key='geluidsoverlast-2',
                         field_type='choice')
    ChoiceFactory(question=q2, display='Horecabedrijf, zoals een café, restaurant, snackbar of kantine', payload='Horecabedrijf, zoals een café, restaurant, snackbar of kantine')  # noqa
    ChoiceFactory(question=q2, display='Ander soort bedrijf, zoals een winkel, supermarkt of sportschool', payload='Ander soort bedrijf, zoals een winkel, supermarkt of sportschool')  # noqa
    ChoiceFactory(question=q2, display='Evenement, zoals een festival, feest of markt', payload='Evenement, zoals een festival, feest of markt')  # noqa
    ChoiceFactory(question=q2, display='Iets anders', payload='Iets anders')

    q3 = QuestionFactory(label='Wie of wat zorgt voor deze overlast, denkt u?',
                         short_label='Wie of wat zorgt voor deze overlast, denkt u?(niet verplicht)',
                         retrieval_key='geluidsoverlast-3',
                         required=False,
                         field_type='plain_text')

    q4 = QuestionFactory(label='Op welk adres hebt u overlast?',
                         short_label='Op welk adres hebt u overlast?',
                         retrieval_key='geluidsoverlast-4',
                         field_type='plain_text')

    q5 = QuestionFactory(label='Gebeurt het vaker?',
                         short_label='Gebeurt het vaker?',
                         retrieval_key='geluidsoverlast-5',
                         field_type='choice')
    ChoiceFactory(question=q5, display='Ja, gebeurt vaker', payload='Ja, gebeurt vaker')
    ChoiceFactory(question=q5, display='Nee, het is de eerste keer', payload='Nee, het is de eerste keer')

    q6 = QuestionFactory(label='Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)',  # noqa
                         short_label='Mogen we contact met u opnemen over de melding? (Bijvoorbeeld om bij u thuis het geluid te meten.)',  # noqa
                         retrieval_key='geluidsoverlast-6',
                         field_type='choice')
    q6_o1 = ChoiceFactory(question=q6, display='Ja, u mag contact met mij opnemen', payload='Ja, u mag contact met mij opnemen')  # noqa
    q6_o2 = ChoiceFactory(question=q6, display='Nee, liever geen contact', payload='Nee, liever geen contact')

    q6_1 = QuestionFactory(label='Waarom hebt u liever geen contact?',
                           short_label='Waarom hebt u liever geen contact?',
                           retrieval_key='geluidsoverlast-6-1',
                           field_type='plain_text')

    q6_2 = QuestionFactory(label='Mogen we u nu bellen?',
                           short_label='Mogen we u nu bellen?',
                           retrieval_key='geluidsoverlast-6-2-2',
                           field_type='choice')
    ChoiceFactory(question=q6_2, display='Binnen 30 minuten', payload='Binnen 30 minuten')
    ChoiceFactory(question=q6_2, display='Binnen 1 uur', payload='Binnen 1 uur')
    ChoiceFactory(question=q6_2, display='Niet nu', payload='Niet nu')

    # Create graph
    graph = QuestionGraphFactory.create(name='Geluidsoverlast', first_question=q1)

    # Create edges
    EdgeFactory.create(graph=graph, question=q1, next_question=q1_1, choice=q1_o2)
    EdgeFactory.create(graph=graph, question=q1_1, next_question=q1_2, choice=None)
    EdgeFactory.create(graph=graph, question=q1_2, next_question=q2, choice=None)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice=q1_o1)
    EdgeFactory.create(graph=graph, question=q2, next_question=q3, choice=None)
    EdgeFactory.create(graph=graph, question=q3, next_question=q4, choice=None)
    EdgeFactory.create(graph=graph, question=q4, next_question=q5, choice=None)
    EdgeFactory.create(graph=graph, question=q5, next_question=q6, choice=None)
    EdgeFactory.create(graph=graph, question=q6, next_question=q6_1, choice=q6_o1)
    EdgeFactory.create(graph=graph, question=q6, next_question=q6_2, choice=q6_o2)

    # Add the graph to the questionnaire
    questionnaire.graph = graph
    questionnaire.save()

    # Return the questionnaire
    return questionnaire
