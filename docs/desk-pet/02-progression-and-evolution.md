# Progression, evolution and powers

The loop: grow, max out, optionally evolve, get a higher ceiling and more power
slots, repeat. Unbounded. Powers are randomised and rerollable.

This document is the design. Slice 1 (levels 1 to 8 in one form, one fixed
power) is what ships in this repo. Everything past §3 is designed but not
built, and it is here because the numbers are the interesting part and I would
rather publish them than have someone re-derive them.

---

## 1. What "forever" actually costs

The first version of this had a pet levelling on token counts. It would have
hit max level in about four days. So before writing a single threshold I
measured what a real week of my own activity actually looks like.

### The three signals that look great and are mostly machines

This is the part I would most want someone else to steal, because I got it
wrong first and the failure is silent. A signal that goes up reliably is not
the same as a signal that means work.

**1. Total agent tokens.** Over a 7-day window my local transcripts showed
8.36 billion tokens. Of that, **95.8% was `cache_read`**. An agentic loop
re-reads its cached prompt on every turn, so that number is a property of the
harness, not of anything I did. At my first draft's rate of 1 XP per million
tokens the pet would have earned 8,361 XP in a week, which is 23.9 times the
entire weekly budget, for sitting still.

Fix: score `output_tokens` only. That was 18.3M for the week, which is a real
number about real work.

**2. Commits in my notes repo.** 1,089 commits in 30 days, against 134 in the
actual code repos. At least 331 of those were definitionally machine-made
(hourly snapshot commits and an auto-sync timer) and most of the rest were
scheduled jobs. Counting them would have let automation outvote my own code
8:1.

Fix: exclude the notes repo from the commit signal entirely. Code repos only.

**3. Machine-filed items on my own issue board.** 59 of 111 items closed in 30
days were filed by an automated scanner, where one dependency bump resolves
nine at once.

Fix: count human-filed items only.

There is a fourth. Assistant turns ran at 45,438 a week, roughly 6,500 a day,
which is dominated by scheduled agents rather than by me. Excluded for the same
reason.

**The general rule:** before you wire a counter to a reward, look at what
fraction of it a machine produces while you are asleep. If the answer is most
of it, you have built a progress bar with a face.

### The XP budget

Every source is capped per day, and each cap sits at roughly twice the typical
value. A cap that always binds is a dead signal, but a genuinely big day should
still be worth something.

| Source | Measured rate | XP rule | Typical day | Daily cap |
|---|---|---|---|---|
| Agent **output** tokens | 2.6M/day | 1 XP per 200k | 13 | 25 |
| Commits, code repos only | 4.4/day | 3 XP each | 13 | 30 |
| Issues shipped, human-filed | 1.7/day | 10 XP each | 17 | 40 |
| Panel touches | see below | 1 XP per 3 touches | ~10 | 45 |
| Active-day bonus | 23 of 30 days | 15 XP flat | 15 | 15 |
| | | | **68** | **125** |

23 active days in 30 is about 5.4 a week, so 68 × 5.4 gives roughly 367 XP a
week. **The planning figure is 350 XP/week, or 50 a day.** The all-caps ceiling
is 875 a week, a 2.5× spread. That is enough range to feel responsive and not
enough for one heroic weekend to skip a month.

Two things stack on top and every date below ignores them, so the dates are the
slow end: a **1.25× multiplier** when both needs are in good shape, and a
**1.1× set bonus** if your creature's parts all match or all differ. A fed
Harmony pet runs at 1.375× and reaches its first power at about 2.5 weeks,
which is the fastest the design permits and is still fine.

**Your numbers will not be my numbers.** 350 XP/week is one month of one
person. Re-tune after two weeks against the XP-by-source history that Home
Assistant records for free. That is what the `Ledger` power in §4 exists for.

---

## 2. The curve

A pet has a **Form** (how many times it has evolved, unbounded) and a **Level
within that Form** (capped per form). Thresholds follow an `L^1.85` shape.

### Form 1, the tutorial form, max level 8

