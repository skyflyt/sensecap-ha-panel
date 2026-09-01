---
name: sensecap-ha-panel
description: Build, adapt or debug a Home Assistant control panel on a Seeed SenseCAP Indicator - ESPHome + LVGL pages for lights, climate, energy, security and media, plus the optional desk pet. Use when the user mentions the SenseCAP Indicator, an ESPHome LVGL touch panel, a Home Assistant wall or desk panel, the desk pet, or asks for help getting the sensecap-ha-panel repo running on their own hardware. Always interviews the user about their setup before writing any YAML, because entity ids, ESPHome flavour and device name are never guessable.
---

# SenseCAP Indicator: Home Assistant control panel

Helps a user build a Home Assistant control panel on a Seeed SenseCAP
Indicator: ESPHome driving LVGL, pages for whatever their house has, live data
pushed from Home Assistant.

The `sensecap-ha-panel` repo also carries a desk pet as one complete worked
page. **Assume the user wants to build THEIR pages against THEIR Home
Assistant** unless they say otherwise; the pet is one thing they might add, not
the point of the project.

**The single most important thing about this skill: the user's setup is not the
author's setup, and almost nothing about it is guessable.** Entity ids, the
device `name:` prefix, whether ESPHome is the HA add-on or standalone, the HA
version, which sensors exist at all. Getting any of those wrong produces YAML
that is confident, plausible and completely useless.

So the workflow is: **interview, then plan, then build one verified step at a
time.**

## Step 1 — Interview. Do this before writing any YAML.

Ask all of it in one batch and wait. Do not fill gaps with defaults; a
placeholder the user can see beats a guess they cannot.

**Home Assistant**
- URL/host and port; HTTP or HTTPS with a valid certificate?
- How will the agent authenticate? Long-lived access token, an already-logged-in
  CLI, or not at all (the agent gives instructions, the user clicks)?
- HA version. The `action:` vs `service:` syntax and the plural
  `triggers:`/`conditions:` keys depend on it.
- Does the user's `configuration.yaml` already have
  `packages: !include_dir_named packages`? If not, ask before adding it.

**ESPHome**
- Add-on ("ESPHome Device Builder"), standalone Docker, or pip? Changes where
  `secrets.yaml` lives, where includes resolve from, and how logs are obtained.
- ESPHome version. `mipi_rgb`, `toolchain: platformio` and the LVGL syntax all
  have floors.
- How will the agent see `esphome config` / `esphome compile` output?

**Device**
- D1, D1S or D1Pro? The D1 has no air-quality sensors and no LoRa; on the other
  two those sensors are behind the RP2040 and need a separate bridged firmware.
- Already flashed and adopted, or first flash? First flash is USB-C, then OTA.
- **The exact `name:` from their ESPHome config.** It prefixes every published
  entity id. Guessing it makes every automation wrong.
- Anything already on the panel that must not break.

**What are they building** — which pages, what goes on each. If undecided,
settle that before writing YAML; nav space is tight and layout drives
everything. Bare panel, or adding to a working config?

**Entities** — ask for the real entity id (from Developer Tools, not the
friendly name) for every control and readout they want. For the pet's optional
gates specifically: presence (a `person.` entity), PC session lock, monitor
power, an in-a-call signal, an incident signal, lights safe to turn off, a
media player safe to pause. All optional. "None" is a fine answer and leaves
the placeholder inert.

**Blast radius**
- What may be changed without asking: `configuration.yaml`, files under
  `packages/`, helpers, automations, an existing ESPHome config, triggering a
  flash?
- Is the HA config in git? If not, copy anything before editing it.

## Step 2 — Plan, in this order

1. Device flashed, adopted, showing anything at all.
2. The chrome: nav bar, tile styles, one page with one real control. Verify on
   the panel before adding a second page.
3. Pages one at a time, verifying each.
4. Optional extras (the pet, a status badge, ambient idle) once the basics are
   solid. If adding the pet: install its HA package, seed the settings, confirm
   `sensor.indicator_pet` has a real state in Developer Tools, then add the
   page and the main-page tile.

Get a go-ahead per step. Never flash without asking; building is cheap,
flashing interrupts a device the user may be watching.

## Step 3 — Verify against the running device, never against the compile

**A clean `esphome compile` means the YAML parsed. It says nothing about
whether anything is on the screen.** The panel will compile, flash, boot and
show a blank area with no tool reporting anything.

After any change touching the display:

1. `esphome config`
2. `esphome compile`, and read the `Flash: [====] NN.N%` line
3. **Ask the user a specific question about what is on the panel.** "Is there a
   number in the top-right of the pet page, and what does it say?" Never "did
   that work?"
