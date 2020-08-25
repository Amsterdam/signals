import graphene

import signals.apps.graphql.query
from signals.apps.graphql.mutation import DeleteQuestion, QuestionMutation


class Query(signals.apps.graphql.query.CategoryQuery,
            signals.apps.graphql.query.DepartmentQuery,
            signals.apps.graphql.query.QuestionQuery,
            graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_question = QuestionMutation.Field()
    update_question = QuestionMutation.Field()
    delete_question = DeleteQuestion.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
