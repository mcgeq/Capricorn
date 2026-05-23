module;

#include <string>
#include <string_view>

export module capricorn;

export namespace capricorn
{
inline constexpr std::string_view k_project_name {"Capricorn"};
inline constexpr std::string_view k_project_version {"0.1.0"};
inline constexpr int k_project_version_major {0};
inline constexpr int k_project_version_minor {1};
inline constexpr int k_project_version_patch {0};

[[nodiscard]] constexpr auto project_name() noexcept -> std::string_view
{
  return k_project_name;
}

[[nodiscard]] constexpr auto project_version() noexcept -> std::string_view
{
  return k_project_version;
}

[[nodiscard]] auto greeting() -> std::string;

[[nodiscard]] auto greeting_for(std::string_view subject) -> std::string;
}  // namespace capricorn

auto capricorn::greeting() -> std::string
{
  return greeting_for(project_name());
}

auto capricorn::greeting_for(std::string_view subject) -> std::string
{
  return std::string {"Hello from "} + std::string {subject} + "!";
}
