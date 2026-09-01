# Building a Home Assistant control panel on the SenseCAP Indicator

This is the main document. It is what I wish had existed when I started.

The Indicator is a $60 4" touchscreen with an ESP32-S3 behind it. Flash ESPHome
onto it, drive LVGL, point it at Home Assistant, and you have a wall or desk
panel that does whatever your house does. Mine runs five pages and has been on
the desk since August 2026.

Everything below is what I learned making that work. Some of it cost an evening
each.

---

## 1. The architecture, in one page

**Home Assistant holds state. The panel is a view.**

Nothing durable lives on the device. Three reasons and they all bite:

- **Reflashing is routine.** A cold ESP-IDF build takes about 8m30s and I do it
  whenever I move a widget. Anything living only in the image is one config
  change away from gone.
- **`restore_value: true` is NVS, and NVS is not a database.** It survives a
  reboot, but the key derives from the global's own definition, so editing your
  config can silently reset the value. And frequent writes are flash wear on a
  partition that also holds your Wi-Fi credentials. Every global in this repo
  is `restore_value: false`.
- **The interesting data is not on the ESP32 anyway.** It cannot reach your
  git repos, your mail, or your solar inverter. State belongs next to whatever
  produces it.

So the panel subscribes to Home Assistant entities, paints them, and sends
actions back. The only thing it owns is what is on screen right now.

### Pages, and the nav-bar arithmetic

Five nav tabs at 86px wide is 430px inside a 456px inner bar, spread
`SPACE_EVENLY`. **A sixth tab needs every tab at 76px or less**, which reflows
the whole bar and shrinks four labels that are already at `montserrat_12`.

So five is the practical ceiling for top-level pages, and anything past that is
a **sub-page**: no nav tab, reached from a tile on a parent page, with an
explicit Back button and an `on_load` that keeps the parent tab lit. That is
how the desk pet, its settings, its power list and all seven of its games fit
without touching the nav bar.

Vertical budget: the nav bar starts at y414, so a page has y0 to y404. Measure
before you assume you have room. I once wrote a design note saying a new badge
would shift everything down 40px; measuring the page showed it had **10px of
slack** and a 40px shift would have pushed the battery ring under the nav bar.
The badge replaced the page heading instead, which was better anyway because
the nav tab already said what page you were on.

### One encoded sensor beats nine subscriptions

The panel pays a fixed cost per subscribed entity: RAM, plus an API round trip
on every push. Nine slow-moving numbers that always change together are one
fact, not nine.

So Home Assistant publishes a single string:

```
xp=418;lvl=3;pct=41;hun=12;rdy=0;stg=2;nxt=585;spi=88;on=1
```

and the panel parses it on-device with two small C++ helpers
(`esphome/desk_pet_helpers.h`). One subscription, one push, one repaint.

Two things about this:

- **A Home Assistant state caps at 255 characters.** Go over and the publisher
  logs an HTTP 400 and the sensor sits silently empty. I lost time to this on a
  different sensor where nine 30-character rows blew straight past it. Use
  short keys and short values.
- **Absent and zero must stay distinguishable.** The int parser takes a
  `fallback` argument rather than returning 0, because a panel that shows `0`
  when it means "not reported yet" is lying. It also handles a leading `-`,
  because a digits-only parser reads `mins=-14` as absent and then shows a
  countdown that never moves.

### Values arrive by push, so the first paint is empty

Home Assistant pushes on change. A slow-moving entity may not push again for
hours, so after a reboot those labels sit on their placeholder text.

Measured on my panel: in the 14 seconds after boot, exactly one subscription
received a value — the one that gets repushed every second. Everything slow
stayed empty.

Two fixes, and you want both:

```yaml
api:
  on_client_connected:
    - delay: 5s
    - homeassistant.action:
        action: homeassistant.update_entity
        data:
          entity_id: >-
            sensor.slow_one, sensor.slow_two
```

and **repaint everything from a script on an interval**, not only from each
sensor's `on_value`:

