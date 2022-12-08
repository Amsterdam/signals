# Signalen and the Standard for Public Code version 0.4.0

<!-- SPDX-License-Identifier: MPL-2.0 -->
<!-- Copyright (C) 2020 - 2022 Gemeente Amsterdam  -->

Link to commitment to meet the Standard for Public Code: [CONTRIBUTING](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md)

## [Code in the open](https://standard.publiccode.net/criteria/code-in-the-open.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All source code for any policy in use (unless used for fraud detection) MUST be published and publicly accessible. |  | What policy is Signalen based upon? Lacks public dataset for easily running the machine learning model.
All source code for any software in use (unless used for fraud detection) MUST be published and publicly accessible. | yes |
Contributors MUST NOT upload sensitive information regarding users, their organization or third parties to the repository. | yes |
Any source code not currently in use (such as new versions, proposals or older versions) SHOULD be published. | yes | Git history and tags per release.
Documenting which source code or policy underpins any specific interaction the general public may have with an organization is OPTIONAL. |  |

## [Bundle policy and source code](https://standard.publiccode.net/criteria/bundle-policy-and-code.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
A codebase MUST include the policy that the source code is based on. |  |
A codebase MUST include all source code that the policy is based on, unless used for fraud detection. |  |
Policy SHOULD be provided in machine readable and unambiguous formats. |  |
Continuous integration tests SHOULD validate that the source code and the policy are executed coherently. |  |

