# Managing dependencies
Managing the dependencies and their versions is crucial for maintaining a stable
and reliable application. This guide explains how to update the requirements
files using the provided [Makefile](../../app/Makefile).

## Prerequisites
Before installing/updating the requirements files, make sure you have the
following:

- Create A virtual environment
    ```
    python -m venv venv
    ```
- Activate the virtual environment 
    ```
    source venv/bin/activate
    ```
- pip-tools installed
    ```
    pip install pip-tools
    ```

## pip-tools

**pip-tools** is a command-line toolset for managing Python package
dependencies. It simplifies the management of requirements files, ensuring
consistent installations across environments. With pip-tools, you can easily
define and synchronize your project's dependencies, maintain reproducibility,
and manage isolated virtual environments.

For detailed instructions, refer to the
[pip-tools documentation](https://pip-tools.readthedocs.io/).

## File Structure
The three requirements files and their corresponding "in" files are located in
the `app/requirements` directory:

- [requirements.in](../../app/requirements/requirements.in): The main requirements
- [requirements_dev.in](../../app/requirements/requirements_dev.in): Requirements specific to development
- [requirements_test.in](../../app/requirements/requirements_test.in): Requirements specific to testing

## Updating the Requirements Files
To update the requirements files, follow these steps:

1. Open a terminal or command prompt and navigate to the root directory
2. Activate your virtual environment
    ```
    source venv/bin/activate
    ```
3. Run the following command to update the requirements files:
    ```
    make --directory app requirements
    ```
    This command uses pip-tools to compile the `*.in` files into `*.txt` files
    with pinned versions and resolves the dependencies 
4. After running the command, the updated requirements files will be generated:
    - [requirements.txt](../../app/requirements/requirements.txt): Contains the main requirements with pinned versions
    - [requirements_dev.txt](../../app/requirements/requirements_dev.txt): Contains development-specific requirements with pinned versions
    - [requirements_test.txt](../../app/requirements/requirements_test.txt): Contains requirements for testing with pinned versions
5. You can now review and modify the generated `*.txt` files if necessary

## Installing the Updated Requirements
To install the updated requirements in your virtual environment, follow these
steps:

- Ensure that your virtual environment is still activated. If not run:
    ```
    source venv/bin/activate
    ```
- Run the following command to install the project requirements:
    ```yaml
    make --directory app install
    ```
    This command will use `pip-tools` to install the dependencies
- After running the command, the required packages will be installed within your virtual environment.

## Conclusion
Updating the requirements files is essential for managing the dependencies
effectively. By following the steps outlined in this guide, you can easily
update and install the necessary requirements while maintaining a clean and
isolated development environment.

Remember to run make requirements whenever you modify the `*.in` files to ensure
that your `*.txt` files stay up to date with the correct versions of the
packages.