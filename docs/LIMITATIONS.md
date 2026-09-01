# Limitations

Things that do not work, things that are unmeasured, and trades I made on
purpose. If you are deciding whether to build this, read this page before the
README's screenshots convince you.

---

## My own control pages are not in this repo

The panel runs five top-level pages plus a dozen sub-pages: room lights and
scenes, a climate dial, energy with solar and battery, door locks and garage
doors, media transport, work controls.

**None of those pages are here**, because they are welded to my entity ids, my
rooms and my hardware. Publishing them would be publishing my house rather than
a project, and they would not run for you anyway.

What is here instead is `esphome/patterns/` and `docs/00-panel-guide.md`: the
chrome, the state plumbing, the traps, and the reasoning. Those are the parts
that transfer. The page that uses them is your own layout, and it is the easy
half.

## The grid badge's alarm rendering is unverified

`esphome/patterns/debounced-state-badge.yaml` is real, running code, but I have
only ever seen its normal state. The obvious way to demo the alarm path was to
POST the alarm value to the source entity, and I checked what else consumed
that entity first: fifteen references across four live automation flows,
including "Power outage" and "Power restored" triggers, none disabled. It would
have driven real exterior loads at 21:00 on a Sunday.

So the red path stays unproven until the next real outage, or until someone
temporarily repoints the text sensor at a scratch entity and reflashes twice.
The debounce logic is verified; the rendering at the far end of it is not.

A related thing worth knowing: that badge and those four automation flows now
share one trigger entity. If it is ever renamed, or the integration changes its
strings, they break together.

---

## The extraction in this repo has not been compiled in this form

This is the big one and it is at the top on purpose.

Every block in `esphome/desk-pet.pkg.yaml` came out of a larger panel config
that has been running on my desk since August 2026. The snippets in
`esphome/patterns/` are the same code, reduced to the minimum that shows the
pattern, so they have been *edited* even where the original was not. The blocks work. **What is new is
the assembly into a standalone package, the `${entity_*}` substitutions, and
`example-device.yaml`.** None of that has been through `esphome config` or
`esphome compile` in this exact shape.

Concretely, expect to fix:

- Substitutions that do not resolve because you skipped one.
- Dangling widget ids if you use the package without pasting
  `main-page-tile.snippet.yaml` into your main page. `refresh_pet` paints six
  widgets that live on *your* page, not on the pet page.
- Anything that changed in ESPHome between my version and yours.

Run `esphome config` first. Then `esphome compile`. Then look at the panel.

## A clean compile is not evidence that anything renders

This is the single hardest-won lesson from the whole build, so it gets its own
heading.

The panel is perfectly capable of compiling successfully, flashing
successfully, booting, and then showing you nothing. I lost real time to
exactly that, twice, and neither time did any tool tell me anything was wrong.

The two mechanisms I actually hit:

**Dark text on a dark tile.** A label inside a styled `obj` container that does
not name its own `text_color` inherits LVGL's default theme color, which is
dark. The text renders. It renders black on near-black. It looks precisely like
missing data, and I spent an evening instrumenting a sensor that was working
the whole time. Button labels are unaffected, which is why some pages looked
right while others looked broken.

**Widgets that are simply not where you think.** A sprite that silently fails
to swap is indistinguishable from a pet that has not levelled.

The rule that came out of it: **verify against the running device, not against
the build output.** Read the panel. Read the entity in Home Assistant developer
tools. A green compile tells you the YAML parsed.

## Flash and RAM headroom are unmeasured

I quote 8,192 bytes for a 64x64 chroma_key sprite and 102KB for the full
modular part library. Those are arithmetic, not measurement.

**The number that actually matters is how much of your OTA app partition your
binary already uses**, and `esphome compile` prints it:

```
Flash: [====      ] 41.2% (used X bytes from Y bytes)
```

On 8MB with OTA there are two app slots and the image has to fit one. Until you
read that line, every budget in `docs/03-sprite-pipeline.md` is a guess wearing
a table. I have not read mine on the current build.

