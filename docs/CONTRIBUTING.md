# Contributing to the Signals project

### Join the Signalen community mailinglist to stay up to date

* Product owners for each development team coordinate in the product steering group. If you wish to contribute or keep up to date please join the [email list](https://lists.publiccode.net/mailman/postorius/lists/signalen-discuss.lists.publiccode.net/) and/or [Slack channel](https://samenorganiseren.slack.com/archives/C01AF8CN495).

### Want to add a new feature?

* See [signalen.org](https://signalen.org/en/using-signalen) for how to help with development or propose new features.

#### **Did you find a bug?**

* **Do not open up a GitHub issue if the bug is a security vulnerability.** Please contact one of the core developers

* **Make sure the bug was not already reported** by searching in the already reported [issues](https://github.com/amsterdam/signals/issues)

* If you're unable to find an open issue addressing the bug, [create a new issue](https://github.com/amsterdam/signals/issues/new). Be sure to include a clear **title** and **description**. Provide as much relevant information and data as possible

* If you found an open issue addressing the bug you can always contribute by leaving additional information. Make sure your comment is adding new information that has not already have been described in the ticket

* Please make new [feature requests](https://github.com/Signalen/product-steering/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=%5BFEATURE-REQUEST%5D) using the [feature request template](https://github.com/Signalen/product-steering/tree/main/.github/ISSUE_TEMPLATE) in the [product steering](https://github.com/Signalen/product-steering) repository if your requirement or wish is not listed.

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

## Standards

Contributors may wish to familiarize themselves with the open standards used within the codebase, including:

* [StUF-ZKN](https://www.gemmaonline.nl/index.php/Sectormodel_Zaken:_StUF-ZKN)
* [OpenAPI2](https://swagger.io/specification/v2/)
* [Oauth2](https://oauth.net/2/)
* [OpenID Connect](https://openid.net/connect/)
* [JSON](https://tools.ietf.org/html/std90)
* [SMTP](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol#Related_requests_for_comments)

## Under Foundation for Public Code incubating codebase stewardship

Signalen is in incubation [codebase stewardship](https://publiccode.net/codebase-stewardship/) with the [Foundation for Public Code](https://publiccode.net).

The [codebase stewardship activities](https://about.publiccode.net/activities/codebase-stewardship/activities.html) by the Foundation for Public Code on this codebase include:

* facilitating the community and its members
* help all contributors contribute in line with the contributing guidelines and the [Standard for Public Code](https://standard.publiccode.net/)
* work with the community to tell their stories, create their brand and market their products
* support the technical and product steering teams
