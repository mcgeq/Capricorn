include_guard(GLOBAL)

add_library("${template_modules_target}")
add_library("${template_modules_alias}" ALIAS "${template_modules_target}")

target_sources(
    "${template_modules_target}"
    PUBLIC
    FILE_SET cxx_modules TYPE CXX_MODULES
    BASE_DIRS
    "${PROJECT_SOURCE_DIR}/source/modules"
    FILES
    "${template_module_interface_source}"
)

target_compile_features("${template_modules_target}" PUBLIC cxx_std_23)
template_apply_options("${template_modules_target}")

if(template_enable_clang_tidy AND template_clang_tidy_profile STREQUAL "strict")
  template_set_target_clang_tidy(
      "${template_modules_target}"
      PROFILE recommended
      WARNINGS_AS_ERRORS OFF
  )
endif()

if(PROJECT_IS_TOP_LEVEL AND template_build_cli)
  add_executable("${template_modules_cli_target}" "${template_module_cli_source}")
  add_executable("${template_modules_cli_alias}" ALIAS "${template_modules_cli_target}")

  set_property(
      TARGET "${template_modules_cli_target}"
      PROPERTY
      OUTPUT_NAME
      "${PROJECT_NAME}-modules"
  )
  set_property(
      TARGET "${template_modules_cli_target}"
      PROPERTY
      CXX_SCAN_FOR_MODULES
      ON
  )
  target_compile_features("${template_modules_cli_target}" PRIVATE cxx_std_23)
  target_link_libraries(
      "${template_modules_cli_target}" PRIVATE
      "${template_modules_target}"
  )
  add_dependencies("${template_modules_cli_target}" "${template_modules_target}")
  template_apply_options("${template_modules_cli_target}")

  if(template_enable_clang_tidy AND template_clang_tidy_profile STREQUAL "strict")
    template_set_target_clang_tidy(
        "${template_modules_cli_target}"
        PROFILE recommended
        WARNINGS_AS_ERRORS OFF
    )
  endif()
endif()
