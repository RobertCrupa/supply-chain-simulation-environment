# Supply Chain Simulation Engine Documentation

This section documents the defence-focused simulation engine in this submodule.
It explains how runs are configured, how state is processed each timestep, and
which outputs are produced.

## Audience

- Engineers extending modules or metrics
- Analysts interpreting simulation outputs
- Contributors creating new scenarios

## Document Map

- `overview.md`: system architecture, execution model, and core concepts
- `runtime-flow.md`: exact runtime lifecycle and timestep processing order
- `inputs.md`: all input sources, schema fields, and how each is consumed
- `outputs.md`: all output artifacts and field-by-field definitions
- `glossary.md`: plain-language definitions of domain and framework terms

## Suggested Reading Order

1. `overview.md`
2. `runtime-flow.md`
3. `inputs.md`
4. `outputs.md`
5. `glossary.md`

## Engine Scope

This documentation covers only the simulation engine in
`supply-chain-simulation-environment`.
