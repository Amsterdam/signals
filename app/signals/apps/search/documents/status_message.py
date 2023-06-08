# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from elasticsearch_dsl import Boolean, Completion, Document, Integer, Keyword, Text


class StatusMessage(Document):
    id = Integer()
    title = Text(analyzer='dutch')
    text = Text(analyzer='dutch')
    state = Keyword()
    active = Boolean()
    suggest = Completion(analyzer='dutch')

    def clean(self):
        self.suggest = {'input': self.text}

    class Index:
        name = 'status_messages'
