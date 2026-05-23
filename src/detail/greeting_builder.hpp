#pragma once

#include <string>
#include <string_view>

namespace capricorn::detail
{
[[nodiscard]] auto build_greeting(std::string_view subject) -> std::string;
}  // namespace capricorn::detail
