# Contributing to the Signals project

**This document is under review** 

### Want to add a new feature?

* **At the moment we do not accept merge request with new features from anyone other than the core developers!**

#### **Did you find a bug?**

* **Do not open up a GitHub issue if the bug is a security vulnerability.** Please contact one of the core developers

* **Make sure the bug was not already reported** by searching in the already reported [issues](https://github.com/amsterdam/signals/issues)

* If you're unable to find an open issue addressing the bug, [create a new issue](https://github.com/amsterdam/signals/issues/new). Be sure to include a clear **title** and **description**. Provide as much relevant information and data as possible

* If you found an open issue addressing the bug you can always contribute by leaving additional information. Make sure your comment is adding new information that has not already have been described in the ticket

* **Please do not put "feature request" into the GitHub Issues**

#### **Did you write a patch that fixes a bug?**

* Make sure that you have fixed the bug and provide prove this with several tests

* Open a new GitHub pull request with containing the fix and tests

* Ensure the PR description clearly describes the problem and solution (Include the relevant issue number if applicable)

* Bug-fix branches must use the *fix* prefix and must be branched of the **master** branch. The branch should include an issue reference number or self explaining name


## Code Review

* Contributions will not be merged until they have been code reviewed by at least 1 other developer

* Contributions will not be merged if there are no test proving that the code works as intended

* Contributions will not be merged if there is no documentation provided

* You should implement any code review feedback unless you strongly object to it 

* In the event that you object to the code review feedback, you should make your case clearly and calmly. If, after doing so, the feedback is judged to still apply, you must either apply the feedback or withdraw your contribution

## Code formatting

**Follow the style you see used in the repository**. Consistency with the project always outweigh other considerations. It doesn’t matter if you have your own style - just follow along.

The Signals codebase uses the [PEP-8](https://pep8.org/) code style in general.
In addition to the standards outlined in PEP 8, we have a few guidelines:

* Line-length can exceed 79 characters, to 120, when convenient.
* Line-length can exceed 120 characters, when doing otherwise would be terribly inconvenient.
* Always use single-quoted strings (e.g. 'some string used as an example'), unless a single-quote occurs within the string (e.g. "don't use single quotes for these kind of strings").
