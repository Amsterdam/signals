import os

from graphene_django.utils import GraphQLTestCase

from signals.apps.signals.models import Category

THIS_DIR = os.path.dirname(__file__)


class TestCategoryGraphQL(GraphQLTestCase):
    GRAPHQL_URL = '/signals/graphql'
    GRAPHQL_SCHEMA = os.path.join(os.path.split(THIS_DIR)[0], '..', 'schema', 'schema.json')

    def test_get_list(self):
        response = self.query(
            '''
            query {
                categories(first: 50 orderBy: "slug") {
                    edges {
                        node {
                            id
                            name
                            description
                            slug
                            handlingMessage
                            isActive
                            slo(first: 50) {
                                edges {
                                    node {
                                        id
                                        nDays
                                        useCalendarDays
                                        createdAt
                                    }
                                }
                            }
                            departments(first: 50) {
                                edges {
                                    node {
                                        id
                                        name
                                        code
                                        isIntern
                                    }
                                }
                            }
                            statusMessageTemplates(first: 50) {
                                edges {
                                    node {
                                        id
                                        title
                                        text
                                        state
                                    }
                                }
                            }
                        }
                    }
                }
            }
            '''
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json['data']['categories']['edges']), 50)

    def test_get_detail(self):
        response = self.query(
            '''
            query {
                categories(first: 1) {
                    edges {
                        node {
                            id
                            slug
                        }
                    }
                }
            }
            '''
        )
        response_json = response.json()
        self.assertEqual(len(response_json['data']['categories']), 1)
        categroy_graphql_id = response_json['data']['categories']['edges'][0]['node']['id']
        categroy_graphql_slug = response_json['data']['categories']['edges'][0]['node']['slug']

        response = self.query(
            '''
            query($id: ID!) {
                category(id: $id) {
                    id
                    name
                    description
                    slug
                    handlingMessage
                    isActive
                    slo(first: 50) {
                        edges {
                            node {
                                id
                                nDays
                                useCalendarDays
                                createdAt
                            }
                        }
                    }
                    departments(first: 50) {
                        edges {
                            node {
                                id
                                name
                                code
                                isIntern
                            }
                        }
                    }
                    statusMessageTemplates(first: 50) {
                        edges {
                            node {
                                id
                                title
                                text
                                state
                            }
                        }
                    }
                }
            }
            ''',
            variables={'id': categroy_graphql_id}
        )
        self.assertEqual(response.status_code, 200)

        category = Category.objects.get(slug=categroy_graphql_slug)
        response_json = response.json()
        self.assertEqual(response_json['data']['category']['id'], categroy_graphql_id)
        self.assertEqual(response_json['data']['category']['name'], category.name)
        self.assertEqual(response_json['data']['category']['description'], category.description)
        self.assertEqual(response_json['data']['category']['slug'], category.slug)
        self.assertEqual(response_json['data']['category']['handlingMessage'], category.handling_message)
        self.assertEqual(response_json['data']['category']['isActive'], category.is_active)
