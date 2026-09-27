# pi-agent SDK Skill Maintenance & Upgrade Protocol

本文档定义 `dfs-agent-sdk` 技能的维护准则、升级审查流程以及从源码/踩坑向知识库回流的 6 大沉淀原则。

---

## 知识沉淀 6 大核心原则 (Ingestion Principles)

从 `node_modules` 源码排障、踩坑或日常开发向本 skill 沉淀知识时，必须严格遵守以下 6 项原则：

1. **真实证据驱动 (Evidence-Driven)**
   - 绝不凭推测或 AI 臆造编写 API 行为说明。必须有真实运行报错、堆栈日志或源码实现作为事实依据。
2. **就近就简模块化 (Colocated & Modular)**
   - API 细节、类型定义推到 `references/sdk_doc/`；典型场景实战代码归入 `references/scenarios/`。`SKILL.md` 仅保留核心心智模型与路由索引，严格控制上下文体积。
3. **最小有效知识 (Token-Efficient Minimal Knowledge)**
   - 提炼关键抽象、核心陷阱与规避策略，避免无意义的大段文档复制。每个引用文件只解决一个清晰的架构或工程问题。
4. **防御性与可验证性 (Defensive & Verifiable)**
   - 涉及事件流、并发控制或生命周期的知识点，必须注明防御措施（如 fire-and-forget 异步推入队列、避免死锁）以及最小验证方式。
5. **基线版本严格对齐 (Baseline Alignment)**
   - 所有代码示例与 API 签名必须与当前基线版本保持一致。禁止混入 latest 版本未稳定或与基线冲突的推测性 API。
6. **双向审查与用户确认 (Maker-Checker & User Consent)**
   - 从源码排查获得的兜底方案，在合并入 skill 前须经开发者确认，防止项目特化的 Hack 代码污染通用知识库。

---

## SDK 版本升级审查流程 (Upgrade Protocol)

当需要将 pi-agent SDK 基线版本升级至新版本时，按以下四步流水线执行：

### Step 1: 变更日志与破坏性差异审查 (Changelog Audit)
- 抓取 GitHub Release Notes 或 CHANGELOG：
  ```bash
  gh release view v<target_version> --repo earendil-works/pi
  ```
- 重点筛查破坏性变更（Breaking Changes）：
  - `createAgentSession` 参数签名变动。
  - `pi.on` 与 `session.subscribe` 事件生命周期更名或废弃。
  - 核心类型定义（如 `AgentSession`, `ModelRegistry`, `ExtensionFactory`）变动。

### Step 2: 符号拓扑与类型定义对比 (d.ts Diff)
- 对比新旧版本的 `.d.ts` 导出符号：
  ```bash
  diff -u node_modules/@earendil-works/pi-coding-agent/dist/index.d.ts <new_dts>
  ```
- 确认是否有被移除或重命名的属性、接口与枚举。

### Step 3: 更新 references/ 知识切片与场景代码
- 检查 `references/sdk_doc/` 下对应文档，同步参数名与返回类型。
- 检查 `references/scenarios/` 下的场景验证代码，确保在新版本下可以通过编译与测试。

### Step 4: 更新基线版本号与发布
- 更新 `SKILL.md` 中的版本描述及相关前置依赖版本说明。
- 运行测试套件校验技能一致性：
  ```bash
  # DFS-PORT: repo-local gate path; the private vault tree keeps its own scripts/tests copy
  python3 -m unittest -v tests/test_skills_conformance.py
  ```
- 提交 Git Commit：
  ```bash
  git commit -m "chore(skills): upgrade dfs-agent-sdk baseline to <target_version>"
  ```
