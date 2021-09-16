# shellcheck disable=SC2148 # We expect this script to be sourced

REPO_ROOT=$(git rev-parse --show-toplevel)
VENV_PATH=venv

# Find the archive with the highest version (good enough-basis)
CONFLUENT_ARCHIVE=$(find . -maxdepth 1 -name "confluent-*.tar.gz" | sort | tail -n 1)
CONFLUENT_ARCHIVE=${CONFLUENT_ARCHIVE#./%%*/}
CONFLUENT_ARCHIVE_PATH="${REPO_ROOT}/${CONFLUENT_ARCHIVE}"
CONFLUENT_BASE="${REPO_ROOT}/.confluent"

function croak() {
	echo "$1"
	exit 1
}

function setup_confluent_files() {

	export CONFLUENT_HOME="${CONFLUENT_BASE}/${CONFLUENT_ARCHIVE%.tar.gz}"
	export PATH="${PATH}:${CONFLUENT_HOME}/bin"

	if [[ ! -d "${CONFLUENT_HOME}" ]]; then

		if [[ ! -f "${CONFLUENT_ARCHIVE_PATH}" ]]; then
			croak "Download the confluent archive ${CONFLUENT_ARCHIVE} from https://confluent.io/installation"
		fi

		mkdir -p "${CONFLUENT_BASE}"
		pushd "${CONFLUENT_BASE}" || croak "Failed to push directory"
		printf "Preparing Confluent CLI\n"
		tar -xzf "${CONFLUENT_ARCHIVE_PATH}"
		popd || croak "Failed to pop directory"
	fi
}

function setup_virtualenv() {
	if [[ ! -d "${VENV_PATH}" ]]; then
		python3 -m venv "${VENV_PATH}" --prompt "pants-venv"
		"${VENV_PATH}/bin/pip3" install -c constraints.txt -r constraints.txt
	fi

	# shellcheck disable=SC1090 # We trust that venv works
	source "${VENV_PATH}/bin/activate"
}

function main() {
	cd "${REPO_ROOT}" || croak "Well, that went south quickly..."
	setup_virtualenv

	if [[ "${CONFLUENT_SKIP:-1}" -eq 0 ]]; then
		setup_confluent_files
	fi

	export PATH="${PATH}:${REPO_ROOT}/scripts"

	# Test that the script was actually successful
	test ! -z "${VIRTUAL_ENV}"

	# Set helpful python Asyncio variables
	export PYTHONASYNCIODEBUG=1
	export PYTHONTRACEMALLOC=1

	export REPO_ROOT
}

main
