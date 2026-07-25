# 0006 — Versioned config identities and leaf-owned locks

## Context

A config name alone cannot identify reviewed behavior across prompt, extension,
settings, and smoke-contract changes. Model+thinking leaves prevent model drift,
but shared config files can still change beneath every leaf. Historical configs
and results have no content provenance and must remain honest legacy evidence.

Confirmed launches need one content identity without adding another result-tree
axis or exposing credentials.

## Decision

A new config release uses `<config-name>@<major>.<minor>.<patch>` as its existing
config path segment. The name uses lowercase behavior-descriptive words. It
retains its purpose across releases and cannot end in the vague lineage suffix
`-v<number>`, `-new`, or `-latest`. Empty segments, extra `@`, `/`, and `,` are
invalid. The full identity occupies the existing config axis in both `configs/`
and `results/`; the result tree keeps five axes.

Each model+thinking leaf owns `config-lock.json`. Schema version 1 records:

- config name, version, version impact, and any declared predecessor;
- the exact model+thinking leaf;
- declared roles, usage sources, required capabilities, tested subject versions,
  and credential routes;
- one fingerprint for each shared and leaf behavior input; and
- one aggregate `lockIdentity` over the canonical, secret-free lock document.

Behavior inputs include prompt layers, Pi flags, non-secret environment settings,
skills, extensions, OMP config surfaces, leaf settings, package identities,
generated tools, and the applicable smoke files. JSON object order, environment
line order, and declaration-list order do not change the lock identity. File
content and executable mode do.

Secret-bearing keys are canonicalized before fingerprinting. Environment
variable references retain only the credential route. Literal secret values are
replaced with the credential name and an exclusion marker. Locks never contain
or derive their identity from secret values.

Lock writes are maintenance operations:

```sh
python -m harness.config_lock create \
  --repository . \
  --config <name>@<version> \
  --model <provider/model> \
  --thinking <level> \
  --version-impact {reuse,recompute,rerun} \
  --metadata <release-metadata.json>
```

`create` refuses to overwrite a lock. `refresh` is explicit and is valid only
while the leaf remains a draft. Planning and subject execution call the
read-only verifier and cannot create or refresh a lock.

A successful preflight that references a lock seals that leaf. The lock does not
carry mutable sealed state; the preflight result is the seal evidence. After the
first leaf is sealed, shared behavior is immutable for the release. A new leaf
may join the release only if its shared fingerprints match the sealed leaf.
Changing sealed leaf or shared behavior requires a new config version.

Unversioned configs remain readable as legacy configs. The resolver does not
fabricate locks for them, and this ADR does not migrate historical results.

## Considered options

- **Add version as another directory axis.** Rejected: it changes canonical cell
  addressing and fragments existing readers. The full release identity fits in
  the config segment.
- **Use one lock at the config root.** Rejected: model settings and smoke
  contracts vary by leaf. A root lock either misses those inputs or couples
  unrelated leaves.
- **Write or refresh locks during planning.** Rejected: execution would approve
  its own inputs. A mismatch must stop before a model call.
- **Hash raw files, including secrets.** Rejected: raw values can leak directly
  or through low-entropy fingerprint guessing. Secret values are excluded before
  hashing.
- **Invent locks for legacy configs.** Rejected: reconstructed provenance would
  claim evidence that historical runs never recorded.

## Consequences

- New confirmed launches can put the config identity and aggregate lock identity
  into plans and results without changing the result path grammar.
- A mismatch lists added, removed, and changed inputs, so maintainers can diagnose
  drift without comparing opaque aggregate hashes.
- Candidate maintenance stays possible after failed preflight through an explicit
  refresh and renewed review.
- Shared behavior cannot change after release without invalidating every locked
  leaf, making a new version the only valid path forward.
- Legacy configs continue to run through existing paths until maintainers adopt
  versioned releases deliberately.
