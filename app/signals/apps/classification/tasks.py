from signals.apps.classification.train import TrainClassifier
from signals.celery import app


@app.task
def train_classifier(training_set_id):
    TrainClassifier(training_set_id).run()



