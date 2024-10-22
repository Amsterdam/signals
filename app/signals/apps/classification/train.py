import os
import re

import pandas as pd
import nltk
from django.core.files.base import ContentFile
from nltk.stem.snowball import DutchStemmer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, accuracy_score
import pickle
from django.conf import settings
from django.utils.text import slugify

from signals.apps.classification.models import TrainingSet, Classifier


class TrainClassifier:
    def __init__(self, training_set_id):
        self.training_set_id = training_set_id
        self.training_set = self.get_training_set()
        self.df = None

        nltk.download('stopwords', download_dir=settings.NLTK_DOWNLOAD_DIR)

    def get_training_set(self):
        return TrainingSet.objects.get(pk=self.training_set_id)

    def read_file(self):
        _, extension = os.path.splitext(self.training_set.file.name)

        if extension == '.csv':
            self.df = pd.read_csv(self.training_set.file, sep=None, engine='python')
        elif extension == '.xlsx':
            self.df = pd.read_excel(self.training_set.file)
        else:
            raise Exception('Could not read input file. Extension should be .csv or .xlsx')

    def preprocess_file(self):
        self.df = self.df.dropna(axis=0)
        self.df["_main_label"] = self.df["Main"]
        self.df["_sub_label"] = f'{self.df["Main"]}|{self.df["Sub"]}'

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

        return precision, recall, accuracy

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
            name=self.training_set.name,
            is_active=False
        )

        classifier.save()

    def create_model(self):
        classifier = Classifier.objects.create(
            name=self.training_set.name,
            is_active=False,
            training_status="RUNNING",
        )

        return classifier

    def persist_model(self, classifier, main_model, sub_model, scores):
        pickled_main_model = pickle.dumps(main_model, pickle.HIGHEST_PROTOCOL)
        pickled_sub_model = pickle.dumps(sub_model, pickle.HIGHEST_PROTOCOL)

        precision, recall, accuracy = scores

        classifier.main_model = ContentFile(pickled_main_model, '_main_model.pkl')
        classifier.sub_model = ContentFile(pickled_sub_model, '_sub_model.pkl')
        classifier.precision=precision
        classifier.recall=recall
        classifier.accuracy=accuracy
        classifier.save()

    def update_status(self, classifier, status, error):
        classifier.training_status = status
        classifier.training_error = error
        classifier.save()

    def run(self):
        self.read_file()
        self.preprocess_file()

        classifier = self.create_model()

        try:
            # Train main model
            train_texts, test_texts, train_labels, text_labels = self.train_test_split(['Main'])
            main_model = self.train_model(train_texts, train_labels)
            main_scores = self.evaluate_model(main_model, test_texts, text_labels)

            # Train sub model
            train_texts, test_texts, train_labels, text_labels = self.train_test_split(['Main', 'Sub'])
            sub_model = self.train_model(train_texts, train_labels)
            sub_scores = self.evaluate_model(sub_model, test_texts, text_labels)

            # scores te delen
            scores = [(x + y) / 2 for x, y in zip(main_scores, sub_scores)]

            self.persist_model(classifier, main_model, sub_model, scores)
            self.update_status(classifier, 'COMPLETED', None)
        except ValueError as e:
            self.update_status(classifier, 'FAILED', e)

