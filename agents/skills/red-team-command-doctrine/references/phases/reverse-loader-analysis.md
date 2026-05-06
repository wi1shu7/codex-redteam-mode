# Reverse / Loader Analysis

## Objective
Understand the execution chain and operator-relevant behavior of a sample/loader.

## Enter when
The task centers on a loader, stager, dropper, or malware sample.

## Prioritize evidence
- process tree
- config/IOCs
- dropped files
- network endpoints
- stage boundaries

## Low-noise path first
Prefer static + controlled sandbox evidence before uncontrolled execution.

## Typical skills/tools
- `malware-loader-analysis`
- strings, x64dbg, Procmon, FakeNet, PCAP

## Exit when
You can describe the execution chain and the best offensive/defensive lesson from it.
