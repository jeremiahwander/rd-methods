# rd-methods

## Introduction

This project provides scripts to prototype and evaluate new methods in rare disease diagnostics.

## Getting started

This project is intended to be run on a Linux host, preferably a Linux VM hosted in Azure.

### Environment Setup

This project is targeted to run on Ubuntu 20.04.

1. One-time environment installation:

    1. Install (and configure) the the following utilities: git, Azure CLI, azcopy, direnv.

    1. Clone this repo.

        ```bash
        git clone https://github.com/jeremiahwander/rd-methods
        ```

    1. Change directory to the `rd-methods` directory you just cloned. From command line, run the `install-env` script to locally install the application environment in a sandbox.

        _Using the "-R" option will remove any existing environment to ensure a clean environment is installed based on the latest environment definition._

        ```bash
        cd rd-methods
        ./install-env -R
        ```

1. Environment activation before each use:

    - This project uses [direnv](https://direnv.net/) to automatically activate the environment when you `cd` into the repo directory, so no explicit action is needed; however, the `setup-shell` script can also be run to active the environment in your current shell in cases in which `direnv` is not used.

1. Open workspace in VS Code:

    - From command line, open VS Code using the workspace file

        ```bash
        code rd-methods.code-workspace
        ```

### Merge Strategy

We use "rebase with merge commit" approach in which the entire history and all commits are preserved. Every merge produces a commit (i.e., no fast-forward) and those commit hashes are persisted forever.

### Branch Names

- `main` branch: latest "stable" version
  - Requires a pull-request with approval from at least one other reviewer and successful completion of CI testing pipeline
- `feature/` branches: new features _intended_ to be merged into `main`
- `fix/` branches: bug fixes _intended_ to be merged into `main`
- `test/` branches: exploratory tests that are _not intended_ to be merged into `main`

### Documentation

All documentation should be included in the repo as Markdown files. All Markdown files should lint with the VS Code extension: `davidanson.vscode-markdownlint`

### Local Library Code

Reusable library code should be included in the `lib/` directory. This `lib` package is automatically installed into the python environment so that any file can import these local library packages using `import lib.module_name` or `from lib import module_name` for any `module_name` within the `lib/` directory.

All code within the `lib/` directory should conform to the [Python Style Guide](https://dev.azure.com/biomedcomp/BiomedComp/_git/Tools?_a=preview&path=/docs/python-style.md) and have corresponding test code located in the `test/` directory. The `tox` command line tool can be run to execute all test code and linters. Pull requests into the `main` branch will fail until `tox` runs without errors in CI. When using VS Code for development, auto-formatters and linters are configured to help enforce the style guide (note: some of these won't run for test code). See the following resources for more information:

- [Python Style Guide](https://dev.azure.com/biomedcomp/BiomedComp/_git/Tools?_a=preview&path=/docs/python-style.md)
- [Python Development Tools](https://dev.azure.com/biomedcomp/BiomedComp/_git/Tools?_a=preview&path=/docs/python-tools.md)

### Running Tests and Linters

To run all tests and linters, simply run `tox` (the first run will create a new environment which may take several minutes to build). This `tox` command is the same command run during CI for pull requests into `main`. The output from `tox` is very verbose and it takes a minute or so to run all of the tests, linters, and other checks. It is therefore common to run just a single step/check, or a few steps/checks during development. See example commands below:

```bash
# Run all tests, linters, and other checks (exactly what gets run in CI).
tox

# Run only tests (very useful when developing tests).
tox -q -e test

# Run only flake8 linter.
tox -q -e lint

# Can list multiple steps/checks to run (ex: flake8 and bandit security linter).
tox -q -e lint,sec
```

### Modifying Python Environment

This project uses [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to manage the python environment and all packages, as defined in `environment.yml`. When adding packages avoid pip packages if possible. Many [PyPI](https://pypi.org/) packages are also available as conda packages (see [conda package index](https://anaconda.org/)) from `conda-forge`, though sometimes with a different package name (see [common package name mapping](https://github.com/regro/cf-graph-countyfair/blob/master/mappings/pypi/grayskull_pypi_mapping.yaml)). If pip packages are required, they can be added to the `environment.yml` file under `dependencies.pip`.

The `update-conda-lock` bash script is used to generate lock files for all supported platforms based on `environment.yml`. This script will generate a `conda-lock.yml` file which exactly defines the environment, including conda and pip packages across all supported platforms, and `conda-lock` uses this file to recreate this exact environment. The `update-conda-lock` also generates `conda-{platform}.lock.yml` files for all supported platforms, which are conda environment YAML files including exact version numbers for all conda and pip packages. These can be used with programs that don't support the `conda-lock.yml` file (e.g., `tox`); however, this is not guaranteed to recreate the _exact_ environment because conda will perform another solve step.

The environment installed by the `install-env` bash script is based only on the `conda-lock.yml` file, so it is important to run the following commands and commit changes to the lock files after any change to `environment.yml` (`tox`, which is run in CI will check that the lock files are in sync with `environment.yml`):

```bash
./update-conda-lock
./install-env -R
source ./setup-shell # Not necessary when using direnv.
```

### Component Governance

[Component Goverance](https://docs.opensource.microsoft.com/tools/cg/index.html) scans can be run via tox, and should eventually be integrated into a github Action with associated alerts.

When new components are used or versions are updated, the `cgmanifest.json` file must be updated manually.
