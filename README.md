# Capricorn

A modern C++ starter template built around CMake, installable library targets,
opt-in developer tooling, and cross-platform CI.

## Highlights

- Installable library target with generated `find_package` config
- Public headers under `include/`, internal helpers under `src/detail/`, and an
  optional `source/modules/` companion target for named C++23 modules
- Optional example CLI executable for top-level builds
- Optional `Capricorn::modules` target for consumers that prefer `import`
  over `#include`
- Catch2 tests, package smoke tests, formatting, spelling, docs, and coverage
- Layered `clang-tidy` profiles for low-noise local analysis and stricter CI gates
- Target-level `clang-tidy` overrides plus directory exclusions for noisy code
- Optional benchmark and fuzzing entry points for performance and robustness work
- Tracked `.clangd`, `.editorconfig`, `.gitattributes`, and VSCode extension
  recommendations for smoother first-open editor support
- Ready-to-use CMake presets for normal builds and full developer workflows

## Quickstart

Build the library and example executable without developer-only dependencies.
The checked-in default path uses `g++` plus `Unix Makefiles`:

```sh
cmake --workflow --preset default-debug
```

Enable tests and the rest of the developer workflow through vcpkg:

```sh
cmake --workflow --preset dev-debug
```

If you are working with MSVC locally, use:

```sh
cmake --workflow --preset msvc-debug
```

If you want to exercise the optional named module target with Clang and Ninja:

```sh
cmake --workflow --preset modules-debug
```

If you want the optional named module path plus developer-mode tests and
installed-package smoke coverage, use:

```sh
cmake --workflow --preset modules-dev-debug
```

For Visual Studio's native module workflow, use:

```sh
cmake --workflow --preset msvc-modules-debug
```

If you rename this template into a real project, read [TEMPLATE](TEMPLATE.md)
first. For more detail, see [BUILDING](BUILDING.md) and [HACKING](HACKING.md).

## Where Outputs Go

Preset builds write into the `binaryDir` configured in
[CMakePresets.json](CMakePresets.json). A few common examples:

- `default-debug` writes to `build/default-debug-gcc/`
- `default-release` writes to `build/default-release-gcc/`
- `dev-debug` writes to `build/dev-debug/`
- `modules-debug` writes to `build/modules-debug-clang/`
- `msvc-debug` writes to `build/msvc-debug/`

The sample CLI executable uses the project name as its final file name. If your
project is `hello_world`, a successful `default-debug` build typically produces:

```text
build/default-debug-gcc/hello_world
```

On Visual Studio generators, the executable usually lands under the active
configuration subdirectory, for example:

```text
build/msvc-debug/Debug/hello_world.exe
```

Other developer binaries follow the target names:

- tests: `build/<preset>/<ProjectName>_test`
- benchmarks: `build/<preset>/<ProjectName>_benchmark`
- fuzzing: `build/<preset>/<ProjectName>_fuzz`
- modules CLI: `build/<preset>/<ProjectName>-modules`

For `clangd`-based editors such as Neovim, the build also refreshes a
gitignored root `compile_commands.json` that mirrors the active preset's
compilation database. This lets `clangd` discover private include paths like
`src/` without extra editor-specific setup.

The checked-in [`.clangd`](.clangd) file also provides a small fallback for
editors that start before the first configure or before a compilation database
is available. It pins the template to C++23 and adds the repository's `include`
and `src` directories as fallback search paths.

For the optional named module sample, clang-based editors usually need the
`modules-debug` build tree as well. Running
`cmake --workflow --preset modules-debug` gives `clangd` a module-aware
compilation database for `source/modules/` and `src/main_modules.cpp`.

The repository also ships a tracked [`.editorconfig`](.editorconfig) plus
[`.vscode/extensions.json`](.vscode/extensions.json) so common editors can pick
up line-ending, indentation, and CMake/clangd recommendations immediately after
clone.

Tracked [`.gitattributes`](.gitattributes) also normalizes line endings across
platforms so shell scripts, CMake files, and Windows wrappers behave more
predictably after clone.

If you do not want to remember the path, use the helper targets:

```sh
cmake --build --preset dev-debug --target run-exe
cmake --build --preset bench-debug --target run-benchmarks
cmake --build --preset fuzz-debug --target run-fuzz-smoke
```

The default dependency policy is layered: keep installed/public dependencies on
explicit `find_package()` boundaries, and keep repository-local developer
tooling behind opt-in `vcpkg` features.

The sample library layout is also intentionally layered:

- `include/<Project>/<basename>.hpp`: umbrella header for the stable public API
- `include/<Project>/core/`: focused public library features that scale beyond a
  single header
- `src/detail/`: private implementation helpers that are not installed
- `source/modules/`: optional named module sources exported as
  `Capricorn::modules` when you enable C++23 modules

The rename helper can initialize the sample names, package name, and tracked
template identifiers in one pass. Prefer the root wrapper that matches your
platform:

```sh
./run.sh --project-name MyProject --check
```

```cmd
run.bat --project-name MyProject --check
```

```powershell
.\run.bat --project-name MyProject --check
```

If you started from `git clone <url> MyProject`, you can instead run:

```sh
cd MyProject
./run.sh --init
```

```cmd
cd MyProject
run.bat --init
```

```powershell
cd MyProject
.\run.bat --init
```

The interactive initializer derives defaults from the clone directory, runs the
tracked residual check, removes cloned `.git` metadata, runs `git init`, and
removes template-maintainer files from the new project so it starts without
template history or one-time initialization tools.

Before the first build, you can quickly check local toolchain readiness with:

```sh
./run.sh --doctor
```

```cmd
run.bat --doctor
```

```powershell
.\run.bat --doctor
```

If you want lightweight local commit checks for formatting, preset validity, and
spelling, install the tracked git hook:

```sh
./run.sh --install-hooks
```

```cmd
run.bat --install-hooks
```

If you want one command to apply the same local formatting and spelling fixes:

```sh
./run.sh --fix
```

```cmd
run.bat --fix
```

```powershell
.\run.bat --fix
```

The fix helper reuses the template's checked-in `clang-format` and `codespell`
policy. It also covers optional module, benchmark, and fuzz source trees when
`clang-format` is available.

## Consuming The Installed Package

After installation, consumers can use:

```cmake
find_package(Capricorn CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE Capricorn::Capricorn)
```

The exported package is intentionally consumer-facing CMake first. Downstream
users do not need to adopt `vcpkg`; they only need to satisfy whatever public
`find_package()` requirements the library exposes.

If you enable the optional module target when building and installing the
package, consumers can instead write:

```cmake
find_package(Capricorn CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE Capricorn::modules)
```

```cpp
import capricorn;
```

The sample module target is a companion surface, not an additive one. Link
either `Capricorn::Capricorn` or `Capricorn::modules` into a given binary, not
both.

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md).

## Licensing

<!--
Please go to https://choosealicense.com/licenses/ and choose a license that
fits your needs. The recommended license for a project of this type is the
GNU AGPLv3.
-->
