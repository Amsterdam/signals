# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2026 Gemeente Amsterdam
"""Exercise real upload and copy boundaries using only generated image pixels."""
from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image, ImageCms, PngImagePlugin
from rest_framework.test import APITestCase

from signals.apps.questionnaires.factories import (
    AnswerFactory,
    QuestionFactory,
    QuestionGraphFactory,
    QuestionnaireFactory,
    SessionFactory
)
from signals.apps.questionnaires.models import Answer, StoredFile
from signals.apps.questionnaires.services.forward_to_external import (
    ForwardToExternalSessionService,
    create_session_for_forward_to_external
)
from signals.apps.questionnaires.tests.rest_framework.views.public.test_public_sessions_endpoint import test_urlconf
from signals.apps.signals.factories import SignalFactory
from signals.apps.signals.models import Attachment, Note, Signal
from signals.apps.signals.workflow import DOORGEZET_NAAR_EXTERN
from signals.test.utils import SignalsBaseApiTestCase

MARKER = b'SYNTHETIC-PRIVATE-IMAGE-METADATA'
FORMATS = (('JPEG', 'jpg', 'image/jpeg'), ('PNG', 'png', 'image/png'), ('GIF', 'gif', 'image/gif'))


def image_bytes(image_format='JPEG', *, invalid_icc=False):
    image = Image.new('RGB', (16, 12), (80, 120, 160))
    options = {}
    if image_format in ('JPEG', 'PNG'):
        exif = Image.Exif()
        exif[270] = MARKER.decode()
        exif[271] = 'Synthetic camera'
        exif[34853] = {1: 'N', 2: (1.0, 2.0, 3.0), 3: 'E', 4: (4.0, 5.0, 6.0)}
        options['exif'] = exif.tobytes()
        options['icc_profile'] = (
            b'invalid-profile-' + MARKER if invalid_icc
            else ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        )
    if image_format == 'PNG':
        info = PngImagePlugin.PngInfo()
        info.add_text('Description', MARKER.decode())
        info.add_itxt('XML:com.adobe.xmp', MARKER.decode())
        options['pnginfo'] = info
    if image_format == 'GIF':
        options['comment'] = MARKER
    output = BytesIO()
    image.save(output, format=image_format, **options)
    return output.getvalue()


def upload(image_format='JPEG', *, invalid_icc=False, truncated=False):
    _, extension, mimetype = next(item for item in FORMATS if item[0] == image_format)
    content = image_bytes(image_format, invalid_icc=invalid_icc)
    if truncated:
        content = content[:-20]
    return SimpleUploadedFile(f'synthetic.{extension}', content, content_type=mimetype)


class IsolatedImageStorageMixin:
    def setUp(self):
        storage_settings = override_settings(STORAGES={
            'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
        })
        storage_settings.enable()
        self.addCleanup(storage_settings.disable)
        super().setUp()

    def stored_names(self, path=''):
        directories, filenames = default_storage.listdir(path)
        names = {f'{path}/{name}'.lstrip('/') for name in filenames}
        for directory in directories:
            names.update(self.stored_names(f'{path}/{directory}'.lstrip('/')))
        return names

    def assert_clean_image(self, name, image_format):
        with default_storage.open(name, 'rb') as saved:
            content = saved.read()
        self.assertNotIn(MARKER, content)
        with Image.open(BytesIO(content)) as image:
            image.load()
            self.assertEqual(image.format, image_format)
            self.assertEqual(image.size, (16, 12))
            self.assertFalse(image.getexif())
            for key in ('exif', 'icc_profile', 'comment', 'xmp', 'XML:com.adobe.xmp', 'Description'):
                self.assertNotIn(key, image.info)


class TestSignalImageUploadSanitization(IsolatedImageStorageMixin, SignalsBaseApiTestCase):
    def setUp(self):
        super().setUp()
        self.signal = SignalFactory.create()

    def endpoint(self, private):
        if private:
            self.client.force_authenticate(user=self.superuser)
            return f'/signals/v1/private/signals/{self.signal.pk}/attachments/'
        self.client.force_authenticate(user=None)
        return f'/signals/v1/public/signals/{self.signal.uuid}/attachments/'

    def assert_successful_uploads(self, private):
        endpoint = self.endpoint(private)
        for image_format, _, mimetype in FORMATS:
            with self.subTest(image_format=image_format):
                response = self.client.post(endpoint, {'file': upload(image_format)}, format='multipart')
                self.assertEqual(response.status_code, 201, response.data)
                attachment = self.signal.attachments.latest('id')
                attachment.refresh_from_db()
                self.assertTrue(attachment.is_image)
                self.assertEqual(attachment.mimetype, mimetype)
                self.assert_clean_image(attachment.file.name, image_format)
        self.assertEqual(self.signal.attachments.count(), 3)
        self.assertEqual(len(self.stored_names()), 3)

    def test_public_upload_persists_only_clean_images(self):
        self.assert_successful_uploads(private=False)

    def test_private_upload_persists_only_clean_images(self):
        self.assert_successful_uploads(private=True)

    def test_rejected_images_create_neither_attachments_notes_nor_blobs(self):
        for private in (False, True):
            endpoint = self.endpoint(private)
            for problem in ('truncated', 'invalid_icc', 'oversized'):
                with self.subTest(private=private, problem=problem):
                    incoming = upload('JPEG', truncated=problem == 'truncated', invalid_icc=problem == 'invalid_icc')
                    limit = incoming.size - 1 if problem == 'oversized' else 20 * 1024 * 1024
                    before_notes = Note.objects.count()
                    with override_settings(API_MAX_UPLOAD_SIZE=limit):
                        with patch.object(default_storage, 'save', wraps=default_storage.save) as save:
                            with self.captureOnCommitCallbacks(execute=True):
                                response = self.client.post(endpoint, {'file': incoming}, format='multipart')
                    self.assertEqual(response.status_code, 400, response.data)
                    save.assert_not_called()
                    self.assertFalse(self.signal.attachments.exists())
                    self.assertEqual(Note.objects.count(), before_notes)
                    self.assertEqual(self.stored_names(), set())


