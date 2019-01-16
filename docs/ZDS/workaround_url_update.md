# ZDS Connection
To connect a Signal to the ZDS components, we send the SIA v0 url to the ZDS components.

At some time in the future the v0 api will be offline. How about all the older ZDS Cases?
How can we update the urls?

Simple we can not update the urls.

What we can do is add an extra connection with the newer url. (example v1 url)

What do we need to do?

We will need to set `connected_in_external_system` and `sync_completed` to `False` for all the
`CaseSignals`

Once this is done the `sync_zds` should take care of adding the new url to the case.
