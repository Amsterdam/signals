# Signalen and the Standard for Public Code

This document describes the progress of implementing [The Standard for Public Code](https://standard.publiccode.net/). The Standard for Public Code gives public organizations a model for building their own open source solutions to enable successful future reuse by similar public organizations in other places.

## [Code in the Open](https://standard.publiccode.net/criteria/code-in-the-open.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All source code for any policy and software in use (unless used for fraud detection) MUST be published and publicly accessible. | yes? | What policy is Signalen based upon? Lacks public dataset for easily running the machine learning model.
Contributors MUST NOT upload sensitive information regarding users, their organization or third parties to the repository.  | yes |
Any source code not currently in use (such as new versions, proposals or older versions) SHOULD be published. | yes | Git history and tags per release. Backend is currently starting to publish tags again.
The source code MAY provide the general public with insight into which source code or policy underpins any specific interaction they have with your organization. | |

## [Bundle policy and source code](https://standard.publiccode.net/criteria/bundle-policy-and-code.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
A codebase MUST include the policy that the source code is based on. |  |
A codebase MUST include all source code that the policy is based on. |  |
All policy and source code that the codebase is based on MUST be documented, reusable and portable. |  |
Policy SHOULD be provided in machine readable and unambiguous formats. |  |
Continuous integration tests SHOULD validate that the source code and the policy are executed coherently. |  |

## [Create reusable and portable code](https://standard.publiccode.net/criteria/reusable-and-portable-codebases.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST be developed to be reusable in different contexts. | yes |
The codebase MUST be independent from any secret, undisclosed, proprietary or non-open licensed code or services for execution and understanding. | yes |
The codebase SHOULD be in use by multiple parties. | yes |
The roadmap SHOULD be influenced by the needs of multiple parties. | yes |
Configuration SHOULD be used to make code adapt to context specific needs. | yes |
Codebases SHOULD include a publiccode.yml metadata description so that they’re easily discoverable. | no | Created [backend#64](https://github.com/Signalen/backend/issues/64).
Code and its documentation SHOULD NOT contain situation-specific information.  | partial | The software is easily configurable, the default configuration is Amsterdam-specific.

## [Welcome contributors](https://standard.publiccode.net/criteria/open-to-contributions.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST allow anyone to submit suggestions for changes to the codebase. | yes |
The codebase MUST include contribution guidelines explaining how contributors can get involved, for example in a CONTRIBUTING file. | yes |
The codebase SHOULD advertise the committed engagement of involved organizations in the development and maintenance. | (maybe) | The signalen.org website shows the logos.
The codebase SHOULD document the governance of the codebase, contributions and its community, for example in a GOVERNANCE file. | no |
The codebase SHOULD have a publicly available roadmap. | no | There is a [product steering group](https://github.com/orgs/Signalen/projects/2), but no roadmap yet.
The codebase MAY include a code of conduct for contributors. |  |

## [Make contributing easy](https://standard.publiccode.net/criteria/make-contributing-easy.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST have a public issue tracker that accepts suggestions from anyone. | yes | Amsterdam has a second private issue tracker.
The codebase MUST include an email address for security issues and responsible disclosure. | no | Consider a SECURITY.md file, see [backend#112](https://github.com/Signalen/backend/issues/112).
The documentation MUST link to both the public issue tracker and submitted codebase changes, for example in a README file. | no | The two different issue trackers in the Amsterdam and Signalen namespaces make this a bit challenging. Maybe disable the issue tracker on the Amsterdam repo and link to the Signalen one?
The project MUST have communication channels for users and developers, for example email lists. | yes | Link to Slack and [email list](https://lists.publiccode.net/mailman/postorius/lists/signalen-discuss.lists.publiccode.net/) on signalen.org.
The documentation SHOULD include instructions for how to report potentially security sensitive issues on a closed channel. | no | Document the process in SECURITY.md, see [backend#112](https://github.com/Signalen/backend/issues/112).

## [Maintain version control](https://standard.publiccode.net/criteria/version-control-and-history.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
You MUST have a way to maintain version control for the code. | yes |
All files in a codebase MUST be version controlled. | yes |
All decisions MUST be documented in commit messages. | no | Commit messages often refer to private issues.
Every commit message MUST link to discussions and issues wherever possible. | partial | Sometimes these are private connections.
You SHOULD group relevant changes in commits. | yes | Commits are grouped by pull request.
You SHOULD mark different versions of the codebase, for example using revision tags or textual labels. | yes | Amsterdam tags new releases on Github using Github releases in the frontend repository. We will start doing this again for the backend as well.
You SHOULD prefer file formats that can easily be version controlled. | yes | Git-friendliness is in the culture.

## [Require review of contributions](https://standard.publiccode.net/criteria/require-review.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All contributions that are accepted or committed to release versions of the codebase MUST be reviewed by another contributor. | yes |
Reviews MUST include source, policy, tests and documentation. | | Code yes, but tests and docs/policy not always - maybe a PR template would help?
Reviewers MUST provide feedback on all decisions made and the implementation in the review. | yes | Weekly dev call for discussion.
Contributions SHOULD conform to the standards, architecture and decisions set out in the codebase in order to pass review. | yes | Architecture docs for both frontend and backend, might be nice to have a checkbox in a PR template.
Reviews SHOULD include running both the code and the tests of the codebase. | yes |
Contributions SHOULD be reviewed by someone in a different context than the contributor. | some | VNG pull requests all reviewed by Amsterdam, frontend & backend cross-review rare, Amsterdam pull requests often not cross-reviewed by VNG. PO acceptance testing is part of review, but during acceptance.
Version control systems SHOULD not accept non-reviewed contributions in release versions. | yes | Sometimes the "Github administrator" override is used when no reviewer is available.
Reviews SHOULD happen within two business days. | some | This is usually done, but there are exceptions.
Reviews MAY be performed by multiple reviewers. | |

## [Document your objectives](https://standard.publiccode.net/criteria/document-objectives.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST contain documentation of its objectives – like a mission and goal statement – that is understandable by designers and developers so that they can use or contribute to the codebase. |  | See signalen.org and [technical goals](https://github.com/Amsterdam/signals/blob/master/docs/topics/application-design.md).
The codebase SHOULD contain documentation of its objectives understandable by policy makers and management. | |
The codebase MAY contain documentation of its objectives for the general public. | |


## [Document your code](https://standard.publiccode.net/criteria/documenting.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All of the functionality of the codebase – policy as well as source – MUST be described in language clearly understandable for those that understand the purpose of the code. | | The documentation is pretty scattered.
The documentation of the codebase MUST contain: a description of how to install and run the source code, examples demonstrating the key functionality. | | There are no docs for system administrators. There is documentation on [helm-charts](https://github.com/Signalen/helm-charts), and developer documentation for [frontend](https://github.com/Signalen/frontend/blob/develop/README.md) and [backend](https://github.com/Signalen/backend/blob/master/README.md).
The documentation of the codebase SHOULD contain: a high level description that is clearly understandable for a wide audience of stakeholders, like the general public and journalists, a section describing how to install and run a standalone version of the source code, including, if necessary, a test dataset, examples for all functionality. |  yes | Signalen.org website.
There SHOULD be continuous integration tests for the quality of your documentation. | no | Link-checker does not check external links. Markdown in code repositories is not automatically checked.
The documentation of the codebase MAY contain examples that make users want to immediately start using the codebase. |  |
You MAY use the examples in your documentation to test the code. |  |

## [Use plain English](https://standard.publiccode.net/criteria/understandable-english-first.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All code and documentation MUST be in English. | no | Some workflow contains Dutch states without English translation; If signalen.org is the source for some documentation (and not only a marketing asset), then it should be also available in English.
Any translation MUST be up to date with the English version and vice versa. | | See above
There SHOULD be no acronyms, abbreviations, puns or legal/domain specific terms in the codebase without an explanation preceding it or a link to an explanation. | | Glossary needs expanding.
The name of the project or codebase SHOULD be descriptive and free from acronyms, abbreviations, puns or branding. | yes | SIA --> Signalen
Documentation SHOULD aim for a lower secondary education reading level, as recommended by the Web Content Accessibility Guidelines. | | Tech documentation will be harder, but a check on signalen.org is needed.
Any code, documentation and tests MAY have a translation. | |

## [Use open standards](https://standard.publiccode.net/criteria/open-standards.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
For features of a codebase that facilitate the exchange of data the codebase MUST use an open standard that meets the Open Source Initiative Open Standard Requirements. | | [StUF-ZKN](https://www.gemmaonline.nl/index.php/Sectormodel_Zaken:_StUF-ZKN) OpenAPI2 spec, GraphQL, Oauth2, OpenID Connect, SMTP, JSON?
If no existing open standard is available, effort SHOULD be put into developing one. |  | Maybe we need a standard way to forward the complaint between bodies, e.g.: City <--> Provice?
Standards that are machine testable SHOULD be preferred over those that are not. | N/A |
Functionality using features from a non-open standard (one that doesn’t meet the Open Source  Initiative Open Standard Requirements) MAY be provided if necessary, but only in addition to compliant features. | |
All non-compliant standards used MUST be recorded clearly in the documentation. | N/A |
The codebase SHOULD contain a list of all the standards used with links to where they are available. | no | Created [backend#65](https://github.com/Signalen/backend/issues/65). |

## [Use continuous integration](https://standard.publiccode.net/criteria/continuous-integration.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All functionality in the source code MUST have automated tests. | mostly | In addition to unit testing, there are end-to-end tests which run on master and release branches (frontend); there are coverage reports, results require manual download.
Contributions MUST pass all automated tests before they are admitted into the codebase. | yes |
Contributions MUST be small. | yes | Each pull request contains a single feature or fix, but this policy is not explicit in CONTRIBUTING.md nor explictily checked by reviewer.
The codebase MUST have active contributors. | yes | Amsterdam & VNG
Source code test and documentation coverage SHOULD be monitored. | no | Coverage statics are not monitored but tests will fail when coverage is below a threshold.
Policy and documentation MAY have testing for consistency with the source and vice versa. |  |
Policy and documentation MAY have testing for style and broken links. |  |

## [Publish with an open license](https://standard.publiccode.net/criteria/open-licenses.html)

- [x] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
All code and documentation MUST be licensed such that it may be freely reusable, changeable and redistributable. | Yes | [Mozilla license](https://github.com/Amsterdam/signals/blob/master/LICENSE)
Software source code MUST be licensed under an OSI-approved open source license. | yes | [MPL-2.0](https://opensource.org/licenses/MPL-2.0)
All code MUST be published with a license file. | yes |
Contributors MUST NOT be required to transfer copyright of their contributions to the codebase. | yes |
All source code files in the codebase SHOULD include a copyright notice and a license header. | yes | Added: [signals#623](https://github.com/Amsterdam/signals/pull/623) and checked with CI: [signals#764](https://github.com/Amsterdam/signals/pull/764)
Codebases MAY have multiple licenses for different types of code and documentation. |  |

## [Use a coherent style](https://standard.publiccode.net/criteria/style.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
Contributions MUST adhere to either a coding or writing style guide, either your own or an existing one that is advertised in or part of the codebase. | yes | CI fails when not adhering to code styles. There are some [design guidelines](https://github.com/Amsterdam/signals/blob/master/docs/topics/application-design.md#goals-and-design-principles).
Contributions SHOULD pass automated tests on style. | yes |
Your codebase SHOULD include inline comments and documentation for non-trivial sections. | mostly | There are many links to non-public resources/tickets.
You MAY include sections in your style guide on understandable English. |  |

## [Document codebase maturity](https://standard.publiccode.net/criteria/document-maturity.html)

- [ ] compliant with this criterion.

Requirement | meets | links and notes
-----|-----|-----
A codebase MUST be versioned. | yes | Semantic versioning and tagged as such. Backend is currently starting to publish tags again.
A codebase that is ready to use MUST only depend on other codebases that are also ready to use. | yes | [Open Source dependencies](./dependencies.md)
A codebase that is not yet ready to use MUST have one of these labels: prototype - to test the look and feel, and to internally prove the concept of the technical possibilities, alpha - to do guided tests with a limited set of users, beta - to open up testing to a larger section of the general public, for example to test if the codebase works at scale, pre-release version - code that is ready to be released but hasn’t received formal approval yet. | N/A |
A codebase SHOULD contain a log of changes from version to version, for example in the CHANGELOG. | yes | There is no changelog, but there are release notes for [backend](https://github.com/Amsterdam/signals/releases) and [frontend](https://github.com/Amsterdam/signals-frontend/releases).
