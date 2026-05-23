find_package(benchmark CONFIG REQUIRED)

add_executable("${template_benchmark_target}" "${template_benchmark_source}")
target_link_libraries(
    "${template_benchmark_target}" PRIVATE
    "${template_main_target}"
    benchmark::benchmark
)
target_compile_features("${template_benchmark_target}" PRIVATE cxx_std_20)
template_apply_options("${template_benchmark_target}")

if(template_enable_clang_tidy AND template_clang_tidy_profile STREQUAL "strict")
  template_set_target_clang_tidy(
      "${template_benchmark_target}"
      PROFILE recommended
      WARNINGS_AS_ERRORS OFF
  )
endif()

add_custom_target(
    run-benchmarks
    COMMAND "${template_benchmark_target}" --benchmark_min_time=0.01
    DEPENDS "${template_benchmark_target}"
    VERBATIM
)

add_folders(Benchmark)
