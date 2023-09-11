# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from elasticsearch_dsl import Boolean, Document, Integer, Keyword, Text

from signals.apps.search.settings import app_settings


class StatusMessage(Document):
    id = Integer()
    title = Text(analyzer='dutch')
    text = Text(analyzer='dutch')
    state = Keyword()
    active = Boolean()

    class Index:
        name = app_settings.CONNECTION['STATUS_MESSAGE_INDEX']
