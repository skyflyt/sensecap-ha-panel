# The sprite pipeline

How the art gets made. The eight stages that ship in this repo are drawn by
[`tools/make-pet-stages.py`](../tools/make-pet-stages.py); the modular parts
system in §3 is designed and not built.

---

## 0. "Utterly fun", not "utterly perfect"

My first brief to myself said the sprites should be *utterly perfect*. I
revised it a day later to *utterly fun*, and to generating head, body, arms and
legs separately so that parts could be individually good and could be uniform,
or not.

That is a better design and not a softening, for three reasons in order of
weight.

**It makes the art problem easier, not harder.** A generator asked for a whole
creature that survives downscaling to 64px does badly. Asked for one isolated
head, centred, on a flat background, it does well: a single object with no
composition to get wrong, getting the full pixel budget instead of a quarter of
it. A head sourced from a 512px sheet cell downsamples about 21x to 24x22.

**It solves the consistency problem structurally.** With modular parts the body
persists while the head changes. Continuity is guaranteed by construction
rather than by remembering to paste the same style string.

**The byte economics are not close.** Four families of six variants per slot is
102KB and 331,776 distinct creatures. That is *less* flash than the 123.9KB the
old fixed ladder spent on about fourteen looks. The same variety pre-baked
would be 2.7GB. Modular is not the cheaper way to get this; it is the only way
it exists.

"Uniform, or not" turned out to be the good bit. A mismatched creature is
funnier and more memorable than a coherent one, so both extremes are rewarded
and the middle is normal.

### Why "perfect" was the wrong target

Generators produce high-resolution painterly images with soft edges,
anti-aliasing, gradients and thousands of colors. The panel needs a 64x64
image in a 16-color palette on an RGB565 display, read from across a room.

Downscaling painterly art to 64px averages neighbouring pixels. At that size a
creature's eye is two pixels, and averaging turns two deliberate pixels into
four muddy ones. It reads as a small blurry picture rather than as a sprite.

Good pixel art at this size is crisp *because* every pixel was a decision, and
that is exactly the information downscaling destroys.

What is honestly achievable: generation gives you the part (silhouette, color
story, character), a deterministic conversion pass gives you a clean,
palette-locked, hard-edged sprite, and **a human eye on the result at panel
scale decides whether it ships.** The human step is looking at a picture for
ten seconds. It exists because every automated pipeline produces some sprites
where the face lands wrong, and the only detector for "this does not read as a
creature" is a person looking at it.

Budget two to four generation rounds per part sheet. That is the actual cost of
"very good". Promising perfection in one pass produces mush, and mush is worse
than a plain icon.

### What is actually in this repo

The eight stages here are **drawn, not generated**, by a 230-line Python script
using nothing but Pillow's `ellipse`, `polygon` and `pieslice`.

That was not purity. I had no text-to-image tool in the loop at the time. But a
procedural ladder turned out to have one property a generated one does not:
**every stage is the same construction with different numbers**, so stage 6 is
provably stage 3 grown, rather than a different animal that happens to look
similar. That is the exact problem §3 spends four separate mechanisms trying to
solve.

The construction, shared by every stage and scaled by it:

```
feet -> body -> wings -> head -> eyes -> beak -> crest -> tail -> horns
```

Later features simply switch on and nothing is ever removed, so the silhouette
accumulates. That is what reads as growing up rather than as changing. One
interpolation parameter `t` runs 0.0 at level 2 to 1.0 at level 8 and every
dimension is a function of it. The crest appears at L4, the tail and scarf at
L5, the eyes light up at L6, horns at L7, and at L7 the whole creature warms
from amber toward gold. Level 1 is the egg and is deliberately outside the
ladder.

The script asserts that no pixel has partial alpha, because partial alpha would
soften the edges and the whole point is that they are hard.

---

## 1. Format, dimensions, palette

### RGB565 with `chroma_key`, 2 bytes per pixel

ESPHome stores RGB565 at 2 B/px with `transparency: chroma_key` and **3 B/px
with `transparency: alpha_channel`**, because the alpha is a separate plane.

Use `chroma_key`. It is not a compromise here, it is correct twice over: it is
a third cheaper, and it forces hard edges, which is what pixel art wants. Alpha
blending at 64px produces exactly the soft halo that makes generated art look
muddy. **The format that saves flash is the format that looks better.**

The trade you are making: no soft edges, ever, and one color in your palette
is spent on the key and can never appear in real art. Check the reserved chroma
value against your installed ESPHome builder before you commit a palette.

Sizes:

| Size | chroma_key | alpha_channel |
|---|---|---|
| 48x48 | 4,608 B | 6,912 B |
| **64x64** | **8,192 B** | 12,288 B |
| 96x96 | 18,432 B | 27,648 B |

