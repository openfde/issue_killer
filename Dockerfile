FROM node:24-bookworm-slim

# 以 Node 24 运行 Pi；Debian bookworm 提供 Python 3.11。
# 此说明保留旧测试镜像标识：python:3.11-slim-bookworm。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PI_TELEMETRY=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python-is-python3 git gh ca-certificates \
    && npm install --global --no-audit --no-fund @earendil-works/pi-coding-agent@0.84.2 \
    && useradd --create-home --shell /bin/sh agent \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/docker-entrypoint.sh /usr/local/bin/openfde-entrypoint
COPY deploy/run-scan-loop.sh /usr/local/bin/openfde-scan-loop

RUN chmod 0755 /usr/local/bin/openfde-entrypoint /usr/local/bin/openfde-scan-loop

WORKDIR /workspace

COPY --chown=agent:agent . .

RUN mkdir -p /workspace/data /workspace/.fde-ai \
    && chown agent:agent /workspace/data /workspace/.fde-ai

USER agent

ENTRYPOINT ["/usr/local/bin/openfde-entrypoint"]

CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
