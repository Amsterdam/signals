# Exceptions

[back](./readme.md)

This are some default exceptions. Some exceptions that are returned from the `ZDS Components` will
be catched. These Exceptions will be thrown so we know how to handle it further.

So if we get the CaseNotCreatedException we will know that we don't have to continue connecting the
`melding` to the case.


## CaseNotCreatedException
The case was not created. We should not do any other steps.

## DocumentNotCreatedException
The document was not created. We should not try to connect the document to the case.

## CaseConnectionException
The case could not be connected to the `melding`. We need to try it again later.

## StatusNotCreatedException
The status could not be added to the case. We need to try it again later.

## DocumentConnectionException
The document could not be connected to the case. We need to try it again later.
