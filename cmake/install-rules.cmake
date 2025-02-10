install(
    TARGETS Capricorn_exe
    RUNTIME COMPONENT Capricorn_Runtime
)

if(PROJECT_IS_TOP_LEVEL)
  include(CPack)
endif()
