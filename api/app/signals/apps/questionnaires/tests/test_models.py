# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021-2022 Gemeente Amsterdam, Vereniging van Nederlandse Gemeenten
"""
Test models and associated manager functions for the questionnaires app.
"""
import os
import uuid
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.timezone import make_aware
from freezegun import freeze_time

from signals.apps.questionnaires.factories import (
    ChoiceFactory,
    EdgeFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory,
    TriggerFactory
)
from signals.apps.questionnaires.models import (
    AttachedFile,
    AttachedSection,
    Edge,
    IllustratedText,
    Question,
    QuestionGraph,
    StoredFile
)
from signals.apps.signals import workflow
from signals.apps.signals.factories import LocationFactory, SignalFactory, StatusFactory

THIS_DIR = os.path.dirname(__file__)
GIF_FILE = os.path.join(THIS_DIR, 'test-data', 'test.gif')


def create_diamond(graph_name='diamond'):
    """
    Seed the database with a diamond shaped graph formed by questions.
    """
    q1 = QuestionFactory.create(analysis_key='q1')
    q2 = QuestionFactory.create(analysis_key='q2')
    q3 = QuestionFactory.create(analysis_key='q3')
    q4 = QuestionFactory.create(analysis_key='q4')
    q5 = QuestionFactory.create(analysis_key='q5')

    # sketch:
    #    q1 <- first_question
    #   /  \
    # q2    q3
    #   \  /
    #    q4
    #    |
    #    q5
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory.create(graph=graph, question=q1, next_question=q2, choice=None)
    EdgeFactory.create(graph=graph, question=q2, next_question=q4, choice=None)
    EdgeFactory.create(graph=graph, question=q1, next_question=q3, choice=None)
    EdgeFactory.create(graph=graph, question=q3, next_question=q4, choice=None)
    EdgeFactory.create(graph=graph, question=q4, next_question=q5, choice=None)

    return graph


def create_diamond_plus(graph_name='diamond_plus'):
    graph = create_diamond(graph_name=graph_name)
    # sketch:
    #    q1 <- first_question
    #   /  \
    # q2    q3
    #   \  /
    #    q4     q6
    #    |      |
    #    q5     q7

    # Add an edge to the graph that cannot be reached from the first
    # question of the question_graph
    q6 = QuestionFactory.create(analysis_key='q6')
    q7 = QuestionFactory.create(analysis_key='q7')
    EdgeFactory.create(graph=graph, question=q6, next_question=q7, choice=None)

    return graph


def create_empty(graph_name='empty'):
    return QuestionGraphFactory.create(name=graph_name, first_question=None)


def create_one(graph_name='one'):
    q1 = QuestionFactory.create(analysis_key='q1')
    # sketch:
    # q1 <- first_question
    return QuestionGraphFactory.create(name=graph_name, first_question=q1)


def create_disconnected(graph_name='disconnected'):
    q1 = QuestionFactory.create(analysis_key='q1')
    q2 = QuestionFactory.create(analysis_key='q2')
    q3 = QuestionFactory.create(analysis_key='q3')

    # sketch:
    # q1 <- first_question
    #
    # q2
    # |
    # q3
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory.create(graph=graph, question=q2, next_question=q3, choice=None)

    return graph


def create_cycle(graph_name='cycle'):
    q1 = QuestionFactory.create(analysis_key='q1')
    q2 = QuestionFactory.create(analysis_key='q2')

    # sketch:
    #  q1 <- first_question
    # (  )
    #  q2
    graph = QuestionGraphFactory.create(name=graph_name, first_question=q1)
    EdgeFactory(graph=graph, question=q1, next_question=q2, choice=None)
    EdgeFactory(graph=graph, question=q2, next_question=q1, choice=None)

    return graph


def create_too_many_questions(graph_name='too_many'):
    questions = [QuestionFactory.create() for i in range(100)]  # TODO: make MAX_QUESTIONS an app setting

    graph = QuestionGraphFactory.create(name=graph_name, first_question=questions[0])
    for i in range(len(questions) - 1):
        EdgeFactory.create(graph=graph, question=questions[i], next_question=questions[i + 1], choice=None)

    return graph


