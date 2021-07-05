# Questionnaires

This app provides the possibility to create Questionnaires.

**Currently the app is in active development**  

# TODO

* [ ] Make sure that a Questionnaire is valid (no circularity or endless flow of questions)
* [ ] Make the Question reusable
* [ ] Add more validation options for a Question/Answer
* [ ] ... (add more todo here if needed)


## App structure

```
/questionnaires         Root of the Questionnaires Django app
    /forms
    /migrations         Django migrations
    /rest_framework     All rest framework related files
        /views          The API views
    /templates          
    /tests              All tests
```

## Models

### Questionnaire

A model to containing a set of questions. The goal of a Questionnaire is to gather information about a specific subject. 
For example: Based on categorisation of a Signal the system needs more information, or after handling a Signal the 
systems sends a satisfaction survey to the citizen.

The *Questionnaire* model:
* id
* uuid
* name
* description
* is_active
* first_question       *Starting point of the questionnaire*
* created_at

### Question

A Question for a specific questionnaire. Based on the given field_type certain validation will be provided for given 
answers. At this moment (14-06-2021) there are 3 field_types that can be used. Text, integer and submit.

The payload contains a json structure given the Quesiton some extra properties, like a label and a shortLabel. The most 
interesting option is that you can specify the next question here. If given this must be an array containing at 
least 1 item, the actual next question. It is also possible to specify next questions based on a given answer.

The *Question* model:
* id
* uuid
* key
* field_type
* payload
* required
* root
* created_at

### Answer

The answer given for a specific question/session combination. The question needs to be part of the questionnaire that 
the session is for. The answer payload is validated against the Question.field_type 

The *Answer* model:
* id
* question
* session
* payload

### Session

A session setup for a specific questionnaire. This will hold all the answers given. If the submit_before is set the 
session will be invalid if passed, otherwise when starting to answer question the started_at + duration will be used as 
the "submit_before".

The *Session* model:
* id
* uuid
* submit_before
* started_at
* duration
* questionnaire
* frozen
* created_at

## Environment Variables
 
* None, so far
