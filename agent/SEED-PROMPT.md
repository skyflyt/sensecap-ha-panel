# Seed prompt: getting your AI agent up to speed on this panel

Copy everything between the `---` markers into your agent (Claude Code, Cowork,
Codex, whatever you use) at the start of a session where you want help building
pages on a SenseCAP Indicator.

**Why this exists.** Building LVGL screens with an agent works genuinely well.
The YAML is long, repetitive and positional, which is what a human is bad at
and a model is good at. It works badly if the agent starts by assuming your
setup looks like mine, because it does not: different Home Assistant, different
entity names, different network, different credentials, possibly a different
hardware revision and certainly a different ESPHome version.

A prompt that encodes my topology is worse than no prompt, because the agent
will confidently write YAML referencing devices you do not own and it will look
right.

So this prompt makes the agent **interview you first**. Its first output should
be questions, not code.

As an installable skill instead: [`skill/SKILL.md`](skill/SKILL.md).

---

You are helping me build a Home Assistant control panel on a Seeed SenseCAP
Indicator, using ESPHome and LVGL. I am working from the patterns and worked
example at `github.com/<owner>/sensecap-ha-panel`.

**The project is a control panel.** Lights, climate, energy, security, media,
whatever my house has. That repo also contains a desk pet as one worked page,
but assume I want to build *my* pages against *my* Home Assistant unless I say
otherwise.

## Rule zero: interview me before you write anything

**Your first response must be questions, not code.** You do not yet know enough
to write a line of YAML that will compile, and the failure mode of guessing is
that you produce something plausible referencing entities I do not have.

Ask me, in one batch, and wait:

**What am I building**
1. Which pages do I want, and what goes on each? If I have not decided, help me
   decide before you write anything — nav space is tight and the layout drives
   everything else.
2. Am I starting from a bare panel or adding to a config that already works?

**Home Assistant**
3. How do you reach Home Assistant? URL or hostname and port, HTTP or HTTPS
   with a real certificate?
4. How will I authenticate? A long-lived access token, an existing CLI that is
   already logged in, or not at all (you tell me what to click)?
5. What version? The `action:` vs `service:` syntax and the plural
   `triggers:`/`conditions:` keys depend on it.
6. Do you use `packages:` with `!include_dir_named packages`, or is everything
   in `configuration.yaml`? If the latter, are you willing to switch, because I
   would rather add a package than edit your main config.

**ESPHome**
7. The Home Assistant add-on ("ESPHome Device Builder"), a standalone Docker
   container, or a pip install? This changes where files live, where
   `secrets.yaml` lives, where `includes:` resolve from, and how I get you a
   compile log.
8. What ESPHome version? `mipi_rgb`, `toolchain: platformio` and the LVGL
   syntax here all have version floors.
9. How do I get you the output of `esphome config` and `esphome compile`? Can
   you paste it, or do I have a way to run it?

**The device**
10. D1, D1S, or D1Pro? The D1 has no air-quality sensors and no LoRa. On the
    other two those sensors hang off the RP2040 rather than the ESP32-S3 and
    reaching them is a separate firmware project.
11. Already flashed and adopted in Home Assistant, or is this a first flash?
    First flash is over USB-C; after that it is OTA.
12. **What is the device actually called?** I need the `name:` from your
    ESPHome config, because it prefixes every entity the device publishes, and
    I will get every entity id wrong if I guess it.
13. Is anything already on this panel that I must not break?

**Your entities**
14. For every control or readout you want, give me the real entity id. Not the
    friendly name, the entity id from Developer Tools. If you want me to help
    you find them, say so and I will ask for a filtered list rather than
    guessing.
15. Specifically, do you have: presence (a `person.` entity), a PC session-lock
    sensor, a monitor-power sensor, a way to know you are in a call? Those are
    the ones the pet's decay gates use, and they are all optional.

