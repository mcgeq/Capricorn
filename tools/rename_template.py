from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RenamePlan:
    project_name: str
    include_dir_name: str
    library_basename: str
    namespace: str
    package_name: str
    old_include_dir_name: str
    old_library_basename: str
    old_namespace: str
    old_project_name: str
    old_package_name: str

    @property
    def old_project_identifier(self) -> str:
        return make_cmake_identifier(self.old_project_name)

    @property
    def project_identifier(self) -> str:
        return make_cmake_identifier(self.project_name)

    @property
    def old_apply_options_name(self) -> str:
        return f"{self.old_library_basename}_apply_options"

    @property
    def apply_options_name(self) -> str:
        return f"{self.library_basename}_apply_options"


TRACKED_TEXT_FILES = [
    ".github/workflows/ci.yml",
    "CMakeLists.txt",
    "CMakePresets.json",
    "README.md",
    "BUILDING.md",
    "HACKING.md",
    "CONTRIBUTING.md",
    "TEMPLATE.md",
    "vcpkg.json",
    "docs/Doxyfile.in",
    "docs/pages/about.dox",
    "cmake/project-metadata.cmake",
    "cmake/dependencies.cmake",
    "cmake/project-config.cmake.in",
    "cmake/project-config.hpp.in",
    "cmake/install-rules.cmake",
    "cmake/dev-mode.cmake",
    "cmake/variables.cmake",
    "cmake/project-options.cmake",
    "cmake/cxx-modules-targets.cmake",
    "cmake/lint.cmake",
    "cmake/lint-targets.cmake",
    "include/Capricorn/core/greeting.hpp",
    "include/Capricorn/core/project_info.hpp",
    "src/detail/greeting_builder.hpp",
    "src/detail/greeting_builder.cpp",
    "source/modules/README.md",
    "src/main_modules.cpp",
    "benchmark/CMakeLists.txt",
    "fuzz/CMakeLists.txt",
    "test/CMakeLists.txt",
    "test/package/CMakeLists.txt.in",
    "test/package/main.cpp.in",
    "test/package/module_main.cpp.in",
    "tools/README.md",
]

RENAMABLE_TEXT_FILES = [
    "include/{old_include_dir_name}/{old_library_basename}.hpp",
    "src/{old_library_basename}.cpp",
    "source/modules/{old_library_basename}.ixx",
    "src/main.cpp",
    "benchmark/src/{old_library_basename}_benchmark.cpp",
    "fuzz/src/{old_library_basename}_fuzz.cpp",
    "test/src/{old_library_basename}_test.cpp",
]

POST_INIT_REMOVE_PATHS = [
    "TEMPLATE.md",
    "compile_commands.json",
    "build",
    "tools/__pycache__",
    "tools/rename_template.py",
    "tools/test_template_init.py",
]

POST_INIT_PROJECT_PREFIX_FILES = [
    "CMakeLists.txt",
    "HACKING.md",
    "benchmark/CMakeLists.txt",
    "fuzz/CMakeLists.txt",
    "test/CMakeLists.txt",
    "test/package/CMakeLists.txt.in",
    "test/package/main.cpp.in",
    "test/package/module_main.cpp.in",
    "cmake/clang-tidy-targets.cmake",
    "cmake/cxx-modules-targets.cmake",
    "cmake/dependencies.cmake",
    "cmake/dev-mode.cmake",
    "cmake/install-rules.cmake",
    "cmake/project-config.cmake.in",
    "cmake/project-config.hpp.in",
    "cmake/project-metadata.cmake",
    "cmake/project-options.cmake",
    "cmake/sync-compile-commands.cmake",
    "cmake/variables.cmake",
]

POST_INIT_RUN_BAT = """@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "DOCTOR_HELPER=%SCRIPT_DIR%tools\\doctor.py"
set "FIX_HELPER=%SCRIPT_DIR%tools\\fix.py"
set "HOOKS_HELPER=%SCRIPT_DIR%tools\\install_git_hooks.py"

if "%~1"=="" goto usage_error
if "%~1"=="--help" goto usage_ok
if "%~1"=="--doctor" goto doctor
if "%~1"=="--fix" goto fix
if "%~1"=="--install-hooks" goto hooks
goto usage_error

:doctor
shift
set "TARGET_HELPER=%DOCTOR_HELPER%"
goto run

:fix
shift
set "TARGET_HELPER=%FIX_HELPER%"
goto run

:hooks
shift
set "TARGET_HELPER=%HOOKS_HELPER%"
goto run

:run
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 "%TARGET_HELPER%" %*
    exit /b !ERRORLEVEL!
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%TARGET_HELPER%" %*
    exit /b !ERRORLEVEL!
)

>&2 echo error: Python 3 interpreter not found. Install Python and retry.
exit /b 1

:usage_ok
echo Usage: run.bat ^<command^>
echo.
echo Commands:
echo   --doctor          Check local toolchain readiness
echo   --fix             Apply formatting and spelling fixes
echo   --install-hooks   Configure tracked git hooks
exit /b 0

:usage_error
call :usage_ok
exit /b 2
"""

POST_INIT_RUN_SH = """#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DOCTOR_HELPER="$SCRIPT_DIR/tools/doctor.py"
FIX_HELPER="$SCRIPT_DIR/tools/fix.py"
HOOKS_HELPER="$SCRIPT_DIR/tools/install_git_hooks.py"

usage() {
    cat <<'EOF'
Usage: ./run.sh <command>

Commands:
  --doctor          Check local toolchain readiness
  --fix             Apply formatting and spelling fixes
  --install-hooks   Configure tracked git hooks
EOF
}

if [ "${1-}" = "" ] || [ "${1-}" = "--help" ]; then
    usage
    if [ "${1-}" = "--help" ]; then
        exit 0
    fi
    exit 2
elif [ "${1-}" = "--doctor" ]; then
    shift
    TARGET_HELPER="$DOCTOR_HELPER"
elif [ "${1-}" = "--fix" ]; then
    shift
    TARGET_HELPER="$FIX_HELPER"
elif [ "${1-}" = "--install-hooks" ]; then
    shift
    TARGET_HELPER="$HOOKS_HELPER"
else
    usage
    exit 2
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$TARGET_HELPER" "$@"
fi

if command -v python >/dev/null 2>&1; then
    exec python "$TARGET_HELPER" "$@"
fi

printf '%s\\n' "error: Python 3 interpreter not found. Install Python and retry." >&2
exit 1
"""

