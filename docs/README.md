# nanoBragg PyTorch Documentation

Welcome to the nanoBragg PyTorch implementation documentation.

## Quick Start

**→ [Architecture Hub](./architecture/README.md)** - Start here for all technical specifications and design documents.

## Documentation Structure

### [Architecture](./architecture/)
The authoritative technical specifications for all components, conventions, and design decisions.
- Global conventions and unit systems
- Component specifications (Detector, Crystal, Simulator)
- C-code analysis and porting guides

### [Development](./development/)
Guides for development workflow, testing, and debugging.
- [Testing Strategy](./development/testing_strategy.md) - Including canonical golden data commands
- [Implementation Plan](./development/implementation_plan.md) - Phased development roadmap
- [Debugging Guide](./development/detector_geometry_debugging.md) - Case study and best practices

### [Reports](./reports/)
Analysis reports, performance benchmarks, and problem investigations.

## Key Documents for New Developers

1. **[CLAUDE.md](../CLAUDE.md)** - Core implementation rules and gotchas
2. **[Architecture Hub](./architecture/README.md)** - Central navigation for all technical specs
3. **[Testing Strategy](./development/testing_strategy.md)** - How to validate your implementation
4. **[C-Code Overview](./architecture/c_code_overview.md)** - Understanding the reference implementation

## Critical Warnings

### ⚠️ Unit System Exceptions
- Physics calculations use Angstroms
- Detector geometry uses meters internally
- User interfaces accept millimeters

### ⚠️ Non-Standard Conventions
- Miller indices use real-space vectors
- F_latt uses fractional indices
- See [Architecture Hub](./architecture/README.md) for details

## Getting Help

- Check the [Architecture Hub](./architecture/README.md) first
- Review relevant component specifications
- Consult the debugging case studies
- Use parallel trace validation for physics bugs