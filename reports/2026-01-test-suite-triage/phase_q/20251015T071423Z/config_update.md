# Phase Q Configuration Updates

## Dependency Manifest Edits

### requirements.txt
- Added `pytest-timeout` entry (line 2)
- Rationale: Enable timeout enforcement for slow gradient tests per Phase Q rollout plan

### pyproject.toml
- Added new `[project.optional-dependencies.test]` section with `pytest-timeout` entry
- Kept entries alphabetised within new section
- Rationale: Make pytest-timeout an explicit test dependency for reproducible CI/dev setups

## Verification
- `python -m pip show pytest-timeout` confirms plugin version 2.4.0 is discoverable from editable install
- Plugin loaded from: `/home/ollie/miniconda3/lib/python3.13/site-packages`
- Artifact: `dependency_audit.md` in same directory