POST_INIT_TOOLS_README = """# Tools

- Preferred developer entrypoints live at the repository root:
  `run.bat` for Windows and `run.sh` for Unix-like systems.
- `doctor.py`: Reports whether the local machine is ready for the project's
  main preset families, including GNU, Clang/modules, developer-mode `vcpkg`,
  and editor-facing `clangd` support, then recommends a sensible next preset.
  Use it through `run.sh --doctor` or `run.bat --doctor`.
- `fix.py`: Applies the project's checked-in `clang-format` and `codespell`
  fixes through one best-effort entrypoint. Use it through `run.sh --fix` or
  `run.bat --fix`.
- `install_git_hooks.py`: Configures `core.hooksPath` to use the tracked
  `.githooks/` directory for this repository. Use it through
  `run.sh --install-hooks` or `run.bat --install-hooks`.
- `pre_commit.py`: Runs the lightweight commit-time checks used by the tracked
  `pre-commit` hook, including preset validation plus optional staged-file
  formatting and spelling checks.
- `cmake/run-clang-tidy.cmake`: Drives the `tidy-check` target over the
  repository's configured source directories using the active build tree's
  compilation database, with optional directory exclusions.
- `cmake/cxx-modules-targets.cmake`: Wires the optional named module companion
  target plus its sample import-based executable.
- `source/modules/`: Holds the checked-in module interface sample and the
  short guidance note for keeping the module path optional.
- `benchmark/` and `fuzz/`: Sample entry points showing how to wire Google
  Benchmark and libFuzzer into this project.
- `cmake/dependencies.cmake`: Documents the dependency policy and provides a
  helper hook for installed-package `find_dependency(...)` requirements.
"""


