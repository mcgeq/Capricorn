cmake_minimum_required(VERSION 3.25)

include(cmake/prelude.cmake)

project(
    Capricorn
    VERSION 0.1.0
    DESCRIPTION "A modern C++ project template"
    HOMEPAGE_URL "https://www.gemc.club"
    LANGUAGES CXX
)

# Template naming knobs. When you fork this template, update these first if you
# want a different header folder, file stem, or sample namespace.
set(TEMPLATE_INCLUDE_DIR_NAME "${PROJECT_NAME}")
set(TEMPLATE_LIBRARY_BASENAME "capricorn")
set(TEMPLATE_LIBRARY_NAMESPACE "capricorn")

include(cmake/project-metadata.cmake)
include(cmake/dependencies.cmake)
include(cmake/variables.cmake)
include(cmake/project-options.cmake)

if(CMAKE_EXPORT_COMPILE_COMMANDS)
  add_custom_target(
      sync-compile-commands ALL
      COMMAND
      "${CMAKE_COMMAND}"
      -D
      "TEMPLATE_BINARY_COMPILE_COMMANDS=${PROJECT_BINARY_DIR}/compile_commands.json"
      -D
      "TEMPLATE_ROOT_COMPILE_COMMANDS=${PROJECT_SOURCE_DIR}/compile_commands.json"
      -P
      "${PROJECT_SOURCE_DIR}/cmake/sync-compile-commands.cmake"
      COMMENT "Syncing compile_commands.json for clangd-based editors"
      VERBATIM
  )
endif()

configure_file(
    "${PROJECT_SOURCE_DIR}/cmake/project-config.hpp.in"
    "${template_generated_include_dir}/${TEMPLATE_INCLUDE_DIR_NAME}/project_config.hpp"
    @ONLY
)

add_library("${template_main_target}")
add_library("${template_main_alias}" ALIAS "${template_main_target}")

target_sources(
    "${template_main_target}"
    PRIVATE
    ${template_library_sources}
    ${template_private_headers}
    PUBLIC
    FILE_SET HEADERS
    BASE_DIRS
    "${PROJECT_SOURCE_DIR}/include"
    "${template_generated_include_dir}"
    FILES
    ${template_public_headers}
    "${template_generated_include_dir}/${TEMPLATE_INCLUDE_DIR_NAME}/project_config.hpp"
)

target_include_directories(
    "${template_main_target}" ${warning_guard}
    PUBLIC
    "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>"
    "$<BUILD_INTERFACE:${template_generated_include_dir}>"
    "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
    PRIVATE
    "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src>"
)

target_compile_features("${template_main_target}" PUBLIC cxx_std_23)
template_apply_options("${template_main_target}")

set(template_build_cli_option "${template_project_identifier}_BUILD_CLI")
option(
    "${template_build_cli_option}"
    "Build the example command-line executable"
    ${PROJECT_IS_TOP_LEVEL}
)
set(template_build_cli "${${template_build_cli_option}}")

if(template_enable_cxx_modules)
  include(cmake/cxx-modules-targets.cmake)
endif()

if(template_build_cli)
  add_executable("${template_cli_target}" src/main.cpp)
  add_executable("${template_cli_alias}" ALIAS "${template_cli_target}")

  set_property(TARGET "${template_cli_target}" PROPERTY OUTPUT_NAME "${PROJECT_NAME}")
  target_compile_features("${template_cli_target}" PRIVATE cxx_std_23)
  target_link_libraries("${template_cli_target}" PRIVATE "${template_main_target}")
  template_apply_options("${template_cli_target}")
  if(template_enable_clang_tidy AND template_clang_tidy_profile STREQUAL "strict")
    template_set_target_clang_tidy(
        "${template_cli_target}"
        PROFILE recommended
        WARNINGS_AS_ERRORS OFF
    )
  endif()
endif()

if(NOT CMAKE_SKIP_INSTALL_RULES)
  include(cmake/install-rules.cmake)
endif()

if(NOT template_developer_mode)
  return()
elseif(NOT PROJECT_IS_TOP_LEVEL)
  message(
      AUTHOR_WARNING
      "Developer mode is intended for developers of ${PROJECT_NAME}"
  )
endif()

include(cmake/dev-mode.cmake)
