Requirements
============

The requirements are used to setup and run the project.

Structure
=========

```
/requirements       # The requirements (without any versioning)
    req-base.txt    # Contains all packages needed to run the project (Except for Django)
    req-dev.txt     # Contains all development packages and includes all files needed to run the project locally for development 
    req-test.txt    # Contains all packages for testing
requirements.txt    # The frozen requirements set for deployment
```

Development
===========

For development you can use install the requirements/req-dev.txt

```
pip install -r requirements/req-dev.txt
```

This will make sure all required packages are installed including the test packages.
It also installs any package needed for development. For now it will add django-debug-toolbar. 
But if we need other packages for development we can add them here

Freeze requirements for deployment
==================================

The requirements.txt contains all the frozen packages that are confirmed working.

***Only overwrite this file with a new set of frozen packages if all tests are still passing!!!*** 
