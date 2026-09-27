---
title: "Pi-Agent MCP 集成指引"
created: 2026-09-05
updated: 2026-09-05
type: reference
audience: agent
tags:
  - topic/agent-sdk
  - category/reference
status: stable
---

# Pi-Agent MCP 集成指引

> 如何用 MCP 工具增强 Pi-Agent 开发体验。

---

## 1. search_vault — 本地知识库检索

**用途**：查询 Defensive Skills 中的架构模式、踩坑经验、设计决策。

**调用方式**：
```
search_vault(query='agent loop pattern')
search_vault(query='tool call trap')
search_vault(query='event driven architecture')
```

**典型场景**：
- 遇到架构问题时：`search_vault(query='agent loop pattern')`
- 遇到踩坑时：`search_vault(query='tool call trap')`
- 需要设计决策参考时：`search_vault(query='event driven architecture')`

**知识库笔记位置**：
- 架构模式：[[01-Rules/AGENT-SDK-PATTERNS]]
- Pi-Agent 实现：[[08-Projects/Pi-Agent/ARCHITECTURE]]
- 踩坑经验：[[08-Projects/Pi-Agent/GOTCHAS]]

---

## 2. context7 — 动态文档查询

**用途**：查询 Pi-Agent SDK 最新文档和代码示例。

**调用方式**：
```
context7(libraryId='@earendil-works/pi-coding-agent', query='createAgentSession options')
context7(libraryId='@earendil-works/pi-coding-agent', query='pi.on event types')
```

**典型场景**：
- 查 API 签名：`context7(query='createAgentSession parameters')`
- 查 SDK 变更：`context7(query='pi-coding-agent changelog')`
- 查使用示例：`context7(query='defineTool example')`

---

## 3. fetch — 外部资源抓取

**用途**：抓取 GitHub release notes、博客文章等外部资源。

**调用方式**：
```
fetch(url='https://github.com/earendil-works/pi/releases')
```

**典型场景**：
- 查看最新 release：`fetch(url='https://github.com/earendil-works/pi/releases')`
- 抓取 API 文档：`fetch(url='https://raw.githubusercontent.com/...')`

---

## 4. 综合工作流

```
用户问题
  │
  ├── 架构/设计问题 → search_vault(query='...')
  │                    └── 找到 → 直接引用
  │                    └── 未找到 → context7(query='...')
  │
  ├── API/用法问题 → context7(libraryId='...', query='...')
  │                  └── 找到 → 返回示例
  │                  └── 未找到 → fetch(url='GitHub docs')
  │
  └── 版本/变更问题 → fetch(url='GitHub releases')
                      └── 解析 CHANGELOG
                      └── 评估影响
```

---

## 5. 最佳实践

- **优先本地**：先 search_vault，再 context7，最后 fetch
- **精确查询**：query 越具体，结果越好
- **缓存友好**：相同查询在会话内复用结果
- **版本对齐**：context7 查询时指定版本号
