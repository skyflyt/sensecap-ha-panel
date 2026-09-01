# Security

## Reporting

Open a GitHub issue. This is a hobby project for a $60 desk panel; there is no
private disclosure process and nothing here handles anyone else's data.

## What this repo does and does not contain

**It contains no credentials, and never has.** `esphome/secrets.yaml.example`
holds obvious dummy strings. `secrets.yaml` is gitignored, along with `*.pem`,
`*.key` and `*.secret`.

Every entity id from the author's own house has been replaced with a
`${entity_*}` substitution or a `CHANGE_ME_` placeholder. No IP addresses
except `192.168.4.1`, which is ESPHome's captive-portal address and is the same
on every ESPHome device.

## Two things to know if you build from this

**ESPHome substitutions expand inside lambdas.** That is genuinely useful — it
is how you build a URL at compile time — and it is also how a password ends up
baked into a compiled binary and, if you are careless, into a config you
publish. If you find yourself putting a credential in `substitutions:`, put
`!secret` on it instead.

**If a credential has ever been committed or pushed, deleting it from the file
is not the fix.** Git history is permanent. Rotating changes what you use; only
revoking closes the old door.

## Things this project deliberately will not do

The pet's "powers" run commands on a PC. Every one of them is something you
could already do by hand, and the pool has a hard rule:

**No power may send, delete, move, archive or spend anything.** The mail sweep
is mark-as-read only, because marking a message read is undone in one click and
archiving is not. Exactly one power in the full design is ever permitted to
fire on its own, it is gated on two conditions at once, and it is locked behind
a rare unlock for that reason.

If you adapt these, keep the rule. A toy that can do something you cannot
easily undo is not a toy.
