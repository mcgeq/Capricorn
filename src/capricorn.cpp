#include <Capricorn/core/greeting.hpp>
#include <Capricorn/core/project_info.hpp>

#include "detail/greeting_builder.hpp"

namespace capricorn {
auto greeting() -> std::string {
  return greeting_for(project_name());
}

auto greeting_for(std::string_view subject) -> std::string {
  return detail::build_greeting(subject);
}
}  // namespace capricorn
