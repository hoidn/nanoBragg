

set -ex



test -f "${PREFIX}/bin/mamba"
test -f "${PREFIX}/condabin/mamba"
test -f "${PREFIX}/etc/profile.d/mamba.sh"
. ${PREFIX}/etc/profile.d/mamba.sh
mamba --help
${PREFIX}/condabin/mamba --help
export MAMBA_ROOT_PREFIX="$(mktemp -d)"
mamba clean --all --dry-run
mamba create -n test --override-channels -c conda-forge --yes python=3.9
"${MAMBA_ROOT_PREFIX}/envs/test/bin/python" --version
"${MAMBA_ROOT_PREFIX}/envs/test/bin/python" -c "import os"
exit 0
