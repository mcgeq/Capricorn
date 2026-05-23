include_guard(GLOBAL)

if(NOT DEFINED ENV{VCPKG_ROOT} OR "$ENV{VCPKG_ROOT}" STREQUAL "")
  message(
      FATAL_ERROR
      "VCPKG_ROOT must point to a vcpkg checkout before using this preset."
  )
endif()

if(CMAKE_HOST_WIN32 AND (NOT DEFINED VCPKG_TARGET_TRIPLET OR VCPKG_TARGET_TRIPLET STREQUAL ""))
  set(
      VCPKG_TARGET_TRIPLET
      "x64-mingw-dynamic"
      CACHE STRING
      "vcpkg target triplet for Windows GNU/Clang developer presets"
  )
endif()

include("$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