def post_init_doctor_content(plan: RenamePlan) -> str:
    return f"""from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_NAME = {plan.project_name!r}
MIN_CMAKE_VERSION = (3, 25, 0)
MIN_MODULES_CMAKE_VERSION = (3, 28, 0)


@dataclass(frozen=True)
class Finding:
    level: str
    subject: str
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Check whether the local environment is ready for {{PROJECT_NAME}}."
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures for CI-style gating.",
    )
    return parser.parse_args()


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\\d+)\\.(\\d+)\\.(\\d+)", text)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def format_version(version: tuple[int, int, int] | None) -> str:
    if version is None:
        return "unknown"
    return ".".join(str(part) for part in version)


def detect_tool(name: str) -> tuple[str | None, tuple[int, int, int] | None]:
    path = shutil.which(name)
    if path is None:
        return None, None

    result = run_command([path, "--version"])
    output = f"{{result.stdout}}\\n{{result.stderr}}"
    return path, parse_version(output)


def detect_cmake() -> tuple[str | None, tuple[int, int, int] | None]:
    path = shutil.which("cmake")
    if path is None:
        return None, None

    result = run_command([path, "--version"])
    output = f"{{result.stdout}}\\n{{result.stderr}}"
    return path, parse_version(output)


def emit(finding: Finding) -> None:
    print(f"[{{finding.level}}] {{finding.subject}}: {{finding.detail}}")


def readiness(condition: bool, subject: str, ok_detail: str, warn_detail: str) -> Finding:
    if condition:
        return Finding("PASS", subject, ok_detail)
    return Finding("WARN", subject, warn_detail)


def recommendation_lines(
    *,
    gxx_ready: bool,
    clangxx_ready: bool,
    ninja_ready: bool,
    vcpkg_ready: bool,
    modules_cmake_ready: bool,
) -> list[str]:
    lines: list[str] = []

    if modules_cmake_ready and clangxx_ready and ninja_ready and vcpkg_ready:
        lines.append(
            "Recommended next step: `cmake --workflow --preset modules-dev-debug`"
        )
        lines.append(
            "Why: this machine is ready for the modern C++ path with modules, tests, and package smoke coverage."
        )
        return lines

    if gxx_ready and vcpkg_ready:
        lines.append(
            "Recommended next step: `cmake --workflow --preset dev-debug`"
        )
        lines.append(
            "Why: this machine is ready for the normal developer workflow with tests."
        )
        if modules_cmake_ready and clangxx_ready and not ninja_ready:
            lines.append(
                "To unlock modules next: install Ninja, then try `cmake --workflow --preset modules-dev-debug`."
            )
        elif modules_cmake_ready and not clangxx_ready:
            lines.append(
                "To unlock modules next: install clang++, then try `cmake --workflow --preset modules-dev-debug`."
            )
        elif modules_cmake_ready and clangxx_ready and ninja_ready and not vcpkg_ready:
            lines.append(
                "To unlock modules tests next: set `VCPKG_ROOT`, then try `cmake --workflow --preset modules-dev-debug`."
            )
        return lines

    if gxx_ready:
        lines.append(
            "Recommended next step: `cmake --workflow --preset default-debug`"
        )
        lines.append(
            "Why: the basic GNU build path is ready, but developer-mode dependencies are incomplete."
        )
        if not vcpkg_ready:
            lines.append(
                "To unlock tests and richer presets: set `VCPKG_ROOT`, then try `cmake --workflow --preset dev-debug`."
            )
        return lines

    if clangxx_ready and ninja_ready and modules_cmake_ready:
        lines.append(
            "Recommended next step: `cmake --workflow --preset modules-debug`"
        )
        lines.append(
            "Why: the optional modules compile path is ready, even though the GNU presets are not."
        )
        if not vcpkg_ready:
            lines.append(
                "To unlock modules tests: set `VCPKG_ROOT`, then try `cmake --workflow --preset modules-dev-debug`."
            )
        return lines

    lines.append("Recommended next step: fix the failing environment checks above first.")
    missing: list[str] = []
    if not gxx_ready:
        missing.append("g++")
    if not clangxx_ready:
        missing.append("clang++")
    if not ninja_ready:
        missing.append("ninja")
    if not vcpkg_ready:
        missing.append("VCPKG_ROOT")
    if missing:
        lines.append("Most useful missing pieces: " + ", ".join(missing))
    return lines


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []

    findings.append(
        Finding(
            "PASS",
            "Workspace",
            f"{{ROOT}} on {{platform.system()}} {{platform.release()}}",
        )
    )
    findings.append(
        Finding(
            "PASS",
            "Python",
            f"{{sys.version_info.major}}.{{sys.version_info.minor}}.{{sys.version_info.micro}}",
        )
    )

    cmake_path, cmake_version = detect_cmake()
    if cmake_path is None:
        findings.append(
            Finding(
                "FAIL",
                "CMake",
                "Not found on PATH. Install CMake 3.25 or newer.",
            )
        )
        for finding in findings:
            emit(finding)
        print("\\nSummary: 2 passed, 0 warnings, 1 failed")
        return 1

    if cmake_version is None or cmake_version < MIN_CMAKE_VERSION:
        findings.append(
            Finding(
                "FAIL",
                "CMake",
                "Found "
                f"{{format_version(cmake_version)}} at {{cmake_path}}, "
                f"but {{PROJECT_NAME}} requires 3.25 or newer.",
            )
        )
    else:
        findings.append(
            Finding(
                "PASS",
                "CMake",
                f"{{format_version(cmake_version)}} at {{cmake_path}}",
            )
        )

    preset_result = run_command(["cmake", "--list-presets"])
    if preset_result.returncode == 0:
        findings.append(
            Finding("PASS", "Preset schema", "CMakePresets.json is readable.")
        )
    else:
        findings.append(
            Finding(
                "FAIL",
                "Preset schema",
                "CMake could not read CMakePresets.json.\\n"
                f"{{preset_result.stderr.strip()}}".strip(),
            )
        )

    gxx_path, gxx_version = detect_tool("g++")
    clangxx_path, clangxx_version = detect_tool("clang++")
    ninja_path, ninja_version = detect_tool("ninja")
    clangd_path, clangd_version = detect_tool("clangd")

    if gxx_path is not None:
        findings.append(
            Finding(
                "PASS",
                "g++",
                f"{{format_version(gxx_version)}} at {{gxx_path}}",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "g++",
                "Not found on PATH. GNU presets such as default-debug are unavailable.",
            )
        )

    if clangxx_path is not None:
        findings.append(
            Finding(
                "PASS",
                "clang++",
                f"{{format_version(clangxx_version)}} at {{clangxx_path}}",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "clang++",
                "Not found on PATH. Modules and fuzz presets are unavailable.",
            )
        )

    if ninja_path is not None:
        findings.append(
            Finding(
                "PASS",
                "Ninja",
                f"{{format_version(ninja_version)}} at {{ninja_path}}",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "Ninja",
                "Not found on PATH. modules-debug and modules-dev-debug need Ninja.",
            )
        )

    if clangd_path is not None:
        findings.append(
            Finding(
                "PASS",
                "clangd",
                f"{{format_version(clangd_version)}} at {{clangd_path}}",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "clangd",
                "Not found on PATH. Editor diagnostics will rely on other tooling.",
            )
        )

    vcpkg_root = os.environ.get("VCPKG_ROOT")
    if not vcpkg_root:
        findings.append(
            Finding(
                "WARN",
                "VCPKG_ROOT",
                "Not set. dev-*, coverage, tidy-*, bench-debug, and modules-dev-debug are unavailable.",
            )
        )
        has_vcpkg = False
    else:
        vcpkg_root_path = Path(vcpkg_root)
        toolchain = vcpkg_root_path / "scripts" / "buildsystems" / "vcpkg.cmake"
        has_vcpkg = toolchain.exists()
        findings.append(
            readiness(
                has_vcpkg,
                "VCPKG_ROOT",
                f"{{vcpkg_root}} (toolchain found)",
                f"{{vcpkg_root}} is set, but {{toolchain}} was not found.",
            )
        )

    has_modules_cmake = (
        cmake_version is not None and cmake_version >= MIN_MODULES_CMAKE_VERSION
    )
    gxx_ready = gxx_path is not None
    clangxx_ready = clangxx_path is not None
    ninja_ready = ninja_path is not None

    findings.append(
        readiness(
            gxx_ready,
            "Preset default-debug/default-release",
            "Ready.",
            "Requires g++ on PATH.",
        )
    )
    findings.append(
        readiness(
            gxx_ready and has_vcpkg,
            "Preset dev-debug/dev-release/asan/coverage/tidy-*",
            "Ready.",
            "Requires g++ on PATH plus a valid VCPKG_ROOT.",
        )
    )
    findings.append(
        readiness(
            gxx_ready and has_vcpkg,
            "Preset bench-debug",
            "Ready.",
            "Requires g++ on PATH plus a valid VCPKG_ROOT.",
        )
    )
    findings.append(
        readiness(
            clangxx_ready and has_vcpkg,
            "Preset fuzz-debug",
            "Ready.",
            "Requires clang++ on PATH plus a valid VCPKG_ROOT.",
        )
    )
    findings.append(
        readiness(
            has_modules_cmake and clangxx_ready and ninja_ready,
            "Preset modules-debug",
            "Ready.",
            "Requires CMake 3.28+, clang++, and Ninja.",
        )
    )
    findings.append(
        readiness(
            has_modules_cmake
            and clangxx_ready
            and ninja_ready
            and has_vcpkg,
            "Preset modules-dev-debug",
            "Ready.",
            "Requires CMake 3.28+, clang++, Ninja, and a valid VCPKG_ROOT.",
        )
    )

    if os.name == "nt":
        findings.append(
            Finding(
                "WARN",
                "MSVC presets",
                "Verify Visual Studio 2022 with the C++ workload is installed before using msvc-* presets.",
            )
        )

    for finding in findings:
        emit(finding)

    passed = sum(1 for finding in findings if finding.level == "PASS")
    warned = sum(1 for finding in findings if finding.level == "WARN")
    failed = sum(1 for finding in findings if finding.level == "FAIL")
    print(f"\\nSummary: {{passed}} passed, {{warned}} warnings, {{failed}} failed")
    print("")
    for line in recommendation_lines(
        gxx_ready=gxx_ready,
        clangxx_ready=clangxx_ready,
        ninja_ready=ninja_ready,
        vcpkg_ready=has_vcpkg,
        modules_cmake_ready=has_modules_cmake,
    ):
        print(line)

    if failed > 0:
        return 1
    if args.strict and warned > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename the Capricorn template into a new project skeleton."
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help=(
            "Interactively initialize the template. Defaults are derived from the "
            "current repository directory name."
        ),
    )
    parser.add_argument(
        "--project-name",
        help="New CMake project name. Required unless --init is used.",
    )
    parser.add_argument(
        "--include-dir-name",
        help="Public include folder name under include/. Defaults to project name.",
    )
    parser.add_argument(
        "--library-basename",
        help=(
            "Example header/source stem. Defaults to a C identifier derived from "
            "the project name."
        ),
    )
    parser.add_argument(
        "--namespace",
        help="Example C++ namespace. Defaults to the library basename.",
    )
    parser.add_argument(
        "--package-name",
        help=(
            "vcpkg package name. Defaults to a lowercase hyphenated form of the "
            "project name."
        ),
    )
    parser.add_argument(
        "--old-project-name",
        default="Capricorn",
        help="Current template project name. Defaults to Capricorn.",
    )
    parser.add_argument(
        "--old-include-dir-name",
        default="Capricorn",
        help="Current include directory name. Defaults to Capricorn.",
    )
    parser.add_argument(
        "--old-library-basename",
        default="capricorn",
        help="Current example library basename. Defaults to capricorn.",
    )
    parser.add_argument(
        "--old-namespace",
        default="capricorn",
        help="Current example namespace. Defaults to capricorn.",
    )
    parser.add_argument(
        "--old-package-name",
        default="capricorn",
        help="Current vcpkg package name. Defaults to capricorn.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without editing files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report any remaining template identifiers after planned replacements.",
    )
    args = parser.parse_args()
    if not args.init and not args.project_name:
        parser.error("--project-name is required unless --init is used.")
    return args


def make_identifier(name: str) -> str:
    lowered = name.strip().lower().replace("-", "_").replace(" ", "_")
    identifier = re.sub(r"[^a-z0-9_]", "_", lowered)
    identifier = re.sub(r"_+", "_", identifier).strip("_")
    if not identifier:
        raise ValueError("Could not derive a valid identifier from the provided name.")
    if identifier[0].isdigit():
        identifier = f"project_{identifier}"
    return identifier


def make_package_name(name: str) -> str:
    lowered = name.strip().lower().replace("_", "-").replace(" ", "-")
    package_name = re.sub(r"[^a-z0-9-]", "-", lowered)
    package_name = re.sub(r"-+", "-", package_name).strip("-")
    if not package_name:
        raise ValueError(
            "Could not derive a valid package name from the provided project name."
        )
    return package_name


def make_cmake_identifier(name: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())
    identifier = re.sub(r"_+", "_", identifier).strip("_")
    if not identifier:
        raise ValueError("Could not derive a valid CMake identifier.")
    if identifier[0].isdigit():
        identifier = f"Project_{identifier}"
    return identifier


def require_non_empty(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty.")
    return stripped


def prompt_value(
    label: str,
    default: str,
    *,
    normalizer: Callable[[str], str] | None = None,
) -> str:
    while True:
        try:
            raw_value = input(f"{label} [{default}]: ")
        except EOFError as exc:
            raise RuntimeError(
                "Interactive initialization requires stdin input."
            ) from exc

        candidate = raw_value.strip() or default
        try:
            if normalizer is None:
                return require_non_empty(candidate, label)
            return normalizer(candidate)
        except ValueError as exc:
            print(f"error: {exc}")


def collect_init_answers(args: argparse.Namespace) -> argparse.Namespace:
    default_project_name = args.project_name or ROOT.name

    print(
        "Interactive template initialization.\n"
        "Press Enter to accept a suggested value. "
        "A residual identifier check will run automatically."
    )

    project_name = prompt_value(
        "CMake project name",
        require_non_empty(default_project_name, "CMake project name"),
        normalizer=lambda value: require_non_empty(value, "CMake project name"),
    )
    include_dir_name = prompt_value(
        "Public include directory",
        args.include_dir_name or project_name,
        normalizer=lambda value: require_non_empty(value, "Public include directory"),
    )
    library_basename = prompt_value(
        "Example library basename",
        args.library_basename or make_identifier(project_name),
        normalizer=make_identifier,
    )
    namespace = prompt_value(
        "Example C++ namespace",
        args.namespace or library_basename,
        normalizer=lambda value: require_non_empty(value, "Example C++ namespace"),
    )
    package_name = prompt_value(
        "vcpkg package name",
        args.package_name or make_package_name(project_name),
        normalizer=make_package_name,
    )

    args.project_name = project_name
    args.include_dir_name = include_dir_name
    args.library_basename = library_basename
    args.namespace = namespace
    args.package_name = package_name
    args.check = True
    return args


def reinitialize_git_repository(dry_run: bool) -> None:
    git_path = ROOT / ".git"

    if dry_run:
        print("git: dry-run would remove existing .git metadata and run `git init`")
        return

    if shutil.which("git") is None:
        raise RuntimeError(
            "Cannot initialize a fresh Git repository because `git` was not "
            "found on PATH."
        )

    if git_path.is_symlink() or git_path.is_file():
        git_path.unlink()
        print("git: removed existing .git metadata")
    elif git_path.is_dir():
        shutil.rmtree(git_path, onerror=retry_remove_writable)
        print("git: removed existing .git metadata")
    else:
        print("git: no existing .git metadata found")

    result = subprocess.run(
        ["git", "init"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to initialize a fresh Git repository with `git init`.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    print("git: initialized fresh repository")


def retry_remove_writable(
    function: Callable[[str], object],
    path: str,
    exc_info: tuple[type[BaseException], BaseException, object],
) -> None:
    exc = exc_info[1]
    if not isinstance(exc, PermissionError):
        raise exc

    os.chmod(path, stat.S_IWRITE)
    function(path)


def load_plan(args: argparse.Namespace) -> RenamePlan:
    include_dir_name = args.include_dir_name or args.project_name
    library_basename = args.library_basename or make_identifier(args.project_name)
    namespace = args.namespace or library_basename
    package_name = args.package_name or make_package_name(args.project_name)
    return RenamePlan(
        project_name=args.project_name,
        include_dir_name=include_dir_name,
        library_basename=library_basename,
        namespace=namespace,
        package_name=package_name,
        old_include_dir_name=args.old_include_dir_name,
        old_library_basename=args.old_library_basename,
        old_namespace=args.old_namespace,
        old_project_name=args.old_project_name,
        old_package_name=args.old_package_name,
    )


def replace_template_knobs(content: str, plan: RenamePlan) -> str:
    replacements = {
        r'set\(TEMPLATE_INCLUDE_DIR_NAME ".*?"\)': (
            f'set(TEMPLATE_INCLUDE_DIR_NAME "{plan.include_dir_name}")'
        ),
        r'set\(TEMPLATE_LIBRARY_BASENAME ".*?"\)': (
            f'set(TEMPLATE_LIBRARY_BASENAME "{plan.library_basename}")'
        ),
        r'set\(TEMPLATE_LIBRARY_NAMESPACE ".*?"\)': (
            f'set(TEMPLATE_LIBRARY_NAMESPACE "{plan.namespace}")'
        ),
    }
    for pattern, replacement in replacements.items():
        content, count = re.subn(pattern, replacement, content)
        if count != 1:
            raise RuntimeError(f"Expected exactly one match for pattern: {pattern}")
    return content


def replace_project_call(content: str, old_name: str, new_name: str) -> str:
    pattern = rf"project\(\s*{re.escape(old_name)}"
    replaced, count = re.subn(pattern, f"project(\n    {new_name}", content, count=1)
    if count != 1:
        raise RuntimeError("Failed to update project() call.")
    return replaced


def replace_exact(content: str, old: str, new: str) -> str:
    return content.replace(old, new)


def apply_generic_replacements(content: str, plan: RenamePlan) -> str:
    generic_replacements = [
        (plan.old_project_name, plan.project_name),
        (plan.old_include_dir_name, plan.include_dir_name),
        (plan.old_library_basename, plan.library_basename),
        (plan.old_namespace, plan.namespace),
        (plan.old_package_name, plan.package_name),
        (plan.old_project_identifier, plan.project_identifier),
        (plan.old_apply_options_name, plan.apply_options_name),
    ]

    updated = content
    for old, new in generic_replacements:
        updated = replace_exact(updated, old, new)
    return updated


def replace_project_option_names(content: str, plan: RenamePlan) -> str:
    option_suffixes = [
        "_DEVELOPER_MODE",
        "_BUILD_BENCHMARKS",
        "_BUILD_FUZZ_TESTS",
        "_ENABLE_SANITIZERS",
        "_ENABLE_CLANG_TIDY",
        "_ENABLE_CXX_MODULES",
        "_CLANG_TIDY_PROFILE",
        "_CLANG_TIDY_WARNINGS_AS_ERRORS",
    ]
    updated = content
    for suffix in option_suffixes:
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}{suffix}",
            f"{plan.project_identifier}{suffix}",
        )
    return updated


def transform_content(path: Path, original: str, plan: RenamePlan) -> str:
    rel_path = path.relative_to(ROOT).as_posix()
    updated = original

    if rel_path == "CMakeLists.txt":
        updated = replace_project_call(updated, plan.old_project_name, plan.project_name)
        updated = replace_template_knobs(updated, plan)
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_BUILD_CLI",
            f"{plan.project_identifier}_BUILD_CLI",
        )
        updated = replace_exact(
            updated, plan.old_apply_options_name, plan.apply_options_name
        )
        return updated

    if rel_path == "CMakePresets.json":
        updated = replace_project_option_names(updated, plan)
        return updated

    if rel_path == "BUILDING.md":
        updated = replace_project_option_names(updated, plan)
        updated = replace_exact(updated, f"{plan.old_project_name}::{plan.old_project_name}", f"{plan.project_name}::{plan.project_name}")
        updated = replace_exact(
            updated,
            f"find_package({plan.old_project_name} CONFIG REQUIRED)",
            f"find_package({plan.project_name} CONFIG REQUIRED)",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "README.md":
        updated = replace_exact(updated, f"# {plan.old_project_name}", f"# {plan.project_name}")
        updated = replace_exact(updated, f"{plan.old_project_name}::{plan.old_project_name}", f"{plan.project_name}::{plan.project_name}")
        updated = replace_exact(
            updated,
            f"find_package({plan.old_project_name} CONFIG REQUIRED)",
            f"find_package({plan.project_name} CONFIG REQUIRED)",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "HACKING.md":
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_DEVELOPER_MODE",
            f"{plan.project_identifier}_DEVELOPER_MODE",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_BUILD_BENCHMARKS",
            f"{plan.project_identifier}_BUILD_BENCHMARKS",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_BUILD_FUZZ_TESTS",
            f"{plan.project_identifier}_BUILD_FUZZ_TESTS",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_name}_cli",
            f"{plan.project_name}_cli",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_name}_benchmark",
            f"{plan.project_name}_benchmark",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_name}_fuzz",
            f"{plan.project_name}_fuzz",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "CONTRIBUTING.md":
        return replace_exact(
            updated,
            f"Thank you for improving {plan.old_project_name}.",
            f"Thank you for improving {plan.project_name}.",
        )

    if rel_path == "vcpkg.json":
        return replace_exact(
            updated,
            f'"name": "{plan.old_package_name}"',
            f'"name": "{plan.package_name}"',
        )

    if rel_path in {
        "cmake/project-options.cmake",
        "cmake/variables.cmake",
    }:
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_DEVELOPER_MODE",
            f"{plan.project_identifier}_DEVELOPER_MODE",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_INCLUDES_WITH_SYSTEM",
            f"{plan.project_identifier}_INCLUDES_WITH_SYSTEM",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_WARNINGS_AS_ERRORS",
            f"{plan.project_identifier}_WARNINGS_AS_ERRORS",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_ENABLE_HARDENING",
            f"{plan.project_identifier}_ENABLE_HARDENING",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_ENABLE_IPO",
            f"{plan.project_identifier}_ENABLE_IPO",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_project_identifier}_ENABLE_SANITIZERS",
            f"{plan.project_identifier}_ENABLE_SANITIZERS",
        )
        updated = replace_exact(
            updated, plan.old_apply_options_name, plan.apply_options_name
        )
        if rel_path == "cmake/variables.cmake":
            updated = replace_exact(
                updated,
                f"developer(s) of {plan.old_project_name}",
                "people working on this repository directly",
            )
            updated = replace_exact(
                updated,
                f"Use SYSTEM modifier for {plan.old_project_name}'s includes, disabling warnings",
                "Use SYSTEM modifier for this project's includes, disabling warnings",
            )
        return updated

    if rel_path == "test/CMakeLists.txt":
        return replace_exact(
            updated, plan.old_apply_options_name, plan.apply_options_name
        )

    if rel_path == "benchmark/CMakeLists.txt":
        updated = replace_exact(
            updated,
            f'"{plan.old_project_name}_benchmark"',
            f'"{plan.project_name}_benchmark"',
        )
        updated = replace_exact(
            updated, plan.old_apply_options_name, plan.apply_options_name
        )
        return updated

    if rel_path == "fuzz/CMakeLists.txt":
        updated = replace_exact(
            updated,
            f'"{plan.old_project_name}_fuzz"',
            f'"{plan.project_name}_fuzz"',
        )
        updated = replace_exact(
            updated, plan.old_apply_options_name, plan.apply_options_name
        )
        return updated

    if rel_path == "include/{}/{}.hpp".format(
        plan.old_include_dir_name, plan.old_library_basename
    ):
        updated = replace_exact(
            updated,
            f"#include <{plan.old_include_dir_name}/project_config.hpp>",
            f"#include <{plan.include_dir_name}/project_config.hpp>",
        )
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}",
            f"namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}",
            f"}}  // namespace {plan.namespace}",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"src/{plan.old_library_basename}.cpp":
        updated = replace_exact(
            updated,
            f'#include <{plan.old_include_dir_name}/{plan.old_library_basename}.hpp>',
            f'#include <{plan.include_dir_name}/{plan.library_basename}.hpp>',
        )
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}",
            f"namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}",
            f"}}  // namespace {plan.namespace}",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"include/{plan.old_include_dir_name}/core/greeting.hpp":
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}",
            f"namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}",
            f"}}  // namespace {plan.namespace}",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"include/{plan.old_include_dir_name}/core/project_info.hpp":
        updated = replace_exact(
            updated,
            f"#include <{plan.old_include_dir_name}/project_config.hpp>",
            f"#include <{plan.include_dir_name}/project_config.hpp>",
        )
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}",
            f"namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}",
            f"}}  // namespace {plan.namespace}",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "src/detail/greeting_builder.hpp":
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}::detail",
            f"namespace {plan.namespace}::detail",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}::detail",
            f"}}  // namespace {plan.namespace}::detail",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "src/detail/greeting_builder.cpp":
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}::detail",
            f"namespace {plan.namespace}::detail",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}::detail",
            f"}}  // namespace {plan.namespace}::detail",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"source/modules/{plan.old_library_basename}.ixx":
        updated = replace_exact(
            updated,
            f"export module {plan.old_library_basename};",
            f"export module {plan.library_basename};",
        )
        updated = replace_exact(
            updated,
            f"namespace {plan.old_namespace}",
            f"namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"}}  // namespace {plan.old_namespace}",
            f"}}  // namespace {plan.namespace}",
        )
        updated = replace_exact(
            updated,
            f"auto {plan.old_namespace}::",
            f"auto {plan.namespace}::",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "src/main.cpp":
        updated = replace_exact(
            updated,
            f'#include <{plan.old_include_dir_name}/{plan.old_library_basename}.hpp>',
            f'#include <{plan.include_dir_name}/{plan.library_basename}.hpp>',
        )
        updated = replace_exact(
            updated,
            f"{plan.old_namespace}::greeting()",
            f"{plan.namespace}::greeting()",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == "src/main_modules.cpp":
        updated = replace_exact(
            updated,
            f"import {plan.old_library_basename};",
            f"import {plan.library_basename};",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_namespace}::",
            f"{plan.namespace}::",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"benchmark/src/{plan.old_library_basename}_benchmark.cpp":
        updated = replace_exact(
            updated,
            f'#include <{plan.old_include_dir_name}/{plan.old_library_basename}.hpp>',
            f'#include <{plan.include_dir_name}/{plan.library_basename}.hpp>',
        )
        updated = replace_exact(
            updated,
            f"{plan.old_namespace}::",
            f"{plan.namespace}::",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"fuzz/src/{plan.old_library_basename}_fuzz.cpp":
        updated = replace_exact(
            updated,
            f'#include <{plan.old_include_dir_name}/{plan.old_library_basename}.hpp>',
            f'#include <{plan.include_dir_name}/{plan.library_basename}.hpp>',
        )
        updated = replace_exact(
            updated,
            f"{plan.old_namespace}::",
            f"{plan.namespace}::",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == f"test/src/{plan.old_library_basename}_test.cpp":
        updated = replace_exact(
            updated,
            f'#include <{plan.old_include_dir_name}/{plan.old_library_basename}.hpp>',
            f'#include <{plan.include_dir_name}/{plan.library_basename}.hpp>',
        )
        updated = replace_exact(
            updated,
            f"[{plan.old_library_basename}]",
            f"[{plan.library_basename}]",
        )
        updated = replace_exact(
            updated,
            f"{plan.old_namespace}::",
            f"{plan.namespace}::",
        )
        return apply_generic_replacements(updated, plan)

    if rel_path == ".github/workflows/ci.yml":
        updated = replace_exact(
            updated,
            f"--preset={plan.old_project_identifier.lower()}",
            f"--preset={plan.project_identifier.lower()}",
        )
        updated = replace_exact(
            updated,
            f"build/{plan.old_package_name}",
            f"build/{plan.package_name}",
        )
        return updated

    return apply_generic_replacements(updated, plan)


def update_text_file(path: Path, plan: RenamePlan, dry_run: bool) -> str:
    original = path.read_text(encoding="utf-8")
    updated = transform_content(path, original, plan)

    if updated != original:
        rel = path.relative_to(ROOT)
        print(f"update: {rel}")
        if not dry_run:
            path.write_text(updated, encoding="utf-8")

    return updated


def rename_path(path: Path, new_path: Path, dry_run: bool) -> None:
    rel_old = path.relative_to(ROOT)
    rel_new = new_path.relative_to(ROOT)
    print(f"rename: {rel_old} -> {rel_new}")
    if dry_run:
        return
    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(new_path))


def validate_paths(plan: RenamePlan) -> None:
    required = [
        ROOT / f"include/{plan.old_include_dir_name}/{plan.old_library_basename}.hpp",
        ROOT / f"include/{plan.old_include_dir_name}/core/greeting.hpp",
        ROOT / f"include/{plan.old_include_dir_name}/core/project_info.hpp",
        ROOT / f"src/{plan.old_library_basename}.cpp",
        ROOT / f"source/modules/{plan.old_library_basename}.ixx",
        ROOT / "src/main_modules.cpp",
        ROOT / "src/detail/greeting_builder.hpp",
        ROOT / "src/detail/greeting_builder.cpp",
        ROOT / f"benchmark/src/{plan.old_library_basename}_benchmark.cpp",
        ROOT / f"fuzz/src/{plan.old_library_basename}_fuzz.cpp",
        ROOT / f"test/src/{plan.old_library_basename}_test.cpp",
        ROOT / "test/package/module_main.cpp.in",
        ROOT / "source/modules/README.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "The template no longer matches the expected source layout: "
            + ", ".join(missing)
        )


def rename_example_files(plan: RenamePlan, dry_run: bool) -> None:
    include_root = ROOT / "include"
    old_include_dir = include_root / plan.old_include_dir_name
    new_include_dir = include_root / plan.include_dir_name

    moved_include_dir = (
        new_include_dir if old_include_dir != new_include_dir else old_include_dir
    )
    header_old = moved_include_dir / f"{plan.old_library_basename}.hpp"
    header_new = moved_include_dir / f"{plan.library_basename}.hpp"
    source_old = ROOT / "src" / f"{plan.old_library_basename}.cpp"
    source_new = ROOT / "src" / f"{plan.library_basename}.cpp"
    module_old = ROOT / "source/modules" / f"{plan.old_library_basename}.ixx"
    module_new = ROOT / "source/modules" / f"{plan.library_basename}.ixx"
    benchmark_old = (
        ROOT / "benchmark/src" / f"{plan.old_library_basename}_benchmark.cpp"
    )
    benchmark_new = ROOT / "benchmark/src" / f"{plan.library_basename}_benchmark.cpp"
    fuzz_old = ROOT / "fuzz/src" / f"{plan.old_library_basename}_fuzz.cpp"
    fuzz_new = ROOT / "fuzz/src" / f"{plan.library_basename}_fuzz.cpp"
    test_old = ROOT / "test/src" / f"{plan.old_library_basename}_test.cpp"
    test_new = ROOT / "test/src" / f"{plan.library_basename}_test.cpp"

    if old_include_dir != new_include_dir and old_include_dir.exists():
        if dry_run:
            print(
                f"rename: {old_include_dir.relative_to(ROOT)} -> "
                f"{new_include_dir.relative_to(ROOT)}"
            )
        else:
            new_include_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_include_dir), str(new_include_dir))

    if header_old != header_new:
        rename_path(header_old, header_new, dry_run)
    if source_old != source_new:
        rename_path(source_old, source_new, dry_run)
    if module_old != module_new:
        rename_path(module_old, module_new, dry_run)
    if benchmark_old != benchmark_new:
        rename_path(benchmark_old, benchmark_new, dry_run)
    if fuzz_old != fuzz_new:
        rename_path(fuzz_old, fuzz_new, dry_run)
    if test_old != test_new:
        rename_path(test_old, test_new, dry_run)


def remove_empty_dir(path: Path) -> None:
    if path.exists() and path.is_dir() and not any(path.iterdir()):
        path.rmdir()


def format_rel_path(template: str, plan: RenamePlan) -> str:
    return template.format(
        old_include_dir_name=plan.old_include_dir_name,
        old_library_basename=plan.old_library_basename,
    )


def render_updated_files(plan: RenamePlan, dry_run: bool) -> dict[str, str]:
    rendered: dict[str, str] = {}

    for rel_path in TRACKED_TEXT_FILES:
        path = ROOT / rel_path
        if path.exists():
            rendered[rel_path] = update_text_file(path, plan, dry_run)

    for rel_path_template in RENAMABLE_TEXT_FILES:
        rel_path = format_rel_path(rel_path_template, plan)
        path = ROOT / rel_path
        if path.exists():
            rendered[rel_path] = update_text_file(path, plan, dry_run)

    return rendered


def gather_residual_matches(
    plan: RenamePlan, rendered_files: dict[str, str]
) -> dict[str, list[str]]:
    watched_terms = [
        plan.old_project_name,
        plan.old_include_dir_name,
        plan.old_library_basename,
        plan.old_namespace,
        plan.old_package_name,
        plan.old_project_identifier,
        plan.old_apply_options_name,
    ]
    unique_terms: list[str] = []
    for term in watched_terms:
        if term not in unique_terms:
            unique_terms.append(term)

    matches: dict[str, list[str]] = {}
    for rel_path, content in rendered_files.items():
        lines = content.splitlines()
        file_matches: list[str] = []
        for line_number, line in enumerate(lines, start=1):
            if any(term in line for term in unique_terms):
                file_matches.append(f"{line_number}: {line}")
        if file_matches:
            matches[rel_path] = file_matches
    return matches


def print_residual_matches(matches: dict[str, list[str]]) -> None:
    if not matches:
        print("check: no remaining template identifiers found in tracked files")
        return

    print("check: remaining template identifiers found")
    for rel_path, file_matches in matches.items():
        print(f"  {rel_path}")
        for line in file_matches:
            print(f"    {line}")


def normalize_newlines(content: str, newline: str = "\n") -> bytes:
    return content.replace("\r\n", "\n").replace("\r", "\n").replace(
        "\n", newline
    ).encode("utf-8")


def write_post_init_file(
    rel_path: str, content: str, dry_run: bool, *, newline: str = "\n"
) -> None:
    path = ROOT / rel_path
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    if original == content:
        return

    print(f"cleanup: update {rel_path}")
    if dry_run:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(normalize_newlines(content, newline))


def clean_post_init_readme(content: str) -> str:
    updated = content
    updated = replace_exact(
        updated,
        (
            "A modern C++ starter template built around CMake, installable "
            "library targets,\nopt-in developer tooling, and cross-platform CI."
        ),
        (
            "A modern C++ project built around CMake, installable library "
            "targets, opt-in\ndeveloper tooling, and cross-platform CI."
        ),
    )
    updated = replace_exact(
        updated,
        (
            "If you rename this template into a real project, read "
            "[TEMPLATE](TEMPLATE.md)\nfirst. For more detail, see "
            "[BUILDING](BUILDING.md) and [HACKING](HACKING.md)."
        ),
        "For more detail, see [BUILDING](BUILDING.md) and [HACKING](HACKING.md).",
    )
    updated = replace_exact(
        updated,
        "is available. It pins the template to C++23 and adds the repository's `include`",
        "is available. It pins the project to C++23 and adds the repository's `include`",
    )
    updated = replace_exact(
        updated,
        """The rename helper can initialize the sample names, package name, and tracked