`animimg`, the LVGL widget that cycles frames for real animation, keeps every
frame resident simultaneously. Nothing here uses it. Confirm it against your
installed builder before designing around it. The idle bob in this repo is a
700ms interval toggling the sprite's `y` between two values, which costs
nothing and reads as breathing.

## RGB565 with chroma_key: what you give up

`transparency: chroma_key` is 2 bytes per pixel. `transparency: alpha_channel`
is 3. I chose the cheaper one and it is also the better-looking one at this
size, but the trade is real:

- **No soft edges, ever.** Every pixel is fully opaque or fully transparent.
  For pixel art that is what you want. For anything with a glow or a soft
  shadow it is not, and you will have to fake it with dithered dark pixels or
  give up.
- **One color is burned.** The chroma key cannot appear anywhere in real art.
  `make-pet-stages.py` uses magenta and asserts on partial alpha to keep this
  honest.
- **Check the reserved value against your builder** before you commit a
  palette. If it differs from what you assumed, parts of your sprite become
  transparent and it will look like a rendering bug.

## What is designed but not built

The repo ships **slice 1**: one form, levels 1 to 8, a fixed power set, seven
minigames, decay with pause gates, XP from panel touches and from play.

Not built:

- Evolution, Ascendant state, Surplus banking, the tier roll, pity counters.
- The modular parts system. The eight stages here are a fixed drawn ladder.
- Random power draws, the owned/equipped split, reroll tokens.
- Traits, higher power tiers, the collection page.
- Accessories of any kind.

`docs/02-progression-and-evolution.md` and `docs/03-sprite-pipeline.md`
describe all of it in enough detail to build from. None of it is here.

## The XP scorer is not in this repo

The pet in this repo earns XP from **panel touches and from playing the
minigames**. Those are the two sources that need nothing but the panel and Home
Assistant.

The work-signal scorer (agent output tokens, git commits, issues shipped) is
not published, because mine is welded to my own machine, my own repo paths and
my own issue board. `docs/01-design-and-feasibility.md` §3 describes exactly
what it has to do and the three rules it must not break, which is the part that
generalises. The 200 lines of PowerShell that do it for me would not run for
you.

Practical consequence: **out of the box this levels much more slowly than the
curve in docs/02 suggests**, because that curve assumes five sources and you
have two. Either wire up your own sources or raise the panel/game caps.

## It inherits the failure mode of whatever publishes its signals

If you point the decay pause gates and the powers at sensors published by an
agent on your PC, then when that agent dies every counter goes `unavailable` at
once. Several unrelated things failing simultaneously is the signature.

A pet showing `--` looks *broken*, where a blank tile just looks idle. Give the
sprite an explicit "napping, no data" state so the degraded case reads as
intentional. I have not built that yet.

## Scripted edits to a 14,000-line YAML file will go wrong

Mine went wrong twice. Both times the fastest fix was `git restore` and doing
it again more carefully, not debugging the mess.

If you are letting an agent edit your panel config: commit before it starts,
keep the diffs small, and treat `git restore` as the first thing you reach for
rather than the last. This is in `agent/SEED-PROMPT.md` as a rule for exactly
that reason.

## Hardware

This is a **D1**: display only. No SCD41 or SGP40 air-quality sensors, no
SX1262 LoRa. On the D1S and D1Pro those sensors hang off the RP2040 rather than
the ESP32-S3, and reaching them means flashing ESPHome to both chips bridged
with `packet_transport`. Nothing here needs that, and the RP2040 keeps its
stock firmware.

Consequence: **there is no sound.** The buzzer is on the RP2040 too. A beeping
pet would violate the cannot-interrupt rail anyway, so I have not missed it.

## Things I decided not to build, which you may want

No streaks, no death, no level loss, no sub-1.0 multiplier, no notifications,
no sad text. Every one of those is a deliberate absence and
`docs/01-design-and-feasibility.md` §4 explains each.

If you add them back, you are building a different thing, and it is the thing I
was specifically trying not to build.
