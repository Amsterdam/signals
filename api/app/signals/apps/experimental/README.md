# Experimental


Contains functionality that is still in the experimental phase.

**All functionality in this app can be removed at any time or if accepted will find its way into the codebase.**


## signals/experimental/private/signals

A newer version of the already existing **signals/v1/private/signals** endpoint.  

### Why is this endpoint created?

The *signals/v1/private/signals* endpoint is not the fastest endpoint implemented in the API. 
It contains a lot of data in the response and a combination of filters is slowing down the queries.  

To speed up the endpoint it is decided to add a database view containing all data used for filtering and creating 
minimal response. This principal is already implemented for the history of a Signal.

See Jira issue [SIG-3418](https://datapunt.atlassian.net/browse/SIG-3418) for more information.

## What is new in this experimental endpoint?

- The new experimental endpoint is only used to return a list of Signals and provide faster filtering
- The new experimental endpoint cannot be used to create, update or retrieve individual Signals
- A database view is used to filter against
- The response contains minimal data needed to render the FE list overview of Signals

### What is the same in this experimental endpoint?

- The new experimental endpoint contains all the same permission check as implemented on the V1 version of this call
- The filter parameters are kept the same
- Stored filters can also be used against this endpoint
