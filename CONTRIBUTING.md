# Contributing

Issues and pull requests welcome. It is a hobby project, so expect a
weekend-shaped response time.

## Most useful contributions

**Your own panel patterns.** `esphome/patterns/` is the point of this repo.
If you have solved something on an Indicator that generalises — a layout, a
widget behavior, a way of getting data on screen reliably — that is worth more
than a fix to my pet.

**Corrections to the docs, especially the numbers.** `docs/00-panel-guide.md`
and `docs/desk-pet/` carry measured figures from one panel in one house. If
yours behaves differently, I would like to know.

**A measured `Flash:` percentage.** Every byte budget in
`docs/desk-pet/03-sprite-pipeline.md` is arithmetic rather than measurement,
and `docs/LIMITATIONS.md` says so. A real number from a real build is a genuine
improvement.

## House style

**Comments carry reasoning, not description.** The code says what it does. A
comment should say why it is that way and what went wrong when it was not —
that is what most of the comments in `esphome/patterns/` are, and it is why
they are long.

**Say what you measured.** "Faster" is not useful; "1216ms to 48ms" is.

**Keep the honesty.** If something is unverified, say so in the same paragraph
rather than in a footnote. `docs/LIMITATIONS.md` exists so nobody is surprised.

## Before you open a PR

- `esphome config` against your device file passes.
- If you touched the display, **you looked at the panel.** A clean compile is
  not evidence that anything renders, and that is the most expensive lesson in
  this repo.
- No credentials, no real entity ids from your own house. Use `CHANGE_ME_`.
