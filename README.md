# Meldingen
meldingen system amsterdam

The beginning of Signalen Amsterdam Rewrite.

Derived from POC git@github.com:Amsterdam/sia.git

https://vaarwatermeldingen.amsterdam.nl/

# TODO
* Better README
* Check parameters when creating Signal
* Test for filtering
* Throttle unauthorized posts. Determine values exclude IP from gemeente and frequent users.
* IP ranges in config
* Add user id from token and IP address to status change propertieds for audit logging


# Celery

We use celery for sending e-mails. That also requires a rabbitmq instance.

To start celery for testing we need to have SMTP settings in celery:

::

    export EMAIL_HOST=smtp.gmail.com
    export EMAIL_HOST_USER=<gmail_account>
    export EMAIL_HOST_PASSWORD=<gmail_password>
    export EMAIL_PORT=465
    export EMAIL_USE_SSL=True
    export EMAIL_USE_TLS=False

    celery -A signals worker -l info


RabbitMQ is run from a docker instance
If the rabbitmq image wash freshly installed we need to add a user with:

::

    docker-compose exec rabbit rabbitmqctl add_user signals insecure
    docker-compose exec rabbit rabbitmqctl add_vhost rabbitmq_signals
    docker-compose exec rabbit rabbitmqctl set_permissions -p rabbitmq_signals signals ".*" ".*" ".*"

...

