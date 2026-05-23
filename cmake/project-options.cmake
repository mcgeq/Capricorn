include_guard(GLOBAL)

include(CheckIPOSupported)
include(CMakeParseArguments)

function(template_escape_regex out_var input)
  string(REGEX REPLACE "([][+.*()^$?{}|\\\\])" "\\\\\\1" escaped "${input}")
  set("${out_var}" "${escaped}" PARENT_SCOPE)
endfunction()

set(
    template_warnings_as_errors_option
    "${template_project_identifier}_WARNINGS_AS_ERRORS"
)
set(
    template_enable_hardening_option
    "${template_project_identifier}_ENABLE_HARDENING"
)
set(template_enable_ipo_option "${template_project_identifier}_ENABLE_IPO")
set(
    template_enable_sanitizers_option
    "${template_project_identifier}_ENABLE_SANITIZERS"
)
set(
    template_enable_clang_tidy_option
    "${template_project_identifier}_ENABLE_CLANG_TIDY"
)
set(
    template_enable_cxx_modules_option
    "${template_project_identifier}_ENABLE_CXX_MODULES"
)
set(
    template_clang_tidy_profile_option
    "${template_project_identifier}_CLANG_TIDY_PROFILE"
)
set(
    template_clang_tidy_warnings_as_errors_option
    "${template_project_identifier}_CLANG_TIDY_WARNINGS_AS_ERRORS"
)

option(
    "${template_warnings_as_errors_option}"
    "Treat compiler warnings as errors"
    ${PROJECT_IS_TOP_LEVEL}
)
option(
    "${template_enable_hardening_option}"
    "Enable hardening compile and link options"
    ${PROJECT_IS_TOP_LEVEL}
)
option(
    "${template_enable_ipo_option}"
    "Enable interprocedural optimization for release-like builds"
    OFF
)
option(
    "${template_enable_sanitizers_option}"
    "Enable address and undefined sanitizers"
    OFF
)
option(
    "${template_enable_clang_tidy_option}"
    "Enable clang-tidy during compilation for this build tree"
    OFF
)
option(
    "${template_enable_cxx_modules_option}"
    "Build the optional named C++23 module companion target"
    OFF
)
set(
    "${template_clang_tidy_profile_option}"
    "recommended"
    CACHE STRING
    "clang-tidy profile to use when compiler-integrated analysis is enabled"
)
set_property(
    CACHE "${template_clang_tidy_profile_option}"
    PROPERTY
    STRINGS
    recommended
    strict
)
option(
    "${template_clang_tidy_warnings_as_errors_option}"
    "Treat clang-tidy findings as errors for compiler-integrated analysis"
    OFF
)
option(ENABLE_COVERAGE "Enable coverage instrumentation and report targets" OFF)

set(template_warnings_as_errors "${${template_warnings_as_errors_option}}")
set(template_enable_hardening "${${template_enable_hardening_option}}")
set(template_enable_ipo "${${template_enable_ipo_option}}")
set(template_enable_sanitizers "${${template_enable_sanitizers_option}}")
set(template_enable_clang_tidy "${${template_enable_clang_tidy_option}}")
set(template_enable_cxx_modules "${${template_enable_cxx_modules_option}}")
set(template_clang_tidy_profile "${${template_clang_tidy_profile_option}}")
set(
    template_clang_tidy_warnings_as_errors
    "${${template_clang_tidy_warnings_as_errors_option}}"
)

if(template_enable_cxx_modules)
  if(CMAKE_VERSION VERSION_LESS 3.28)
    message(
        FATAL_ERROR
        "Optional C++23 modules require CMake 3.28 or newer."
    )
  endif()

  if(NOT CMAKE_GENERATOR MATCHES "Ninja|Visual Studio")
    message(
        FATAL_ERROR
        "Optional C++23 modules require a generator with module dependency "
        "scanning support, such as Ninja or Visual Studio 2022."
    )
  endif()

  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(
        FATAL_ERROR
        "This template's optional C++23 module target is currently wired for "
        "Clang-family and MSVC toolchains. Use the header target on GCC, or "
        "switch to a Clang/MSVC preset for modules."
    )
  endif()
endif()

if(template_clang_tidy_profile STREQUAL "recommended")
  set(template_clang_tidy_config_file "${PROJECT_SOURCE_DIR}/.clang-tidy")
elseif(template_clang_tidy_profile STREQUAL "strict")
  set(template_clang_tidy_config_file "${PROJECT_SOURCE_DIR}/.clang-tidy-strict")
