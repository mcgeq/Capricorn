include_guard(GLOBAL)

include(CMakeParseArguments)

set(
    TEMPLATE_DEPENDENCY_STRATEGY
    "Public runtime and library dependencies must be discovered with find_package() and surfaced explicitly in installed package metadata. Developer-only tooling dependencies should live behind vcpkg manifest features. FetchContent is reserved for opt-in repository-local tooling or documentation helpers, not for consumer-visible runtime dependencies."
    CACHE INTERNAL
    "Template package-management strategy guidance"
)

set(template_package_dependency_find_snippets "")

function(template_note_dependency_strategy)
  message(STATUS "Dependency strategy: ${TEMPLATE_DEPENDENCY_STRATEGY}")
endfunction()

function(template_register_package_dependency)
  set(one_value_args
      NAME
      VERSION
      FIND_PACKAGE_ARGS
      FIND_SNIPPET
  )
  cmake_parse_arguments(ARG "" "${one_value_args}" "" ${ARGN})

  if(ARG_NAME STREQUAL "")
    message(FATAL_ERROR "template_register_package_dependency requires NAME.")
  endif()

  set(find_package_args "${ARG_FIND_PACKAGE_ARGS}")
  if(find_package_args STREQUAL "")
    set(find_package_args CONFIG REQUIRED)
    if(NOT ARG_VERSION STREQUAL "")
      set(find_package_args "${ARG_VERSION} ${find_package_args}")
    endif()
  endif()

  if(ARG_FIND_SNIPPET STREQUAL "")
    set(find_snippet "find_dependency(${ARG_NAME} ${find_package_args})")
  else()
    set(find_snippet "${ARG_FIND_SNIPPET}")
  endif()

  list(APPEND template_package_dependency_find_snippets "${find_snippet}")
  set(
      template_package_dependency_find_snippets
      "${template_package_dependency_find_snippets}"
      PARENT_SCOPE
  )
endfunction()
