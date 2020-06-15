import os

from graphene_django.utils import GraphQLTestCase

from signals.apps.signals.models import Department

THIS_DIR = os.path.dirname(__file__)


class TestDepartmentGraphQL(GraphQLTestCase):
    GRAPHQL_URL = '/signals/graphql'
    GRAPHQL_SCHEMA = os.path.join(os.path.split(THIS_DIR)[0], '..', 'schema', 'schema.json')

    def test_get_list(self):
        response = self.query(
            '''
            query {
                departments(first: 50 orderBy: "code") {
                    edges {
                        node {
                            id
                            name
                            code
                            isIntern
                        }
                    }
                }
            }
            '''
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json['data']['departments']['edges']), Department.objects.count())

    def test_get_detail(self):
        response = self.query(
            '''
            query {
                departments(first: 1) {
                    edges {
                        node {
                            id
                            code
                        }
                    }
                }
            }
            '''
        )
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json['data']['departments']), 1)
        department_graphql_id = response_json['data']['departments']['edges'][0]['node']['id']
        department_graphql_code = response_json['data']['departments']['edges'][0]['node']['code']

        response = self.query(
            '''
            query($id: ID!) {
                department(id: $id) {
                    id
                    name
                    code
                    isIntern
                }
            }
            ''',
            variables={'id': department_graphql_id}
        )
        self.assertEqual(response.status_code, 200)

        department = Department.objects.get(code=department_graphql_code)
        response_json = response.json()
        self.assertEqual(response_json['data']['department']['id'], department_graphql_id)
        self.assertEqual(response_json['data']['department']['name'], department.name)
        self.assertEqual(response_json['data']['department']['code'], department.code)
        self.assertEqual(response_json['data']['department']['isIntern'], department.is_intern)
