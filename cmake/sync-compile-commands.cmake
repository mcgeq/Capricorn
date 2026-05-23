if(NOT DEFINED TEMPLATE_BINARY_COMPILE_COMMANDS)
  message(FATAL_ERROR "TEMPLATE_BINARY_COMPILE_COMMANDS is required")
endif()

if(NOT DEFINED TEMPLATE_ROOT_COMPILE_COMMANDS)
  message(FATAL_ERROR "TEMPLATE_ROOT_COMPILE_COMMANDS is required")
endif()

if(NOT EXISTS "${TEMPLATE_BINARY_COMPILE_COMMANDS}")
  message(
      STATUS
      "Skipping compile_commands sync because '${TEMPLATE_BINARY_COMPILE_COMMANDS}' does not exist yet."
  )
  return()
endif()

execute_process(
    COMMAND
    "${CMAKE_COMMAND}" -E copy_if_different
    "${TEMPLATE_BINARY_COMPILE_COMMANDS}"
    "${TEMPLATE_ROOT_COMPILE_COMMANDS}"
    RESULT_VARIABLE template_sync_result
)

if(NOT template_sync_result EQUAL 0)
  message(
      FATAL_ERROR
      "Failed to sync compile_commands.json to '${TEMPLATE_ROOT_COMPILE_COMMANDS}'."
  )
endif()
