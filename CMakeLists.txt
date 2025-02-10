cmake_minimum_required(VERSION 3.14)

include(cmake/prelude.cmake)

project(
    Capricorn
    VERSION 0.1.0
    DESCRIPTION "CPP project template"
    HOMEPAGE_URL "https://www.gemc.club"
    LANGUAGES CXX
)

include(cmake/project-is-top-level.cmake)
include(cmake/variables.cmake)

# ---- Declare library ----

add_library(
    Capricorn_lib OBJECT
    source/lib.cpp
)

target_include_directories(
    Capricorn_lib ${warning_guard}
    PUBLIC
    "\$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/source>"
)

target_compile_features(Capricorn_lib PUBLIC cxx_std_20)

find_package(fmt REQUIRED)
target_link_libraries(Capricorn_lib PRIVATE fmt::fmt)

# ---- Declare executable ----

add_executable(Capricorn_exe source/main.cpp)
add_executable(Capricorn::exe ALIAS Capricorn_exe)

set_property(TARGET Capricorn_exe PROPERTY OUTPUT_NAME Capricorn)

target_compile_features(Capricorn_exe PRIVATE cxx_std_20)

target_link_libraries(Capricorn_exe PRIVATE Capricorn_lib)

# ---- Install rules ----

if(NOT CMAKE_SKIP_INSTALL_RULES)
  include(cmake/install-rules.cmake)
endif()

# ---- Developer mode ----

if(NOT Capricorn_DEVELOPER_MODE)
  return()
elseif(NOT PROJECT_IS_TOP_LEVEL)
  message(
      AUTHOR_WARNING
      "Developer mode is intended for developers of Capricorn"
  )
endif()

include(cmake/dev-mode.cmake)
