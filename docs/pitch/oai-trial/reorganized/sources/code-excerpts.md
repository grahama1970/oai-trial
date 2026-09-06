# Pinned code excerpts

Exact text from the inspected frozen implementation. Navigation ranges describe inspected code regions; they need not span the full function. Excerpts are not executable proof or a new runtime copy.

## policy

[src/anonymization_trial/policy.py::compile_policy](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L129-L164)

```python
def compile_policy(payload: object) -> Policy:
    """Validate a policy payload strictly and compile its matcher."""
    _require(isinstance(payload, dict), AnonErrorCode.INVALID_POLICY, "policy is not an object")
    version = payload.get("version")
```

## identity

[src/anonymization_trial/policy.py::Rule.identity](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/policy.py#L38-L40)

```python
    @property
    def identity(self) -> CanonicalIdentity:
        return (self.data_type, self.subject_id or self.rule_id)
```

## digest

[src/anonymization_trial/pseudonyms.py::_digest](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pseudonyms.py#L41-L43)

```python
def _digest(policy_version: int, data_type: str, identity: str, salt: int) -> str:
    material = f"{ALGORITHM_VERSION}:{SCOPE_ID}:{policy_version}:{data_type}:{identity}:{salt}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
```

## spans

[src/anonymization_trial/matcher.py::Matcher.replace](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/matcher.py#L120-L131)

```python
        cursor = 0
        for span in spans:
            out.append(text[cursor:span.start])
            out.append(span.replacement)
            cursor = span.end
        out.append(text[cursor:])
        return "".join(out), len(spans)
```

## types

[src/anonymization_trial/verification.py::_typed_equal](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/verification.py#L129-L143)

```python
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_typed_equal(a[k], b[k]) for k in a)
```

## boundary

[src/anonymization_trial/bundle.py::separate_output](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/bundle.py#L22-L37)

```python
    if any(
        (parent / "report.json").is_file() and (parent / "corpus").is_dir()
        for parent in out.parents
    ):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "work artifacts must stay outside a release")
    return out
```

## approve

[src/anonymization_trial/discovery.py::approve](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/discovery.py#L329-L378)

```python
def approve(bundle: Path, review_path: Path, ids: list[str], output: Path, *inputs: Path) -> dict:
    output = separate_output(output, bundle, review_path, *inputs)
    receipt_path = separate_output(
        output.with_name(output.name + ".approval.json"), bundle, review_path, output, *inputs
    )
```

## formats

[src/anonymization_trial/formats.py::transform_file](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/formats.py#L39-L49)

```python
def transform_file(source: Path, destination: Path, policy: Policy) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == ".csv":
        return _transform_csv(source, destination, policy)
```

## publish

[src/anonymization_trial/pipeline.py::_publish](https://github.com/grahama1970/oai-trial/blob/0375af56bf681e9441edcb7433cfe58951db77b2/src/anonymization_trial/pipeline.py#L166-L211)

```python
        remaining = memoryview(data)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("report write made no progress")
            remaining = remaining[written:]
        os.fsync(fd)
```