template identifiers in one pass. Prefer the root wrapper that matches your
platform:

```sh
./run.sh --project-name MyProject --check
```

```cmd
run.bat --project-name MyProject --check
```

```powershell
.\\run.bat --project-name MyProject --check
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
.\\run.bat --init
```

The interactive initializer derives defaults from the clone directory, runs the
tracked residual check, removes cloned `.git` metadata, runs `git init`, and
removes template-maintainer files from the new project so it starts without
template history or one-time initialization tools.

""",
        "",
    )
    updated = replace_exact(
        updated,
        "The fix helper reuses the template's checked-in `clang-format` and `codespell`",
        "The fix helper reuses the project's checked-in `clang-format` and `codespell`",
    )
    updated = replace_exact(
        updated,
        """## Licensing

<!--
Please go to https://choosealicense.com/licenses/ and choose a license that
fits your needs. The recommended license for a project of this type is the
GNU AGPLv3.
-->
""",
        """## Licensing

This project is licensed under the terms in [LICENSE](LICENSE).
""",
    )
    return updated


def clean_post_init_building(content: str) -> str:
    replacements = [
        ("This template separates dependency management", "This project separates dependency management"),
        ("The checked-in template follows", "The checked-in project follows"),
        ("the template's default local cleanups", "the project's default local cleanups"),
        ("away from the rest of the template.", "away from the rest of the project."),
        ("the template provides helper targets", "the project provides helper targets"),
        ("This template separates the sample code", "This project separates the sample code"),
        ("The template ships two `clang-tidy` profiles", "The project ships two `clang-tidy` profiles"),
        ("The template wires a small Google Benchmark", "The project wires a small Google Benchmark"),
        ("The template assumes a Clang toolchain", "The project assumes a Clang toolchain"),
        ("this template builds an additional", "this project builds an additional"),
        ("Current template assumptions:", "Current assumptions:"),
        (
            "- If you fork this template into a new project, follow [TEMPLATE](TEMPLATE.md)\n"
            "  before doing the first real build.\n",
            "",
        ),
    ]

    updated = content
    for old, new in replacements:
        updated = replace_exact(updated, old, new)
    return updated


def clean_post_init_hacking(content: str) -> str:
    replacements = [
        ("the template's default local\nformatting", "the project's default local\nformatting"),
        ("When extending this template", "When extending this project"),
        (
            "This keeps downstream consumers from inheriting the template author's local\n"
            "package-manager choice just to use the library.",
            "This keeps downstream consumers from inheriting a local package-manager choice\n"
            "just to use the library.",
        ),
        ("the template exports a separate", "the project exports a separate"),
        ("this template intentionally keeps", "this project intentionally keeps"),
    ]

    updated = content
    for old, new in replacements:
        updated = replace_exact(updated, old, new)
    return updated


def clean_post_init_contributing(content: str) -> str:
    return replace_exact(
        content,
        "Please preserve the template's dependency layering:",
        "Please preserve the project's dependency layering:",
    )


def clean_post_init_source_modules_readme(content: str) -> str:
    return replace_exact(
        content,
        "This template keeps `source/modules/` as an opt-in companion surface, not the",
        "This project keeps `source/modules/` as an opt-in companion surface, not the",
    )


def clean_post_init_fix_helper(content: str) -> str:
    return replace_exact(
        content,
        "Apply the template's common local formatting and spelling fixes.",
        "Apply the project's common local formatting and spelling fixes.",
    )


def clean_post_init_dependencies(content: str) -> str:
    return replace_exact(
        content,
        '"Template package-management strategy guidance"',
        '"Project package-management strategy guidance"',
    )


def clean_post_init_project_options(content: str) -> str:
    replacements = [
        (
            "This template's optional C++23 module target is currently wired for ",
            "This project's optional C++23 module target is currently wired for ",
        ),
        (
            "# std::type_info::operator== while this C++23 template emits the inline",
            "# std::type_info::operator== while this C++23 project emits the inline",
        ),
    ]

    updated = content
    for old, new in replacements:
        updated = replace_exact(updated, old, new)
    return updated


def clean_post_init_project_prefixes(content: str, plan: RenamePlan) -> str:
    lower_prefix = plan.library_basename
    upper_prefix = make_cmake_identifier(plan.library_basename).upper()
    updated = content.replace("template_", f"{lower_prefix}_")
    return updated.replace("TEMPLATE_", f"{upper_prefix}_")


def clean_post_init_ci(content: str) -> str:
    return replace_exact(
        content,
        """    - name: Template initialization smoke test
      run: python tools/test_template_init.py