## [Create reusable and portable code](https://standard.publiccode.net/criteria/reusable-and-portable-codebases.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST be developed to be reusable in different contexts. | yes | [signalen.org](https://signalen.org)
The codebase MUST be independent from any secret, undisclosed, proprietary or non-open licensed code or services for execution and understanding. | yes |
The codebase SHOULD be in use by multiple parties. | yes |
The roadmap SHOULD be influenced by the needs of multiple parties. | yes | [product steering](https://github.com/Signalen/product-steering/)
Configuration SHOULD be used to make code adapt to context specific needs. | yes |
The codebase SHOULD be localizable. |  |
Code and its documentation SHOULD NOT contain situation-specific information. | partial | The software is easily configurable, the default configuration is Amsterdam-specific.
Codebase modules SHOULD be documented in such a way as to enable reuse in codebases in other contexts. |  |

## [Welcome contributors](https://standard.publiccode.net/criteria/open-to-contributions.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST allow anyone to submit suggestions for changes to the codebase. | yes |
The codebase MUST include contribution guidelines explaining what kinds of contributions are welcome and how contributors can get involved, for example in a `CONTRIBUTING` file. | yes | [CONTRIBUTING](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md)
The codebase MUST document the governance of the codebase, contributions and its community, for example in a `GOVERNANCE` file. |  |
The codebase SHOULD advertise the committed engagement of involved organizations in the development and maintenance. |  | The [signalen.org](https://signalen.org) website shows the logos of who is using it.
The codebase SHOULD have a publicly available roadmap. | yes | There is product steering meetings which [prioritizes issues](https://github.com/orgs/Signalen/projects/2)
The codebase SHOULD publish codebase activity statistics. | yes | [GitHub pulse](https://github.com/Amsterdam/signals/pulse)
Including a code of conduct for contributors in the codebase is OPTIONAL. |  |

## [Make contributing easy](https://standard.publiccode.net/criteria/make-contributing-easy.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST have a public issue tracker that accepts suggestions from anyone. | yes | Amsterdam has a second private issue tracker.
The codebase MUST include instructions for how to privately report security issues for responsible disclosure. |  | Consider a SECURITY.md file, see [backend#112](https://github.com/Signalen/backend/issues/112).
The documentation MUST link to both the public issue tracker and submitted codebase changes, for example in a `README` file. |  | The two different issue trackers in the Amsterdam and Signalen namespaces make this a bit challenging. Maybe disable the issue tracker on the Amsterdam repo and link to the Signalen one?
The codebase MUST have communication channels for users and developers, for example email lists. |  | There is a Slack channel and [email list](https://lists.publiccode.net/mailman/postorius/lists/signalen-discuss.lists.publiccode.net/), but only linked from [CONTRIBUTING](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md), they are [not advertised](https://signalen.org/contact) elsewhere
The documentation SHOULD include instructions for how to report potentially security sensitive issues on a closed channel. |  | Document the process in SECURITY.md, see [backend#112](https://github.com/Signalen/backend/issues/112).

## [Maintain version control](https://standard.publiccode.net/criteria/version-control-and-history.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The community MUST have a way to maintain version control for the code. | yes | Git
All files in a codebase MUST be version controlled. | yes |
All decisions MUST be documented in commit messages. |  | Commit messages often refer to private issues.
Every commit message MUST link to discussions and issues wherever possible. |  | Sometimes these are to non-public issue tracker.
The codebase SHOULD be maintained in a distributed version control system. | yes | Git
Contributors SHOULD group relevant changes in commits. | yes | Commits are grouped by pull request.
Maintainers SHOULD mark released versions of the codebase, for example using revision tags or textual labels. | yes |
Contributors SHOULD prefer file formats where the changes within the files can be easily viewed and understood in the version control system. | yes | Git-friendliness is in the culture.
It is OPTIONAL for contributors to sign their commits and provide an email address, so that future contributors are able to contact past contributors with questions about their work. | yes |

## [Require review of contributions](https://standard.publiccode.net/criteria/require-review.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All contributions that are accepted or committed to release versions of the codebase MUST be reviewed by another contributor. | yes |
Reviews MUST include source, policy, tests and documentation. | yes | [pull request template](https://github.com/Amsterdam/signals/blob/master/.github/pull_request_template.md)
Reviewers MUST provide feedback on all decisions to not accept a contribution. | yes | Weekly dev call for discussion.
Contributions SHOULD conform to the standards, architecture and decisions set out in the codebase in order to pass review. | yes | Architecture docs for both frontend and backend.
Reviews SHOULD include running both the code and the tests of the codebase. | yes |
Contributions SHOULD be reviewed by someone in a different context than the contributor. | yes | Amsterdam and VNG review each other's contributions.
Version control systems SHOULD NOT accept non-reviewed contributions in release versions. | yes |
Reviews SHOULD happen within two business days. |  | This is usually done, but there are exceptions.
Performing reviews by multiple reviewers is OPTIONAL. |  |

## [Document codebase objectives](https://standard.publiccode.net/criteria/document-objectives.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST contain documentation of its objectives, like a mission and goal statement, that is understandable by developers and designers so that they can use or contribute to the codebase. |  | See signalen.org and [technical goals](https://github.com/Amsterdam/signals/blob/master/docs/topics/application-design.md).
Codebase documentation SHOULD clearly describe the connections between policy objectives and codebase objectives. |  |
Documenting the objectives of the codebase for the general public is OPTIONAL. |  |

## [Document the code](https://standard.publiccode.net/criteria/documenting.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All of the functionality of the codebase, policy as well as source, MUST be described in language clearly understandable for those that understand the purpose of the code. |  | Much documentation is tagged as "status under review"
The documentation of the codebase MUST contain a description of how to install and run the source code. | yes | There is documentation on [helm-charts](https://github.com/Signalen/helm-charts), and developer documentation for [frontend](https://github.com/Signalen/frontend/blob/develop/README.md) and [backend](https://github.com/Signalen/backend/blob/master/README.md).
The documentation of the codebase MUST contain examples demonstrating the key functionality. |  | Documentation will be written
The documentation of the codebase SHOULD contain a high level description that is clearly understandable for a wide audience of stakeholders, like the general public and journalists. |  | Documentation will be written
The documentation of the codebase SHOULD contain a section describing how to install and run a standalone version of the source code, including, if necessary, a test dataset. | yes |
The documentation of the codebase SHOULD contain examples for all functionality. |  | Documentation will be written, some examples exists in Swagger and Postman
The documentation SHOULD describe the key components or modules of the codebase and their relationships, for example as a high level architectural diagram. | yes | [application design](https://github.com/Amsterdam/signals/blob/master/docs/topics/application-design.md)
There SHOULD be continuous integration tests for the quality of the documentation. |  |
Including examples that make users want to immediately start using the codebase in the documentation of the codebase is OPTIONAL. |  |
Testing the code by using examples in the documentation is OPTIONAL. |  |

## [Use plain English](https://standard.publiccode.net/criteria/understandable-english-first.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All codebase documentation MUST be in English. |  |
All code MUST be in English, except where policy is machine interpreted as code. |  | Some workflow contains Dutch states without English translation
All bundled policy not available in English MUST have an accompanying summary in English. |  | No bundled policy yet.
Any translation MUST be up to date with the English version and vice versa. |  |
There SHOULD be no acronyms, abbreviations, puns or legal/non-English/domain specific terms in the codebase without an explanation preceding it or a link to an explanation. |  | Glossary needs expanding.
The name of the codebase SHOULD be descriptive and free from acronyms, abbreviations, puns or organizational branding. | yes |
Documentation SHOULD aim for a lower secondary education reading level, as recommended by the [Web Content Accessibility Guidelines 2](https://www.w3.org/WAI/WCAG21/quickref/?showtechniques=315#readable). |  |
Providing a translation of any code, documentation or tests is OPTIONAL. |  |

## [Use open standards](https://standard.publiccode.net/criteria/open-standards.html)

- [x] criterion met.

Requirement | meets | links and notes
-----|-----|-----
For features of a codebase that facilitate the exchange of data the codebase MUST use an open standard that meets the [Open Source Initiative Open Standard Requirements](https://opensource.org/osr). | yes | [standards](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md#standards)
Any non-open standards used MUST be recorded clearly as such in the documentation. | N/A |
Any standard chosen for use within the codebase MUST be listed in the documentation with a link to where it is available. | yes | [standards](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md#standards)
Any non-open standards chosen for use within the codebase MUST NOT hinder collaboration and reuse. | N/A |
If no existing open standard is available, effort SHOULD be put into developing one. | N/A |
Standards that are machine testable SHOULD be preferred over those that are not. | N/A |

## [Use continuous integration](https://standard.publiccode.net/criteria/continuous-integration.html)

- [x] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All functionality in the source code MUST have automated tests. | Ok |
Contributions MUST pass all automated tests before they are admitted into the codebase. | yes |
The codebase MUST have guidelines explaining how to structure contributions. | yes | [CONTRIBUTING](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md)
The codebase MUST have active contributors. | yes | Amsterdam & VNG, [pulse](https://github.com/Amsterdam/signals/pulse/monthly)
The codebase guidelines SHOULD state that each contribution should focus on a single issue. | yes | [CONTRIBUTING](https://github.com/Amsterdam/signals/blob/master/docs/CONTRIBUTING.md) (could be more explicit)
Source code test and documentation coverage SHOULD be monitored. | Ok | [Monitored](https://github.com/Amsterdam/signals/blob/main/api/app/tox.ini#L64)
Testing policy and documentation for consistency with the source and vice versa is OPTIONAL. |  |
Testing policy and documentation for style and broken links is OPTIONAL. |  |

## [Publish with an open license](https://standard.publiccode.net/criteria/open-licenses.html)

- [x] criterion met.

Requirement | meets | links and notes
-----|-----|-----
All code and documentation MUST be licensed such that it may be freely reusable, changeable and redistributable. | yes | [Mozilla license](https://github.com/Amsterdam/signals/blob/master/LICENSE) |
Software source code MUST be licensed under an [OSI-approved or FSF Free/Libre license](https://spdx.org/licenses/). | yes | [MPL-2.0](https://opensource.org/licenses/MPL-2.0)
All code MUST be published with a license file. | yes | [LICENSE](https://github.com/Amsterdam/signals/blob/master/LICENSE)
Contributors MUST NOT be required to transfer copyright of their contributions to the codebase. | yes |
All source code files in the codebase SHOULD include a copyright notice and a license header that are machine-readable. | yes | checked with CI: [signals#764](https://github.com/Amsterdam/signals/pull/764)
Having multiple licenses for different types of code and documentation is OPTIONAL. |  |

## [Make the codebase findable](https://standard.publiccode.net/criteria/findability.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
The codebase MUST be findable using a search engine by describing the problem it solves in natural language. |  |
The codebase MUST be findable using a search engine by codebase name. | yes |
Maintainers SHOULD submit the codebase to relevant software catalogs. | yes | [Developers Italia](https://developers.italia.it/it/software/amsterdam-signals-frontend-24a47e), [International Software Collaborative](https://softwarecollaborative.org/cooperatives/signalen.html) - both via the Frontend
The codebase SHOULD have a website which describes the problem the codebase solves using the preferred jargon of different potential users of the codebase (including technologists, policy experts and managers). | yes | [signalen.org](https://signalen.org)
The codebase SHOULD have a unique and persistent identifier where the entry mentions the major contributors, repository location and website. |  |
The codebase SHOULD include a machine-readable metadata description, for example in a [publiccode.yml](https://github.com/publiccodeyml/publiccode.yml) file. |  | In the Frontend repository
A dedicated domain name for the codebase is OPTIONAL. | yes | signalen.org
Regular presentations at conferences by the community are OPTIONAL. |  |

## [Use a coherent style](https://standard.publiccode.net/criteria/style.html)

- [ ] criterion met.

Requirement | meets | links and notes
-----|-----|-----
Contributions MUST adhere to either a coding or writing style guide, either the codebase community's own or an existing one that is advertised in or part of the codebase. | yes | CI fails when not adhering to code styles. There are some [design guidelines](https://github.com/Amsterdam/signals/blob/master/docs/topics/application-design.md#goals-and-design-principles).
Contributions SHOULD pass automated tests on style. | yes |
The codebase SHOULD include inline comments and documentation for non-trivial sections. |  | There are many links to non-public resources/tickets.
Including sections on [understandable English](https://standard.publiccode.net/criteria/understandable-english-first.html) in the style guide is OPTIONAL. |  |

## [Document codebase maturity](https://standard.publiccode.net/criteria/document-maturity.html)

- [x] criterion met.

Requirement | meets | links and notes
-----|-----|-----
A codebase MUST be versioned. | yes | [releases](https://github.com/Amsterdam/signals/releases)
A codebase that is ready to use MUST only depend on other codebases that are also ready to use. | yes | [Open Source dependencies](./dependencies.md)
A codebase that is not yet ready to use MUST have one of the labels: prototype, alpha, beta or pre-release version. | N/A |
A codebase SHOULD contain a log of changes from version to version, for example in the `CHANGELOG`. | yes | release details in [releases](https://github.com/Amsterdam/signals/releases)
