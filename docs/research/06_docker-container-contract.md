# Container contract / Dockerfile

## Requirement (brief)
Dockerfile builds without host services or secrets, self-contained. Bare
`docker run` executes the demo and exits. Mounted run: `-v IN:/trial/input:ro
-v OUT:/trial/output ... run`. Both commands must be preserved.

## Sources
- CloudCops — Docker best practices 2026 (slim vs alpine vs distroless): https://resources.cloudcops.com/blogs/docker-best-practices
- TestDriven.io — Docker best practices for Python (multi-stage, non-root): https://testdriven.io/blog/docker-best-practices/
- dataskew.io — containerize data pipelines (layer caching, slim base): https://dataskew.io/blog/docker-for-data-engineers/
- KDnuggets — self-contained image, bake assets in: https://www.kdnuggets.com/docker-for-python-data-projects-a-beginners-guide
- Graf Clouds — Dockerfile best practices 2026 (size = attack surface): https://grafclouds.com/insights/dockerfile-best-practices/

## Key findings
- **`python:3.12-slim` is the safe default** for Python (Alpine's musl causes
  wheel/debug pain). (CloudCops, TestDriven)
- **Layer caching:** copy dependency manifests and install before copying source,
  so code edits don't bust the dependency layer. Our starter has zero third-party
  runtime deps, so this is cheap; still order COPYs deps-first.
- **Self-contained:** bake everything needed into the image (KDnuggets). No host
  services (rules out $memory/ArangoDB/Qdrant — see the SQLite decision).
- **Env hygiene:** `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`,
  `PIP_NO_CACHE_DIR=1`.
- **Non-root user** for the runtime is a security best practice; the mounted
  `/trial/output` must be writable by that user (evaluator controls mount perms —
  document the assumption; default root is acceptable for the trial and simplest).
- **Smaller image = smaller attack surface.** `--no-install-recommends`, clean
  apt lists, `.dockerignore` to exclude `.git/.venv/tests` from context.
- **ENTRYPOINT + CMD split** gives the two required commands from one image:
  `ENTRYPOINT ["anonymization-trial"]`, `CMD ["demo"]`; `... run` overrides CMD.

## Implication for our implementation
- Current `Dockerfile` already follows this (slim, deps-first COPY, ENTRYPOINT/CMD
  split, `.dockerignore`). Add the env hygiene vars; consider `--no-install-
  recommends` only if apt packages get added (none yet).
- Multi-stage is unnecessary while there are no compiled deps — **skip it**
  (ponytail); add only if a C-extension dep (e.g. `ijson`) enters.
- Keep `pip install .` (not `-e .`) in the image so it's a clean install.
- Do not add a non-root user yet unless mount permissions are confirmed, to avoid
  a write-permission failure on `/trial/output`; document the choice.
