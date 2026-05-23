#include <cstddef>
#include <cstdint>
#include <string_view>

#include <Capricorn/core/greeting.hpp>
#include <Capricorn/core/project_info.hpp>

extern "C" auto LLVMFuzzerTestOneInput(const std::uint8_t* data,
                                       std::size_t size) -> int
{
  const auto bytes = std::string_view {
      reinterpret_cast<const char*>(data),
      size,
  };

  (void)capricorn::greeting_for(bytes);

  if (bytes == capricorn::project_name()) {
    (void)capricorn::greeting();
  }

  return 0;
}
