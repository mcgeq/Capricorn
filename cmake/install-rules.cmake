include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(
    TARGETS "${template_main_target}"
    EXPORT "${template_export_name}"
    RUNTIME COMPONENT "${PROJECT_NAME}_Runtime"
    LIBRARY COMPONENT "${PROJECT_NAME}_Runtime"
    ARCHIVE COMPONENT "${PROJECT_NAME}_Development"
    FILE_SET HEADERS COMPONENT "${PROJECT_NAME}_Development"
)

if(TARGET "${template_modules_target}")
  install(
      TARGETS "${template_modules_target}"
      EXPORT "${template_export_name}"
      RUNTIME COMPONENT "${PROJECT_NAME}_Runtime"
      LIBRARY COMPONENT "${PROJECT_NAME}_Runtime"
      ARCHIVE COMPONENT "${PROJECT_NAME}_Development"
      FILE_SET cxx_modules DESTINATION
      "${CMAKE_INSTALL_INCLUDEDIR}/${TEMPLATE_INCLUDE_DIR_NAME}/modules"
      COMPONENT "${PROJECT_NAME}_Development"
      CXX_MODULES_BMI DESTINATION ""
  )
endif()

if(TARGET "${template_cli_target}")
  install(
      TARGETS "${template_cli_target}"
      RUNTIME COMPONENT "${PROJECT_NAME}_Runtime"
  )
endif()

write_basic_package_version_file(
    "${PROJECT_BINARY_DIR}/${template_config_version_file}"
    VERSION "${PROJECT_VERSION}"
    COMPATIBILITY SameMajorVersion
)

set(template_package_dependency_block "")
foreach(template_dependency_snippet IN LISTS template_package_dependency_find_snippets)
  string(APPEND template_package_dependency_block "${template_dependency_snippet}\n")
endforeach()

configure_package_config_file(
    "${PROJECT_SOURCE_DIR}/cmake/project-config.cmake.in"
    "${PROJECT_BINARY_DIR}/${template_config_file}"
    INSTALL_DESTINATION "${template_package_install_dir}"
)

if(TARGET "${template_modules_target}")
  install(
      EXPORT "${template_export_name}"
      NAMESPACE "${template_package_namespace}"
      DESTINATION "${template_package_install_dir}"
      FILE "${template_export_name}.cmake"
      CXX_MODULES_DIRECTORY modules
      COMPONENT "${PROJECT_NAME}_Development"
  )
else()
  install(
      EXPORT "${template_export_name}"
      NAMESPACE "${template_package_namespace}"
      DESTINATION "${template_package_install_dir}"
      FILE "${template_export_name}.cmake"
      COMPONENT "${PROJECT_NAME}_Development"
  )
endif()

install(
    FILES
    "${PROJECT_BINARY_DIR}/${template_config_file}"
    "${PROJECT_BINARY_DIR}/${template_config_version_file}"
    DESTINATION "${template_package_install_dir}"
    COMPONENT "${PROJECT_NAME}_Development"
)

if(PROJECT_IS_TOP_LEVEL)
  include(CPack)
endif()
