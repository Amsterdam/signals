import pickle
import re
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from nltk.stem.snowball import DutchStemmer

from signals.apps.classification.models import Classifier


# =============================================================================
# Mock objects for unpickling old models
# =============================================================================
# Old models reference an 'engine' module that may not exist in the current
# codebase. We create a minimal mock to allow pickle to load these models.

class _TextClassifier:
    """Mock TextClassifier for unpickling old models that reference engine.TextClassifier."""

    @staticmethod
    def preprocessor(text):
        """Dutch text preprocessor (required by old models during unpickling)."""
        return ' '.join([DutchStemmer().stem(word) for word in text.split()])


sys.modules['engine'] = type(sys)('engine')
sys.modules['engine'].TextClassifier = _TextClassifier


# =============================================================================
# Sklearn compatibility shim
# =============================================================================
# Old models (sklearn 1.0.2) reference _passthrough_scorer which doesn't exist
# in newer sklearn versions. We create it to allow unpickling.

import sklearn.metrics._scorer
if not hasattr(sklearn.metrics._scorer, '_passthrough_scorer'):
    from sklearn.metrics import make_scorer
    sklearn.metrics._scorer._passthrough_scorer = make_scorer(lambda y_true, y_pred: 0)


def transform_main_slug(slug: str) -> str:
    """Transform /categories/afval -> afval"""
    if slug.startswith('/categories/'):
        return slug.split('/categories/')[-1].rstrip('/')
    return slug


def transform_sub_slug(slug: str) -> str:
    """Transform /categories/afval/sub_categories/container -> afval|container"""
    if '|' in slug:
        return slug

    match = re.match(r'.*/categories/([^/]+)/sub_categories/([^/]+)/?$', slug)
    if match:
        return f"{match.group(1)}|{match.group(2)}"
    return slug


def transform_model(model_path: Path, slugs_path: Path, model_type: str):
    """Load model and slugs, transform, and return transformed model."""
    # Load model (GridSearchCV with Pipeline)
    model = joblib.load(model_path)

    # Load and transform slugs
    with open(slugs_path, 'rb') as f:
        slugs = pickle.load(f)

    if model_type == 'main':
        slugs = np.array([transform_main_slug(s) for s in slugs])
    else:  # sub
        slugs = np.array([transform_sub_slug(s) for s in slugs])

    # Set classes_ on the classifier (last step in pipeline)
    clf = model.best_estimator_.steps[-1][1]
    clf.classes_ = slugs

    # Clean up scorer references that cause issues when loading in other contexts
    # Replace custom scorer with None so it doesn't reference _passthrough_scorer_func
    if hasattr(model, 'scorer_'):
        model.scorer_ = None
    if hasattr(model, 'multimetric_'):
        model.multimetric_ = False

    return model, len(slugs)


class Command(BaseCommand):
    help = "Import old-format classification models and save as a new Classifier"

    def add_arguments(self, parser):
        parser.add_argument(
            '--main-model',
            type=str,
            required=True,
            help='Path to main_model.pkl file',
        )
        parser.add_argument(
            '--main-slugs',
            type=str,
            required=True,
            help='Path to main_slugs.pkl file',
        )
        parser.add_argument(
            '--sub-model',
            type=str,
            required=True,
            help='Path to sub_model.pkl file',
        )
        parser.add_argument(
            '--sub-slugs',
            type=str,
            required=True,
            help='Path to sub_slugs.pkl file',
        )
        parser.add_argument(
            '--activate',
            action='store_true',
            help='Set the imported model as active',
        )

    def handle(self, *args, **options):
        # Validate file paths
        main_model_path = Path(options['main_model'])
        main_slugs_path = Path(options['main_slugs'])
        sub_model_path = Path(options['sub_model'])
        sub_slugs_path = Path(options['sub_slugs'])

        for path, name in [
            (main_model_path, '--main-model'),
            (main_slugs_path, '--main-slugs'),
            (sub_model_path, '--sub-model'),
            (sub_slugs_path, '--sub-slugs'),
        ]:
            if not path.exists():
                raise CommandError(f'{name} file does not exist: {path}')

        # Check if there's already an active trained model
        active_classifier = Classifier.objects.filter(is_active=True).first()
        if active_classifier and active_classifier.precision is not None:
            raise CommandError(
                f'Active classifier #{active_classifier.id} is already a trained model with metrics. '
                'Importing old models is only allowed when no trained model is active.'
            )

        # Generate name with timestamp
        classifier_name = f"Geimporteerd model {datetime.now().strftime('%d-%m-%Y %H:%M')}"

        self.stdout.write(self.style.SUCCESS('Starting model transformation and import...'))

        try:
            # Transform main model
            self.stdout.write('Transforming main model...')
            main_model, main_categories = transform_model(
                main_model_path,
                main_slugs_path,
                'main'
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Main model transformed ({main_categories} categories)'))

            # Transform sub model
            self.stdout.write('Transforming sub model...')
            sub_model, sub_categories = transform_model(
                sub_model_path,
                sub_slugs_path,
                'sub'
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Sub model transformed ({sub_categories} categories)'))

            # Pickle the transformed models
            pickled_main_model = pickle.dumps(main_model, pickle.HIGHEST_PROTOCOL)
            pickled_sub_model = pickle.dumps(sub_model, pickle.HIGHEST_PROTOCOL)

            # Create Classifier
            self.stdout.write('Saving as Classifier...')

            # If activating, deactivate all other classifiers first
            if options['activate']:
                deactivated_count = Classifier.objects.filter(is_active=True).update(is_active=False)
                if deactivated_count > 0:
                    self.stdout.write(f'  Deactivated {deactivated_count} existing classifier(s)')

            classifier = Classifier.objects.create(
                name=classifier_name,
                is_active=options['activate'],
                training_status='COMPLETED',
                precision=None,  # Old models don't have these metrics
                recall=None,
                accuracy=None,
            )

            classifier.main_model = ContentFile(pickled_main_model, '_main_model.pkl')
            classifier.sub_model = ContentFile(pickled_sub_model, '_sub_model.pkl')
            classifier.save()

            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully imported Classifier (ID: {classifier.id})'))
            self.stdout.write(f'  Name: {classifier.name}')
            self.stdout.write(f'  Main categories: {main_categories}')
            self.stdout.write(f'  Sub categories: {sub_categories}')
            self.stdout.write(f'  Active: {classifier.is_active}')

            if options['activate']:
                self.stdout.write(self.style.WARNING('\nNote: This model is now the active classifier.'))

        except Exception as e:
            raise CommandError(f'Failed to import model: {str(e)}')