64x64 is big enough for a readable face and a silhouette that changes
meaningfully between forms, small enough that a three-year art budget stays
trivial, and it sits comfortably in the pet page's top 200px alongside the
needs bars. This repo also ships 48x48 copies for the main-page tile, because
the tile's inner box is 76x78 and a 64px sprite plus a caption gets clipped.

### The palette is extracted, not invented

The panel config already carried a coherent house palette of 22 distinct
colors, dominated by a handful:

| Hex | Role |
|---|---|
| `0x9AA0A6` | muted gray, the workhorse text color |
| `0xE8EAED` | near-white |
| `0x6B7280` | dim gray |
| `0xE5484D` | alert red |
| `0x1E2228` | tile background |
| `0xF2B01E` | the accent amber |
| `0x14161A` | screen background |
| `0x2A2F37`, `0x4B5563`, `0x2563EB`, `0x35C759` | the rest |

**Lock the sprite palette to 16 entries total**: roughly 10 drawn from the set
above, about 5 creature-specific tints, and one reserved as the chroma key.
The pet then looks native to the panel rather than pasted onto it. The palette
lock is also what makes the conversion pass deterministic and keeps every form
visually related.

`make-pet-stages.py` uses a 13-color subset of exactly this palette, with
magenta `(255, 0, 255)` as the key.

---

## 2. The pipeline, seven steps

For generated parts rather than drawn ones.

**Step 1: generate a part sheet, not a creature.** One call per slot per
family. The prompt shape:

> six \<family\> heads in a 3x2 grid, evenly spaced, each centred in its cell,
> front-facing, isolated on flat magenta, no shadow, no ground plane, no text,
> \<STYLE BLOCK\>

at 1536x1024, so each cell is about 512x512 and downsamples about 21x to a
24x22 head. Six variants in one call are far more consistent with each other
than six separate calls, because the generator sees them all in one context.
**Freeze the style block before you start.**

**Step 2: cut out.** Background removal to a transparent PNG. Better than a
color key at this stage because generated backgrounds are rarely perfectly
flat.

**Step 3: tight crop.** Slice the sheet into its six cells with a fixed
geometric crop, then subject-detect and crop tight to the part with a small
margin. Do not eyeball normalised bounds. At a 24px head, two pixels off-centre
means the neck no longer meets the body.

**Step 4: vectorise, then re-rasterise.** This is the step that does most of
the work and it is the non-obvious one.

Convert the PNG to SVG with clean vector paths, then render that SVG down to
target size. This is fundamentally different from downscaling a raster: the
renderer has *actual edges* to sample rather than a field of already-blurred
pixels. Vectorising also flattens painterly gradients into flat regions, which
is precisely the posterisation a sprite needs.

Put plainly: **raster to small raster is averaging; vector to small raster is
drawing.**

Honest caveat: vectorising a busy image can produce hundreds of paths and
over-simplify fine detail like eyes. If a part comes back with its face erased,
skip this step for that part and go straight to step 5. The
quantise-and-point-downscale path alone is decent, just less crisp.

**Step 5: quantise and downscale, locally and deterministically.** Run per
part, at that part's rig canvas. A head is 24x22, not 64x64.

```bash
# 1. render the SVG at 4x the part's rig size, quantise to the locked palette
#    (no dithering: at this size dithering is noise, not shading)
convert head-rp3.svg -background none -resize 96x88 \
        -dither None -remap palette-16.png head-rp3-q.png

# 2. downscale 4x with POINT sampling: nearest neighbour, no averaging
convert head-rp3-q.png -filter point -resize 24x22 head-rp3-24.png

# 3. flatten transparency onto the chroma key
convert head-rp3-24.png -background '#FF00FF' -alpha remove -alpha off \
        head-rp3-final.png
```

Three rules, each of which is the difference between crisp and mush:

1. **`-dither None`.** Dithering scatters pixels to fake intermediate shades.
   At this size that reads as dirt.
2. **`-filter point`.** Any other filter (Lanczos, Mitchell, the default) is an
   averaging kernel and will soften every edge you just worked to create.
3. **Quantise at the larger size, then downscale.** The other way round
   quantises already-averaged pixels and locks the mud in.

**Step 6: assemble and look at it, at panel scale.** Composite the part against
the rest of the rig, not in isolation. A head that looks good alone can still
meet the body wrong, and the join is what makes a modular creature read as a
creature.

Render at 64x64 on the actual background color, at the size it will occupy,
and answer four questions:

- Can you tell what it is in half a second from six feet?
- Are the eyes still eyes?
- Do the joints look attached?
- Does it sit in the same world as the other families?

