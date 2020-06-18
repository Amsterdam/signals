# W.I.P. GraphQL

This is an work in progress (W.I.P.) implementation of GraphQL and is not yet production ready.

Keep a close eye on this documentation to get more information about the status of the implementation in SIA.

## What is GraphQL

> GraphQL is a query language for APIs and a runtime for fulfilling those queries with your existing data. 
GraphQL provides a complete and understandable description of the data in your API, gives clients the power to ask for exactly what they need and nothing more, makes it easier to evolve APIs over time, and enables powerful developer tools. - [https://graphql.org/](https://graphql.org/]) 

More information about GraphQL and how to implement it in python/django:
* [https://graphql.org/](https://graphql.org/])
* [https://relay.dev/graphql/connections.htm](https://relay.dev/graphql/connections.htm)
* [https://graphene-python.org/](https://graphene-python.org/)

## Implementation in SIA

Only queries are available. Mutations are not implemented (yet).

At this moment only the **public** queries to get information about categories and departments are implemented.

Path:
* {URL_TO_API}/signals/graphql

### Examples

Request:
```
query {
  categories(first:5 orderBy: "slug") {
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    edges {
      node {
        id
        name
      }
    }
  }  
}

```

Response:
```
{
  "data": {
    "categories": {
      "pageInfo": {
        "hasNextPage": true,
        "hasPreviousPage": false,
        "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
        "endCursor": "YXJyYXljb25uZWN0aW9uOjQ="
      },
      "edges": [
        {
          "node": {
            "id": "Q2F0ZWdvcnlUeXBlOjc4",
            "name": "Afval"
          }
        },
        {
          "node": {
            "id": "Q2F0ZWdvcnlUeXBlOjE0NA==",
            "name": "Afwatering brug"
          }
        },
        {
          "node": {
            "id": "Q2F0ZWdvcnlUeXBlOjEw",
            "name": "Asbest / accu"
          }
        },
        {
          "node": {
            "id": "Q2F0ZWdvcnlUeXBlOjM0",
            "name": "Auto- / scooter- / bromfiets(wrak)"
          }
        },
        {
          "node": {
            "id": "Q2F0ZWdvcnlUeXBlOjkx",
            "name": "Autom. Verzinkbare palen"
          }
        }
      ]
    }
  }
}
```

Request:
```
query{
  department(id:"RGVwYXJ0bWVudFR5cGU6Ng==") {
    id
    name
    code
    isIntern
  }
}
```

Response:
```
{
  "data": {
    "department": {
      "id": "RGVwYXJ0bWVudFR5cGU6Ng==",
      "name": "Actie Service Centrum",
      "code": "ASC",
      "isIntern": true
    }
  }
}
```
