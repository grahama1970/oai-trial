# Self-contained image for the anonymization trial.
# docker build -t anonymization-trial .
# docker run --rm anonymization-trial            -> bundled demo
# docker run --rm -v IN:/trial/input:ro -v OUT:/trial/output anonymization-trial run
FROM python:3.12-slim

WORKDIR /trial

# Install the package first (deps are declared in pyproject.toml).
COPY pyproject.toml README.md ./
COPY src ./src
COPY fixtures ./fixtures
RUN pip install --no-cache-dir .

# Bare run executes the self-contained demo; `run` processes a mounted bundle.
ENTRYPOINT ["anonymization-trial"]
CMD ["demo"]
