FROM node:24-bookworm-slim

# 以 Node 24 运行 Pi；Debian bookworm 提供 Python 3.11。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PI_TELEMETRY=0

ARG NPM_REGISTRY=https://registry.npmjs.org
ARG DEBIAN_MIRROR=mirrors.tuna.tsinghua.edu.cn
RUN sed -i "s|deb.debian.org|$DEBIAN_MIRROR|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
    sed -i "s|deb.debian.org|$DEBIAN_MIRROR|g" /etc/apt/sources.list 2>/dev/null || true; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python-is-python3 git openssh-client gh ca-certificates curl ripgrep fd-find util-linux \
    && (apt-get install -y --no-install-recommends adb || apt-get install -y --no-install-recommends android-tools-adb) \
    && adb version \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
    && fd --version \
    && npm config set registry "$NPM_REGISTRY" \
    && npm install --global --no-audit --no-fund @earendil-works/pi-coding-agent@0.84.2 \
    && useradd --create-home --shell /bin/sh agent \
    && rm -rf /var/lib/apt/lists/*

# Android repo 工具（repo 模式需要；默认 GitHub 同步不依赖它，下载失败不阻塞构建）。
ARG REPO_URL=https://storage.googleapis.com/git-repo-downloads/repo
ARG REPO_FALLBACK_URL=https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/repo
RUN if curl -fsSL "$REPO_URL" -o /usr/local/bin/repo || curl -fsSL "$REPO_FALLBACK_URL" -o /usr/local/bin/repo; then \
        chmod 0755 /usr/local/bin/repo && repo --version; \
    else \
        echo "warning: repo launcher unavailable; github source sync still works"; \
    fi

COPY deploy/docker-entrypoint.sh /usr/local/bin/openfde-entrypoint
COPY deploy/run-scan-loop.sh /usr/local/bin/openfde-scan-loop
COPY --chown=agent:agent deploy/server/pi-agent-template/settings.json /opt/pi-agent-template/settings.json
COPY --chown=agent:agent deploy/server/pi-agent-template/models-store.json /opt/pi-agent-template/models-store.json

RUN chmod 0755 /usr/local/bin/openfde-entrypoint /usr/local/bin/openfde-scan-loop

WORKDIR /workspace

COPY --chown=agent:agent . .

RUN mkdir -p /workspace/data /workspace/.fde-ai /workspace/pi-agent \
    && chown agent:agent /workspace/data /workspace/.fde-ai /workspace/pi-agent

USER agent

ENTRYPOINT ["/usr/local/bin/openfde-entrypoint"]

CMD ["/usr/local/bin/openfde-scan-loop"]
