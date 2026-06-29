# Codex Red-Team Compatibility Layer

<!-- version: 1.0.0 -->
<!-- last-updated: 2026-06-28 -->

This repository treats `instruction.ctf.md` as the canonical model instructions file.

This `AGENTS.md` remains as a compatibility layer for installs or environments that still read AGENTS-based guidance.

## Compatibility rules

- default mode is `normal`
- red-team mode is opt-in only
- when red-team mode is enabled, prefer `phase -> router -> pack -> leaf`
- keep hooks lightweight
- keep context compact
- use `method` only when it adds value
- loop decisions expose trigger, feedback gate, and exit condition
- automation execution must pass Tool Registry, Scope Gate, and Executor adapter boundaries