| Level | Cumulative XP | Days at 50/day | Elapsed |
|---|---|---|---|
| 2 | 60 | 1.2 | day 1 |
| 3 | 345 | 6.9 | 1 week |
| 4 | 585 | 11.7 | 1.7 weeks |
| 5 | 880 | 17.6 | 2.5 weeks |
| **6** | **1,240** | **24.8** | **3.5 weeks, first power** |
| 7 | 1,660 | 33.2 | 4.7 weeks |
| **8** | **2,110** | **42.2** | **6.0 weeks, Ascendant** |

Level 2 was originally 160 XP. On the day it hatched, slice 1 was running on
two XP sources at about 34 XP/day, which made 160 four days of watching a
static egg. I wanted the *powers* to take forever, not the first visual change.
L2 dropped to 60 and nothing above it moved.

**Why 3.5 weeks for the first power.** Under a week and it is not earned. Past
two months and the thing gets uninstalled before it gets interesting. Levels
land on day 1 and day 7, so there is visible motion in the first week; the wait
is for the power, not for any feedback at all.

Sensitivity, because 350 is one sample:

| If your real rate is | First power at | First evolution at |
|---|---|---|
| 175 XP/wk | 7.1 weeks | 12.1 weeks |
| 350 XP/wk | 3.5 weeks | 6.0 weeks |
| 700 XP/wk | 1.8 weeks | 3.0 weeks |

### Later forms, a season model

Making each form dramatically longer runs out of road fast. A 2.4× growth
factor puts Form 3 at seven months. So the ramp softens and then plateaus at
about a quarter of a year per form, forever.

```
FormXP(F)   = 350 XP/wk x min(6 + 4(F-1), 20) weeks
MaxLevel(F) = min(8 + 2(F-1), 20)
```

| Form | Weeks to max | XP | Max level | Cumulative |
|---|---|---|---|---|
| 1 | 6 | 2,110 | 8 | 6 wk |
| 2 | 10 | 3,500 | 10 | 16 wk |
| 3 | 14 | 4,900 | 12 | 30 wk |
| 4 | 18 | 6,300 | 14 | 48 wk |
| 5 | 20 | 7,000 | 16 | 68 wk |
| 6+ | 20 | 7,000 | 18, then 20 | +20 wk each |

About 11 months to Form 5, then a form every 4.6 months indefinitely. Three
years lands inside Form 10. Powers are granted at 60% and 100% of max level
from Form 2 onward, two per form; Form 1 grants one, at L6.

### What keeps it alive past the plateau

The cadence plateaus. The content does not.

1. **Power tiers deepen.** Tier II at Form 2, Tier III at Form 4, Tier IV at
   Form 6. A Form-8 pet can roll powers a Form-2 pet cannot.
2. **Traits accumulate.** Epic evolutions grant permanent modifiers that
   persist across all future forms. A Form-12 pet differs from a Form-3 pet
   mainly by the trait stack it is carrying.
3. **The loadout becomes the game.** From about Form 4 you own more powers than
   you can equip.
4. **Epics get rarer and more dramatic**, with a pity floor so that rarity
   never turns into drought.

**Decay rates never scale with form.** A Form-9 pet is not hungrier than a
Form-1 pet. Scaling upkeep with progress is the mechanism that turns a
companion into an obligation, and it is the most common way this genre goes
wrong.

---

## 3. Evolution: voluntary, rolled, three tiers

At max level the pet enters **Ascendant**. Evolving is a button you may press.
There is no prompt, no nag, no badge and no countdown anywhere in the UI.

| Staying gets you | Evolving gets you |
|---|---|
| +10% XP rate while Ascendant | A new Form with a higher level ceiling |
| XP over the cap banks as **Surplus** | +1 power slot, guaranteed, every form |
| +1 reroll token per 2 weeks held | A power at 60% and at 100% of the new max |
| | An evolution roll: minor, major or epic |

Surplus caps at 50% of the next form's requirement. Without a cap the optimal
play is to never evolve. At 50% it is worth banking for a few weeks and never
worth banking for a season.

### The tier roll

Rolled on evolve. Not chosen, not earned.

| Tier | Odds | What changes |
|---|---|---|
| **Minor** | 65% | Reroll one part, plus a palette shift |
| **Major** | 28% | Reroll two parts, palette shift, +1 reroll token |
| **Epic** | 7% | Reroll all four parts, unlock the next part tier, new accent color, +2 tokens, and a permanent **Trait** |

