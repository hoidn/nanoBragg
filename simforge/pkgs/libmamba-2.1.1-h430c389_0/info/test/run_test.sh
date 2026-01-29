

set -ex



test ! -f "${PREFIX}/etc/profile.d/mamba.sh"
test -d ${PREFIX}/include/mamba
test -f ${PREFIX}/include/mamba/version.hpp
test -f ${PREFIX}/lib/cmake/libmamba/libmambaConfig.cmake
test -f ${PREFIX}/lib/cmake/libmamba/libmambaConfigVersion.cmake
test -e ${PREFIX}/lib/libmamba${SHLIB_EXT}
cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_MAJOR 2"
cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_MINOR 1"
cat $PREFIX/include/mamba/version.hpp | grep "LIBMAMBA_VERSION_PATCH 1"
exit 0