If any answer is no, regenerate that sheet. This step is the difference between
"generated" and "good", and it belongs to a person.

**Step 7: emit the ESPHome blocks.**

```yaml
image:
  - id: img_pet_head_rp3
    file: images/pet/heads/rp3-final.png
    type: RGB565
    transparency: chroma_key
    resize: 24x22
```

Store the sources alongside (prompt, seed, sheet, SVG, cells) so a sheet can be
regenerated years later.

---

## 3. The modular rig

Designed, not built. Ships in slice 3.

### The runtime capability is already proven

Four image widgets stacked in one container, each with a `src` chosen at
runtime from HA-held state. Both halves already exist in a working config:
runtime `src` swapping (the camera page repoints an image widget while
running) and transparent images composited over other content (every app mark
is drawn inside a styled tile button). So the pet is four `image:` widgets
inside a 64x64 container, each pointed at a part id. **No new mechanism.**

Z-order, back to front: body, legs, arms, head.

### The rig: decide this before generating anything

This is the one genuinely hard part and everything else follows from it. A head
generated on its own has no idea where its neck is. Get the joints wrong and
you get floating limbs, which reads as broken rather than charming.

The fix is a fixed skeleton: every part authored to a fixed canvas at a fixed
offset with its attachment pixel at a fixed coordinate.

| Slot | Canvas | Placed at | Occupies | Attachment (local to absolute) |
|---|---|---|---|---|
| body | 26x26 | x19, y20 | x19-44, y20-45 | the reference frame |
| head | 24x22 | x20, y1 | x20-43, y1-22 | neck (11,21),(12,21) to **(31,22),(32,22)** |
| arms | 32x18 | x16, y22 | x16-47, y22-39 | shoulders (3,2),(28,2) to **(19,24),(44,24)** |
| legs | 22x16 | x21, y43 | x21-42, y43-58 | hips (4,0),(17,0) to **(25,43),(38,43)** |

Checked, because a rig that does not close is worse than no rig: every part is
centred on x31.5, head/body overlap is 3 rows, legs/body overlap is 3 rows, and
the assembled bounding box is x16-47, y1-58, inside 0-63 on both axes with room
at the bottom for the idle bob.

An earlier draft of that table had a neck pixel 4px inside the body, a shoulder
1px off the body entirely, and 6 to 8px joint overlaps against a stated rule of
2 to 3. It was arithmetic, and arithmetic is checkable, which is the whole
argument for writing the rig down as numbers rather than as a description.

Three rules with it:

1. **Overlap joints by 2 to 3px.** A butt-join leaves a one-pixel seam that
   reads as a gap.
2. **Bake a 1px dark outline into every part.** Makes joins read as deliberate
   and keeps a composite creature legible against the dark background.
3. **A part that does not honour the rig does not ship.**

Accessory anchors live in the same table, in absolute 64x64 coordinates, so a
new body inherits them:

| Anchor | At | Used by |
|---|---|---|
| `head` | (31, 2) | visor, lantern, goggles, crest |
| `neck` | (31, 22) | collar tag |
| `back` | (31, 32) | satchel, cloak |
| `ground` | (31, 57) | boots |

Keep all of this in a `RIG.json`. It is data, it is tiny, and it is the
contract every generated part and accessory is measured against.

### The art budget

| Slot | Size | Bytes each |
|---|---|---|
| head | 24x22 | 1,056 |
| body | 26x26 | 1,352 |
| arms | 32x18 | 1,152 |
| legs | 22x16 | 704 |
| | **one set** | **4,264** |

| Families x variants | Per slot | Library | Distinct creatures |
|---|---|---|---|
| 4 x 3 | 12 | 51.2 KB | 20,736 |
| **4 x 6** | **24** | **102.3 KB** | **331,776** |
| 6 x 6 | 36 | 153.5 KB | 1,679,616 |
| 8 x 6 | 48 | 204.7 KB | 5,308,416 |

Recommended: 4 families of 6 variants. With eight accessory overlays that is
111.6KB total.

**If flash comes back thin, cut variants, never families.** Four families is a
floor rather than a preference, because the Chimera bonus below needs all four
parts from four different families and with three families it silently never
fires.

The starting four families: `reptile`, `fluff`, `bug`, `construct`.

### Harmony and Chimera

| Result | Condition | Reward |
|---|---|---|
| **Harmony** | all four parts from one family | matching aura tint, 1.1x XP |
| **Chimera** | all four parts from four different families | shimmer outline, 1.1x XP |
| ordinary | anything in between | nothing, and nothing lost |

