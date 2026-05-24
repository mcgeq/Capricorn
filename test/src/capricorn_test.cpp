#include <Capricorn/capricorn.hpp>
#include <catch2/catch_test_macros.hpp>

TEST_CASE("project_name reports the package name", "[capricorn]") {
  REQUIRE(capricorn::project_name() == capricorn::k_project_name);
  REQUIRE(capricorn::project_version() == capricorn::k_project_version);
}

TEST_CASE("greeting builds a friendly message", "[capricorn]") {
  auto const expected =
      std::string{"Hello from "} + std::string{capricorn::k_project_name} + "!";

  REQUIRE(capricorn::greeting() == expected);
}

TEST_CASE("greeting_for formats arbitrary subjects", "[capricorn]") {
  REQUIRE(capricorn::greeting_for("templates") ==
          std::string{"Hello from templates!"});
}
