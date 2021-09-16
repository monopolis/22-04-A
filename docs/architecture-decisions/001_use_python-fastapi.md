# 001 Use FastAPI
## Status: ACCEPTED


## Decision

I have decided to use FastAPI as the basis of this microservice.

## Discussion

There are many web frameworks that are available in the Python ecosystem and they are broadly divided into three camps: WSGI, ASGI and the rest. In recent years, the ASGI-framework FastAPI has received attention due to its integration with Pydantic for parsing and pseudo-validation, and its out-of-box integration for OpenAPI documentation.

It promises to provide a "smooth" developer experience and while it leaves some things to be desired, it is undeniably convenient.

## Risks

Some of its decisions make structuring the application more difficult compared to simply using Starlette (the underlying ASGI-framework) and there is a clear trap to focus the application around the framework, which makes integration and other input sources much more difficult to achieve. It should be noted, that it is possible to fall back on Starlette should it be required.

Pydantic pretends to be a validation library, but has clear flaws in this respect. It should primarily be viewed as a parsing library.