```yaml
interval:
  - interval: 30s
    then:
      - script.execute: refresh_env
      - script.execute: refresh_cast
```

The interval repaint is cheap (a handful of label writes) and it makes the
panel independent of *when* a value arrived. `has_state()` guards mean an
entity that genuinely never arrives keeps its placeholder rather than showing a
zero.

Fair warning on `update_entity`: it does not always help. An unchanged value
re-emits as `state_reported`, not `state_changed`, and the ESPHome integration
ignores the former. It closes the after-boot gap; it is not a general "make it
refresh" button.

---

## 2. The traps

These are the ones that cost real time. Every one of them is silent.

### A label inside a styled container renders dark-on-dark

**This is the worst one, and it is completely convincing as a data bug.**

Symptom: on my Climate and Energy pages, several values appeared blank for a
whole afternoon. Not dashes. Nothing at all, while the caption above each one
rendered perfectly.

Three diagnoses were wrong before the right one:

1. *Wrong entity ids, or disabled sensors.* No. Every entity was queried
   directly against Home Assistant and all had live numeric values.
2. *HA never sends initial state.* Plausible, and the device log did show a
   14.7s gap between boot and the first `Got state`. But forcing a refresh with
   `on_client_connected` changed nothing.
3. *Values lost at boot.* Also no.

What settled it was **making the device report what it held**: I temporarily
published the five sensors back to HA as `Echo …` entities, and every one
matched HA exactly. The data was never the problem.

The real tell was in the config all along. **Every invisible label lacked
`text_color`. Every visible one had it.** The top-level `text_color` applies to
the screen; LVGL's default theme then re-asserts a dark text color inside
plain `obj` containers. Button labels inherit correctly, which is exactly why
one page looked fine while another looked broken, and why comparing them was so
confusing.

Set `text_color` on the style itself and it cannot recur:

```yaml
style_definitions:
  - id: tile
    bg_color: 0x1E2228
    text_color: 0xE8EAED   # ⚠️ DO NOT DELETE
```

**Two lessons worth more than the fix.** When several widgets fed by
*different* entities fail together while others fed by the *same* integration
work, stop investigating the data and diff the widget definitions. And publish
the device's own view of a value early: one `internal: false` echo entity turns
a day of inference into a fact.

### A clean compile is not evidence that anything renders

Following directly from the above. The panel will compile, flash, boot, and
show you a blank area, and no tool anywhere reports a problem.

So after any change that touches the display: `esphome config`, then
`esphome compile`, then **look at the panel**. And when you ask someone else to
check, ask a specific question. "Is there a number in the top-right and what
does it say" gets an answer. "Did it work" does not.

### Keep label text ASCII

`U+2212 MINUS SIGN` is not in the built-in montserrat glyph set. My climate
page's decrement button rendered as an empty box until it became an ASCII
hyphen. Same for `—`, `·` and `…`. Any Material Design Icons codepoint must be
listed explicitly in your `font:` block.

### YAML eats inline `!lambda` ternaries

```yaml
text_color: !lambda return x ? "a" : "b";     # fails to parse
```

YAML reads the `" : "` as a mapping separator. Use a `|-` block scalar for any
lambda containing `: `.

### Per-component log levels cannot exceed the global level

`logs: {homeassistant.sensor: DEBUG}` under `level: INFO` fails validation
outright. Set `level: DEBUG` globally and pin the noisy components back to
INFO.

### `board:` is still required

On ESPHome 2025.x and earlier, `board:` is required even when `variant:` is
given. Setting `board: esp32-s3-devkitc-1` explicitly means the config builds
on old and new versions.

### Home Assistant actions need explicit permission

After adopting the device, open its page in HA and enable **"Allow the device
to perform Home Assistant actions"**. Without it every control button silently
does nothing. No error, no log line. Check this before debugging a button.

### Never POST a fake state to an entity id a device will later own

I was testing an automation before the device published its sensor, so I pushed
a fake state to that id via `POST /api/states/...`.

That creates a real **entity registry** entry. When the device next booted it
found the id taken and silently claimed `..._2` instead. The automation went on
watching the squatted corpse, which never changes again, and simply never
fired. Nothing errors. Nothing logs. The feature is just dead.

