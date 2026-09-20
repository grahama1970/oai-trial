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
ARG INCLUDE_DISCOVERY=0
ARG INCLUDE_MULTIMODAL=0
RUN if [ "$INCLUDE_MULTIMODAL" = "1" ]; then \
      apt-get update && apt-get install -y --no-install-recommends tesseract-ocr poppler-utils \
      && rm -rf /var/lib/apt/lists/*; \
    elif [ "$INCLUDE_MULTIMODAL" != "0" ]; then echo 'INCLUDE_MULTIMODAL must be 0 or 1' >&2; exit 2; fi \
    && if [ "$INCLUDE_DISCOVERY" = "1" ] && [ "$INCLUDE_MULTIMODAL" = "1" ]; then pip install '.[discovery,multimodal]'; \
    elif [ "$INCLUDE_DISCOVERY" = "1" ]; then pip install '.[discovery]'; \
    elif [ "$INCLUDE_MULTIMODAL" = "1" ]; then pip install '.[multimodal]'; \
    elif [ "$INCLUDE_DISCOVERY" = "0" ]; then pip install .; \
    else echo 'INCLUDE_DISCOVERY must be 0 or 1' >&2; exit 2; fi

# Preserve the brief's default-root mounted-run contract. Production callers can
# set both ANON_HOST_UID and ANON_HOST_GID; the launcher drops privileges before
# the engine starts so private mode-0600 receipts remain owned/readable by the
# invoking host identity.
ENTRYPOINT ["python", "-m", "anonymization_trial.container_entrypoint"]
CMD ["demo"]
