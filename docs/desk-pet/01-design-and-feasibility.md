# Design and feasibility

Why the pet is built the way it is. Read this before you change anything
structural, because most of the decisions here were made to avoid a specific
failure that had already happened once.

---

## 1. What the panel can actually do

Established from a working config, not from the datasheet.

| Fact | |
|---|---|
| ESP32-S3, 8MB flash, octal PSRAM at 80MHz, ESP-IDF via PlatformIO | |
| `mipi_rgb` / `SEEED-INDICATOR-D1`, FT5X06 touch | |
| 480x480, from the model preset rather than anything in the YAML | |
| One physical input: the side button on GPIO38 | |
| A 456x256 RGB565 frame already decodes into PSRAM without complaint | |

**There was no room for a sixth nav tab.** Five tabs at 86px is 430px inside a
456px inner width. A sixth needs every tab at 76px or less, which reflows the
whole bar and shrinks four labels that are already at `montserrat_12`. Not
worth it for a toy.

So the pet is a **sub-page**, reached from a tile on the main page. It inherits
the persistent nav bar and needs an explicit Back button. That is the pattern
this repo assumes; `main-page-tile.snippet.yaml` is the tile.

The pet page gets y0 to y404 to itself, above the nav bar. That is plenty.

### Sprites: what fits

ESPHome stores RGB565 at **2 bytes per pixel with `transparency: chroma_key`,
and 3 bytes per pixel with `transparency: alpha_channel`**. The alpha is a
separate plane, not free. Two earlier drafts of my own design costed everything
at a flat 2 B/px while assuming transparency, which understated every figure by
50%.

| Sprite | chroma_key | alpha_channel |
|---|---|---|
| 48x48 | 4,608 B | 6,912 B |
| **64x64** | **8,192 B** | 12,288 B |
| 96x96 | 18,432 B | 27,648 B |

**Those numbers are arithmetic, not measurement.** The number that actually
matters is how much of the OTA app partition your current binary already uses,
and `esphome compile` prints it:

```
Flash: [====      ] 41.2% (used X bytes from Y bytes)
```

On 8MB with OTA there are two app slots and the image has to fit one. Until you
read that line, any sprite budget is a guess wearing a table. Mine is still
unmeasured, which is why it appears in [LIMITATIONS.md](LIMITATIONS.md) rather
than being quietly assumed away.

### Two traps that cost me real time

**Any label inside a styled container must name its own `text_color`.** The
top-level `text_color` applies to the screen. LVGL's default theme then
re-asserts a dark text color on plain `obj` containers, so a label inside a
styled tile that does not set its own color renders dark-on-dark. Button
labels are unaffected, which is why some of my pages looked perfect while
others looked like the data was missing. The text and the data were there the
whole time. The `tile` style in `example-device.yaml` sets `text_color` for
this reason. Do not delete that line.

**Keep new label text ASCII.** The characters `−`, `—`, `·` and `…` are not in
the built-in montserrat glyph set and render as empty boxes. Same for any
Material Design Icons codepoint you have not explicitly listed in your `font:`
block.

---

## 2. Home Assistant holds the brain, the panel is the face

Nothing about the pet's state lives in the ESPHome image. Four reasons.

**Reflashing is routine.** A cold ESP-IDF build here takes about 8m30s and I do
it whenever I change a page. Anything living only in the image is one config
change away from gone.

**`restore_value: true` is NVS, and NVS is not a database.** It survives a
reboot, but the key is derived from the global's definition, so editing the
config can silently reset the value. Worse, a pet writing XP every few minutes
is flash wear on a partition that also holds your Wi-Fi credentials. Every
global in this package uses `restore_value: false`.

**Every XP source is on a PC or the network.** The ESP32 cannot reach your git
repos or your issue tracker. The scorer has to live where the signals are, and
the state should live next to the scorer.

**HA gives you history, backup and graphs for nothing.** `input_number` state
is recorded, so the decay curve and XP-over-time are inspectable without
building anything.

The panel subscribes with the standard `homeassistant` sensor and text_sensor
platforms. No new transport.

### One encoded sensor, not nine

Home Assistant publishes the pet's whole state as one string:

```
xp=418;lvl=3;pct=41;hun=12;rdy=0;stg=2;nxt=585;spi=88;on=1
```

