# My Signals

_Currently, this app is in active development_  

This app will return the signals created in the last 12 months by the logged in reporter.

# TODO

* [ ] Login/Authentication flow
* [ ] Implement history
* [ ] ... (add more here if needed)

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

### /signals/v1/my/signals

Method: GET  
Status code: 200  
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
Response: 
```json
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
