# Codex Red Team Opt-In Mode

[English](./README.md)

> 默认保持 normal，只有显式开启时才进入 red-team。

这是一个面向 Codex 的**轻量、pack-first** 红队运行时 / 配置层。

它的目标不是把 Codex 变成自动化攻击平台

## 项目说明

- 这个仓库是 **GitHub 通用版**
- 不应包含个人本地路径、私有目标数据或用户专属工具偏好
- 文档描述必须和当前实际运行行为一致，不能写成“计划中的样子”

## 为什么做这个项目

很多“常驻红队提示词”最后都会变成两种坏结果：

1. **污染普通工作**
2. **注入过重，导致上下文膨胀**

这个项目反过来做：

- **普通模式保持普通**
- **红队模式必须显式开启**
- **hooks 保持轻量**
- **路由保持分层与克制**

## 核心特性

- opt-in 红队模式
- `normal` / `redteam-light` / `redteam-full`
- 结构化 JSON 运行时状态
- 规则优先 + 语义兜底的 phase 检测
- session 隔离状态文件
- 轻量 prompt overlay
- pack-first 路由主线：

```text
phase -> router -> pack -> leaf
```

## 覆盖场景

核心 phase：

- web
- ad
- postex
- reverse
- code-audit
- payload
- evasion

扩展 router / pack 家族：

- recon
- api
- auth
- injection
- file
- business logic
- cloud
- container / kubernetes
- network / protocol
- crypto
- mobile

## 安装

安装器采用**托管式增量安装**：

- 保留用户原有 `AGENTS.md`
- 保留用户原有 `hooks.json`
- 只注入本仓库的托管区块
- 删除本仓库旧版本 runtime 残留
- 干净安装当前版本
- 写入 install manifest
- 安装后自动执行 validate

### Python

```bash
python scripts/install.py
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

### macOS / Linux

```bash
python3 scripts/install.py
```

## 快速开始

### 开启 red-team mode

```text
进入红队模式
开启红队模式
/redteam on
/redteam light
/redteam full
enable red team mode
```

### 关闭 red-team mode

```text
退出红队模式
关闭红队模式
/redteam off
disable red team mode
```

### 验证安装

```bash
python scripts/validate.py
```

## 工作方式

### 运行时主线

当前实际路由主线是：

```text
phase -> router -> pack -> leaf
```

`method` 仍然存在，但只在确实有帮助时作为软提示使用，不再是主路由轴。

### 模式说明

| 模式 | 默认 | 典型用途 |
|---|---:|---|
| `normal` | 是 | 编码、文档、普通研究 |
| `redteam-light` | 否 | 定向安全分析、规划、复核 |
| `redteam-full` | 否 | 更强约束的红队工作流 |

## 验证

仓库内置了：

- installer 检查
- routing 测试
- mode 切换测试
- orchestration gate 检查
- prompt-chain 检查

可执行：

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/validate.py
```

## 已知限制

- 这是控制层 / 配置层，不是完整攻击平台
- prompt overlay 的实际效果仍依赖目标 Codex 环境
- 用户本地私人 prompt 体系可能与仓库版不同
- 实际执行深度仍依赖你的 MCP / 工具面


⚠️ 免责声明
本项目仅供授权渗透测试（Authorized Penetration Testing）、红队研究与防御性安全实验使用。

仅限在你拥有明确授权的系统或环境中使用。
未经授权用于第三方或生产系统属于禁止行为。
作者及贡献者对误用、法律后果、服务中断或数据损失 不承担任何责任。
使用本项目即表示你同意自行承担全部风险，并确保行为符合适用法律和规则。

## 贡献与致谢
感谢米斯特安全团队的洺熙大佬提出的修改意见：加入语义判定，取消方法论，细分skill，让AI在工作阶段更智能。。
洺熙 X：@xishan12509850

感谢Nirvana提出的修改意见：优化工作流程，实现覆盖安装 Nirvana X：@Nirvana_543

感谢PINGS提出的修改意见：强化越狱文本

感谢 qiushi-skill、hack-skills 与 Anthropic-Cybersecurity-Skills 提供的方法层、技术路由层与 skill pack 结构参考。
参考项目：qiushi-skill / yaklang/hack-skills / mukul975/Anthropic-Cybersecurity-Skills

## 贡献

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

MIT，见 [LICENSE](./LICENSE)。
