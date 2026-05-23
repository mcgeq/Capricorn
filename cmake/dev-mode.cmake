include(cmake/folders.cmake)

include(CTest)
if(BUILD_TESTING)
  add_subdirectory(test)
endif()

set(template_build_benchmarks_option "${template_project_identifier}_BUILD_BENCHMARKS")
option(
    "${template_build_benchmarks_option}"
    "Build benchmark targets for local performance regression tracking"
    OFF
)
set(template_build_benchmarks "${${template_build_benchmarks_option}}")
if(template_build_benchmarks)
  add_subdirectory(benchmark)
endif()

set(template_build_fuzz_tests_option "${template_project_identifier}_BUILD_FUZZ_TESTS")
option(
    "${template_build_fuzz_tests_option}"
    "Build libFuzzer-based fuzz targets for parser and API hardening"
    OFF
)
set(template_build_fuzz_tests "${${template_build_fuzz_tests_option}}")
if(template_build_fuzz_tests)
  add_subdirectory(fuzz)
endif()

if(TARGET "${template_cli_target}")
  add_custom_target(
      run-exe
      COMMAND "${template_cli_target}"
      VERBATIM
  )
  add_dependencies(run-exe "${template_cli_target}")
endif()

if(TARGET "${template_modules_cli_target}")
  add_custom_target(
      run-modules-exe
      COMMAND "${template_modules_cli_target}"
      VERBATIM
  )
  add_dependencies(run-modules-exe "${template_modules_cli_target}")
endif()

option(BUILD_MCSS_DOCS "Build documentation using Doxygen and m.css" OFF)
if(BUILD_MCSS_DOCS)
  include(cmake/docs.cmake)
endif()

if(ENABLE_COVERAGE)
  include(cmake/coverage.cmake)
endif()

include(cmake/lint-targets.cmake)
include(cmake/clang-tidy-targets.cmake)
include(cmake/spell-targets.cmake)

add_folders(Project)