else()
  message(
      FATAL_ERROR
      "Unsupported clang-tidy profile '${template_clang_tidy_profile}'. "
      "Expected one of: recommended, strict."
  )
endif()

template_escape_regex(template_source_dir_regex "${PROJECT_SOURCE_DIR}")
set(
    template_clang_tidy_header_filter
    "^${template_source_dir_regex}/(include|src|test)/"
)

function(template_require_clang_tidy_command out_var)
  if(DEFINED template_clang_tidy_command AND NOT template_clang_tidy_command STREQUAL "")
    set("${out_var}" "${template_clang_tidy_command}" PARENT_SCOPE)
    return()
  endif()

  find_program(template_local_clang_tidy_command NAMES clang-tidy)
  if(NOT template_local_clang_tidy_command)
    message(
        FATAL_ERROR
        "clang-tidy was requested but no clang-tidy executable was found on PATH."
    )
  endif()

  set(template_clang_tidy_command "${template_local_clang_tidy_command}" PARENT_SCOPE)
  set("${out_var}" "${template_local_clang_tidy_command}" PARENT_SCOPE)
endfunction()

function(template_resolve_clang_tidy_warnings_as_errors out_var value)
  if("${value}" STREQUAL "")
    set("${out_var}" "${template_clang_tidy_warnings_as_errors}" PARENT_SCOPE)
    return()
  endif()

  string(TOUPPER "${value}" template_clang_tidy_warnings_mode)
  if(template_clang_tidy_warnings_mode IN_LIST CMAKE_TRUE_STRINGS)
    set("${out_var}" ON PARENT_SCOPE)
    return()
  endif()
  if(template_clang_tidy_warnings_mode IN_LIST CMAKE_FALSE_STRINGS)
    set("${out_var}" OFF PARENT_SCOPE)
    return()
  endif()

  message(
      FATAL_ERROR
      "Invalid clang-tidy WARNINGS_AS_ERRORS value '${value}'. "
      "Expected ON, OFF, or an empty value to inherit the global setting."
  )
endfunction()

function(template_resolve_clang_tidy_profile_config out_var profile)
  if("${profile}" STREQUAL "" OR "${profile}" STREQUAL "recommended")
    set("${out_var}" "${PROJECT_SOURCE_DIR}/.clang-tidy" PARENT_SCOPE)
    return()
  endif()
  if("${profile}" STREQUAL "strict")
    set("${out_var}" "${PROJECT_SOURCE_DIR}/.clang-tidy-strict" PARENT_SCOPE)
    return()
  endif()

  message(
      FATAL_ERROR
      "Unsupported clang-tidy profile '${profile}'. "
      "Expected one of: recommended, strict."
  )
endfunction()

function(template_build_clang_tidy_arguments out_var)
  set(one_value_args PROFILE WARNINGS_AS_ERRORS)
  cmake_parse_arguments(ARG "" "${one_value_args}" "" ${ARGN})

  set(profile "${ARG_PROFILE}")
  if(profile STREQUAL "")
    set(profile "${template_clang_tidy_profile}")
  endif()

  template_resolve_clang_tidy_profile_config(config_file "${profile}")
  template_resolve_clang_tidy_warnings_as_errors(
      warnings_as_errors
      "${ARG_WARNINGS_AS_ERRORS}"
  )
  template_require_clang_tidy_command(clang_tidy_command)

  set(
      arguments
      "${clang_tidy_command}"
      "--config-file=${config_file}"
      "--header-filter=${template_clang_tidy_header_filter}"
  )
  if(warnings_as_errors)
    list(APPEND arguments "--warnings-as-errors=*")
  endif()

  set("${out_var}" "${arguments}" PARENT_SCOPE)
endfunction()

function(template_set_target_clang_tidy target)
  set(options DISABLE)
  set(one_value_args PROFILE WARNINGS_AS_ERRORS)
  cmake_parse_arguments(ARG "${options}" "${one_value_args}" "" ${ARGN})

  if(ARG_DISABLE)
    set_property(TARGET "${target}" PROPERTY CXX_CLANG_TIDY "")
    return()
  endif()

  template_build_clang_tidy_arguments(
      target_clang_tidy_arguments
      PROFILE "${ARG_PROFILE}"
      WARNINGS_AS_ERRORS "${ARG_WARNINGS_AS_ERRORS}"
  )
  set_property(
      TARGET "${target}"
      PROPERTY CXX_CLANG_TIDY "${target_clang_tidy_arguments}"
  )
endfunction()

if(template_enable_clang_tidy)
  template_build_clang_tidy_arguments(template_clang_tidy_arguments)
endif()

