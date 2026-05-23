find_package(Catch2 3 CONFIG REQUIRED)
include(Catch)

add_executable("${template_test_target}" "${template_test_source}")
target_link_libraries(
    "${template_test_target}" PRIVATE
    "${template_main_target}"
    Catch2::Catch2WithMain
)
target_compile_features("${template_test_target}" PRIVATE cxx_std_23)
template_apply_options("${template_test_target}")
if(template_enable_clang_tidy AND template_clang_tidy_profile STREQUAL "strict")
  template_set_target_clang_tidy(
      "${template_test_target}"
      PROFILE recommended
      WARNINGS_AS_ERRORS OFF
  )
endif()

catch_discover_tests("${template_test_target}")

set(package_prefix "${PROJECT_BINARY_DIR}/package")

file(MAKE_DIRECTORY "${template_package_source_dir}")
configure_file(
    "${PROJECT_SOURCE_DIR}/test/package/CMakeLists.txt.in"
    "${template_package_source_dir}/CMakeLists.txt"
    @ONLY
)
configure_file(
    "${PROJECT_SOURCE_DIR}/test/package/main.cpp.in"
    "${template_package_source_dir}/main.cpp"
    @ONLY
)
configure_file(
    "${PROJECT_SOURCE_DIR}/test/package/module_main.cpp.in"
    "${template_package_source_dir}/module_main.cpp"
    @ONLY
)

add_test(
    NAME "${PROJECT_NAME}.install"
    COMMAND
    "${CMAKE_COMMAND}" --install "${PROJECT_BINARY_DIR}" --prefix
    "${package_prefix}"
)
set_tests_properties(
    "${PROJECT_NAME}.install"
    PROPERTIES
    FIXTURES_SETUP ProjectInstall
)

set(
    template_package_configure_command
    "${CMAKE_COMMAND}"
    --fresh
    -G
    "${CMAKE_GENERATOR}"
)
if(CMAKE_GENERATOR_PLATFORM)
  list(APPEND template_package_configure_command -A "${CMAKE_GENERATOR_PLATFORM}")
endif()
if(CMAKE_GENERATOR_TOOLSET)
  list(APPEND template_package_configure_command -T "${CMAKE_GENERATOR_TOOLSET}")
endif()
if(CMAKE_CXX_COMPILER)
  list(APPEND template_package_configure_command -D "CMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}")
endif()
if(CMAKE_MAKE_PROGRAM)
  list(APPEND template_package_configure_command -D "CMAKE_MAKE_PROGRAM=${CMAKE_MAKE_PROGRAM}")
endif()
list(
    APPEND
    template_package_configure_command
    -S
    "${template_package_source_dir}"
    -B
    "${template_package_build_dir}"
    -D
    "CMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
    -D
    "CMAKE_PREFIX_PATH=${package_prefix}"
)

add_test(
    NAME "${PROJECT_NAME}.package.configure"
    COMMAND ${template_package_configure_command}
)
set_tests_properties(
    "${PROJECT_NAME}.package.configure"
    PROPERTIES
    FIXTURES_REQUIRED ProjectInstall
    FIXTURES_SETUP ProjectPackageConfigured
)

add_test(
    NAME "${PROJECT_NAME}.package.build"
    COMMAND
    "${CMAKE_COMMAND}" --build "${template_package_build_dir}"
)
set_tests_properties(
    "${PROJECT_NAME}.package.build"
    PROPERTIES
    FIXTURES_REQUIRED ProjectPackageConfigured
)

add_folders(Test)