""",
        "",
    )


def clean_post_init_cmake_lists(content: str) -> str:
    updated = replace_exact(
        content,
        'DESCRIPTION "A modern C++ project template"',
        'DESCRIPTION "A modern C++ project"',
    )
    updated = replace_exact(
        updated,
        '    HOMEPAGE_URL "https://www.gemc.club"\n',
        "",
    )
    updated = replace_exact(
        updated,
        (
            "# Template naming knobs. When you fork this template, update these first if you\n"
            "# want a different header folder, file stem, or sample namespace."
        ),
        "# Project naming knobs for the public include folder, file stem, and namespace.",
    )
    return updated


def cleanup_post_init_text(plan: RenamePlan, dry_run: bool) -> None:
    transforms: list[tuple[str, Callable[[str], str]]] = [
        (".github/workflows/ci.yml", clean_post_init_ci),
        ("README.md", clean_post_init_readme),
        ("BUILDING.md", clean_post_init_building),
        ("HACKING.md", clean_post_init_hacking),
        ("CONTRIBUTING.md", clean_post_init_contributing),
        ("CMakeLists.txt", clean_post_init_cmake_lists),
        ("source/modules/README.md", clean_post_init_source_modules_readme),
        ("tools/fix.py", clean_post_init_fix_helper),
        ("cmake/dependencies.cmake", clean_post_init_dependencies),
        ("cmake/project-options.cmake", clean_post_init_project_options),
    ]

    for rel_path, transform in transforms:
        path = ROOT / rel_path
        if not path.exists():
            continue
        updated = transform(path.read_text(encoding="utf-8"))
        write_post_init_file(rel_path, updated, dry_run)

    for rel_path in POST_INIT_PROJECT_PREFIX_FILES:
        path = ROOT / rel_path
        if not path.exists():
            continue
        updated = clean_post_init_project_prefixes(
            path.read_text(encoding="utf-8"),
            plan,
        )
        write_post_init_file(rel_path, updated, dry_run)

    write_post_init_file("run.bat", POST_INIT_RUN_BAT, dry_run, newline="\r\n")
    write_post_init_file("run.sh", POST_INIT_RUN_SH, dry_run)
    write_post_init_file("tools/README.md", POST_INIT_TOOLS_README, dry_run)
    write_post_init_file("tools/doctor.py", post_init_doctor_content(plan), dry_run)


def ensure_inside_root(path: Path) -> None:
    root = ROOT.resolve()
    resolved = path.resolve(strict=False)
    if resolved == root or root in resolved.parents:
        return
    raise RuntimeError(f"Refusing to remove path outside repository root: {path}")


def remove_post_init_path(rel_path: str, dry_run: bool) -> None:
    path = ROOT / rel_path
    if not path.exists() and not path.is_symlink():
        return

    ensure_inside_root(path)
    print(f"cleanup: remove {rel_path}")
    if dry_run:
        return

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, onerror=retry_remove_writable)


def cleanup_post_init_repository(plan: RenamePlan, dry_run: bool) -> None:
    cleanup_post_init_text(plan, dry_run)
    for rel_path in POST_INIT_REMOVE_PATHS:
        remove_post_init_path(rel_path, dry_run)


def print_post_rename_notes(args: argparse.Namespace, plan: RenamePlan) -> None:
    if args.dry_run:
        return

    print(
        "note: `src/main_modules.cpp` is an optional named-modules sample."
    )
    print(
        "note: if clangd reports "
        f"`Module '{plan.library_basename}' not found`, configure a modules-aware "
        "build first with `cmake --workflow --preset modules-debug`."
    )
    print(
        "note: that preset needs clang++ and Ninja; otherwise start from "
        "`src/main.cpp` and the regular header-based target."
    )


def main() -> int:
    args = parse_args()
    if args.init:
        args = collect_init_answers(args)
    plan = load_plan(args)
    validate_paths(plan)

    print(
        "plan:",
        f"project={plan.project_name}",
        f"include_dir={plan.include_dir_name}",
        f"basename={plan.library_basename}",
        f"namespace={plan.namespace}",
        f"package={plan.package_name}",
    )

    rendered_files = render_updated_files(plan, args.dry_run)
    rename_example_files(plan, args.dry_run)

    if not args.dry_run:
        remove_empty_dir(ROOT / "include" / plan.old_include_dir_name)

    if args.check or args.dry_run:
        print_residual_matches(gather_residual_matches(plan, rendered_files))

    if args.init:
        reinitialize_git_repository(args.dry_run)
        cleanup_post_init_repository(plan, args.dry_run)

    print_post_rename_notes(args, plan)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
