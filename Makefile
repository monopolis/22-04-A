### Configuration ###############################
.DEFAULT_GOAL := none
.DELETE_ON_ERROR: ;
.SUFFIXES: ;

### Required environment ########################

ifndef REPO_ROOT
$(error "You must source the environment (source init_env.sh).")
endif


### Macros ######################################

### Verbs #######################################

none:
	@echo "Default target does nothing..."

.PHONY: none

fix_format:
	pants fmt ::

.PHONY: fix_format

check_unit_tests:
	pants test ::

.PHONY: check_unit_tests

check_lint:
	pants lint ::

.PHONY: check_lint

check_types:
	pants check ::

.PHONY: check_types

check_generated_files: generate_constraints
	git update-index -q --refresh
	git --no-pager diff --exit-code HEAD -- constraints.txt

.PHONY: check_generated_files

check_all: check_generated_files
	pants lint check test ::

.PHONY: check_all


generate_constraints:
	pants generate-user-lockfile ::

.PHONY: generate_constraints

generate_build_support:
	pants generate-lockfiles

.PHONY: generate_build_support

### Nouns #######################################