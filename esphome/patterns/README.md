# Panel patterns

Self-contained snippets for building pages on a SenseCAP Indicator. None of
them depend on the desk pet; take what you want.

Each one carries its reasoning in comments, because in almost every case the
non-obvious decision is the load-bearing one and the obvious version fails
silently.

| File | What it gives you |
|---|---|
| [`tiles-nav-and-idle.yaml`](tiles-nav-and-idle.yaml) | The panel chrome: tile styles, the nav bar and its arithmetic, sub-pages, optimistic tiles, two-stage ambient idle |
| [`encoded-state-sensor.yaml`](encoded-state-sensor.yaml) | One `key=value;` sensor instead of nine subscriptions, with the parser and the 255-character trap |
| [`debounced-state-badge.yaml`](debounced-state-badge.yaml) | A status badge that does not lie: the right source entity, a 60s hold, and painting from a committed global |

Full write-up: [`../../docs/00-panel-guide.md`](../../docs/00-panel-guide.md).

## The three that will cost you an evening each

Repeated here because they are the ones I would want shouted at me.

**A label inside a styled container renders dark-on-dark unless it names its
own `text_color`.** It looks exactly like a broken sensor. Three wrong
diagnoses and an afternoon.

**A clean compile is not evidence that anything renders.** The panel will
compile, flash, boot and show you a blank area with no tool reporting anything.
Look at the screen.

**Never POST a fake state to an entity id a device will later own.** It creates
a real registry entry, the device silently claims a `_2` suffix, and your
automation watches a corpse forever. Nothing errors.