def create_illustrated_text():
    """
    Create an IllustratedText instance that can be used for explanatory text.

    Note, for now only Question an Questionnaire instances get this explanatory
    text.
    """
    illustrated_text = IllustratedText.objects.create(title='TITLE')
    section_1 = AttachedSection.objects.create(header='HEADER 1', text='SECTION 1', illustrated_text=illustrated_text)
    section_2 = AttachedSection.objects.create(header='HEADER 2', text='SECTION 2', illustrated_text=illustrated_text)

    with open(GIF_FILE, 'rb') as f:
        suf = SimpleUploadedFile('test.gif', f.read(), content_type='image/gif')
        stored_file = StoredFile.objects.create(file=suf)
    attached_file_1 = AttachedFile.objects.create(description='IMAGE 1', stored_file=stored_file, section=section_1)
    attached_file_2 = AttachedFile.objects.create(description='IMAGE 2', stored_file=stored_file, section=section_2)

    return illustrated_text, section_1, section_2, attached_file_1, attached_file_2


class TestEmpty(TestCase):
    def setUp(self):
        create_empty()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='empty')
        self.assertEqual(len(question_graph.edges.all()), 0)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 0)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='empty')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 0)


class TestOne(TestCase):
    def setUp(self):
        create_one()

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='one')
        self.assertEqual(len(question_graph.edges.all()), 0)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='one')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)


class TestDiamond(TestCase):
    def setUp(self):
        create_diamond()

    def test_factories(self):
        self.assertEqual(Question.objects.count(), 5)
        self.assertEqual(Edge.objects.count(), 5)

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond')
        self.assertEqual(len(question_graph.edges.all()), 5)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond')
        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)


class TestDiamondPlus(TestCase):
    def setUp(self):
        create_diamond_plus()

    def test_factories(self):
        self.assertEqual(Question.objects.count(), 7)
        self.assertEqual(Edge.objects.count(), 6)

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond_plus')
        self.assertEqual(len(question_graph.edges.all()), 5 + 1)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 7)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='diamond_plus')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 5)

        self.assertEqual(Question.objects.count(), 7)
        self.assertEqual(Edge.objects.count(), 6)


class TestDisconnected(TestCase):
    def setUp(self):
        create_disconnected()

    def test_factories(self):
        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(Edge.objects.count(), 1)

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='disconnected')
        self.assertEqual(len(question_graph.edges.all()), 1)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 3)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='disconnected')

        questions = Question.objects.get_reachable_from_question_graph(question_graph)
        self.assertEqual(len(questions), 1)

        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(Edge.objects.count(), 1)


class TestCycle(TestCase):
    def setUp(self):
        create_cycle()

    def test_factories(self):
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Edge.objects.count(), 2)

    def test_get_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='cycle')
        self.assertEqual(len(question_graph.edges.all()), 2)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 2)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='cycle')

        with self.assertRaises(Exception) as e:
            Question.objects.get_reachable_from_question_graph(question_graph)
            self.assertIn('not acyclic', str(e))


class TestTooMany(TestCase):
    def setUp(self):
        create_too_many_questions()

    def test_get_from_question_graph(self):
        # TODO: consider whether we want to raise an error in QuestionManager.get_from_question_graph in case too many
        # questions are added to the graph.
        question_graph = QuestionGraph.objects.get(name='too_many')
        self.assertEqual(len(question_graph.edges.all()), 99)

        questions = Question.objects.get_from_question_graph(question_graph)
        self.assertEqual(len(questions), 100)

    def test_get_reachable_from_question_graph(self):
        question_graph = QuestionGraph.objects.get(name='too_many')

        with self.assertRaises(Exception) as e:
            Question.objects.get_reachable_from_question_graph(question_graph)
            self.assertIn('too many', str(e))


class TestEdges(TestCase):
    def setUp(self):
        #    q1
        #   / | \
        #  q2 q3 q4
        q1 = QuestionFactory.create()
        q2 = QuestionFactory.create()
        q3 = QuestionFactory.create()
        q4 = QuestionFactory.create()

        self.graph = QuestionGraphFactory.create(name='edge_order',  first_question=q1)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q2, choice=None)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q3, choice=None)
        EdgeFactory.create(graph=self.graph, question=q1, next_question=q4, choice=None)

    def test_edge_ordering(self):
        question = self.graph.first_question
        before = self.graph.get_edge_order(question)
        for id_, edge in zip(before, self.graph.get_edges(question)):
            self.assertEqual(id_, edge.id)

        # now reorder our edges
        change = before[1:] + before[:1]
        self.graph.set_edge_order(question, change)

        for id_, edge in zip(change, self.graph.get_edges(question)):
            self.assertEqual(id_, edge.id)


