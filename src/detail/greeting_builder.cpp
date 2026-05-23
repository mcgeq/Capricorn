#include "detail/greeting_builder.hpp"

namespace capricorn::detail
{
auto build_greeting(std::string_view subject) -> std::string
{
  return std::string {"Hello from "} + std::string {subject} + "!";
}
}  // namespace capricorn::detail
