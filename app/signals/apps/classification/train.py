from datetime import datetime
import os
import re
import io

import pandas as pd
import nltk
from django.core.files.base import ContentFile
from django.db.models import F
from nltk.stem.snowball import DutchStemmer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, accuracy_score, ConfusionMatrixDisplay
import pickle
from django.conf import settings
from django.utils.text import slugify
import matplotlib

from signals.apps.signals import workflow
from signals.apps.signals.models import Signal

matplotlib.use('agg')

if settings.NLTK_DOWNLOAD_DIR:
    nltk.data.path.append(settings.NLTK_DOWNLOAD_DIR)

import matplotlib.pyplot as plt

from signals.apps.classification.models import TrainingSet, Classifier


class TrainClassifier:
    def __init__(self, training_set_ids, use_signals_in_database_for_training):
        self.training_set_ids = training_set_ids
        self.use_signals_in_database_for_training = use_signals_in_database_for_training
        self.training_sets = self.get_training_sets()
        self.df = None

        nltk.download('stopwords', download_dir=settings.NLTK_DOWNLOAD_DIR)

    def get_training_sets(self):
        return TrainingSet.objects.filter(pk__in=self.training_set_ids)

    def read_files(self):
        dataframes = []

        for training_set in self.training_sets:
            _, extension = os.path.splitext(training_set.file.name)

            if extension == '.xlsx':
                df = pd.read_excel(training_set.file)
            else:
                raise Exception(f'Unsupported file type: {extension} in {training_set.file.name}')

            dataframes.append(df)

        if dataframes:
            self.df = pd.concat(dataframes, ignore_index=True)
        else:
            self.df = pd.DataFrame()

    def read_database(self):
        if self.use_signals_in_database_for_training and self.use_signals_in_database_for_training != "False":
            signals = Signal.objects.filter(
                status__state=workflow.AFGEHANDELD,
                category_assignment__category__is_active=True,
                category_assignment__category__parent__is_active=True
            ).exclude(
                category_assignment__category__slug="overig",
                category_assignment__category__parent__slug="overig"
            ).values(
                'text',
                sub_category=F('category_assignment__category__name'),
                main_category=F('category_assignment__category__parent__name'),
            )

            data = [{
                "Sub": signal["sub_category"],
                "Main": signal["main_category"],
                "Text": signal["text"]
            } for signal in signals]

            signals_df = pd.DataFrame(data)

            self.df = pd.concat([self.df, signals_df], ignore_index=True)

    def preprocess_data(self):
        self.df = self.df.dropna(axis=0)

        self.df = (
            self.df.groupby("Sub")
                   .apply(lambda x: x.sample(n=min(len(x), 5000), random_state=42))
                   .reset_index(drop=True)
        )

    def stopper(self):
        stop_words = list(set(nltk.corpus.stopwords.words('dutch')))
        return stop_words

    def preprocessor(self, text):
        stemmer = DutchStemmer(ignore_stopwords=True)

        text = str(text)
        text = text.lower()

        words = re.split("\\s+", text)
        stemmed_words = [stemmer.stem(word=word) for word in words]
        return ' '.join(stemmed_words)

    def train_test_split(self, columns):
        labels = self.df[columns].map(lambda x: slugify(x)).apply('|'.join, axis=1)

        return train_test_split(
            self.df["Text"], labels, test_size=0.2, stratify=labels
        )

    def train_model(self, train_texts, train_labels):
        stop_words = self.stopper()

        pipeline = Pipeline([
            ('vect', CountVectorizer(preprocessor=self.preprocessor, stop_words=stop_words)),
            ('tfidf', TfidfTransformer()),
            ('clf', LogisticRegression()),
        ])

        parameters_slow = {
            'clf__class_weight': (None, 'balanced'),
            'clf__max_iter': (300, 500),
            'clf__penalty': ('l1',),
            'clf__multi_class': ('auto',),
            'clf__solver': ('liblinear',),
            'tfidf__norm': ('l2',),
            'tfidf__use_idf': (False,),
            'vect__max_df': (1.0,),
            'vect__max_features': (None,),
            'vect__ngram_range': ((1, 1), (1, 2))
        }

        grid_search = GridSearchCV(pipeline, parameters_slow, verbose=True, n_jobs=1, cv=5)
        grid_search.fit(train_texts, train_labels)

        return grid_search

    def evaluate_model(self, model, test_texts, test_labels):
        test_predict = model.predict(test_texts)
        precision = precision_score(test_labels, test_predict, average='macro', zero_division=0)
        recall = recall_score(test_labels, test_predict, average='macro')
        accuracy = accuracy_score(test_labels, test_predict)

        plt.rcParams["figure.figsize"] = (30,30)

        confusion_matrix = ConfusionMatrixDisplay.from_predictions(
            y_true=test_labels,
            y_pred=test_predict,
            xticks_rotation='vertical',
            cmap="Blues"
        )

        pdf = io.BytesIO()
        plt.savefig(pdf, format="pdf")
        confusion_matrix_pdf = pdf.getvalue()
        pdf.close()

        return (precision, recall, accuracy), confusion_matrix_pdf

    def save_model(self, main_model, sub_model, scores):
        pickled_main_model = pickle.dumps(main_model, pickle.HIGHEST_PROTOCOL)
        pickled_sub_model = pickle.dumps(sub_model, pickle.HIGHEST_PROTOCOL)

        precision, recall, accuracy = scores

        classifier = Classifier.objects.create(
            main_model=ContentFile(pickled_main_model, '_main_model.pkl'),
            sub_model=ContentFile(pickled_sub_model, '_sub_model.pkl'),
            precision=precision,
            recall=recall,
            accuracy=accuracy,
            name=f"model-{datetime.now().strftime('%d-%m-%Y-%H:%M')}",
            is_active=False
        )

        classifier.save()

    def create_model(self):
        classifier = Classifier.objects.create(
            name=f"model-{datetime.now().strftime('%d-%m-%Y-%H:%M')}",
            is_active=False,
            training_status="RUNNING",
        )

        return classifier

    def persist_model(self, classifier, main_model, sub_model, scores, main_confusion_matrix, sub_confusion_matrix):
        pickled_main_model = pickle.dumps(main_model, pickle.HIGHEST_PROTOCOL)
        pickled_sub_model = pickle.dumps(sub_model, pickle.HIGHEST_PROTOCOL)

        precision, recall, accuracy = scores

        classifier.main_model = ContentFile(pickled_main_model, '_main_model.pkl')
        classifier.sub_model = ContentFile(pickled_sub_model, '_sub_model.pkl')
        classifier.main_confusion_matrix = ContentFile(main_confusion_matrix, '_main_confusion_matrix.pdf')
        classifier.sub_confusion_matrix = ContentFile(sub_confusion_matrix, '_sub_confusion_matrix.pdf')
        classifier.precision=precision
        classifier.recall=recall
        classifier.accuracy=accuracy
        classifier.save()

    def update_status(self, classifier, status, error):
        classifier.training_status = status
        classifier.training_error = error
        classifier.save()

    def run(self):
        self.read_files()
        self.read_database()
        self.preprocess_data()

        classifier = self.create_model()

        try:
            # Train main model
            train_texts, test_texts, train_labels, text_labels = self.train_test_split(['Main'])
            main_model = self.train_model(train_texts, train_labels)
            main_scores, main_confusion_matrix = self.evaluate_model(main_model, test_texts, text_labels)

            # Train sub model
            train_texts, test_texts, train_labels, text_labels = self.train_test_split(['Main', 'Sub'])
            sub_model = self.train_model(train_texts, train_labels)
            sub_scores, sub_confusion_matrix = self.evaluate_model(sub_model, test_texts, text_labels)

            # scores te delen
            scores = [(x + y) / 2 for x, y in zip(main_scores, sub_scores)]

            self.persist_model(classifier, main_model, sub_model, scores, main_confusion_matrix, sub_confusion_matrix)
            self.update_status(classifier, 'COMPLETED', None)
        except ValueError as e:
            self.update_status(classifier, 'FAILED', e)