Because parts come from a fixed library (see
[03-sprite-pipeline.md](03-sprite-pipeline.md)), **no evolution ever needs a
sprite drawn for it**. That was the most fragile assumption in the first draft
of this design and modular parts removed it.

**A bad run is never a punishment, by construction.** The level ceiling, the
guaranteed +1 slot and the two powers per form are identical at all three
tiers. Tier affects visual drama, reroll tokens and traits only.

One honest exception: the `Wide Kit` trait grants a slot beyond the normal cap,
and traits come only from epics. So a lucky pet really can end up with more
slots at the same form. The floor is guaranteed and identical. The ceiling is
not.

**Pity.** A counter tracks consecutive non-epic evolutions. Epic chance ramps
`7% + 7pp per pity`, reaching 56% at pity 7, and at pity 8 the roll is forced
epic. Read the counter before the roll and increment after a non-epic result.
Expect 4.4 evolutions between epics, worst case 9. There is also a guaranteed
major after three consecutive minors, which fires 27.5% of the time on base
odds, often enough to be worth having.

### Rolls must be seeded, not random

```
roll = hash(pet_id, form_number, roll_index)
```

Which parts get rerolled is seeded identically. Two consequences, both
required:

**Idempotency.** The scorer can crash and re-run without rolling a different
creature. A non-deterministic roll inside a system that retries is the same
class of bug as double-counted XP, and it is worse: XP can be corrected, a
creature that changed identity on a retry cannot.

**Auditability.** A bad roll you can recompute is bad luck. A bad roll you
cannot recompute is arbitrary, and arbitrary is what makes people stop caring.

---

## 4. Powers: owned, equipped, slots

**Owned** is every power ever granted, unlimited, listed on a collection
sub-page. **Equipped** is the active set, which is literally the buttons
rendered on the pet page.

Swapping the loadout is free and instant. The scarcity is in owning, not in
switching. A swap cost would mean the right loadout for a bad morning is the
one you cannot be bothered to select.

```
Slots(F) = min(F, 8)   + 1 per Wide Kit trait
```

**The 8 is a layout fact, not a taste.** The pet page has y0 to y404 above the
nav bar. The sprite and needs bars take the top 200px, leaving room for a 2x4
grid of roughly 200x70 buttons. More than eight and the buttons stop being
tappable from across the room. A ninth power means shrinking the sprite, which
is a real tradeoff and the page should make it visible.

Owned outgrows equipped from Form 2 onward, widening by one each form. By Form
5 it is 9 owned against 5 equipped, which is where the collection starts being
a decision rather than a technicality.

### Draw rules

- Draw **without replacement**, so you never get a power you already own.
- Tier weights over unlocked tiers: **60 / 25 / 12 / 3**.
- **Precondition filtering.** A power whose dependency is unavailable is never
  offered. A granted power that cannot run is a dead slot.

### The pools, and the "no junk tier" rule

Every entry is something I would otherwise do by hand, so even the worst roll
is mildly useful. That is how the randomisation is made safe here: not by
tuning odds, but by refusing to put anything in the bag that is not worth
drawing.

The four powers in this repo are Tier I: **Fetch** (focus whatever is shouting
loudest, or say "all quiet" rather than opening something at random),
**Tidy** (run the two mark-as-read sweeps), **Den** (lights down, mic muted,
media paused) and **Doctor** (run the panel health script).

Higher tiers in the design add things like a status roll-up, a one-tap
end-of-day macro, and a `Ledger` power that shows today's XP broken down by
source, which is genuinely useful for re-tuning §1.

**One power in the whole design ever acts on its own**, and it is locked behind
an epic trait for exactly that reason. See §7 of
[01-design-and-feasibility.md](01-design-and-feasibility.md) for the standing
rail: powers are manual-trigger only.

---

## 5. Rerolling: a cooldown, not a price

Unconstrained rerolling means rerolling until the best set appears, which
drains the randomness of meaning. Tokens limit the total; a cooldown limits the
session.

- +1 token on every evolution, +1 more on a major, +2 more on an epic, +1 per
  two weeks held at Ascendant.
- Spend 1 token to discard an owned power and draw a replacement.
- **One reroll per 24 hours, tokens notwithstanding.** This is the constraint
  that does the actual work. It also caps rerolls at 365 a year no matter how
  many tokens pile up.
