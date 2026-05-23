if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  message(
      STATUS
      "Skipping fuzz target because libFuzzer entrypoints are only wired for Clang."
  )
  return()
endif()

add_executable("${template_fuzz_target}" "${template_fuzz_source}")
target_link_libraries("${template_fuzz_target}" PRIVATE "${template_main_target}")
target_compile_features("${template_fuzz_target}" PRIVATE cxx_std_20)
template_apply_options("${template_fuzz_target}")

target_compile_options(
    "${template_fuzz_target}"
    PRIVATE
    -fsanitize=fuzzer,address,undefined
)
target_link_options(
    "${template_fuzz_target}"
    PRIVATE
    -fsanitize=fuzzer,address,undefined
)

if(template_enable_clang_tidy)
  template_set_target_clang_tidy(
      "${template_fuzz_target}"
      PROFILE recommended
      WARNINGS_AS_ERRORS OFF
  )
endif()

add_custom_target(
    run-fuzz-smoke
    COMMAND "${template_fuzz_target}" -max_total_time=3
    DEPENDS "${template_fuzz_target}"
    VERBATIM
)

add_folders(Fuzz)
