from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def template_command(arguments: list[str]) -> list[str]:
    if os.name == "nt":
        return ["cmd", "/c", "run.bat", *arguments]
    wrapper = ROOT / "run.sh"
    if os.access(wrapper, os.X_OK):
        return ["./run.sh", *arguments]
    return ["sh", "run.sh", *arguments]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def run_with_input(
    command: list[str], cwd: Path, stdin_text: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        input=stdin_text,
        capture_output=True,
        check=False,
    )


def assert_success(result: subprocess.CompletedProcess[str], context: str) -> None:
    if result.returncode == 0:
        return
    raise RuntimeError(
        f"{context} failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def assert_contains(path: Path, expected: str) -> None:
    content = path.read_text(encoding="utf-8")
    if expected not in content:
        raise AssertionError(f"Expected to find {expected!r} in {path}")


def assert_not_contains(path: Path, unexpected: str) -> None:
    content = path.read_text(encoding="utf-8")
    if unexpected in content:
        raise AssertionError(f"Did not expect to find {unexpected!r} in {path}")


def assert_tree_not_contains(root: Path, unexpected: str) -> None:
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if unexpected in content:
            raise AssertionError(f"Did not expect to find {unexpected!r} in {path}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="capricorn-template-init-") as tmp_dir:
        temp_root = Path(tmp_dir)
        repo_copy = temp_root / ROOT.name
        shutil.copytree(ROOT, repo_copy)

        result = run(
            template_command(
                [
                    "--project-name",
                    "StarTrail",
                    "--include-dir-name",
                    "StarTrail",
                    "--library-basename",
                    "star_trail",
                    "--namespace",
                    "startrail",
                    "--package-name",
                    "star-trail",
                    "--check",
                ]
            ),
            cwd=repo_copy,
        )
        assert_success(result, "template rename wrapper smoke test")

        preset_result = run(["cmake", "--list-presets"], cwd=repo_copy)
        assert_success(preset_result, "preset schema validation after template rename")

        stdout = result.stdout
        if "check: no remaining template identifiers found in tracked files" not in stdout:
            raise AssertionError(
                "Expected the initializer to report a clean residual check.\n"
                f"stdout:\n{stdout}"
            )
        if "optional named-modules sample" not in stdout:
            raise AssertionError(
                "Expected the initializer to explain the module sample note.\n"
                f"stdout:\n{stdout}"
            )
        if "Module 'star_trail' not found" not in stdout:
            raise AssertionError(
                "Expected the initializer to mention the common clangd module "
                "diagnostic after renaming.\n"
                f"stdout:\n{stdout}"
            )
        if "cmake --workflow --preset modules-debug" not in stdout:
            raise AssertionError(
                "Expected the initializer to point users at the modules-debug preset.\n"
                f"stdout:\n{stdout}"
            )

        header_path = repo_copy / "include" / "StarTrail" / "star_trail.hpp"
        greeting_header_path = repo_copy / "include" / "StarTrail" / "core" / "greeting.hpp"
        project_info_header_path = (
            repo_copy / "include" / "StarTrail" / "core" / "project_info.hpp"
        )
        source_path = repo_copy / "src" / "star_trail.cpp"
        module_interface_path = repo_copy / "source" / "modules" / "star_trail.ixx"
        modules_main_path = repo_copy / "src" / "main_modules.cpp"
        detail_header_path = repo_copy / "src" / "detail" / "greeting_builder.hpp"
        detail_source_path = repo_copy / "src" / "detail" / "greeting_builder.cpp"
        benchmark_path = repo_copy / "benchmark" / "src" / "star_trail_benchmark.cpp"
        fuzz_path = repo_copy / "fuzz" / "src" / "star_trail_fuzz.cpp"
        test_path = repo_copy / "test" / "src" / "star_trail_test.cpp"
        modules_readme_path = repo_copy / "source" / "modules" / "README.md"
        editorconfig_path = repo_copy / ".editorconfig"
        gitattributes_path = repo_copy / ".gitattributes"
        clangd_path = repo_copy / ".clangd"
        vscode_extensions_path = repo_copy / ".vscode" / "extensions.json"
        doctor_path = repo_copy / "tools" / "doctor.py"
        fix_path = repo_copy / "tools" / "fix.py"
        hook_installer_path = repo_copy / "tools" / "install_git_hooks.py"
        pre_commit_path = repo_copy / "tools" / "pre_commit.py"
        tracked_pre_commit_hook = repo_copy / ".githooks" / "pre-commit"

        for path in [
            header_path,
            greeting_header_path,
            project_info_header_path,
            source_path,
            module_interface_path,
            modules_main_path,
            detail_header_path,
            detail_source_path,
            benchmark_path,
            fuzz_path,
            test_path,
            modules_readme_path,
            editorconfig_path,
            gitattributes_path,
            clangd_path,
            vscode_extensions_path,
            doctor_path,
            fix_path,
            hook_installer_path,
            pre_commit_path,
            tracked_pre_commit_hook,
        ]:
            if not path.exists():
                raise FileNotFoundError(f"Expected renamed file to exist: {path}")

        doctor_result = run(template_command(["--doctor"]), cwd=repo_copy)
        assert_success(doctor_result, "environment doctor wrapper smoke test")
        if "Preset default-debug/default-release" not in doctor_result.stdout:
            raise AssertionError(
                "Expected the doctor output to summarize preset readiness.\n"
                f"stdout:\n{doctor_result.stdout}"
            )
        if "Recommended next step:" not in doctor_result.stdout:
            raise AssertionError(
                "Expected the doctor output to recommend a next preset.\n"
                f"stdout:\n{doctor_result.stdout}"
            )

        fix_result = run(template_command(["--fix"]), cwd=repo_copy)
        assert_success(fix_result, "local fix wrapper smoke test")
        if "Summary:" not in fix_result.stdout:
            raise AssertionError(
                "Expected the fix helper to print a summary.\n"
                f"stdout:\n{fix_result.stdout}"
            )

        hooks_result = run(template_command(["--install-hooks"]), cwd=repo_copy)
        assert_success(hooks_result, "git hooks installer wrapper smoke test")
        if "Installed local git hooks." not in hooks_result.stdout:
            raise AssertionError(
                "Expected the hook installer to confirm success.\n"
                f"stdout:\n{hooks_result.stdout}"
            )

        hooks_path_result = run(
            ["git", "config", "--local", "--get", "core.hooksPath"],
            cwd=repo_copy,
        )
        assert_success(hooks_path_result, "git hooks path verification")
        if hooks_path_result.stdout.strip() != ".githooks":
            raise AssertionError(
                "Expected core.hooksPath to be set to .githooks.\n"
                f"stdout:\n{hooks_path_result.stdout}"
            )

        old_paths = [
            repo_copy / "include" / "Capricorn",
            repo_copy / "benchmark" / "src" / "capricorn_benchmark.cpp",
            repo_copy / "fuzz" / "src" / "capricorn_fuzz.cpp",
            repo_copy / "src" / "capricorn.cpp",
            repo_copy / "source" / "modules" / "capricorn.ixx",
            repo_copy / "test" / "src" / "capricorn_test.cpp",
        ]
        for path in old_paths:
            if path.exists():
                raise AssertionError(f"Expected old template path to be gone: {path}")

        assert_contains(repo_copy / "CMakeLists.txt", "StarTrail")
        assert_contains(repo_copy / "CMakeLists.txt", 'set(TEMPLATE_LIBRARY_BASENAME "star_trail")')
        assert_contains(repo_copy / "CMakeLists.txt", 'set(TEMPLATE_LIBRARY_NAMESPACE "startrail")')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_DEVELOPER_MODE": "ON"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_ENABLE_SANITIZERS": "ON"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_ENABLE_CLANG_TIDY": "ON"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_ENABLE_CXX_MODULES": "ON"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_CLANG_TIDY_PROFILE": "recommended"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_CLANG_TIDY_WARNINGS_AS_ERRORS": "ON"')
        assert_contains(repo_copy / "BUILDING.md", "StarTrail_CLANG_TIDY_PROFILE=strict")
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_BUILD_BENCHMARKS": "ON"')
        assert_contains(repo_copy / "CMakePresets.json", '"StarTrail_BUILD_FUZZ_TESTS": "ON"')
        assert_contains(repo_copy / "vcpkg.json", '"name": "star-trail"')
        assert_contains(
            repo_copy / "cmake" / "cxx-modules-targets.cmake",
            'CXX_SCAN_FOR_MODULES'
        )
        assert_contains(
            repo_copy / "test" / "package" / "CMakeLists.txt.in",
            'CXX_SCAN_FOR_MODULES'
        )
        assert_contains(header_path, "#include <StarTrail/core/greeting.hpp>")
        assert_contains(header_path, "#include <StarTrail/core/project_info.hpp>")
        assert_contains(greeting_header_path, "namespace startrail")
        assert_contains(project_info_header_path, "#include <StarTrail/project_config.hpp>")
        assert_contains(project_info_header_path, "namespace startrail")
        assert_contains(source_path, '#include <StarTrail/core/greeting.hpp>')
        assert_contains(source_path, '#include <StarTrail/core/project_info.hpp>')
        assert_contains(source_path, "namespace startrail")
        assert_contains(module_interface_path, "export module star_trail;")
        assert_contains(module_interface_path, 'k_project_name {"StarTrail"}')
        assert_contains(module_interface_path, "namespace startrail")
        assert_contains(modules_main_path, "import star_trail;")
        assert_contains(modules_main_path, "startrail::greeting()")
        assert_contains(detail_header_path, "namespace startrail::detail")
        assert_contains(detail_source_path, "namespace startrail::detail")
        assert_contains(benchmark_path, '#include <StarTrail/core/greeting.hpp>')
        assert_contains(benchmark_path, 'startrail::greeting_for("benchmark")')
        assert_contains(fuzz_path, '#include <StarTrail/core/greeting.hpp>')
        assert_contains(fuzz_path, '#include <StarTrail/core/project_info.hpp>')
        assert_contains(fuzz_path, "startrail::project_name()")
        assert_contains(repo_copy / "src" / "main.cpp", '#include <StarTrail/star_trail.hpp>')
        assert_contains(repo_copy / "src" / "main.cpp", "startrail::greeting()")
        assert_contains(test_path, '#include <StarTrail/star_trail.hpp>')
        assert_contains(test_path, "[star_trail]")
        assert_contains(test_path, "startrail::project_name()")
        assert_contains(modules_readme_path, "include/StarTrail/")
        assert_contains(clangd_path, "-std=c++23")
        assert_contains(clangd_path, "CompilationDatabase: build/modules-debug-clang")
        assert_contains(editorconfig_path, "root = true")
        assert_contains(gitattributes_path, "* text=auto eol=lf")
        assert_contains(
            vscode_extensions_path,
            '"llvm-vs-code-extensions.vscode-clangd"',
        )

        for path in [
            repo_copy / "CMakeLists.txt",
            repo_copy / "CMakePresets.json",
            repo_copy / "README.md",
            repo_copy / "BUILDING.md",
            repo_copy / "HACKING.md",
            repo_copy / "CONTRIBUTING.md",
            header_path,
            source_path,
            module_interface_path,
            modules_main_path,
            benchmark_path,
            fuzz_path,
            repo_copy / "src" / "main.cpp",
            test_path,
        ]:
            assert_not_contains(path, "Capricorn")
            assert_not_contains(path, "capricorn")

    with tempfile.TemporaryDirectory(prefix="capricorn-template-init-interactive-") as tmp_dir:
        temp_root = Path(tmp_dir)
        repo_copy = temp_root / "NebulaKit"
        shutil.copytree(ROOT, repo_copy)

        result = run_with_input(
            template_command(["--init"]),
            cwd=repo_copy,
            stdin_text="\n" * 5,
        )
        assert_success(result, "interactive template init wrapper smoke test")

        interactive_preset_result = run(["cmake", "--list-presets"], cwd=repo_copy)
        assert_success(
            interactive_preset_result,
            "preset schema validation after interactive template init",
        )

        stdout = result.stdout
        if "Interactive template initialization." not in stdout:
            raise AssertionError(
                "Expected the interactive init banner to be shown.\n"
                f"stdout:\n{stdout}"
            )
        if "project=NebulaKit" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to derive the project name "
                "from the clone directory.\n"
                f"stdout:\n{stdout}"
            )
        if "check: no remaining template identifiers found in tracked files" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to run the residual check.\n"
                f"stdout:\n{stdout}"
            )
        if "Module 'nebulakit' not found" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to explain the common clangd "
                "module diagnostic.\n"
                f"stdout:\n{stdout}"
            )
        if "git: removed existing .git metadata" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to remove cloned git metadata.\n"
                f"stdout:\n{stdout}"
            )
        if "git: initialized fresh repository" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to initialize a fresh git repo.\n"
                f"stdout:\n{stdout}"
            )
        if "cleanup: remove tools/rename_template.py" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to remove the template "
                "rename helper from the new project.\n"
                f"stdout:\n{stdout}"
            )
        if "cleanup: remove TEMPLATE.md" not in stdout:
            raise AssertionError(
                "Expected the interactive init flow to remove template-only "
                "documentation from the new project.\n"
                f"stdout:\n{stdout}"
            )

        git_work_tree_result = run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_copy,
        )
        assert_success(git_work_tree_result, "fresh git repository verification")
        if git_work_tree_result.stdout.strip() != "true":
            raise AssertionError(
                "Expected the interactive init flow to leave a git work tree.\n"
                f"stdout:\n{git_work_tree_result.stdout}"
            )

        git_history_result = run(
            ["git", "rev-list", "--count", "--all"],
            cwd=repo_copy,
        )
        assert_success(git_history_result, "fresh git history verification")
        if git_history_result.stdout.strip() != "0":
            raise AssertionError(
                "Expected the fresh git repository to have no template commits.\n"
                f"stdout:\n{git_history_result.stdout}"
            )

        assert_contains(repo_copy / "CMakeLists.txt", "NebulaKit")
        assert_contains(repo_copy / "CMakeLists.txt", 'DESCRIPTION "A modern C++ project"')
        assert_contains(
            repo_copy / "CMakeLists.txt",
            'set(NEBULAKIT_LIBRARY_BASENAME "nebulakit")',
        )
        assert_contains(
            repo_copy / "CMakeLists.txt",
            'set(NEBULAKIT_LIBRARY_NAMESPACE "nebulakit")',
        )
        assert_contains(repo_copy / "vcpkg.json", '"name": "nebulakit"')
        assert_not_contains(repo_copy / "README.md", "run.bat --init")
        assert_not_contains(repo_copy / "README.md", "./run.sh --init")
        assert_not_contains(repo_copy / "README.md", "TEMPLATE.md")
        assert_not_contains(repo_copy / "README.md", "starter template")
        assert_not_contains(repo_copy / "README.md", "choosealicense")
        assert_contains(repo_copy / "README.md", "This project is licensed under the terms in [LICENSE](LICENSE).")
        assert_not_contains(repo_copy / "BUILDING.md", "TEMPLATE.md")
        assert_not_contains(repo_copy / "HACKING.md", "template author")
        assert_not_contains(repo_copy / "CONTRIBUTING.md", "template's dependency layering")
        assert_contains(repo_copy / "CONTRIBUTING.md", "project's dependency layering")
        assert_not_contains(repo_copy / "tools" / "README.md", "rename_template.py")
        assert_not_contains(repo_copy / "tools" / "README.md", "test_template_init.py")
        assert_not_contains(repo_copy / "tools" / "doctor.py", "this template")
        assert_not_contains(repo_copy / "tools" / "fix.py", "the template")
        assert_not_contains(
            repo_copy / "source" / "modules" / "README.md",
            "This template keeps",
        )
        assert_not_contains(
            repo_copy / "cmake" / "dependencies.cmake",
            "Template package-management strategy guidance",
        )
        assert_not_contains(
            repo_copy / "cmake" / "project-options.cmake",
            "This template's optional C++23 module target",
        )
        assert_not_contains(
            repo_copy / "cmake" / "project-options.cmake",
            "C++23 template emits",
        )
        assert_contains(
            repo_copy / "HACKING.md",
            "nebulakit_set_target_clang_tidy(my_target PROFILE strict WARNINGS_AS_ERRORS ON)",
        )
        assert_contains(
            repo_copy / "cmake" / "project-options.cmake",
            "function(nebulakit_apply_options target)",
        )
        assert_contains(
            repo_copy / "cmake" / "dependencies.cmake",
            "function(nebulakit_register_package_dependency)",
        )
        assert_contains(
            repo_copy / "cmake" / "project-config.cmake.in",
            "@nebulakit_package_dependency_block@",
        )
        assert_contains(
            repo_copy / "cmake" / "project-config.hpp.in",
            "namespace @NEBULAKIT_LIBRARY_NAMESPACE@",
        )
        assert_contains(
            repo_copy / "cmake" / "sync-compile-commands.cmake",
            "NEBULAKIT_BINARY_COMPILE_COMMANDS",
        )
        assert_not_contains(
            repo_copy / ".github" / "workflows" / "ci.yml",
            "Template initialization smoke test",
        )
        assert_not_contains(
            repo_copy / ".github" / "workflows" / "ci.yml",
            "tools/test_template_init.py",
        )
        assert_not_contains(repo_copy / "CMakeLists.txt", "https://www.gemc.club")
        assert_not_contains(repo_copy / "run.bat", "rename_template.py")
        assert_not_contains(repo_copy / "run.sh", "rename_template.py")
        assert_tree_not_contains(repo_copy, "template_")
        assert_tree_not_contains(repo_copy, "TEMPLATE_")
        interactive_header = repo_copy / "include" / "NebulaKit" / "nebulakit.hpp"
        interactive_core_header = (
            repo_copy / "include" / "NebulaKit" / "core" / "project_info.hpp"
        )
        interactive_module_interface = (
            repo_copy / "source" / "modules" / "nebulakit.ixx"
        )
        interactive_benchmark = (
            repo_copy / "benchmark" / "src" / "nebulakit_benchmark.cpp"
        )
        interactive_fuzz = repo_copy / "fuzz" / "src" / "nebulakit_fuzz.cpp"
        if not interactive_header.exists():
            raise FileNotFoundError(
                "Expected the interactive init flow to rename the public header."
            )
        for path in [
            interactive_core_header,
            interactive_module_interface,
            interactive_benchmark,
            interactive_fuzz,
        ]:
            if not path.exists():
                raise FileNotFoundError(
                    f"Expected the interactive init flow to rename: {path}"
                )

        removed_after_init = [
            repo_copy / "TEMPLATE.md",
            repo_copy / "tools" / "rename_template.py",
            repo_copy / "tools" / "test_template_init.py",
            repo_copy / "tools" / "__pycache__",
            repo_copy / "compile_commands.json",
            repo_copy / "build",
        ]
        for path in removed_after_init:
            if path.exists():
                raise AssertionError(
                    f"Expected the interactive init flow to remove: {path}"
                )

        for path in [
            repo_copy / "tools" / "doctor.py",
            repo_copy / "tools" / "fix.py",
            repo_copy / "tools" / "install_git_hooks.py",
            repo_copy / "tools" / "pre_commit.py",
            repo_copy / ".githooks" / "pre-commit",
        ]:
            if not path.exists():
                raise FileNotFoundError(
                    f"Expected the interactive init flow to preserve: {path}"
                )

        post_init_help_result = run(template_command(["--help"]), cwd=repo_copy)
        assert_success(post_init_help_result, "post-init wrapper help")
        if "--init" in post_init_help_result.stdout:
            raise AssertionError(
                "Expected the post-init wrapper help to omit template init.\n"
                f"stdout:\n{post_init_help_result.stdout}"
            )

    print("template initialization smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
