# Self-contained image for the anonymization trial. No network, daemon, or host
# service is required at runtime.
#   docker build -t anonymization-trial .
#   docker run --rm anonymization-trial            -> bundled demo
#   docker run --rm -v IN:/trial/input:ro -v OUT:/trial/output anonymization-trial run
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /trial

# Install the package (runtime deps are stdlib-only; the build is reproducible
# from pyproject.toml). Copy manifests first for layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
COPY fixtures ./fixtures
RUN pip install .

# Runs as root by default so the evaluator's mounted /trial/output is always
# writable (the brief's mounted-run contract is the hard requirement). The
# production non-root variant is documented in SUBMISSION.md:
#   RUN useradd --create-home --uid 1000 trial && chown -R trial /trial
#   USER trial
# Bare run executes the self-contained demo; `run` processes a mounted bundle.
ENTRYPOINT ["anonymization-trial"]
CMD ["demo"]