One subscription instead of nine. The panel pays a fixed cost per subscribed
entity, and nine slow-moving numbers that always change together are one fact.
`desk_pet_helpers.h` parses it.

---

## 3. XP has to come from something real

A pet fed by an invented number is a progress bar with a face. The measurement
work, including the three signals that look great and are mostly machine
output, is in
[02-progression-and-evolution.md](02-progression-and-evolution.md) §1. What
follows is the part that generalises.

### Signals that are not reachable, and why that is a hard no

Three categories I looked at and dropped:

- **A vendor's monthly usage export.** A hand-downloaded console CSV with no
  API behind it. The date-stamped filename is the tell. It is a monthly
  artifact, not a pollable signal.
- **Invoices.** Hand-transcribed, monthly, vendor-forced.
- **Anything read out of a UI automation tree rather than a file.** You can get
  *event*-shaped XP out of that (a session transitioning to working) but never
  volume, and you should say so and drop it rather than invent a proxy.

**The common principle: a signal that depends on a human remembering to export
a file monthly is not a signal.** It will be stale within one cycle and wrong
within two.

### The ledger, and why it is the hard part

**Every source must be counted as a delta against a durable last-seen mark, and
every award must be idempotent.**

Windowed metrics (a "last 5 hours" figure, say) go down as well as up, so they
cannot be differenced. The scorer keeps its own `last_scan_ts` and counts rows
newer than it.

Three rules the scorer must not break:

1. **Dedupe on identity, not on count.** Commit sha, issue id, ticket id. A
   count is not an identity and a re-run will double it.
2. **A source that is unreachable awards zero and does not move the mark.** If
   the network drops for four hours, the returning delta legitimately contains
   four hours of items, and awarding that is correct. But an *error* (auth
   failure, timeout, unparseable output) must be a no-op that leaves
   `last_scan_ts` where it was. Both failure directions lose data; only one of
   them is loud.
3. **Cap panel-tap XP.** Otherwise the fastest route to a level is mashing a
   button, which makes the whole number meaningless.

**The thing most likely to kill this project is the ledger being wrong.** Not
flash, not sprites, not LVGL. If the scorer double-counts on a re-run, or eats
a window after an error, or backfills a burst after an outage, the number stops
corresponding to anything you did. A pet whose XP is uncorrelated with your
work is a random number generator with a face, and that is about a week from
being ignored.

Spend the effort on identity-keyed dedupe and on a no-op-on-error path.
Everything else here is assembly of parts that already work.

---

## 4. Pet mechanics

### Decay

Two needs, both 0 to 100, both moved by a single automation on a 15-minute
interval. Decay lives in HA because it has to continue while the panel is
asleep and survive reboots, and the ESP32 can promise neither.

- **Hunger**: 0 (fed) to 100 over about 48 hours. `+0.13` per tick.
- **Spirit**: 100 (happy) to 0 over about 72 hours. `-0.09` per tick.

Deliberately slow. A pet that needs attention every four hours is a pager.

Spirit exists because hunger is about care and spirit is about attention.
Feeding does not fix spirit; only playing does. A pet that is fed and ignored
should still fade. The two rates differ so the needs never go hollow on the
same day.

### The decay pause gates are the load-bearing part

**Decay does not accrue when you are not there, and does not accrue during
something bad.** Every gate reads an entity the panel is already subscribed to,
so none of them cost a new integration:

- PC session locked
- Monitor powered off
- In a call
- An incident or on-call queue is hot

Weekends, time off, a 2am outage and a bad Tuesday all cost nothing. During an
incident the pet enters quiet mode: calm sprite, no badge, no decay. Not
asleep-and-sad. Calm.

Each gate is individually switchable, and turning one off makes decay continue
through that state rather than disabling decay.

### The honest failure mode, and how it is designed out

A pet that guilt-trips you about a dead streak while you are mid-incident is
worse than no pet. Five mitigations, all structural rather than tonal:

1. **No streaks. Ever.** No consecutive-day counter, no "you haven't visited in
   N days". A streak is a mechanism whose only purpose is to make stopping feel
   bad. It is not being tuned down. It is not being built.
