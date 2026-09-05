"""Adapt a file/folder plus policy to the existing engine's private input bundle.

No application logic is duplicated. Refuse unsafe originals before copying; the
engine verifies the snapshot. External hostile writers remain outside the
read-only/single-writer contract. Output must not overlap original inputs.
"""

from __future__ import annotations

import json
import shutil
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .errors import AnonError, AnonErrorCode
from .pipeline import _manifest_digest
from .policy import _no_duplicate_keys, compile_policy


def separate_output(output: Path, *inputs: Path) -> Path:
    if output.is_symlink() and not output.is_dir():
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "output artifact is a symlink")
    out = output.resolve()
    for source in inputs:
        path = source.resolve()
        if out == path or out.is_relative_to(path) or path.is_relative_to(out):
            raise AnonError(AnonErrorCode.UNSAFE_INPUT, "output overlaps an input")
    if out.is_dir() and any(out.iterdir()):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "use an empty output directory")
    if any(
        (parent / "report.json").is_file() and (parent / "corpus").is_dir()
        for parent in out.parents
    ):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "work artifacts must stay outside a release")
    return out


@contextmanager
def input_bundle(source: Path, policy_path: Path, output: Path):
    separate_output(output, source, policy_path)
    if policy_path.is_symlink() or not policy_path.is_file():
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "policy must be a regular file")
    raw = policy_path.read_bytes()
    payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    compile_policy(payload)
    if source.is_symlink() or not (source.is_file() or source.is_dir()):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "input must be a regular file or directory")
    if source.is_dir() and policy_path.resolve().is_relative_to(source.resolve()):
        raise AnonError(AnonErrorCode.UNSAFE_INPUT, "policy must be outside the input corpus")
    paths = [source, *source.rglob("*")] if source.is_dir() else [source]
    for path in paths:
        mode = path.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise AnonError(AnonErrorCode.UNSAFE_INPUT, "input contains a symlink or special file")
    with tempfile.TemporaryDirectory(prefix="anon-input-") as temp:
        bundle = Path(temp)
        (bundle / "policy.json").write_bytes(raw)
        if source.is_dir():
            before = _manifest_digest(source)
            shutil.copytree(source, bundle / "corpus", symlinks=True)
            if before != _manifest_digest(source) or before != _manifest_digest(bundle / "corpus"):
                raise AnonError(AnonErrorCode.SOURCE_CHANGED, "input changed while snapshotting")
        else:
            (bundle / "corpus").mkdir()
            data = source.read_bytes()
            (bundle / "corpus" / source.name).write_bytes(data)
            if data != source.read_bytes():
                raise AnonError(AnonErrorCode.SOURCE_CHANGED, "input changed while snapshotting")
        yield bundle