function(template_apply_options target)
  set_target_properties("${target}" PROPERTIES CXX_EXTENSIONS OFF)

  if(template_enable_clang_tidy)
    set_target_properties(
        "${target}"
        PROPERTIES
        CXX_CLANG_TIDY "${template_clang_tidy_arguments}"
    )
  endif()

  if(MSVC)
    target_compile_options(
        "${target}"
        PRIVATE
        /W4
        /permissive-
        /utf-8
        /w14242
        /w14254
        /w14263
        /w14265
        /w14287
        /w14296
        /w14311
        /w14545
        /w14546
        /w14547
        /w14549
        /w14555
        /w14619
        /w14640
        /w14826
        /w14905
        /w14906
        /w14928
    )

    if(template_warnings_as_errors)
      target_compile_options("${target}" PRIVATE /WX)
    endif()
  elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(
        "${target}"
        PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Wconversion
        -Wsign-conversion
        -Wcast-qual
        -Wformat=2
        -Wundef
        -Werror=float-equal
        -Wshadow
        -Wcast-align
        -Wunused
        -Wnull-dereference
        -Wdouble-promotion
        -Wimplicit-fallthrough
        -Wextra-semi
        -Woverloaded-virtual
        -Wnon-virtual-dtor
        -Wold-style-cast
    )

    if(template_warnings_as_errors)
      target_compile_options("${target}" PRIVATE -Werror)
    endif()
  endif()

  if(template_enable_hardening)
    if(MSVC)
      target_compile_options("${target}" PRIVATE /sdl /guard:cf)
      target_link_options("${target}" PRIVATE /guard:cf)
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
      set(
          template_hardening_compile_options
          -D_GLIBCXX_ASSERTIONS=1
          -fstack-protector-strong
      )
      if(CMAKE_CONFIGURATION_TYPES)
        list(
            APPEND
            template_hardening_compile_options
            "$<$<NOT:$<CONFIG:Debug>>:-U_FORTIFY_SOURCE>"
            "$<$<NOT:$<CONFIG:Debug>>:-D_FORTIFY_SOURCE=3>"
        )
      else()
        string(TOUPPER "${CMAKE_BUILD_TYPE}" template_build_type_upper)
        if(NOT template_build_type_upper STREQUAL "DEBUG" AND NOT template_build_type_upper STREQUAL "")
          list(
              APPEND
              template_hardening_compile_options
              -U_FORTIFY_SOURCE
              -D_FORTIFY_SOURCE=3
          )
        endif()
      endif()

      target_compile_options(
          "${target}"
          PRIVATE
          ${template_hardening_compile_options}
      )

      if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
        target_compile_options("${target}" PRIVATE -fstack-clash-protection)
        target_link_options("${target}" PRIVATE -Wl,-z,relro,-z,now,-z,noexecstack)

        if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|i[3-6]86)$")
          target_compile_options("${target}" PRIVATE -fcf-protection=full)
        endif()
      endif()
    endif()
  endif()

  if(MINGW AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # GCC 13 MinGW's static libstdc++ can provide a non-inline
    # std::type_info::operator== while this C++23 template emits the inline
    # version.
    target_link_options("${target}" PRIVATE -Wl,--allow-multiple-definition)
  endif()

  if(template_enable_sanitizers)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
      target_compile_options(
          "${target}"
          PRIVATE
          -fsanitize=address,undefined
          -fno-omit-frame-pointer
          -fno-common
      )
      target_link_options("${target}" PRIVATE -fsanitize=address,undefined)
    else()
      message(FATAL_ERROR "Sanitizers are only supported with Clang or GCC.")
    endif()
  endif()

  if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
      target_compile_options(
          "${target}"
          PRIVATE
          -Og
          -g
          --coverage
          -fkeep-inline-functions
          -fkeep-static-functions
      )
      target_link_options("${target}" PRIVATE --coverage)
    else()
      message(FATAL_ERROR "Coverage is only supported with Clang or GCC.")
    endif()
  endif()

  if(template_enable_ipo)
    check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error LANGUAGES CXX)
    if(NOT ipo_supported)
      message(FATAL_ERROR "IPO/LTO is not supported: ${ipo_error}")
    endif()

    if(CMAKE_CONFIGURATION_TYPES)
      foreach(config IN ITEMS RELEASE RELWITHDEBINFO MINSIZEREL)
        set_property(
            TARGET "${target}"
            PROPERTY "INTERPROCEDURAL_OPTIMIZATION_${config}"
            TRUE
        )
      endforeach()
    elseif(NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
      set_property(TARGET "${target}" PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
    endif()
  endif()
endfunction()
