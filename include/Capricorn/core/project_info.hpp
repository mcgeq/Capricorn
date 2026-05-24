#pragma once

#include <string_view>

#include <Capricorn/project_config.hpp>

namespace capricorn {
[[nodiscard]] constexpr auto project_name() noexcept -> std::string_view {
  return k_project_name;
}

[[nodiscard]] constexpr auto project_version() noexcept -> std::string_view {
  return k_project_version;
}
}  // namespace capricorn
