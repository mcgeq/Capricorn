include_guard(GLOBAL)

include(GNUInstallDirs)

string(MAKE_C_IDENTIFIER "${PROJECT_NAME}" template_project_identifier)

string(TOLOWER "${PROJECT_NAME}" template_default_library_basename)
string(
    MAKE_C_IDENTIFIER
    "${template_default_library_basename}"
    template_default_library_basename
)

if(NOT DEFINED TEMPLATE_INCLUDE_DIR_NAME)
  set(TEMPLATE_INCLUDE_DIR_NAME "${PROJECT_NAME}")
endif()

if(NOT DEFINED TEMPLATE_LIBRARY_BASENAME)
  set(TEMPLATE_LIBRARY_BASENAME "${template_default_library_basename}")
endif()

if(NOT DEFINED TEMPLATE_LIBRARY_NAMESPACE)
  set(TEMPLATE_LIBRARY_NAMESPACE "${TEMPLATE_LIBRARY_BASENAME}")
endif()

set(template_main_target "${PROJECT_NAME}")
set(template_main_alias "${PROJECT_NAME}::${PROJECT_NAME}")
set(template_cli_target "${PROJECT_NAME}_cli")
set(template_cli_alias "${PROJECT_NAME}::cli")
set(template_modules_target "${PROJECT_NAME}_modules")
set(template_modules_alias "${PROJECT_NAME}::modules")
set(template_modules_cli_target "${PROJECT_NAME}_modules_cli")
set(template_modules_cli_alias "${PROJECT_NAME}::modules_cli")
set(template_test_target "${PROJECT_NAME}_test")
set(template_benchmark_target "${PROJECT_NAME}_benchmark")
set(template_fuzz_target "${PROJECT_NAME}_fuzz")
set(template_export_name "${PROJECT_NAME}Targets")
set(template_package_namespace "${PROJECT_NAME}::")
set(template_config_file "${PROJECT_NAME}Config.cmake")
set(template_config_version_file "${PROJECT_NAME}ConfigVersion.cmake")
set(template_package_install_dir "${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}")

set(template_generated_include_dir "${PROJECT_BINARY_DIR}/generated/include")
set(
    template_public_header
    "${PROJECT_SOURCE_DIR}/include/${TEMPLATE_INCLUDE_DIR_NAME}/${TEMPLATE_LIBRARY_BASENAME}.hpp"
)
set(
    template_public_headers
    "${template_public_header}"
    "${PROJECT_SOURCE_DIR}/include/${TEMPLATE_INCLUDE_DIR_NAME}/core/greeting.hpp"
    "${PROJECT_SOURCE_DIR}/include/${TEMPLATE_INCLUDE_DIR_NAME}/core/project_info.hpp"
)
set(
    template_library_source
    "${PROJECT_SOURCE_DIR}/src/${TEMPLATE_LIBRARY_BASENAME}.cpp"
)
set(template_module_name "${TEMPLATE_LIBRARY_BASENAME}")
set(
    template_library_sources
    "${template_library_source}"
    "${PROJECT_SOURCE_DIR}/src/detail/greeting_builder.cpp"
)
set(
    template_private_headers
    "${PROJECT_SOURCE_DIR}/src/detail/greeting_builder.hpp"
)
set(
    template_module_interface_source
    "${PROJECT_SOURCE_DIR}/source/modules/${template_module_name}.ixx"
)
set(
    template_module_cli_source
    "${PROJECT_SOURCE_DIR}/src/main_modules.cpp"
)
set(
    template_test_source
    "${PROJECT_SOURCE_DIR}/test/src/${TEMPLATE_LIBRARY_BASENAME}_test.cpp"
)
set(
    template_benchmark_source
    "${PROJECT_SOURCE_DIR}/benchmark/src/${TEMPLATE_LIBRARY_BASENAME}_benchmark.cpp"
)
set(
    template_fuzz_source
    "${PROJECT_SOURCE_DIR}/fuzz/src/${TEMPLATE_LIBRARY_BASENAME}_fuzz.cpp"
)
set(template_package_source_dir "${PROJECT_BINARY_DIR}/package-smoke-src")
set(template_package_build_dir "${PROJECT_BINARY_DIR}/package-smoke")
set(
    template_package_test_target
    "${TEMPLATE_LIBRARY_BASENAME}_package_smoke_test"
)
set(
    template_package_module_test_target
    "${TEMPLATE_LIBRARY_BASENAME}_package_module_smoke_test"
)
