# Fix Plan

## TODO
- [ ] Complete CLI interface refinements
  - Add support for -mat matrix files
  - Implement header precedence rules for -img/-mask files
  - Add Fdump.bin caching functionality for HKL files
  - Add Poisson noise generation for -noisefile
- [ ] Implement missing physics functions (sinc3, polarization_factor) in utils/physics.py
- [ ] Add console script entry point to pyproject.toml
- [ ] Verify all AT-CLI-* acceptance tests pass (CLI conformance)
- [ ] Verify all AT-GEO-* acceptance tests pass (geometry conventions)
- [ ] Verify all AT-SAM-* acceptance tests pass (sampling/normalization)
- [ ] Verify all AT-STR-* acceptance tests pass (structure factors)

## DONE
- [x] Fixed test_configuration_consistency.py tests (mode detection, trigger tracking)
- [x] Fixed test_suite.py golden data tests (generated missing golden reference files)
- [x] Verified test suite runs (106 passing, 6 were fixed)
- [x] Implemented CLI interface (__main__.py) with AT-CLI-001 and AT-CLI-002 support
  - Parsed all required arguments per spec-a-cli.md
  - Mapped CLI flags to internal config objects
  - Supported basic file I/O (float binary, SMV, PGM outputs)
  - Added help/usage functionality
- [x] Implemented basic I/O module (HKL reader, matrix reader)
- [x] Added missing detector conventions (ADXV, DENZO, DIALS, CUSTOM)
- [x] Fixed unit conversion functions (added mm_to_meters)
- [x] Fixed SMV header generation with correct field mappings

## Known Issues
- Missing critical physics functions (sinc3, polarization_factor)
- No Poisson noise generation yet
- No matrix file support yet
- No header precedence from -img/-mask files

## Next Priority
Completing the remaining physics functions and adding console script entry point to make the tool fully usable.