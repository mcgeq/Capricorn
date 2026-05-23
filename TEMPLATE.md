# Renaming The Template

If you cloned the template with a real destination name, the smoothest path is:

```sh
git clone <url> MyProject
cd MyProject
./run.sh --init
```

```cmd
git clone <url> MyProject
cd MyProject
run.bat --init
```

```powershell
git clone <url> MyProject
cd MyProject
.\run.bat --init
```

The initializer suggests defaults from the current directory name, runs a
tracked residual check, removes cloned `.git` metadata, runs `git init`, and
removes template-maintainer files from the new project so it starts without
template history or one-time initialization tools.

For non-interactive use, the fastest path is:

```sh
./run.sh --project-name MyProject --dry-run --check
./run.sh --project-name MyProject --check
```

```cmd
run.bat --project-name MyProject --dry-run --check
run.bat --project-name MyProject --check
```

```powershell
.\run.bat --project-name MyProject --dry-run --check
.\run.bat --project-name MyProject --check
```

Optional knobs:

- `--include-dir-name`
- `--library-basename`
- `--namespace`
- `--package-name`

Example:

```cmd
run.bat --project-name FancyApp --include-dir-name Fancy --library-basename fancy --namespace fancy --package-name fancy-app --check
```

```powershell
.\run.bat --project-name FancyApp --include-dir-name Fancy --library-basename fancy --namespace fancy --package-name fancy-app --check
```

```sh
./run.sh --project-name FancyApp --include-dir-name Fancy --library-basename fancy --namespace fancy --package-name fancy-app --check
```

After running the helper:

1. Review the resulting diff.
2. Review the `check:` output for any intentional sample text you still want to rename.
3. Re-run the build presets you care about.

The CMake package export names, install paths, and generated package config
files already follow `PROJECT_NAME`, so they update automatically. The helper
also updates the manifest package name in [`vcpkg.json`](vcpkg.json) plus the
project-specific CMake option names used in presets and docs. The wrapper
scripts forward directly to [`tools/rename_template.py`](tools/rename_template.py)
if you need to integrate the helper into other automation.

After the rename, the example code is intentionally split into layers instead of
staying as a single flat demo:

1. `include/<Project>/<basename>.hpp` is the main public umbrella include.
2. `include/<Project>/core/` is where new public features should usually land.
3. `src/detail/` is for private implementation helpers.
4. `source/modules/<basename>.ixx` is the optional named module companion
   source if your toolchain support matures enough to use it.

If you keep the optional module target, treat it as a second frontend for the
same API surface:

1. Keep `find_package()` and install rules explicit.
2. Export it as a separate `<ProjectName>::modules` target.
3. Do not ask downstreams to link both the header target and the module target
   into the same final binary.

When you start adding real dependencies after the rename:

1. Keep public library dependencies on explicit `find_package()` boundaries.
2. Keep test / benchmark / fuzz / tooling dependencies behind opt-in
   `vcpkg.json` features.
3. Use `FetchContent` only for repository-local helper tooling that does not
   leak into the installed package surface.

For template maintainers, `python tools/test_template_init.py` runs the
initializer against a temporary copy of the repository and verifies that the
tracked sample names, file paths, wrapper entrypoints, and option identifiers
all move together.