2. **The pet cannot die and cannot lose a level.** Neglect makes it sleepy and
   gray; the first interaction restores it. Losing four months of progress to a
   vacation is the fastest way to make this thing hateful.
3. **Needs gate a bonus, never a penalty.** Well-tended is 1.25×. Neglected is
   1.0×. There is no sub-1.0 multiplier anywhere in the design. Care is
   rewarded; neglect simply is not rewarded.
4. **The pet cannot interrupt.** No notification, no sound, no badge on any
   page except its own. It has no route to your attention that you did not
   initiate by opening its page. This is the whole safety property, and it is
   worth defending against every future "it would be cute if...".
5. **Sad text is banned, not discouraged.** The copy is neutral and factual:
   `hungry`, `sleepy`, `resting`. Never "where have you been", never "I missed
   you".

### Interaction: existing hardware only

480x480 of touch and one side button. Nothing else exists.

- **Feed.** Tap the pet. Zeroes hunger. Four-hour cooldown so it stays a small
  ritual rather than a button to mash.
- **Play.** The pet hops between six slots and you tap it, 12 seconds on the
  clock. **The whole round runs on the ESP32 with no HA round trip during
  play.** That matters: the seconds in this system live in serial PowerShell
  spawns at about 870ms each, and a reaction game with a network hop in it is
  not a game. HA is told once, at the end.
  
  Play got built on day one. My first reaction after the hatch was that it was
  cute but there was not much to do with it, which was right. Feed has a
  four-hour cooldown and Train only acts on a level-up, so between those two
  events the pet was inert. A companion you cannot interact with is a widget.
  
  There are now seven games. A score of zero costs nothing and there is no
  penalty branch anywhere.
- **Train.** The deliberate act of levelling. When XP crosses the threshold the
  button lights and pressing it commits the level. Evolution is something you
  do and watch, not something that happened while you were in a meeting.

---

## 5. Powers

The command bus is: a panel button calls an HA script, that script flips a
switch, and an agent on the PC runs the matching command. Adding a power is one
HA script plus one wrapper plus one button. Nothing architectural.

**The standing rail: powers are manual-trigger only. The pet never fires one on
its own.** Level unlocks the *button*; you press it. A companion that runs a
macro because it felt like it is a companion that gets unplugged.

Exactly one power in the full design is ever permitted to auto-fire, it is
gated on two conditions at once, and it is locked behind an epic trait for that
reason.

**No power may send, delete, move or spend.** `Tidy` is mark-as-read only,
because the sweeps it calls are mark-as-read only, and it inherits their
protect lists rather than reimplementing them. Marking a message read is undone
in one click. Moving or deleting is not, which is why archiving was left out.
Nothing in a toy should be the first thing in your setup to acquire a new write
capability.

---

## 6. Effort, honestly

| Piece | Effort |
|---|---|
| HA package: helpers, decay, panel-tap XP | ~150 lines of YAML, half an evening |
| The scorer plus its state file plus a scheduled task | one full evening, nearly all of it in idempotency |
| The ESPHome page: sprite, bars, buttons, scripts, globals | ~250 lines plus 2 placeholder images, one evening including compile-and-look |
| Each power after the first | about an hour |

Roughly 3 to 4 focused evenings for the whole design. Budget 2 to 3 flashes.

### Second-order, worth knowing rather than solving

If the pet reads signals published by an agent on your PC, then **the pet
inherits that agent's failure mode**. When the publisher dies, every counter
goes `unavailable` at once. A pet showing `--` looks *broken*, where a blank
tile just looks idle. Give the sprite an explicit "napping, no data" state so
the degraded case reads as intentional.

---

## 7. Not built, deliberately

- **Multiple pets.** One first. A second pet multiplies the state, the decay
  automation, the sprite budget and the page layout, in exchange for nothing
  until the first one has proved it is fun.
- **Sound.** On the D1 the buzzer hangs off the RP2040, which is on stock
  firmware. Getting at it means flashing ESPHome to both chips bridged with
  `packet_transport`, which is a genuine firmware project, for a beep. A
  beeping pet violates the cannot-interrupt rail anyway.
- **XP from any monthly console export.** See §3.
- **Any power that sends, deletes, moves or spends.** See §5.
- **Auto-firing powers.** See §5.
- **Storing pet state on the device.** See §2.
