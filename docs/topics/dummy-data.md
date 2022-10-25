# How to setup dummy data

## docker-compose

When starting with a fresh new checkout of the project it is possible to start-up the API using
`docker-compose up -d api`. This will start the API using the 
[docker-compose/scripts/initialize.sh](../../docker-compose/scripts/initialize.sh) script.

The script will check if the environment variable `INITIALIZE_WITH_DUMMY_DATA` is set to 1 
(by default this functionality is turned of). If so the script will reset the database and setup 
some dummy data for you using the management commands explained a little bit later in this document.
The `app/initialize.log` will contain a line with the date time when the initialize has run. The 
line will have the following format: `[2020-11-10T00:00:00+0000] - Done!!!`

## Management commands for dummy data

If for some reason you do not want to use the docker-compose method or add more dummy data later 
there are several management commands that can help you. Just login to the docker container 
(or how ever you have setup the API locally) and run one or more of the following commands.

### dummy_categories
```
usage: manage.py dummy_categories [-h] [--parent-slug PARENT_SLUG] [--parents-to-create PARENTS_TO_CREATE] [--children-to-create CHILDREN_TO_CREATE] [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                                  [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  --parent-slug PARENT_SLUG
                        If given the child elements will be created for this Parent. If used this will overrule the option--parents-to-create
  --parents-to-create PARENTS_TO_CREATE
                        Total random parent Categories to create (max 10). Default 1.
  --children-to-create CHILDREN_TO_CREATE
                        Total random child Categories per parent Category to create (max 10). Default 1 per parent Category.
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```

### dummy_departments
```
usage: manage.py dummy_departments [-h] [--to-create TO_CREATE] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  --to-create TO_CREATE
                        Total random Departments to create (max 10). Default 1.
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```

### dummy_sources
```
usage: manage.py dummy_sources [-h] [--to-create TO_CREATE] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  --to-create TO_CREATE
                        Total random Sources to create (max 10). Default 1.
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```

### dummy_signals
```
usage: manage.py dummy_signals [-h] [--to-create TO_CREATE] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  --to-create TO_CREATE
                        Total random Signals to create (max 1000). Default 100.
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```