class TestTriggers(TestCase):
    def setUp(self):
        q1 = QuestionFactory.create(field_type='plain_text')

        self.graph = QuestionGraphFactory.create(name='trigger_order', first_question=q1)

        trigger_payloads = ['one', 'two', 'three']
        for payload in trigger_payloads:
            TriggerFactory.create(graph=self.graph, question=q1, payload=payload)

    def test_trigger_ordering(self):
        question = self.graph.first_question
        before = self.graph.get_trigger_order(question)
        for id_, trigger in zip(before, self.graph.get_triggers(question)):
            self.assertEqual(id_, trigger.id)

        # now reorder our edges
        change = before[1:] + before[:1]
        self.graph.set_trigger_order(question, change)
        for id_, trigger in zip(change, self.graph.get_triggers(question)):
            self.assertEqual(id_, trigger.id)


class TestChoices(TestCase):
    def setUp(self):
        q1 = QuestionFactory.create(field_type='plain_text')
        self.graph = QuestionGraphFactory.create(name='info_trigger_order', first_question=q1)

        choice_payloads = ['one', 'two', 'three']
        for payload in choice_payloads:
            ChoiceFactory.create(question=q1, payload=payload)

    def test_choice_ordering(self):
        question = self.graph.first_question
        before = question.get_choice_order()
        for id_, choice in zip(before, question.choices.all()):
            self.assertEqual(id_, choice.id)

        # now reorder our choices
        change = before[1:] + before[:1]
        question.set_choice_order(change)
        question.refresh_from_db()

        for id_, choice in zip(change, question.choices.all()):
            self.assertEqual(id_, choice.id)


class TestGetByReference(TestCase):
    def setUp(self):
        self.question = QuestionFactory.create(retrieval_key='question')

    def test_get_by_reference_none(self):
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference(None)

    def test_get_by_reference_key(self):
        question = Question.objects.get_by_reference('question')
        self.assertEqual(self.question, question)

        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference('NO SUCH QUESTION')

    def test_get_by_reference_uuid(self):
        question = Question.objects.get_by_reference(str(self.question.uuid))
        self.assertEqual(question, self.question)

        generated = uuid.uuid4()
        while generated == self.question.uuid:
            generated = uuid.uuid4()

        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get_by_reference(str(generated))

    def test_pathological_case_key_is_valid_uuid(self):
        # Set up a question that has a valid UUID as a key, make sure that
        # that one UUID does not match the question's `uuid` property.
        question = QuestionFactory.create()

        generated = uuid.uuid4()
        while generated == question.uuid:
            generated = uuid.uuid4()

        question.retrieval_key = generated
        question.save()
        question.refresh_from_db()

        retrieved = Question.objects.get_by_reference(str(generated))
        self.assertEqual(retrieved, question)


class TestQuestion(TestCase):
    def setUp(self):
        self.now = make_aware(datetime(2021, 8, 11, 20, 0, 0))

    def test_deadline_and_duration(self):
        session = SessionFactory.create(submit_before=self.now + timedelta(weeks=2), duration=timedelta(hours=2))

        # submit on time and within allowed duration
        session.started_at = self.now
        with freeze_time(self.now + timedelta(hours=1)):
            self.assertFalse(session.is_expired)

        # submit before deadline but outside allowed duration
        with freeze_time(self.now + timedelta(hours=4)):
            self.assertTrue(session.is_expired)

        # submit after deadline within allowed duration
        session.started_at = session.submit_before + timedelta(minutes=5)
        with freeze_time(session.submit_before + timedelta(minutes=10)):
            self.assertTrue(session.is_expired)

        # submit after deadline and outside allowed duration
        session.started_at = session.submit_before + timedelta(minutes=5)
        with freeze_time(session.submit_before + timedelta(hours=4)):
            self.assertTrue(session.is_expired)

        # start just before deadline, submit just after deadline but within allowed duration
        session.started_at = session.submit_before - timedelta(minutes=5)
        with freeze_time(session.submit_before + timedelta(minutes=5)):
            self.assertTrue(session.is_expired)

    def test_deadline_none(self):
        session = SessionFactory.create(submit_before=None, duration=timedelta(hours=2))

        # submit within allowed duration
        session.started_at = self.now
        with freeze_time(self.now + timedelta(minutes=5)):
            self.assertFalse(session.is_expired)

        # submit outside of allowed duration
        with freeze_time(self.now + timedelta(hours=4)):
            self.assertTrue(session.is_expired)

    def test_duration_none(self):
        session = SessionFactory.create(submit_before=self.now + timedelta(days=14), duration=None)

        # submit before deadline
        session.started_at = self.now
        with freeze_time(session.submit_before - timedelta(minutes=5)):
            self.assertFalse(session.is_expired)

        # submit after deadline
        with freeze_time(session.submit_before + timedelta(minutes=5)):
            self.assertTrue(session.is_expired)

    def test_deadline_and_duration_none(self):
        session = SessionFactory.create(submit_before=None, duration=None)

        # submit waaayyyy long after starting the questionnaire
        session.started_at = self.now
        with freeze_time(self.now + timedelta(days=10000)):
            self.assertFalse(session.is_expired)