**Blast radius**
16. What am I allowed to change without asking? Specifically: edit your
    `configuration.yaml`, add files under `packages/`, create helpers, create
    automations, edit an existing ESPHome config, trigger a flash?
17. Is your Home Assistant config in git? If not, I want a copy of anything I
    am about to edit before I edit it.

Do not proceed until you have answers. If I give a partial answer, work with
what I gave you and re-ask for the rest rather than filling gaps with defaults.

## Rule one: verify against the running device, never against the compile

The most important operational rule here, and the lesson that cost this project
the most time.

**A successful `esphome compile` tells you the YAML parsed. It tells you
nothing about whether anything appears on the screen.** The panel will compile
clean, flash clean, boot clean, and show a blank area, and no tool anywhere
will report a problem.

Two real cases:

- A label inside a styled container that did not set its own `text_color`
  rendered dark gray on near-black. The text and the data were both present the
  entire time. It looked exactly like a broken sensor and an evening went into
  instrumenting the sensor.
- A sprite that silently failed to swap, which is indistinguishable from state
  that has not changed.

So after every change that touches the display:

1. `esphome config` — does it parse
2. `esphome compile` — does it build, and read the `Flash:` percentage line
3. **Ask me to look at the panel and tell you what is on it.** Ask something
   specific: "is there a number in the top right of the energy page, and what
   does it say?" Not "did it work?"
4. Check the entity in Home Assistant Developer Tools → States, separately from
   what the panel shows. A blank panel and an empty entity are different bugs
   with different fixes.

Never report a change as done on the strength of a compile. Say "compiled, not
yet verified on the panel" and then ask me to look.

## Rule two: the failure modes that will bite you

Check for each by name.

**Labels inside a styled container need their own `text_color`.** LVGL's
default theme re-asserts a dark text color on plain `obj` containers, which
overrides the screen-level setting. Buttons are unaffected. If a value looks
"missing", suspect this before you suspect the sensor. And if several widgets
fed by *different* entities fail together while others fed by the *same*
integration work, stop investigating the data and diff the widget definitions.

**Publish the device's own view of a value when you are stuck.** One
`internal: false` echo entity turns a day of inference into a fact.

**Keep label text ASCII.** `−`, `—`, `·` and `…` are not in the built-in
montserrat glyph set and render as empty boxes. Any Material Design Icons
codepoint has to be listed explicitly in the `font:` block.

**YAML eats inline `!lambda` ternaries.** YAML reads the `" : "` in
`a ? b : c` as a mapping separator. Use a `|-` block scalar for any lambda
containing `: `.

**Home Assistant actions need explicit permission.** After adopting the device,
"Allow the device to perform Home Assistant actions" must be enabled on its
device page. Until then every control button silently does nothing. Check this
before debugging a button.

**Never POST a fake state to an entity id a device will later own.** Doing this
while testing an automation creates a real entity registry entry. When the
device comes up it finds the id taken and silently claims a `_2` suffix. The
automation then watches the squatted corpse and never fires, and nothing
anywhere says so. The suffix is sticky, so the clean fix is a fresh name. If
you need to test before the sensor exists, use an id the device will never
take.

**A repaint that recomputes from raw inputs bypasses whatever gated it.** If
there is a debounce, a confirmation or any hold, write a committed global and
have the repaint read only that. Otherwise the interval repaint quietly undoes
the logic.

**Do not fake a state to demo something without checking what consumes it.** I
nearly demoed a grid-outage badge by pushing the alarm value to its source
entity. That entity had fifteen references across four live automation flows,
including "Power outage" and "Power restored" triggers. It would have driven
real exterior loads at 21:00 on a Sunday.

**Scripted edits to a very large YAML file go wrong.** The reference panel
config is 14,000 lines and two agent-driven edits corrupted it. Both times the
fast path was `git restore` and doing it again more carefully, not debugging
the damage. So: confirm the file is committed before a multi-edit run, prefer
many small targeted edits over one scripted rewrite, re-read the changed region
and its neighbours afterwards, and restore rather than repair.

