# Use drf-spectacular for OpenAPI Specification generation

Date: 2023-06-15  
Author: David van Buiten

## Status

2023-06-15 - Final (David van Buiten)

## Context

Our project requires an OpenAPI Specification (OAS) to document the API
endpoints and provide a clear understanding of the available resources,
operations, and data models. Previously, we manually maintained the OAS
documentation, which proved to be time-consuming, error-prone, and difficult
to keep in sync with the API. Also, when deadlines are approaching, it is easy
to skip the manual documentation updates, which can result in inconsistencies.

## Decision

We have decided to adopt the `drf-spectacular` library as the tool for
generating the OpenAPI Specification for our project.

## Substantiation

- **Automated Documentation**: By using `drf-spectacular`, we can automate the
  generation of the OpenAPI Specification directly from our codebase
- **Consistency and Accuracy**: Manual updates to the OpenAPI Specification
  often result in inconsistencies and errors. By using `drf-spectacular`, we can 
  use the library's capabilities to extract the correct endpoint information
  directly from the codebase
- **Reduce Development Overhead**: Manual documentation updates require
  developer effort and can become a time-consuming process that is easily
  skipped when deadlines are approaching
- **Maintainability**: With `drf-spectacular`, the OpenAPI Specification is kept
  in sync with the codebase, as any changes made to the API endpoints are
  "automatically" reflected in the documentation
- **Standard Compliance**: `drf-spectacular` is designed to work seamlessly with
  `DRF`. It follows the OpenAPI Specification guidelines and provides support
  for advanced features such as schema generation, authentication and
  permissions, allowing us to easily incorporate these aspects into our API
  documentation

## Alternatives

- **Manual Specification Updates**: We could continue manually updating the
  OpenAPI Specification, but this approach is time-consuming, error-prone, and
  difficult to maintain as the API evolves
- **Other OpenAPI Tools**: There are other libraries and tools available for
  OpenAPI Specification generation, such as `drf-yasg`. However, after
  evaluating different options, we have determined that `drf-spectacular` best
  meets our requirements and is the most suitable tool for our project

## Risks and Mitigations
**Risk**:
- There is a risk that `drf-spectacular` might have limitations or issues that
  could affect the accuracy or completeness of the generated OpenAPI 
  Specification
- There is a risk that `drf-spectacular` might not work well with our project
  and still needs to be adapted to our project's needs 

**Mitigation**:
- We conducted thorough research of the `drf-spectacular` package to ensure its
  is suitability for our project, or could be easily adapted to our project's
  needs
