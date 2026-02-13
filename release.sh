#!/usr/bin/env bash

# Release script for Python packages.

set -e -o pipefail

if test -z "${GITHUB_TOKEN}"; then
    echo -e "\033[0;33m ***Please set \$GITHUB_TOKEN\033[0m"
    exit 1
fi

if test "$(git rev-parse --abbrev-ref HEAD)" != "main"; then
    echo -e "\033[0;33m*** Please switch to the main branch\033[0m"
    exit 1
fi

MODE=$(test "$1" = "-f" && echo run || echo test)

if test "$MODE" != "run"; then
    echo -e "\033[0;33m*** Running in test mode, use '-f' to publish the package\033[0m"
    echo
fi

if test $(git status --porcelain | wc -l) -ne 0; then
    echo -e "\033[0;31m*** Working directory is not clean, aborting\033[0m"
    exit 1
fi

VERSION=$(grep -e '## [0-9].*–' CHANGELOG.md | head -1 | cut -d " " -f 2)
PKG_VERSION=$(grep -e '^version =' pyproject.toml | cut -d '"' -f 2)

if test "$VERSION" == "Unreleased"; then
    echo -e "\033[0;31m*** Please update version in CHANGELOG.md\033[0m"
    exit 1
fi

if test "$VERSION" != "$PKG_VERSION"; then
    echo -e "\033[0;31m*** Versions in CHANGELOG.md and pyproject.toml don't match, aborting\033[0m"
    exit 1
fi

echo -e "\033[0;34m*** Building version ${VERSION}\033[0m"
echo

rm -rf dist

poetry run poe i18n-compile
poetry build

echo -e "\033[0;34m*** Publishing version ${VERSION}\033[0m"
echo

if test "${MODE}" = "run"; then
    git tag "v${VERSION}" -m "Release ${VERSION}"
    git push origin "v${VERSION}"
    poetry publish
else
    poetry publish --dry-run
fi

echo
echo -e "\033[0;32m*** Package built in dist\033[0m"
echo

if test "${MODE}" = "run"; then
    echo -e "\033[0;36m*** Create a new GitHub release\033[0m"
    echo -e "\033[0;36m*** Add '## Unreleased' header to CHANGELOG.md\033[0m"
    echo -e "\033[0;36m*** Bump version in pyproject.toml and add .dev\033[0m"
else
    echo -e "\033[0;33m*** Dry run successful, rerun with '-f' to publish the package\033[0m"
fi
