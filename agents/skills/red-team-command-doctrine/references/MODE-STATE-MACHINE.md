# Mode State Machine

## States
- `normal`
- `redteam-active`

## Entry
New top-level session always resets to `normal`.

## Transitions
- `normal` -> `redteam-active` when the user explicitly says:
  - `进入红队模式`
  - `开启红队模式`
  - `/redteam on`
  - `enable red team mode`
- `redteam-active` -> `normal` when the user explicitly says:
  - `退出红队模式`
  - `关闭红队模式`
  - `/redteam off`
  - `disable red team mode`

## Behavior
### normal
- no offensive doctrine injection
- no reinterpretation of ordinary prompts

### redteam-active
- inject compact offensive guidance
- detect phase when possible
- keep context lightweight

## Invariants
- red-team mode is never the default
- session start never injects a heavy doctrine block
- explicit off immediately stops offensive injection
