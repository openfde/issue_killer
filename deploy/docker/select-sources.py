#!/usr/bin/env python3
"""从 repo 解析后的 manifest 中选择需要同步的项目。

用法: select-sources.py <manifest.xml> <module> [<module> ...]
输出: 每行一个 project name（去重，保持 manifest 顺序）。
"""

import sys
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: select-sources.py <manifest.xml> <module> [...]", file=sys.stderr)
        return 2

    manifest, modules = sys.argv[1], set(sys.argv[2:])
    tree = ET.parse(manifest)
    seen: set[str] = set()

    for project in tree.iter("project"):
        name = project.get("name")
        if not name or name in seen:
            continue
        path = project.get("path") or name
        top = path.split("/", 1)[0]
        if top in modules:
            seen.add(name)
            print(name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
