#!/bin/bash
# 在 aosp17-ai 容器内运行一次：为挂载的源码树建立工具链软链接并自检。
# 用法: /aosp/aosp17-docker/dk exec aosp17-ai bash /workspace/deploy/server/ai-container-setup.sh
set -e

apt-get update -o Acquire::Retries=3 >/dev/null 2>&1 || true
apt-get install -y --no-install-recommends -o DPkg::Options::=--force-unsafe-io ripgrep jq

TOOLS=/workspace/fde-build/prebuilts/mesa-tools
for tool in mesa_clc asahi_clc panfrost_compile vtn_bindgen2; do
    if [ -x "$TOOLS/$tool" ]; then
        ln -sf "$TOOLS/$tool" /usr/local/bin/"$tool"
    fi
done

[ -x /usr/local/bin/glslang ] && ln -sf /usr/local/bin/glslang /usr/local/bin/glslangValidator

echo "== python 模块 =="
python3 -c 'import packaging, yaml, pycparser, mako; print("python modules OK")'

echo "== 工具版本 =="
node --version
pi --version
gh --version | head -1
adb version 2>/dev/null | head -1 || true
glslangValidator --version 2>/dev/null | head -1 || true

echo "== 挂载自检 =="
[ -d /workspace/fde-build/.repo ] && echo "fde-build OK" || echo "警告: fde-build 未挂载"
[ -d /workspace/fde-sources/.repo ] && echo "fde-sources OK" || echo "警告: fde-sources 未挂载"

echo "aosp17-ai 容器自检完成"
