#include <Capricorn/core/greeting.hpp>
#include <benchmark/benchmark.h>

static void bm_greeting_for(benchmark::State& state)
{
  for (auto _ : state) {
    benchmark::DoNotOptimize(capricorn::greeting_for("benchmark"));
  }
}

BENCHMARK(bm_greeting_for);
