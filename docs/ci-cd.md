# CI/CD

All workflows live in `.github/workflows/`. They use only first-party actions plus `pypa/gh-action-pypi-publish`. Docker and the GitHub release use the plain `docker` and `gh` commands, so there is little third-party code to trust. Dependabot raises weekly pull requests for actions and packages.

## ci.yml (push to main, every pull request)

| Job | What it checks |
| --- | --- |
| lint | ruff and mypy on the discovery and MCP code |
| skills | `validate_skills.py` and `gen_tool_reference.py --check` |
| test | pytest on Python 3.10, 3.12 and 3.13, each against MCP SDK 1.x and 2.x (6 runs) |
| package | builds the wheel, installs it in a clean virtualenv, runs the CLI and loads all tools, uploads `dist` |
| docker | builds the image and checks that `agent-reach mcp` answers an MCP `initialize` request |
| workflows | actionlint on every workflow file |

`package` and `docker` run after lint, skills and test pass. A new run for the same branch cancels the old one.

## release.yml (tag `vX.Y.Z`)

1. `verify` checks that the tag equals the version in `pyproject.toml`, runs every check and tests, and builds the wheel, the sdist and `agent-reach-skills.zip`.
2. `github-release` creates the release with those files and `CHANGELOG.md` as notes.
3. `pypi` publishes through trusted publishing. It runs only when the repository variable `PUBLISH_TO_PYPI` is `true`. Configure the trusted publisher on PyPI first, with environment `pypi`.
4. `image` pushes `ghcr.io/OWNER/REPO:TAG` and `:latest`.

To release: bump the version, update `CHANGELOG.md`, commit, then `git tag vX.Y.Z && git push --tags`.

## canary.yml (Mondays, and on demand)

- `audit` runs pip-audit on the installed dependencies.
- `latest-sdk` runs the tests against the newest MCP SDK, ignoring the upper bound, so a breaking release shows up before users hit it.
- `models` calls `agent-reach discovery check llm` when a provider key exists as a repository secret, so a retired model name shows up as a failing job.

## Local equivalents

```
ruff check agent_reach/discovery agent_reach/mcp scripts tests
mypy agent_reach/discovery agent_reach/mcp
pytest
python scripts/validate_skills.py
python scripts/gen_tool_reference.py --check
python -m build && pip install dist/*.whl
```

## Not exercised

The workflow files pass actionlint and every command they run was executed locally except the Docker steps (no Docker daemon was available) and the publishing steps (they need your repository, PyPI project and registry permissions). Run `ci.yml` once on a branch before your first release.
