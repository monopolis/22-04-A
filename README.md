# Getting started

This repository uses Pantsbuild to build packages. To get started, source the development environment by executing `source init_env.sh`.

You will now be able to access Pantsbuild via the command `pants`.

You may use `pants` directly, or you can use the `Makefile`-shortcuts for formatting, linting, and testing etc.

* `pants fmt ::` or `make fix_format`
* `pants lint ::` or `make check_lint`
* `pants check ::` or `make check_types`

To the lockfile for dependencies you can execute `make generate_constraints`.

# Discount Service

Ensure that you have the environment configured according to the steps in the "Getting started" section.

You may then run the development server by executing `pants run packages/discounter:server-hotreload`.

To produce a server artifact, execute `pants package packages/discounter:server` and find the artifact in `dist/packages.discounter/`.

You may find an additional overview of the package in [docs/discounter/discount_service.md](docs/discounter/discount_service.md)


# Running checks
You may run checks by using either Pantsbuild directly `pants lint check ::`, or by using the Makefile shortcut `make check_all`.


# scripts/kafka
A wrapper around Confluent CLI. Requires that a `confluent-*.tar.gz` archive has been downloaded from Confluent and placed in the repository.

# scripts/postgres
A wrapper around docker-compose to enable easy access to PostgreSQL for development. Requires that docker-compose is installed on the system.

# scripts/rabbitmq
A wrapper around docker-compose to enable easy access to RabbitMQ for development. Requires that docker-compose is installed on the system.

