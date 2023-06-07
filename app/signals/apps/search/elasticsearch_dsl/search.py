# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam
from elasticsearch_dsl import FacetedSearch, TermsFacet, Search

from signals.apps.search.documents.status_message import StatusMessage


class StatusMessagesSearch(FacetedSearch):
    """The Elasticsearch DSL library requires us to subclass FacetedSearch in order to
    configure a faceted search, which allows us to use filters and provides us with
    counts for each possible filter option.
    """
    index = 'status_messages'
    doc_types = (StatusMessage,)
    fields = ('title', 'text',)
    facets = {
        'state': TermsFacet(field='state', size=20, min_doc_count=0),
        'active': TermsFacet(field='active', min_doc_count=0),
    }

    def query(self, search: Search, query: str):
        """Overridden query method in order to set the fuzziness of the query and
        to provide the zero_terms_query option in order to get (all) results when
        no query term is provided.
        """
        return search.query(
            'multi_match',
            query=query,
            fields=self.fields,
            fuzziness='AUTO',
            zero_terms_query='all',
        )
