---
name: publish-intake-issue
description: 当取证草稿已生成、需要人工确认后自动创建 GitHub issue 并上传取证附件时使用。
---

# 发布取证 issue

把 `data/intake/<slug>/issue-draft.md` 发布为 GitHub issue。默认同时把 intake 目录中的取证文件上传为 GitHub Release asset，并把链接写入正文 `## 取证包`。**必须人工确认**，不得默认发布。

## 用法

```text
/skill:publish-intake-issue 2026-10-28-applist-filter
/skill:publish-intake-issue 发布 2026-10-28-applist-filter
```

也接受自然语言：`把取证包 2026-10-28-applist-filter 发成 issue`。

## 步骤

1. 确认 `data/intake/<slug>/issue-draft.md` 存在；标题优先读 `title.txt`，否则读 `issue-draft.md` 或让调用方给标题。
2. 先 dry-run，展示：

   ```bash
   python3 automation/create_issue.py --workspace . --intake <slug> --dry-run
   ```

   报告：标题、正文摘要、待上传附件列表、目标 repo/release、`body_sha256`。dry-run 不创建 issue、不上传附件。

3. 给一次确认菜单：

   ```text
   A. 发布（正文 + 附件）
   B. 修改标题/正文后再发布
   C. 取消
   ```

4. 只有明确选择 A 后，执行：

   ```bash
   python3 automation/create_issue.py --workspace . \
     --intake <slug> --repo <repo> --confirm
   ```

   可选：`--evidence-repo <附件仓库>`、`--evidence-tag <tag>`、`--evidence-url <外部链接>`、`--label <标签>`、`--no-upload-attachments`。

5. 校验 `data/intake/<slug>/issue.json` 和 issue URL；报告附件是否上传。上传失败时脚本返回非零，**不要创建 issue，也不要声称附件已上传**。

## 权限

- `GH_TOKEN`：Issues 写、Contents 写（release）
- 先执行 `gh auth status`；失败即停止
- 默认 release 在 issue 仓库；如果仓库私有，链接对无权限用户不可见，建议用 `--evidence-repo` 指向公开的 evidence 仓库

## 边界

- 不自动关闭 issue、不自动评论、不批量创建、不整理其他 issue
- 不修改源码、不推送
- 附件上传失败时不回退成“只发正文”；由调用方决定是否改用 `--no-upload-attachments`
- 不把 `draft`/`dry-run` 结果说成已发布