@override_settings(ROOT_URLCONF=test_urlconf)
class TestQuestionnaireImageUploadSanitization(IsolatedImageStorageMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.question = QuestionFactory.create(field_type='image', multiple_answers_allowed=True)
        graph = QuestionGraphFactory.create(first_question=self.question)
        questionnaire = QuestionnaireFactory.create(graph=graph)
        self.session = SessionFactory.create(questionnaire=questionnaire, duration=None)
        self.endpoint = f'/public/qa/sessions/{self.session.uuid}/attachments'

    def test_public_questionnaire_upload_persists_clean_answer_blobs(self):
        response = self.client.post(self.endpoint, {
            'question_uuid': str(self.question.uuid),
            'file': [upload(image_format) for image_format, _, _ in FORMATS],
        }, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        answer = Answer.objects.get(session=self.session, question=self.question)
        self.assertEqual(len(answer.payload), 3)
        for payload, (image_format, extension, _) in zip(answer.payload, FORMATS):
            self.assertEqual(payload['original_filename'], f'synthetic.{extension}')
            self.assert_clean_image(payload['file_path'], image_format)
        self.assertEqual(self.stored_names(), {item['file_path'] for item in answer.payload})

    def test_rejected_questionnaire_upload_writes_no_answer_or_blob(self):
        for problem in ('truncated', 'invalid_icc', 'oversized'):
            with self.subTest(problem=problem):
                incoming = upload('JPEG', truncated=problem == 'truncated', invalid_icc=problem == 'invalid_icc')
                limit = incoming.size - 1 if problem == 'oversized' else 20 * 1024 * 1024
                before_notes = Note.objects.count()
                with override_settings(API_MAX_UPLOAD_SIZE=limit):
                    with patch.object(default_storage, 'save', wraps=default_storage.save) as save:
                        response = self.client.post(self.endpoint, {
                            'question_uuid': str(self.question.uuid), 'file': incoming,
                        }, format='multipart')
                self.assertEqual(response.status_code, 400, response.data)
                save.assert_not_called()
                self.assertFalse(Answer.objects.filter(session=self.session).exists())
                self.assertFalse(Attachment.objects.exists())
                self.assertEqual(Note.objects.count(), before_notes)
                self.assertEqual(self.stored_names(), set())

    def test_invalid_later_image_does_not_persist_earlier_batch_member(self):
        with patch.object(default_storage, 'save', wraps=default_storage.save) as save:
            response = self.client.post(self.endpoint, {
                'question_uuid': str(self.question.uuid),
                'file': [upload('PNG'), upload('JPEG', invalid_icc=True)],
            }, format='multipart')
        self.assertEqual(response.status_code, 400, response.data)
        save.assert_not_called()
        self.assertFalse(Answer.objects.filter(session=self.session).exists())
        self.assertEqual(self.stored_names(), set())


class TestImageModelPersistenceSanitization(IsolatedImageStorageMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.signal = SignalFactory.create()

    def test_attachment_assignment_and_update_fields_replacement(self):
        attachment = Attachment(_signal=self.signal)
        attachment.file = upload('JPEG')
        attachment.save()
        self.assert_clean_image(attachment.file.name, 'JPEG')
        old_name = attachment.file.name

        attachment.file = upload('PNG')
        attachment.save(update_fields=['file'])
        attachment.refresh_from_db()
        self.assertNotEqual(attachment.file.name, old_name)
        self.assertEqual(attachment.mimetype, 'image/png')
        self.assertTrue(attachment.is_image)
        self.assert_clean_image(attachment.file.name, 'PNG')

    def test_fieldfile_save_without_model_save_sanitizes_immediately(self):
        for model in (Attachment, StoredFile):
            with self.subTest(model=model.__name__):
                instance = model(_signal=self.signal) if model is Attachment else model()
                instance.file.save('synthetic.gif', upload('GIF'), save=False)
                self.assertIsNone(instance.pk)
                self.assert_clean_image(instance.file.name, 'GIF')
                instance.save()
                instance.refresh_from_db()
                self.assert_clean_image(instance.file.name, 'GIF')

    def test_stored_file_assignment_and_replacement(self):
        stored_file = StoredFile.objects.create(file=upload('PNG'))
        self.assert_clean_image(stored_file.file.name, 'PNG')
        stored_file.file = upload('JPEG')
        stored_file.save(update_fields=['file'])
        stored_file.refresh_from_db()
        self.assert_clean_image(stored_file.file.name, 'JPEG')

    def test_fieldfile_replacement_then_update_fields_preserves_image_attributes(self):
        attachment = Attachment.objects.create(_signal=self.signal, file=upload('JPEG'))
        attachment.file.save('replacement.png', upload('PNG'), save=False)
        self.assert_clean_image(attachment.file.name, 'PNG')
        attachment.save(update_fields=['file'])
        attachment.refresh_from_db()
        self.assertEqual(attachment.mimetype, 'image/png')
        self.assertTrue(attachment.is_image)

    def test_invalid_new_files_are_rejected_before_fieldfile_storage(self):
        for model in (Attachment, StoredFile):
            for fieldfile_save in (False, True):
                with self.subTest(model=model.__name__, fieldfile_save=fieldfile_save):
                    instance = model(_signal=self.signal) if model is Attachment else model()
                    incoming = upload('JPEG', invalid_icc=True)
                    with patch.object(default_storage, 'save', wraps=default_storage.save) as save:
                        with self.assertRaises(ValidationError):
                            if fieldfile_save:
                                instance.file.save(incoming.name, incoming, save=False)
                            else:
                                instance.file = incoming
                                instance.save()
                    save.assert_not_called()
                    self.assertIsNone(instance.pk)
                    self.assertEqual(self.stored_names(), set())

    def test_failed_replacement_preserves_database_reference_and_storage(self):
        for model in (Attachment, StoredFile):
            with self.subTest(model=model.__name__):
                kwargs = {'_signal': self.signal} if model is Attachment else {}
                instance = model.objects.create(file=upload('PNG'), **kwargs)
                original_name = instance.file.name
                before = self.stored_names()
                instance.file = upload('JPEG', invalid_icc=True)
                with patch.object(default_storage, 'save', wraps=default_storage.save) as save:
                    with self.assertRaises(ValidationError):
                        instance.save(update_fields=['file'])
                save.assert_not_called()
                instance.refresh_from_db()
                self.assertEqual(instance.file.name, original_name)
                self.assertEqual(self.stored_names(), before)
                self.assert_clean_image(original_name, 'PNG')

    def legacy_attachment(self):
        # Seed a pre-existing unsanitized blob without exercising the new write boundary.
        name = default_storage.save('legacy/synthetic.jpg', ContentFile(image_bytes()))
        return Attachment.objects.create(
            _signal=self.signal, file=name, mimetype='image/jpeg', is_image=True,
        )

    def test_child_attachment_copy_sanitizes_legacy_source(self):
        source = self.legacy_attachment()
        child = SignalFactory.create(parent=self.signal)
        copied, = Signal.actions.copy_attachments([source], child, 'synthetic@example.com')
        copied.refresh_from_db()
        self.assertEqual(copied._signal_id, child.pk)
        self.assertNotEqual(copied.file.name, source.file.name)
        self.assert_clean_image(copied.file.name, 'JPEG')

    def test_forwarding_explanation_sanitizes_legacy_attachment(self):
        self.legacy_attachment()
        self.signal.status.state = DOORGEZET_NAAR_EXTERN
        self.signal.status.email_override = 'synthetic@example.com'
        self.signal.status.save()
        session = create_session_for_forward_to_external(self.signal)
        stored_file = StoredFile.objects.get()
        self.assertTrue(stored_file.attached_files.filter(
            section__illustrated_text=session.questionnaire.explanation,
        ).exists())
        self.assert_clean_image(stored_file.file.name, 'JPEG')

    def test_forwarding_response_copy_sanitizes_legacy_questionnaire_blob(self):
        self.signal.status.state = DOORGEZET_NAAR_EXTERN
        self.signal.status.email_override = 'synthetic@example.com'
        self.signal.status.save()
        session = create_session_for_forward_to_external(self.signal)
        question = session.questionnaire.graph.edges.get().next_question
        name = default_storage.save('legacy/questionnaire.jpg', ContentFile(image_bytes()))
        AnswerFactory.create(session=session, question=question, payload=[
            {'original_filename': 'synthetic.jpg', 'file_path': name},
        ])
        service = ForwardToExternalSessionService(session)
        service.refresh_from_db()
        service._copy_attachments_from_session_to_signal()
        attachment = self.signal.attachments.get()
        self.assertEqual(attachment.created_by, 'synthetic@example.com')
        self.assert_clean_image(attachment.file.name, 'JPEG')
