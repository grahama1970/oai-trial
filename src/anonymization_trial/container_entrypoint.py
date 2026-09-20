"""Container launcher with an explicit host UID/GID ownership contract."""
from __future__ import annotations

import os
import shutil
import sys


def requested_identity(environ: dict[str, str]) -> tuple[int, int] | None:
    """Return the requested host identity, failing closed on partial/invalid input."""
    uid_text = environ.get("ANON_HOST_UID")
    gid_text = environ.get("ANON_HOST_GID")
    if uid_text is None and gid_text is None:
        return None
    if uid_text is None or gid_text is None:
        raise ValueError("ANON_HOST_UID and ANON_HOST_GID must be supplied together")
    if not uid_text.isdecimal() or not gid_text.isdecimal():
        raise ValueError("ANON_HOST_UID and ANON_HOST_GID must be decimal integers")
    uid, gid = int(uid_text), int(gid_text)
    if not 0 <= uid <= 2**31 - 1 or not 0 <= gid <= 2**31 - 1:
        raise ValueError("ANON_HOST_UID or ANON_HOST_GID is out of range")
    return uid, gid


def main() -> int:
    try:
        identity = requested_identity(dict(os.environ))
    except ValueError as error:
        print(f"container identity rejected: {error}", file=sys.stderr)
        return 64
    if identity is not None:
        uid, gid = identity
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
    executable = shutil.which("anonymization-trial")
    if executable is None:
        print("anonymization-trial executable not found", file=sys.stderr)
        return 127
    os.execv(  # noqa: S606 - resolved installed console script; argv is intentionally forwarded
        executable, [executable, *(sys.argv[1:] or ["demo"])]
    )
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