4. Check the entity separately in Developer Tools → States. A blank panel and
   an empty entity are different bugs.

Report state honestly: "compiled, not yet verified on the panel".

## Known failure modes — check these by name

**Dark text on a dark tile.** A label inside a styled `obj` container that does
not set its own `text_color` inherits LVGL's default dark theme color, which
overrides the screen-level `text_color`. Buttons are unaffected. It looks
exactly like a broken sensor. Suspect this before suspecting the data.

**Non-ASCII label text.** `−`, `—`, `·`, `…` are not in the built-in montserrat
glyph set and render as empty boxes. MDI codepoints must be listed in the
`font:` block.

**Entity-id squatting.** POSTing a fake state to an id a device will later own
creates a real registry entry. The device then silently claims a `_2` suffix,
and any automation watching the original never fires. The suffix is sticky, so
the fix is a fresh name. Never fake a state on an id a device will take.

**Large-file edits.** The reference config is 14,000 lines. Two scripted edits
corrupted it and both times `git restore` plus a more careful second attempt
beat debugging the damage. Confirm the file is committed before a multi-edit
run; prefer many small targeted edits; re-read the changed region and its
neighbours afterwards; restore rather than repair.

**HA actions not enabled.** After adopting the device, "Allow the device to
perform Home Assistant actions" must be turned on in its device page or every
button silently does nothing. Check this before debugging a button.

**A repaint that recomputes from raw inputs bypasses whatever gated it.** If
there is a debounce, a hold or a confirmation, write a committed global and
have the repaint read only that. Otherwise the interval repaint quietly undoes
the logic.

**Do not fake a state to demo something without checking what consumes it.**
A grid-badge demo nearly pushed an alarm value to an entity that had fifteen
references across four live automation flows, including "Power outage" and
"Power restored" triggers. It would have driven real exterior loads.

**Two strikes and stop.** Same step, same error, twice: stop and report. Do not
try a third variation.

## Architecture facts worth knowing before designing a page

- 480x480, ESP32-S3, 8MB flash, octal PSRAM, FT5X06 touch, LVGL, one physical
  button on the D1.
- **HA holds state, the panel is a view.** Nothing durable on the device.
  `restore_value: true` is NVS: the key derives from the global's definition so
  a config edit can silently reset it, and frequent writes are flash wear on a
  partition that also holds Wi-Fi credentials.
- **Encode related values into one string sensor** (`xp=418;lvl=3;pct=41;...`)
  and parse it on-device. Nine numbers that always change together are one
  subscription, not nine.
- **HA states cap at 255 characters.** Over it: HTTP 400 on the publisher and a
  silently empty sensor.
- **Values arrive by push**, so slow entities leave placeholder text after a
  reboot. Use `homeassistant.update_entity` on `api: on_client_connected:`.
- Nav space is tight: five tabs at 86px fills a 456px bar. A sixth needs every
  tab under 76px and reflows everything. Past five, use sub-pages off a tile
  with no nav tab, an explicit Back button, and an `on_load` that keeps the
  parent tab lit. A page owns y0..y404; the nav bar starts at y414.
- **Optimistic tiles for deterministic toggles only.** Repainting to the
  expected state on tap is what makes the panel feel instant. Never for
  anything with a confirmation dialog or anything that can fail halfway.

## Hard limits

- Never send, delete, move, archive or spend on the user's behalf.
  Mark-as-read is the ceiling for any sweep-style action, because it is undone
  in one click and archiving is not.
- Never add a power that fires on its own.
- Never add notifications, sounds, off-page badges, streaks, or guilt-tripping
  copy. Those absences are deliberate design, not oversights.
- Never print, log or paste a credential value. Report its location and type.
  If one is found in plaintext, say so, and note that deleting it from the file
  is not the fix if it has ever been committed. Rotating changes what is used;
  only revoking closes the old door.
- ESPHome substitutions expand **inside lambdas**, which is how a credential
  ends up baked into a binary. Credentials go in `secrets.yaml` behind
  `!secret`.

## Placeholders in this repo

Two different schemes, because Home Assistant has no substitution mechanism:

- **ESPHome package:** four `${entity_*}` substitutions, declared in
  `example-device.yaml`. All optional, all guarded by `has_state()`.
- **Home Assistant package:** about thirteen literal `CHANGE_ME_` entity ids.
  Filling in the ESPHome substitutions does not fill these in. Grep the file.

Both are deliberately loud. Never silently replace one with a
plausible-looking id from the user's system without saying it is a guess.
