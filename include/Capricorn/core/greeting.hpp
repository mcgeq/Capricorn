#pragma once

#include <string>
#include <string_view>

namespace capricorn {
[[nodiscard]] auto greeting() -> std::string;

[[nodiscard]] auto greeting_for(std::string_view subject) -> std::string;
}  // namespace capricorn
