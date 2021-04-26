# Open Source dependencies

Signalen would not be possible without a number of other Open Source dependencies.

The backend is written in [Python](https://www.python.org/) utilizing the [Django framework](https://www.djangoproject.com/).
The Django framework is a stable, supported, and actively maintained.
While Django pulls in some <= 1.0 libraries (e.g.: sqlparse),
if there is an issue with these, the Django community can be trusted to address it.

A full list of dependencies of the backend can be generated with `pipdeptree`.
The majority of other dependices are stable.
Some exceptions include:

| library | mitigation | notes |
|---------|------------|-------|
| jwcrypto | codebase is active, developers can work with upstream |needs documenting (token valadation and user authentication code)|
| drf-amsterdam | Signalen developers maintain this | |
| [entrypoints](https://pypi.org/project/entrypoints/) | developers could maintain |(maybe not even needed) |
| [freezegun](https://pypi.org/project/freezegun/) | developers could maintain | will be updated to 1.x soon; used by tests to control the clock |
| wheel | mitigation not-needed | This library is the reference implementation of the Python wheel packaging standard, as defined in PEP 427.
| xmlunittest | can work with upstream if needed | only used by tests |

