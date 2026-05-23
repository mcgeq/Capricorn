include_guard(GLOBAL)

# ---- Developer mode ----

# Developer mode enables targets and code paths in the CMake scripts that are
# only relevant for people working on this repository directly.
# Targets necessary to build the project must be provided unconditionally, so
# consumers can trivially build and package the project
set(template_developer_mode_option "${template_project_identifier}_DEVELOPER_MODE")
set(
    template_includes_with_system_option
    "${template_project_identifier}_INCLUDES_WITH_SYSTEM"
)

if(PROJECT_IS_TOP_LEVEL)
  option("${template_developer_mode_option}" "Enable developer mode" OFF)
endif()

set(template_developer_mode OFF)
if(DEFINED ${template_developer_mode_option})
  set(template_developer_mode "${${template_developer_mode_option}}")
endif()

# ---- Warning guard ----

# target_include_directories with the SYSTEM modifier will request the compiler
# to omit warnings from the provided paths, if the compiler supports that
# This is to provide a user experience similar to find_package when
# add_subdirectory or FetchContent is used to consume this project
set(warning_guard "")
if(NOT PROJECT_IS_TOP_LEVEL)
  option(
      "${template_includes_with_system_option}"
      "Use SYSTEM modifier for this project's includes, disabling warnings"
      ON
  )
  mark_as_advanced("${template_includes_with_system_option}")
  if(${template_includes_with_system_option})
    set(warning_guard SYSTEM)
  endif()
endif()
