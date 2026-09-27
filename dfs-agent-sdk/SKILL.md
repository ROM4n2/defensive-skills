---
name: dfs-agent-sdk
description: Develop with pi-agent SDK and enterprise LLM endpoints.
version: 0.2.0
author: Defensive Skills contributors
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pi-agent, sdk, agent-session, define-tool, extensions, enterprise-api]
    related_skills: [dfs-pipeline, dfs-exec]
    mcp_tools: [search_vault]
---

# pi-agent SDK Knowledge-Enhanced Skill

> Pi-Agent SDK 开发的知识库增强 skill。API 细节推到 `references/`，本文件只做路由和心智对齐。

## Core Mental Model

```
createAgentSession()     -- 组装入口(Provider + 工具 + 资源)
       |
       +-- session.prompt(text)        -- 驱动 Agent 主循环
       |
       +-- session.subscribe(handler)  -- 外部订阅(外部层事件)
       |     turn_* / message_* / tool_execution_* / agent_settled / queue_update
       |
       +-- pi.on(event, handler)       -- 扩展订阅(内部层事件)
             context / tool_call / tool_result / before_agent_start / input / model_select
```

**关键区分**：6 个扩展独有事件用 `session.subscribe` 监听会**静默失败**。需要抓这 6 个事件必须写成扩展走 `pi.on`。

## 3 Key Pitfalls

1. **subscribe vs pi.on 混用** -- 6 个扩展独有事件(context/tool_call/tool_result/before_agent_start/input/model_select)用 subscribe 会静默丢弃。
2. **pi.on 阻塞 agent loop** -- pi.on handler 被派发方 await，落库等慢 I/O 必须 fire-and-forget（推队列后台写）。
3. **版本漂移** -- 安装 latest 而非基线版本，API 描述立即失效。

## Scenario Routing

| 任务类型 | 路由 |
|---------|------|
| 创建 Agent / 会话管理 | [references/sdk_doc/](references/sdk_doc/) |
| 自定义工具(defineTool) | [references/sdk_doc/](references/sdk_doc/) |
| 事件系统(subscribe / pi.on) | [references/sdk_doc/04-events.md](references/sdk_doc/04-events.md) |
| 扩展开发(extensionFactories) | [references/sdk_doc/](references/sdk_doc/) |
| 模型配置 / Provider | [references/sdk_doc/](references/sdk_doc/) |
| 企业接口接入评估 | 本文件 -> 知识库集成 |
| Skill 维护 / 升级 | [references/skill-maintenance.md](references/skill-maintenance.md) |

## Knowledge Base Integration

遇到问题时优先查 Obsidian 知识库，不要凭记忆写代码：

- **架构问题**（agent loop 模式、扩展设计）: `search_vault(query='agent loop pattern')`
- **踩坑经验**（静默失败、阻塞陷阱）: `search_vault(query='tool call trap')`
- **需要最新文档**（API 签名、参数变化）: `context7(libraryId='npm:@earendil-works/pi-coding-agent', query='...')`
- **接口协议**（OpenAI 兼容判断）: `search_vault(query='OpenAI compatible endpoint')`

## MCP Tool Quick Reference

| 工具 | 使用场景 | 示例 |
|------|---------|------|
| `search_vault` | 查本机 Obsidian 知识库中的规范、踩坑、模板 | `search_vault(query='pi-agent event subscribe')` |
| `context7` | 查 npm 包最新文档，验证 API 签名 | `context7(libraryId='npm:@earendil-works/pi-coding-agent', query='defineTool')` |
| `fetch` | 抓 GitHub CHANGELOG / release notes | 用于升级评估，对比基线与 latest 变更 |

## Version Protocol

本 skill 对齐到指定基线版本（见 references/）。升级时遵循：默认装基线版本，不装 latest；升级前用 GitHub 渠道对比 CHANGELOG 评估破坏性变更；升级后按 `references/skill-maintenance.md` 流程审查 skill 差异并更新基线版本号。详见 [references/](references/)。
