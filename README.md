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
* 
* Custom backend for django authentication that gives a user
* Extend Django  User for authentication
* Django admin for user maintenance
* Tables for categories, subcategories, departments 
* Admin maintenance for these tables 
* Add index on email for user table
* Add view for user. what am I. superusers can see all users
* Add management script to import users 




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


RabbitMQ is run from a docker instance.  In order to be able to use it we need to specify 
at startup the signala user and password and a vhost.

This is most easily using the default docker rabbitmq:3 and environment variables :

::

     - RABBITMQ_ERLANG_COOKIE='secret cookie here'
     - RABBITMQ_DEFAULT_USER=signals
     - RABBITMQ_DEFAULT_PASS=insecure
     - RABBITMQ_DEFAULT_VHOST=vhost

Otherwise we need to add a user with:

::

    docker-compose exec rabbit rabbitmqctl add_user signals insecure
    docker-compose exec rabbit rabbitmqctl add_vhost vhost
    docker-compose exec rabbit rabbitmqctl set_permissions -p rabbitmq_signals signals ".*" ".*" ".*"

...


# Admin

To maintain user and groups we use Django Admin. We cannot yet login to Djang Admin with JWT tokens so for 
this we need to set  a password for a staff account.  This is needed to login to Djang Admin 