# Acceptance Recipes — 三种"让系统自己报告状态"的验收配方

> 本文件是 `dfs-exec`（Gear 2/3）、`dfs-orchestrate`（verify before merge）、`dfs-review` 共用的验收参考。
> 核心原则一句话：**优先采集"被验证系统对自身状态的报告"，而不是"调用方对自己退出码的陈述"**。
> 退出码 0 只证明"没炸"，不证明"做对了"。下面三个配方各覆盖一类"零报错但结果是错的"。

---

## 配方 A · 前后快照回归（数据/输出类）

**适用**：任何碰数据库、生成文件、做迁移的任务。尤其是 Tier 3 的 schema 迁移。

```bash
# 跑前（基线快照）
python - <<'PY'
import sqlite3, hashlib, os, json
p = os.path.join(os.environ['LOCALAPPDATA'], 'lover-instance', 'data.db')
c = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
snap = {
  'tables': {n: c.execute(f'SELECT COUNT(*) FROM {n}').fetchone()[0]
             for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")},
  'sums':   {'word_freq': c.execute('SELECT COALESCE(SUM(cnt),0) FROM word_freq').fetchone()[0]},
  'versions': [r[0] for r in c.execute('SELECT DISTINCT model_version FROM sentiment')],
  'report_sha256': hashlib.sha256(open('out/report.html','rb').read()).hexdigest(),
}
print(json.dumps(snap, indent=1))
PY

# 跑后：同一条脚本，逐键比对。判定规则：
#   - 计数/sum 不变            → 幂等（重复跑不翻倍）
#   - 输出文件 sha256 相同     → 行为未变（重构安全的硬证据）
#   - 只有预期键变化           → 变化面与声明一致
```

**判定红线**：任何未预期的键变化都是 finding，不是"顺便提一下"。

---

## 配方 B · 状态机 kill/resume 演练（任务/作业类）

**适用**：任何带持久状态机的长任务（`queued/running/done/failed/interrupted`）。

```bash
# 1. 起任务，跑到一半强杀（模拟进程死亡，而非优雅退出）
./tool --long-running &  PID=$!
sleep 25 && kill -9 $PID

# 2. 读状态：必须留下"进行中 + 已提交进度"的检查点
sqlite3 data.db "SELECT id,status,done,total FROM jobs ORDER BY id DESC LIMIT 1;"
#    期望：status=running（或 interrupted）、done>0 —— 不是 0，也不是 done

# 3. 立即重启：必须被单飞/活性判定拦住，而不是静默双跑
./tool --long-running ; echo "exit=$?"     # 期望非 0 + 明确消息

# 4. 等活性窗口过期后重启：必须"接着跑"而不是"从头跑"
./tool --long-running | tail -1
#    期望：scored_this_run == total - 已检查点数（不是 total）
```

**判定红线**：第 3 步若静默成功（exit 0 并开始干活），说明单飞失效——两个进程会重叠写，
而累加型写（`cnt = cnt + x`）会让数据**翻倍**。第 4 步的"不重做"比"能跑完"更重要。

---

## 配方 C · 可视化自报告（UI/图表类）

**适用**：任何"渲染出来了"的交付物（报告、Dashboard、PDF 预览）。

`--screenshot` 在 `load` 事件就按下快门，异步图表（wordcloud、Vue mount 后的 ECharts）
还没画；`--virtual-time-budget` 会把计时器拍平，反而更容易出空白。正确顺序：

```bash
# 1. 以调试端口起 headless 浏览器（Edge/Chrome 均可）
msedge --headless=new --remote-debugging-port=9222 --window-size=1440,1800 about:blank &

# 2. Node 脚本（Node 22+ 自带全局 WebSocket）：导航 → 等真实时间 → 让页面自报 → 截图
#    workmem/cdp-shot.js 是可复制模板，三条 CDP 命令：
#      Page.navigate
#      Runtime.evaluate → 数每个 <canvas> 的不透明像素：
#          [...document.querySelectorAll('canvas')].map(c => {
#            const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
#            let lit = 0; for (let i = 3; i < d.length; i += 4) if (d[i] !== 0) lit += 1;
#            return lit; })
#      Page.captureScreenshot {captureBeyondViewport: true}
node cdp-shot.js "http://127.0.0.1:8787/" out.png 8000

# 3. 读 PNG 放大可疑区域（坐标轴标签、图例、空区）——文字类缺陷只有放大才看得见
python -c "from PIL import Image; im=Image.open('out.png'); im.crop((30,2540,1170,2960)).resize((2280,840)).save('zoom.png')"
```

**判定红线**：
- 像素数 = 0 而调用方报成功 → **空白图**（最常见：快门按早了）。
- 像素数 > 0 但文字被裁/数值异常 → **渲染正确、呈现错误**（实例：把拟合浮点
  `-0.3796374984823631` 直接交给坐标轴 `min/max`，ECharts 原样打印，被画布边缘裁成 `823631`）。
- 反向证据同样有效：门控场景断言 `canvas 数 == 0`（"不该画的时候真的没画"）。

---

## 配方 D · 人类产物的自动化安全（HITL 类）

**适用**：任何"人编辑、脚本读回"的产物（评测标签、评审清单、配置签字）。

三条硬规则，缺一条就会静默损坏人的输入：

1. **Round-trip 自检（生成侧）**：写文件前，用读回侧的正则/解析器验证**每一行都能被解析**。
   解析不了就拒绝写文件，不要"先写下去再说"。实例：表格渲染漏转义 `|`、行尾 `|` 被当成
   可选——3 行人工改判被静默吞掉，并据此得出了一个**看起来合理的错误结论**。
2. **Dry-run 先行（改写侧）**：任何重写人类输入的脚本，先 dry-run 并打印
   `reviewed / corrected / accepted` 三类计数，人确认后才落盘。
3. **只增不改（默认）**：自动化对人类判断值只能"追加溯源字段"（`label_source`、
   `previous_label`）；改判断值必须让人 visible 地确认。

**判定红线**：自动化触碰人类判断通道时，"跑完了"不等于"改对了"。宁可让脚本拒绝执行，
也不要让它安静地丢一行。
