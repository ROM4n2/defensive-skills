---
title: "Pi-Agent 场景路由矩阵"
created: 2026-09-05
updated: 2026-09-05
type: reference
audience: agent
tags:
  - topic/agent-sdk
  - category/reference
status: stable
---

# Pi-Agent 场景路由矩阵

> 按任务类型组合场景文件，快速定位所需参考文档。

---

## 任务类型路由

### 从零搭建 DataAgent
A01（最小化启动）→ A02（模型选择）→ A03（系统提示词）→ D01（自定义工具）→ E02（扩展基础）→ F01（会话持久化）

### 企业内网模型接入
B01（认证配置）→ A02（模型选择）→ B03（可用模型）

### 自定义工具 + 拦截
D01（自定义工具）→ D02（动态工具）→ E01（工具拦截）→ E02（扩展基础）

### 会话持久化 + 恢复
F01（会话持久化）→ F02（会话运行时）→ F05（控制会话）

### 系统提示词与 Skill 定制
C01（自定义 Skill）→ C02（Prompt 模板）→ C03（Context Files）

### 认证与密钥管理
B01（认证配置）→ B02（设置）→ A04（工具白名单）

### 多 Agent 协作
H06（多 Agent 协作）→ H01（完全控制）→ I05（子 Agent）→ F01（会话持久化）

### 扩展开发与分发
E02（扩展基础）→ E04（生命周期钩子）→ I01（Pi Package 打包）→ I02（分发扩展）

### 上下文与性能优化
G01（上下文注入）→ G02（自定义压缩）→ G03（自动总结）→ G04（预加载上下文）

---

## 场景编号索引

### A - 核心启动配置

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| A01 | 最小化启动 | `A01-minimal-startup.md` |
| A02 | 模型选择 | `A02-model-selection.md` |
| A03 | 系统提示词 | `A03-system-prompt.md` |
| A04 | 工具白名单 | `A04-tool-whitelist.md` |
| A05 | 自定义工作目录 | `A05-custom-cwd.md` |
| A06 | 加载扩展 | `A06-load-extensions.md` |

### B - 认证与配置

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| B01 | 认证配置 | `B01-auth-config.md` |
| B02 | 设置 | `B02-settings.md` |
| B03 | 可用模型 | `B03-available-models.md` |
| B04 | 项目信任 | `B04-project-trust.md` |

### C - Skill 与提示词

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| C01 | 自定义 Skill | `C01-custom-skill.md` |
| C02 | Prompt 模板 | `C02-prompt-templates.md` |
| C03 | Context Files | `C03-context-files.md` |

### D - 工具

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| D01 | 自定义工具 | `D01-custom-tool.md` |
| D02 | 动态工具 | `D02-dynamic-tools.md` |
| D04 | 确认破坏性操作 | `D04-confirm-destructive.md` |
| D05 | 工具结果渲染 | `D05-tool-result-render.md` |
| D06 | 受保护路径 | `D06-protected-paths.md` |

### E - 扩展与拦截

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| E01 | 工具拦截 | `E01-tool-intercept.md` |
| E02 | 扩展基础 | `E02-extension-basics.md` |
| E04 | 生命周期钩子 | `E04-lifecycle-hooks.md` |
| E05 | 输入转换 | `E05-input-transform.md` |
| E06 | 流式转换 | `E06-streaming-transform.md` |
| E11 | SSE 进度流 | `E11-sse-progress-streaming.md` |

### F - 会话管理

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| F01 | 会话持久化 | `F01-session-persistence.md` |
| F02 | 会话运行时 | `F02-session-runtime.md` |
| F04 | 中止会话 | `F04-abort-session.md` |
| F05 | 控制会话 | `F05-steer-session.md` |

### G - 上下文与压缩

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| G01 | 上下文注入 | `G01-context-injection.md` |
| G02 | 自定义压缩 | `G02-custom-compaction.md` |
| G03 | 自动总结 | `G03-auto-summarize.md` |
| G04 | 预加载上下文 | `G04-preload-context.md` |

### H - 高级控制

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| H01 | 完全控制 | `H01-full-control.md` |
| H02 | 自定义 Provider | `H02-custom-provider.md` |
| H03 | 模拟 Provider | `H03-faux-provider.md` |
| H06 | 多 Agent 协作 | `H06-multi-agent.md` |
| H07 | 企业接口 | `H07-enterprise-interface.md` |

### I - 分发与沙箱

| 编号 | 场景名称 | 文件 |
|------|---------|------|
| I01 | Pi Package 打包 | `I01-pi-package.md` |
| I02 | 分发扩展 | `I02-distribute-extension.md` |
| I03 | 扩展依赖 | `I03-extension-deps.md` |
| I04 | 沙箱 | `I04-sandbox.md` |
| I05 | 子 Agent | `I05-subagent.md` |

---

## 使用方式

1. 确定任务类型
2. 按路由表顺序阅读场景文件
3. 前置场景包含后续场景所需的上下文
