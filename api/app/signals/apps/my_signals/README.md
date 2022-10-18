# My Signals

_Currently, this app is in active development_  

The "my signals" app provides a way for reporters to get an overview of the signals they created over the last 12 months.

A reporter can request a login link that will be sent by email to the provided email address. This link is valid for X amount of time. The default is set to 2 hours and can be changed setting the `MY_SIGNALS_TOKEN_EXPIRES_SECONDS` env variable.

To request access to "my signals" the following flow must be followed:
* The reporter has received an email when he/she created a signal and left their email address
  * This email will contain a link to the "request access" page
* The reporter will "request access" with the email address they provided when creating a signal
* If over the last 12 months one or more signals have been created with this email address as the `Reporter.email` an email will be sent
  * This email will provide a token that can be set as a header to all other "My signals" calls, `Authorisation: Token { TOKEN }`
  * This link can be configured by setting the `MY_SIGNALS_LOGIN_URL` env variable

# TODO
* [ ] Implement history

## App structure

```
/my_signals
    /rest_framework             All rest framework related files
        /fields
        /filters
        /serializers
        /views
    /templates
        /my_signals/swagger     The swagger documentation for this app
    /tests
        /rest_framework
```

## Endpoints

### /signals/v1/my/signals/request-auth-token

Method: POST  
Status code: 200  
Request:   
```json
{
  "email": "reporter@example.com"
}
```
Response: 
```json
```

### /signals/v1/my/signals

Method: GET  
Status code: 200  
Header: Authorization: Token {{ TOKEN }}  
Response: 
```json
{
    "_links": {
        "self": {
            "href": "http://127.0.0.1:8000/signals/v1/my/signals?page_size=2"
        },
        "next": {
            "href": "http://127.0.0.1:8000/signals/v1/my/signals?page=2&page_size=2"
        },
        "previous": {
            "href": null
        }
    },
    "count": 100,
    "results": [
        {
            "_links": {
                "curies": {
                    "name": "sia",
                    "href": "http://127.0.0.1:8000/signals/v1/relations"
                },
                "self": {
                    "href": "http://127.0.0.1:8000/signals/v1/my/signals/46aac42b-6083-40cd-8857-279e5b76ca07"
                }
            },
            "_display": "SIG-100",
            "uuid": "46aac42b-6083-40cd-8857-279e5b76ca07",
            "id_display": "SIG-100",
            "text": "Everyone power method friend. Machine star eat ahead unit.",
            "status": {
                "state": "CLOSED",
                "state_display": "Afgesloten"
            },
            "created_at": "2022-10-03T10:51:33.101530+02:00"
        },
        {
            "_links": {
                "curies": {
                    "name": "sia",
                    "href": "http://127.0.0.1:8000/signals/v1/relations"
                },
                "self": {
                    "href": "http://127.0.0.1:8000/signals/v1/my/signals/887f19df-6dac-43d5-886f-3c6036de38ec"
                }
            },
            "_display": "SIG-99",
            "uuid": "887f19df-6dac-43d5-886f-3c6036de38ec",
            "id_display": "SIG-99",
            "text": "Weight occur successful another spend mind. Least true push many difference. After course fact.",
            "status": {
                "state": "OPEN",
                "state_display": "Open"
            },
            "created_at": "2022-10-03T10:51:33.080447+02:00"
        }
    ]
}
```

Method: GET  
Status code: 401  
Response: 
```json
{
  "detail": "Invalid token."
}
```

Method: GET  
Status code: 404  
Response: 
```json
{
  "detail": "Niet gevonden."
}
```

### /signals/v1/my/signals/{uuid}

Method: GET  
Status code: 200  
Header: Authorization: Token {{ TOKEN }}  
Response: 
```json
{
    "_links": {
        "curies": {
            "name": "sia",
            "href": "http://127.0.0.1:8000/signals/v1/relations"
        },
        "self": {
            "href": "http://127.0.0.1:8000/signals/v1/my/signals/46aac42b-6083-40cd-8857-279e5b76ca07"
        },
        "archives": {
            "href": "http://127.0.0.1:8000/signals/v1/my/signals/46aac42b-6083-40cd-8857-279e5b76ca07/history"
        },
        "sia:attachments": [
            {
                "href": "http://127.0.0.1:8000/signals/media/attachments/2022/10/03/shutterstock_151256423.jpg",
                "created_by": null,
                "created_at": "2022-10-03T10:58:13.260177Z"
            },
            {
                "href": "http://127.0.0.1:8000/signals/media/attachments/2022/10/03/long-1.jpg",
                "created_by": null,
                "created_at": "2022-10-03T09:53:45.434161Z"
            }
          ]
    },
    "_display": "SIG-100",
    "uuid": "46aac42b-6083-40cd-8857-279e5b76ca07",
    "id_display": "SIG-100",
    "text": "Everyone power method friend. Machine star eat ahead unit.",
    "status": {
        "state": "CLOSED",
        "state_display": "Afgesloten"
    },
    "location": {
        "address": {
            "postcode": "1011AA",
            "huisnummer": 666,
            "woonplaats": "Ergens",
            "openbare_ruimte": "Sesamstraat"
        },
        "address_text": "Sesamstraat 666 1011AA Ergens",
        "geometrie": {
            "type": "Point",
            "coordinates": [
                4.66284698634491,
                52.4368224806247
            ]
        }
    },
    "extra_properties": {},
    "created_at": "2022-10-03T10:51:33.101530+02:00"
}
```

Method: GET  
Status code: 401  
Response: 
```json
{
  "detail": "Invalid token."
}
```

Method: GET  
Status code: 404  
Response: 
```json
{
  "detail": "Niet gevonden."
}
```

### /signals/v1/my/signals/{uuid}/history

Method: GET  
Status code: 501  
Header: Authorization: Token {{ TOKEN }}  
Response: 
```json
```

Method: GET  
Status code: 401  
Response: 
```json
{
  "detail": "Invalid token."
}
```

Method: GET  
Status code: 404  
Response: 
```json
{
  "detail": "Niet gevonden."
}
```

## Feature flag
 
* MY_SIGNALS_ENABLED (By default is set to False)