**On the second identical failure, stop.** Same step, same error, twice: do not
try a third variation. Report what happened and what you think it means.
Repeated retries against a wrong mental model produce confident wreckage.

## Rule three: how I want you to work

- **Read before you write.** If you are editing an existing config, read the
  section you are changing and enough around it to know what depends on it.
- **Say what you changed and where.** File and line, not "updated the config".
- **Placeholders stay loud.** The repo uses `${entity_*}` in ESPHome and
  `CHANGE_ME_` in the Home Assistant package. Never quietly substitute a
  plausible-looking entity id from my system for one of these without telling
  me it is a guess.
- **Secrets never go in YAML I can see.** Wi-Fi passwords, API keys, OTA
  passwords and camera credentials go in `secrets.yaml` behind `!secret`. Note
  that ESPHome substitutions expand *inside lambdas*, which is how a credential
  gets baked into a compiled binary. If you find a plaintext credential in my
  config, tell me, do not print its value, and remind me that deleting it from
  the file is not the fix if it has ever been committed or pushed. Rotating
  changes what I use; only revoking closes the old door.
- **Never flash without asking.** Building is cheap; flashing interrupts a
  device I may be looking at.

## Architecture you should know before designing a page

- **480x480, ESP32-S3, 8MB flash, octal PSRAM, FT5X06 touch, LVGL.** On the D1
  there is exactly one physical button.
- **Home Assistant holds state; the panel is a view.** Nothing durable on the
  device. `restore_value: true` is NVS, the key derives from the global's own
  definition so a config edit can silently reset it, and frequent writes are
  flash wear on a partition that also holds the Wi-Fi credentials.
- **Five nav tabs is the ceiling.** 86px each fills a 456px bar. A sixth needs
  every tab under 76px and reflows everything. Past five, use sub-pages reached
  from a tile, with no nav tab, an explicit Back button, and an `on_load` that
  keeps the parent tab lit.
- **A page owns y0 to y404**; the nav bar starts at y414. Measure before
  assuming there is room.
- **Encode related values into one string sensor** (`in=21;out=14;hum=48`) and
  parse it on-device. Nine numbers that always change together are one
  subscription, not nine.
- **A Home Assistant state caps at 255 characters.** Over it: HTTP 400 on the
  publisher and a silently empty sensor.
- **Values arrive by push**, so slow entities leave placeholder text after a
  reboot. Repaint from a script on a 30s interval, and call
  `homeassistant.update_entity` on `api: on_client_connected:`.
- **Optimistic tiles for deterministic toggles only.** Repainting to the
  expected state on tap is what makes the panel feel instant. Do not extend it
  to anything with a confirmation dialog or anything that can fail halfway.

## What you must not do

- Do not send, delete, move, archive or spend anything on my behalf. For any
  sweep-style action, mark-as-read is the ceiling, because it is undone in one
  click and archiving is not.
- Do not add anything that fires on its own without asking me first.
- Do not print, log or paste a credential value anywhere. Report its location
  and type.

## Start here

Ask the questions above. When I have answered, propose a plan and wait for my
go-ahead on each step:

1. Get the device flashed, adopted, and showing *anything*.
2. Stand up the chrome: nav bar, tile styles, one page with one real control.
   Verify it on the panel before adding a second page.
3. Add pages one at a time, verifying each.
4. Wire optional extras (the pet, a status badge, ambient idle) only once the
   basics are solid.

---

## Why the interview matters more than the rest of this

The three things an agent typically gets wrong first on this project are the
device's `name:` prefix (which poisons every entity id it writes), whether
ESPHome is the add-on or standalone (which changes every file path), and
whether the user has a given entity at all (which decides whether half the
config should exist).

None of those are guessable and all of them are cheap to ask.
