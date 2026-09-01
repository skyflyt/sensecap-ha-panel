# AGENTS.md

Instructions for AI agents working in this repository.

**If you are helping someone build a panel, the file you want is
[`agent/SEED-PROMPT.md`](agent/SEED-PROMPT.md).** Read it first. This file is
about working on *this repo*.

## The one rule that matters

**Verify against the running device, never against the compile output.**

`esphome compile` succeeding means the YAML parsed and the C++ built. It says
nothing about whether anything appears on the screen. This panel will compile,
flash, boot, and show a blank area with no tool anywhere reporting a problem.

So never report a display change as done on the strength of a build. Say
"compiled, not yet verified on the panel", then ask the user a *specific*
question about what they can see. "Is there a number in the top right of the
energy page, and what does it say" gets an answer. "Did it work" does not.

## Before you write YAML

Read [`docs/00-panel-guide.md`](docs/00-panel-guide.md). It is 400 lines and it
will save you from most of what follows.

The traps, by name:

- **Labels inside a styled container need their own `text_color`**, or they
  render dark-on-dark and look exactly like a broken sensor.
- **Keep label text ASCII.** `−`, `—`, `·`, `…` are not in the built-in
  montserrat glyph set.
- **YAML eats inline `!lambda` ternaries** — the `" : "` reads as a mapping
  separator. Use a `|-` block scalar.
- **Never POST a fake state to an entity id a device will later own.** It
  creates a real registry entry and the device silently claims a `_2` suffix.
- **A repaint that recomputes from raw inputs bypasses whatever gated it.**
  Write a committed global; have the repaint read only that.
- **Home Assistant states cap at 255 characters.** Over it, the publisher logs
  an HTTP 400 and the sensor sits silently empty.

## Placeholders are load-bearing

Two schemes, because Home Assistant has no substitution mechanism:

- ESPHome: `${entity_*}` substitutions, declared in `esphome/example-device.yaml`
- Home Assistant: literal `CHANGE_ME_` entity ids in `homeassistant/packages/`

**Never silently replace one with a plausible-looking id.** If you are
suggesting a value, say it is a guess.

## Never

- Commit a credential. Anything secret goes in `secrets.yaml` behind `!secret`,
  and `secrets.yaml` is gitignored. Note that ESPHome substitutions expand
  *inside lambdas*, which is how a password gets baked into a binary.
- Print, log or paste a credential value. Report location and type.
- Add anything to the pet that fires on its own, interrupts, keeps a streak, or
  can punish the user. Those absences are deliberate design and
  `docs/desk-pet/01-design-and-feasibility.md` §4 explains each.
- Flash a device without being asked.

## Two strikes and stop

Same step, same error, twice: stop and report what you think it means. A third
variation will not help, and repeated attempts against a wrong mental model
produce confident wreckage.