- The discarded power leaves the collection and re-enters the pool. Rerolling
  is a gamble, not a free filter.
- One free mulligan per form: the first power granted in a new form can be
  rerolled once at no token cost, ignoring the cooldown.

**Why not an XP price.** An XP price competes directly with the level curve, so
rerolling would read as losing progress. The one thing this pet must never do
is make a legitimate choice feel like a punishment. A cooldown costs nothing
you value except waiting.

And no countdown badge. The reroll button is simply disabled with the word
`tomorrow` on it. A ticking timer is a small machine for generating impatience.

---

## 6. The rule that bounds all of it

> **Randomness may only ever add, or be neutral. Nothing is rolled that can go
> against you.**

Decay rates, level thresholds, slot counts and the guaranteed per-form
progression are all fixed. No unlucky day, no bad streak, no cursed form. A
prestige system where the dice can take something away is a slot machine, and a
slot machine on your desk during a bad morning is precisely the failure mode
this design exists to avoid.

The other randomisation is a daily mood roll, which is cosmetic only (idle bob
speed and a one-word caption, zero mechanical effect), and ±10% variance per XP
award, which is enough that the number is not perfectly predictable and not
enough to break the link between the number and the work.

There is no sad face in the mood table. That is deliberate and it is not a
detail.

---

## 7. State

Slice 1's helpers are in
[`homeassistant/packages/desk_pet.yaml`](../homeassistant/packages/desk_pet.yaml).
The full design adds:

```yaml
input_number:
  pet_form:          { min: 0, max: 999,    step: 1 }   # evolutions, unbounded
  pet_level:         { min: 1, max: 20,     step: 1 }
  pet_surplus:       { min: 0, max: 999999, step: 1 }   # banked at Ascendant
  pet_reroll_tokens: { min: 0, max: 99,     step: 1 }
  pet_epic_pity:     { min: 0, max: 99,     step: 1 }
input_text:
  pet_owned:    { max: 255 }   # csv of 3-char power ids
  pet_equipped: { max: 255 }
  pet_traits:   { max: 255 }
  pet_parts:    { max: 255 }   # e.g. "hd=rp3;bd=fl1;ar=rp2;lg=cn4"
input_datetime:
  pet_last_reroll: { has_date: true, has_time: true }
```

**Use short ids and separate fields.** A Home Assistant state caps at 255
characters. I have already been bitten by this on a different sensor: nine
30-character rows blew past the cap, the publisher logged an HTTP 400, and the
sensor sat silently empty. Three-character ids give the full 16-power
collection in about 64 characters with room to grow. Do not merge `pet_owned`
and `pet_traits` into one field to save a helper.

`pet_form`, `pet_level` and `pet_parts` are **committed values**, written only
by the level-up and evolve routines and never recomputed by a repaint. A
repaint that recomputes from raw inputs bypasses whatever logic was supposed to
gate it.

---

## 8. What ships, in what order

**Slice 1, the egg that hatches.** One evening. Form 1 only, levels 1 to 8, one
fixed power at L6. XP from two local sources. No evolution, no slots, no
rerolls, no randomness. Form and slot fields exist and read 1. It goes first
because it is a complete loop: real work in, visible level-ups from day 1, a
power at 3.5 weeks. If that is not fun, none of the rest was going to save it.

**Slice 2, the pool.** Tier I powers, random draw with precondition filtering,
the owned/equipped split, reroll tokens and the 24-hour cooldown.

**Slice 3, evolution.** Ascendant, Surplus banking, the seeded tier roll and
pity counters, slot growth, the part library, the unknown-part fallback, and
the modular parts system. This is where the loop becomes unbounded.

**Slice 4, depth.** Traits, Tier II to IV pools, the collection page.

### The risk this layer adds

The feasibility doc named the XP ledger as the thing most likely to kill this.
The prestige layer adds a second and sharper one: **an evolution roll that is
not idempotent.**

XP that double-counts can be corrected by editing a number. A pet that rerolled
into a different creature on a retry cannot be un-seen, and the attachment that
makes the whole thing worth building goes with it.

Seed every roll from `(pet_id, form, roll_index)` before writing a single line
of slice 3.