The `_2` suffix is sticky in the registry, so deleting the orphan state does
not hand the id back. The clean fix is to rename the sensor on the device.

Test against a scratch id, or against the real entity after it exists.

### Verify the file you think you are compiling

Uploading to a Home Assistant host over SSH, `scp` runs as your user and cannot
overwrite a root-owned file left in `/tmp` by an earlier session. The copy
fails, and a following `sudo cp /tmp/... /config/esphome/...` cheerfully
installs the *old* file. I hit this once and spent a while wondering why my
change had no effect.

`md5sum` the remote config against the local one before compiling. It is the
only step that catches it.

Also: the HA SSH add-on has no SFTP subsystem, so plain `scp` fails with
`subsystem request failed`. Use `scp -O`, one file per invocation. Multi-source
`scp -O` silently dropped files and created others named after the literal
Windows path.

---

## 3. Latency: where the seconds go

My original complaint was about five seconds between tapping a control and the
screen agreeing. Measuring the chain was more useful than any amount of
guessing.

If your panel talks to a PC through a bridge that spawns a shell per poll, the
cost is dominated by process startup. I measured **~870ms per spawn** before
any script ran: ~170ms process start, plus ~700ms loading the shell profile.
Three sensors each did their own ~1.2s UI walk. Demanded ~3.4 polls/sec against
~1 poll/sec of capacity. **The queue is the latency**, and any interval shorter
than the cycle time is aspirational.

Four fixes, in order of effect:

1. **Skip the profile for non-interactive spawns.** 870ms → ~540ms. The
   remaining ~330ms was the cloud-sync filter driver probing the profile paths,
   which is not fixable by editing content.
2. **Cache one expensive walk and feed several sensors from it.** One walk on a
   4-second TTL, written atomically as temp-plus-rename JSON. One sensor went
   1216ms → 48ms.
3. **Trim the roster.** A sensor for a thing I had retired was still burning a
   3-second slot. Slow-moving sensors moved to 15s.
4. **Optimistic tiles.** Repaint to the expected state the instant a control is
   tapped; the sensor confirms or corrects within a poll. **Deterministic
   toggles only.** Do not extend this to anything with a confirmation dialog or
   anything that can fail halfway, because then the panel is confidently
   showing you a state that never happened.

That took action-to-confirm from a uniform 8-12s to 2-10s, and made the touched
tile itself instant.

Then I removed the floor entirely by replacing per-poll spawns with **one warm
long-lived process** calling the same scripts in-process on staggered cadences
and POSTing to HA over REST. Action-to-confirm: **1.8-2.9s**.

Two things worth knowing if you do that:

- **Never leave the old publisher publishing the same entity.** Two writers on
  one entity is the exact bug the change was meant to remove. And retained MQTT
  values can reassert after a restart, so the daemon needs a keepalive that
  re-posts over them. That also covers HA restarts, which drop REST-set states.
- **Give it a heartbeat file and a log.** If every counter goes stale at once,
  you want to check one process rather than fifteen sensors.

---

## 4. A worked example: the grid/islanding badge

This is the pattern I would most want someone to copy, because every decision
in it came from a real event rather than from a datasheet. See
[`esphome/patterns/debounced-state-badge.yaml`](../esphome/patterns/debounced-state-badge.yaml)
for the code.

There was a grid outage. Afterwards I pulled the history rather than designing
from the spec.

**Pick the entity that actually changes during the event.** Two entities looked
like the obvious choice and both were green for the entire outage. One had
changed state exactly once in the whole window queried, and that was an
integration dropping to `unavailable`. **Wire either of those to a badge and
you have an indicator that cannot go red during the event it exists for.** Go
and read the history of your candidate entity across a real occurrence before
you trust it.

**Debounce, or the badge lies twice per event.** The outage contained two
sub-15-second transients. Without a hold, the badge flashes red for five
seconds on a Sunday morning and teaches you to ignore it. Require the state to
hold **60 seconds** before the badge moves: a `mode: restart` script with a
leading `delay: 60s` is the whole mechanism.