Both extremes rewarded, the middle normal, nothing punished. It obeys the
bounding rule in
[02-progression-and-evolution.md](02-progression-and-evolution.md) §6:
randomness may only add or be neutral.

The 1.1x stacks with the well-tended 1.25x, so a fed Harmony pet runs 1.375x,
which pulls the first power from 2.80 weeks to 2.55. That is small, and small
is the point. A set bonus should be a nice thing to notice, not a reason to
reroll.

### The three risks, honestly

**Style drift between sheets.** Heads from one call and bodies from another can
differ in line weight and lighting. Three mitigations, and the third does most
of the work: a frozen style block, six variants per sheet in one call, and
**the palette lock**, which lands everything in the same 16 colors at quantise
time regardless of what the generator did.

**Scale incoherence.** Solved by the rig. Each slot has a fixed canvas, so a
head is 24x22 whatever the generator produced.

**Silhouette.** The real legibility risk. A hand-drawn whole creature has a
deliberate outline; a composite has whatever its parts happen to make. The
mitigation is the outline rule and the detector is the step-6 check at panel
scale.

### Ship an `unknown part` sprite per slot

A part id the firmware has no art for must render as a placeholder shape.
Otherwise a pet that evolves into a tier you have not flashed yet appears
headless. A progression system that breaks the first time its state outruns its
art is, on a three-year arc, a certainty rather than a risk.

---

## 4. Accessories

### Layered, not baked

| Approach | 8 accessories over one 64x64 creature |
|---|---|
| **Layered at draw time** | 1 base + 8 overlays = **17.4 KB** |
| Baked combinations | 2^8 = 256 pre-rendered bases = **2.1 MB** |

120x difference, and the baked version does not fit. Layering is not an
optimisation, it is the only version of this feature that exists. With modular
parts it gets worse for baking: you would additionally multiply by the 331,776
part combinations, which makes it unthinkable rather than merely unaffordable.

Three practical constraints:

- Keep the pet and its overlays inside one small LVGL container so a repaint
  invalidates about 64x64 px rather than the whole 480x480 screen.
- **Cap simultaneous visible overlays at 4.** Not a technical limit, a
  legibility one. A 64px creature wearing six things is a smudge.
- Widget count is 4 for the creature plus up to 4 accessories, all inside one
  container. Trivial for LVGL. The binding constraint stays legibility, not
  compute.

### Accessories are a kind of power, not a parallel system

The temptation is a second progression track with its own currency, slots and
drops. That is how this stops being fun: two ladders to climb, neither legible.

So an accessory **is** an equipped power that happens to be visible. Same
collection, same slots, same rerolls, same draw pools. The only genuinely new
data is a per-power `{visible, anchor, sprite}` triple pointing at one of the
four rig anchors.

**Parts are identity; accessories are capability.**

| | Parts | Accessories |
|---|---|---|
| What they are | who the pet *is* | what the pet can *do* |
| Granted by | evolution rolls | the power draw pools |
| Cost a slot? | no | yes |
| Grant powers? | **no** | yes, that is the point |

**Parts must never grant powers.** The moment they do there are two power
economies, the slot budget stops meaning anything, and you have the parallel
progression mess this whole section exists to avoid.

### Amplifiers, and what "amplify" is allowed to mean

Wearables render and grant an action like any other power. Amplifiers are the
interesting half, and "amplify existing" needs a concrete definition, because a
macro either fires or it does not and "50% stronger" is meaningless.

Amplification means exactly one of three things:

| Mode | Meaning |
|---|---|
| **Broader scope** | the power acts on more |
| **Deeper result** | the power returns more |
| **Stronger variant** | the power gains a second, gated action |

**An amplifier must add something the baseline does not already do.** Two of my
own drafts failed that test, both describing behavior that was already
baseline. An amplifier that describes what the power already did is a dead slot
wearing a costume. Check the baseline before writing an amplifier.

Deliberately not on the list: *faster* and *more often*. Speed is bounded
upstream of the panel and a hat cannot change that. "More often" means an
accessory that makes the pet act on its own, which violates the manual-trigger
rail.

An amplifier with no valid target is never drawn. If its target power is not
equipped, it is greyed in the collection and does not render on the creature:
visibly inert rather than silently useless.

### Order of operations, non-negotiable

1. `esphome compile` and read the `Flash:` line.
2. Confirm the chroma-key reserved color against your installed builder.
3. Extract `palette-16.png` from your config's own colors.
4. Freeze `STYLE-PROMPT.txt`.
5. **Freeze `RIG.json`.**
6. Then generate.

Generating before step 1 is producing art for a target that might not exist.
Generating before step 5 is worse: parts made without a rig cannot be made to
fit one afterwards, so every sheet has to be regenerated.
