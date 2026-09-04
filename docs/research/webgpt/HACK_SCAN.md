Yes — I would add a **bounded `$hack` security audit as a final evidence gate**, but I would not make `$hack` a dependency of the submitted application or let it displace the correctness work.

The skill is well suited to this because its SAST path runs Semgrep and Bandit inside isolated Docker containers, mounts the target read-only, uses `--network=none`, and emits a typed `hack.audit_receipt.v1` with findings, severities, CWEs, Docker-isolation evidence, and explicit non-claims. It also has an SCA path for dependency vulnerabilities.

## What I would run

For `oai-trial`, the useful security gate is:

```bash
# Static application security analysis
skills/hack/run.sh audit /path/to/oai-trial \
  --no-memory-store \
  --receipt-out /tmp/oai-trial-hack-audit.json

# Dependency vulnerability analysis
skills/hack/run.sh sca /path/to/oai-trial
```

I would use `--no-memory-store` for the submission audit because there is no reason for a disposable trial scan to write anything into Graph Memory.

Then run a second focused audit at high severity:

```bash
skills/hack/run.sh audit /path/to/oai-trial \
  --severity high \
  --no-memory-store \
  --receipt-out /tmp/oai-trial-hack-high.json
```

The final gate should be:

```text
CRITICAL findings = 0
HIGH findings     = 0

MEDIUM/LOW:
  fixed,
  explicitly justified,
  or recorded as known non-blocking limitations
```

A scanner PASS still should not be called proof that the application is secure—the `$hack` contract itself says a SAST finding or absence of findings does not establish exploitability or complete security.

## It complements our existing verification very well

There are different evidence classes:

```text
PROPERTY / ADVERSARIAL TESTS
    ↓
"Does our anonymization/release contract behave correctly?"

INDEPENDENT CORPUS VERIFIER
    ↓
"Is this particular release correct?"

$hack SAST + SCA
    ↓
"Did we introduce common software-security weaknesses?"

CONTAINER INSPECTION
    ↓
"Is the packaged execution environment appropriately hardened?"

OPTIONAL RESIDUAL-RISK ATTACK
    ↓
"Can the anonymized data still reveal identities under a declared attack model?"
```

Those should remain separate. A Bandit scan cannot tell us that protected values survived, and our corpus verifier cannot tell us that we accidentally used `shell=True`.

## Areas `$hack` should specifically scrutinize

This project actually has several interesting security boundaries where static analysis matters.

### Filesystem handling

We are processing an untrusted mounted tree, so look for:

* symlink following;
* path traversal;
* unsafe `resolve()` assumptions;
* TOCTOU between inventory and open;
* insecure temporary files;
* broad permissions;
* unsafe cleanup/deletion;
* output/input aliasing;
* archive-style path mistakes even though there are no archives.

### SQLite handling

Look for:

* SQL constructed from raw identifiers;
* value interpolation rather than parameters;
* unexpected extension loading;
* writable source database;
* unsafe URI construction;
* unbounded busy behavior.

### Parsing and resource exhaustion

Look for:

* unbounded file reads;
* unbounded JSON depth;
* unbounded CSV fields;
* regex DoS;
* uncontrolled policy-size growth;
* pathological overlap behavior;
* decompression or special-file assumptions.

### Secrets and privacy leakage

Especially inspect:

```text
logger.*
print(...)
exception formatting
report construction
temp filenames
debug output
pytest failure messages
```

for possible exposure of:

* sensitive literals;
* generated pseudonyms;
* mapping material;
* entire rows;
* policy bodies.

Static scanners will not understand all of this domain leakage, so our custom leak tests remain necessary.

### Subprocess/container behavior

Especially around:

* `shell=True`;
* command interpolation;
* inherited environment variables;
* unsafe Docker invocation;
* accidental network requirements.

### Cryptography

If we add HMAC:

* no homemade MAC algorithm;
* no truncated output below our documented security level;
* no implicit encoding;
* constant/version/domain separation explicit;
* no secret logged or serialized.

---

# I would add a dedicated security audit artifact

Something like:

```text
docs/security/
    SECURITY.md
    THREAT_MODEL.md
    hack-audit.receipt.json
    sca-summary.json
```

`SECURITY.md` can be short:

```markdown
# Security Review

## Static analysis
Semgrep + Bandit executed through containerized `$hack`.

Critical: 0
High: 0

## Dependency analysis
Python dependency SCA executed against the locked environment.

Known critical/high vulnerabilities: 0

## Domain-specific controls
- input filesystem treated as untrusted
- symlinks/special files rejected
- SQL values parameterized
- identifiers quoted and inventoried
- private staging permissions
- no sensitive data in logs/reports
- runtime network not required
- release committed only after independent verification

## Non-claims
Static analysis does not establish absence of vulnerabilities.
Independent anonymization verification is a separate gate.
```

That would play extremely well during the OpenAI walkthrough.

You could say:

> “I treated both the data and the software implementing the transformation as adversarial surfaces. The domain verifier checks anonymization correctness; separately, I ran the code through containerized Semgrep/Bandit and dependency analysis.”

That's a strong engineering signal.

## Should we use the heavier `$hack` modes?

Probably **not initially**.

I would not spend trial time on:

```text
session-audit
evolve-campaign
battle
network scans
exploit probes
```

The core submission has no network server, so DAST offers little. The skill's heavier modes are designed for live service targets and authorized red/blue hardening.

If we later add an optional FastAPI demonstration service, then a bounded `session-audit` becomes interesting:

```text
FastAPI container
    ↓
$hack session-audit
    ↓
SAST + DAST
    ↓
route/security findings
```

But I would not add FastAPI merely to have something to attack.

## One especially useful addition

I would add a **security abuse-case test pack** inspired by `$hack`, but implemented directly in the trial tests:

```text
malicious symlink
FIFO/device input
path component containing sensitive literal
huge policy
huge literal
huge CSV field
deep JSON
malformed UTF-8
malformed SQLite
database lock
output disk exhaustion
SIGTERM during publication
permission failure
corrupt report
extra release file
```

That gives us security-specific deterministic evidence even if `$hack` itself is unavailable to the evaluator.

## Presentation value

This becomes another nice evidence layer in the deck:

```text
RELIABILITY & SECURITY

  100% corpus verification          ✓
  property/adversarial tests        ✓
  crash publication tests          ✓
  Semgrep/Bandit SAST               ✓
  dependency SCA                    ✓
  clean-container execution         ✓
  raw/mapping leakage scan          ✓
```

And then immediately qualify it:

```text
Security scans are supporting evidence,
not a claim of vulnerability-free software.
```

That combination—security depth without overclaiming—will look better than simply displaying a green scanner badge.

So **yes: add `$hack` SAST + SCA to the final audit and presentation evidence**, after the deterministic P0 implementation is working. I would not put `$hack`, Memory, or any of its scanner dependencies inside `oai-trial` itself.