**Paint from a committed global, not from the live sensor.** This is the part
people get wrong. The 30-second repaint interval also calls the badge painter.
If that painter reads the text sensor directly, it bypasses the debounce
entirely and shows every transient anyway. So the debounce writes a committed
global (0 unknown / 1 normal / 2 alarm) and the painter reads only that.

The same rule applies anywhere a repaint and a gate coexist: **a repaint that
recomputes from raw inputs bypasses whatever logic was supposed to gate it.**

**Put the word on the label, not just the color.** This panel gets read from
across a room. Color alone fails that, and it fails color-blind users
entirely.

**Gray for the boring case, not green.** On-grid is true 99.9% of the time and
a green light that is always green is decoration.

**Do not fake a state to test it.** The obvious demo was to POST the alarm
value to that entity. I checked what else consumed it first and found fifteen
references across four live automation flows, including triggers named "Power
outage" and "Power restored", none disabled. Faking the value would have driven
real loads at 21:00 on a Sunday and then fired the restore path when the next
poll corrected it. **A demo that drives real hardware is not a demo.**

The honest consequence: my alarm rendering is still unverified, because I have
not had a second outage. That is in
[LIMITATIONS.md](LIMITATIONS.md) rather than glossed over.

**Do not reimplement a number that already exists.** My first draft
back-solved a battery capacity constant and divided by live house load. Home
Assistant already had a runtime-remaining entity, already on a dashboard, and
when I checked it against what I remembered from the outage it matched. I
caught that one mid-compile and stopped the build.

---

## 5. Building this with an agent

The LVGL YAML is long, repetitive and positional. A game board is 81
near-identical widgets with different coordinates. That is exactly what a human
is bad at and a model is good at, and it is the main reason this panel has as
many pages as it does.

The prompt is in [`../agent/SEED-PROMPT.md`](../agent/SEED-PROMPT.md) and it is
written to make the agent **interview you before it writes anything**, because
your entity ids, your device name and your ESPHome flavour are not guessable
and an agent that assumes mine will write confident YAML against devices you do
not own.

Beyond the traps in §2, two working rules:

**Verify against the running device, not the build output.** Stated already,
repeated here because it is the one that matters.

**On the second identical failure, stop.** If the same step fails twice with
the same error, a third variation will not help. Something in the mental model
is wrong and more attempts produce confident wreckage.

And one about editing: my panel config is 14,000 lines, and two agent-driven
scripted edits corrupted it. Both times the fastest fix was `git restore` and
doing it again more carefully, not debugging the damage. Commit before the
agent starts, keep the diffs small, and reach for restore first rather than
last.

### A pattern-matching trap specific to agents reading UIs

If you are driving a chat application through UI automation, **never
pattern-match its element names loosely, because the whole transcript is in the
accessibility tree.** I broadened a detector to `^Working\b` and it reported
success instantly: it had matched a text node containing the words "Working →
NeedsYou" from the conversation *about building that very feature*.

Any pattern loose enough to catch an unknown label is loose enough to match the
chat discussing it. Two rules follow: filter to `Button` (a control is a
control, transcript text is not), and anchor the match. When the real label is
unknown, capture the tree, log candidates and stay narrow. A detector that
misses is recoverable; one that false-positives poisons persisted state and has
to be reset by hand.

---

## 6. What is in this repo, and what is not

**In:** the panel patterns in `esphome/patterns/`, this guide, and the desk pet
as a complete worked page with its Home Assistant package, its sprites and its
seven games.

**Not in:** my own pages. My lights, climate, energy, security and work pages
are welded to my entity ids, my rooms and my hardware, and publishing them
would be publishing my house rather than a project. The patterns are the part
that transfers; the page that uses them is five minutes of your own layout.

The pet is in full because it is self-contained, it is the fun one, and it is a
complete example of every pattern above working together: encoded state,
committed values, an interval repaint, sub-pages off a tile, and a lot of LVGL.
