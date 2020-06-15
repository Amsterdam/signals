import graphene

import signals.apps.graphql.query


class Query(signals.apps.graphql.query.CategoryQuery,
            signals.apps.graphql.query.DepartmentQuery,
            graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