class TestQuestionModel(TestCase):
    def setUp(self):
        # We set this to the default because it is normally overwritten by QuestionFactory:
        self.question = QuestionFactory.create(analysis_key='PLACEHOLDER')

    def test_analysis_key_default(self):
        # We cannot test this using the QuestionFactory because it overwrites
        # the `analysis_key` placeholder value.
        q = Question.objects.create(
            label='label',
            short_label='short_label',
            field_type='plain_text'
        )
        self.assertEqual(q.analysis_key, f'PLACEHOLDER-{str(q.uuid)}')


class TestQuestionnaireModel(TestCase):
    def setUp(self):
        illustrated_text, section_1, section_2, attached_file_1, attached_file_2 = create_illustrated_text()
        self.illustrated_text = illustrated_text
        self.section_1 = section_1
        self.section_2 = section_2
        self.attached_file_1 = attached_file_1
        self.attached_file_2 = attached_file_2

        self.questionnaire = QuestionnaireFactory.create(explanation=illustrated_text)

    def test_questionnaire_explanation(self):
        self.assertEqual(self.questionnaire.explanation, self.illustrated_text)
        self.assertEqual(list(self.questionnaire.explanation.sections.all()), [self.section_1, self.section_2])
        self.assertEqual(
            list(self.questionnaire.explanation.sections.first().files.all()), [self.attached_file_1])
        self.assertEqual(
            list(self.questionnaire.explanation.sections.last().files.all()), [self.attached_file_2])

        self.assertEqual(StoredFile.objects.count(), 1)
        stored_file = StoredFile.objects.first()
        self.assertEqual(set(stored_file.attached_files.all()), set([self.attached_file_1, self.attached_file_2]))
        self.assertEqual(
            self.questionnaire.explanation.sections.first().files.first().stored_file, stored_file)
        self.assertEqual(self.questionnaire.explanation.sections.last().files.first().stored_file, stored_file)

    def test_questionnaire_explanation_section_order(self):
        # sections of text in an explanation can be reordered
        order = self.questionnaire.explanation.get_attachedsection_order()
        self.assertEqual(list(order), [self.section_1.id, self.section_2.id])

        self.questionnaire.explanation.set_attachedsection_order([self.section_2.id, self.section_1.id])
        order = self.questionnaire.explanation.get_attachedsection_order()
        self.assertEqual(list(order), [self.section_2.id, self.section_1.id])


class TestStoredFile(TestCase):
    def setUp(self):
        illustrated_text_1, section_1, section_2, attached_file_1, attached_file_2 = create_illustrated_text()
        self.illustrated_text_1 = illustrated_text_1
        self.attached_file_1 = attached_file_1
        self.stored_file = attached_file_1.stored_file

    def test_stored_file_get_reference_count(self):
        self.assertEqual(self.stored_file.get_reference_count(), 2)
        self.attached_file_1.delete()
        self.assertEqual(self.stored_file.get_reference_count(), 1)


class TestSession(TestCase):
    def setUp(self):
        self.signal = SignalFactory.create(
            status__text='STATUS TEXT',
            status__state=workflow.DOORGEZET_NAAR_EXTERN,
            status__email_override='a@example.com',
        )

    def test_model_clean_status(self):
        # should work:
        session = SessionFactory.create(
            _signal_status=self.signal.status,
            _signal=self.signal
        )

        # should not work:
        wrong_status = StatusFactory.create(
            text='STATUS TEXT',
            state=workflow.DOORGEZET_NAAR_EXTERN,
            email_override='a@example.com',
        )

        with self.assertRaises(ValidationError):
            session._signal_status = wrong_status
            session.save()

    def test_model_clean_location(self):
        # should work:
        session = SessionFactory.create(
            _signal_location=self.signal.location,
            _signal=self.signal
        )

        # should not work:
        wrong_location = LocationFactory.create()

        with self.assertRaises(ValidationError):
            session._signal_location = wrong_location
            session.save()

    def test_no_signal_then_no_signal_properties_allowed(self):
        with self.assertRaises(ValidationError):
            session = SessionFactory.create(
                _signal=None,
                _signal_status=self.signal.status
            )

        with self.assertRaises(ValidationError):
            session = SessionFactory.create(
                _signal=None,
                _signal_status=self.signal.status,
                _signal_location=self.signal.location
            )

        with self.assertRaises(ValidationError):
            session = SessionFactory.create(
                _signal=None,
                _signal_status = self.signal.status,
                _signal_location = self.signal.location
            )
