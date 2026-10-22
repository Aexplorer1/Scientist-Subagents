# Scientist Subagents

给 Codex 子代理分配随机科学家代号：例如 `curie`、`newton`、`feynman`。代号通过原生 `spawn_agent.task_name` 设置，专业职责写在任务消息里。主代理负责拆分独立任务、等待结果和汇总验证。

这是一个本地 Codex skill，采用 MIT 许可证。仅在明确调用 `$dispatch-scientist-subagents` 时启用，不会让所有聊天自动并行执行。

## 1. 环境要求与兼容范围

- 已安装并登录可正常使用的 Codex；Python **3.11+**（环境检查使用标准库 TOML 解析；名称脚本本身兼容 3.10+）；安装方式使用 Git。
- 当前会话必须暴露带 **`task_name`** 参数的 `spawn_agent`，以及列出、等待、发送消息和中断子代理的原生工具。
- 本地检查基线：**Codex CLI 0.163.0 / Windows / Python 3.13**，该 CLI 提供 `multi_agent` 和 `multi_agent_v2` 开关。其他版本需要运行下面的环境检查，不承诺旧版兼容。
- skill 只能使用宿主提供的工具，不能自行增加子代理能力。旧版接口若只有 `agent_type` / `fork_context` 而没有 `task_name`，不符合本 skill 的命名要求。
- 不需要额外的 MCP 服务、独立 API key、Python 第三方包或每位科学家的 agent 配置文件；沿用 Codex 当前登录、模型和权限。

## 2. 安装

推荐直接把本仓库克隆为一个完整的 skill 文件夹。根据[官方技能文档](https://learn.chatgpt.com/docs/build-skills)，当前用户级发现路径为 `~/.agents/skills`。

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force -Path "$HOME/.agents/skills" | Out-Null
git clone https://github.com/Aexplorer1/Scientist-Subagents.git "$HOME/.agents/skills/dispatch-scientist-subagents"
python "$HOME/.agents/skills/dispatch-scientist-subagents/scripts/check_environment.py"
```

如果系统的 Python 命令是 `py`，把最后一行开头的 `python` 换成 `py -3`。

### macOS / Linux

```sh
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/Aexplorer1/Scientist-Subagents.git "$HOME/.agents/skills/dispatch-scientist-subagents"
python3 "$HOME/.agents/skills/dispatch-scientist-subagents/scripts/check_environment.py"
```

已有同名文件夹时，请先检查现有内容，不要直接覆盖。配置了其他技能目录的客户端也可安装到它实际扫描的路径，例如部分现有安装使用的 `$CODEX_HOME/skills`（默认 `~/.codex/skills`）；同一 skill 只保留一份，避免重复发现。也可以在 Codex 中明确让内置 `$skill-installer` 从本仓库根目录 `.` 安装，目标名称使用 `dispatch-scientist-subagents`。

## 3. 开启相关设置

### Codex CLI

本 skill 的命名能力需要 V2 工具接口。对提供这些 feature 的版本，运行：

```sh
codex features enable multi_agent
codex features enable multi_agent_v2
```

然后重新启动 Codex，并新建会话。可先用 `codex features list` 确认两项均为 `true`。如果提示未知 feature，请升级 Codex，并再次检查，不能通过改任务提示词补出缺失的工具参数。

### Codex 桌面客户端

在客户端设置中打开 Codex 的 `config.toml`（通常为 `~/.codex/config.toml`，自定义 `CODEX_HOME` 时以该目录为准），将下面键合并到**已有**同名表中。不同版本的设置入口名称可能不同；也可以直接用文本编辑器打开此文件。

```toml
[features]
multi_agent = true
multi_agent_v2 = true

[agents]
enabled = true
max_concurrent_threads_per_session = 3
```

不要重复创建已有的 `[features]` 或 `[agents]` 表。`max_concurrent_threads_per_session` 是子代理数量上限，不含主代理；3 是示例，可按任务和账户限制调整。若已有 `[agents] enabled = false`，需要改为 `true`。CLI 的 `features enable` 只修改对应开关键，不会替你修改此项。

重启客户端并开启新聊天，让客户端重新加载配置。若技能列表中禁用了该 skill，请启用它；输入 `$` / 打开技能选择器，选择 **Scientist Subagents**。检查脚本读到的是本地 CLI 和配置，它不能证明另一个版本的桌面客户端已经加载相同工具。

当前官方文档说明子代理默认启用，并给出 `[agents]` 设置；但“可以使用子代理”和“可以指定 `task_name`”是两个检查项。`multi_agent_v2` 是本机 CLI 核实存在的版本相关开关，未来版本可能调整。参见[官方子代理说明](https://learn.chatgpt.com/docs/agent-configuration/subagents)。

## 4. 使用与验收

先执行环境检查；退出码 `0` 表示本地静态检查通过，`1` 表示有缺失项，`2` 表示运行或配置错误。检查只读，不修改配置、不创建代理，也不向外部服务提交任务。

随后在**新会话**明确发送：

```text
$dispatch-scientist-subagents
请用两个只读子代理分别检查当前项目的依赖清单和测试入口。
每个子代理只报告发现，不修改文件。等待两个结果，再汇总。
```

验收时确认：

1. 主代理确实调用原生工具创建了两个子代理。
2. `task_name` 使用脚本返回的不同小写科学家代号，职责在 `message` 中。
3. 支持的客户端活动视图显示对应代号，主代理等待两个结果后汇总。

只在回复里写出科学家名字不算通过。若只需要单条依赖链，skill 应说明不适合并行；若缺少工具，应报告缺失能力而不是伪装派发。子代理会消耗额外的模型用量，并继承当前会话的权限。

## 5. 常见问题

| 现象 | 检查方式 |
| --- | --- |
| 找不到 skill | 确认安装文件夹内直接包含 `SKILL.md`，检查客户端实际发现路径、技能是否禁用，重启后新建会话。 |
| 默认没有自动触发 | 设计如此：`agents/openai.yaml` 中 `allow_implicit_invocation: false`，请显式调用。 |
| 有子代理却不能命名 | 检查当前 `spawn_agent` 是否有 `task_name`；启用受支持的 V2 接口并新建会话。 |
| Python 找不到 | 安装 Python 3.11+；Windows 可用 `py -3`，macOS/Linux 常用 `python3`。 |
| 名称生成失败 | 单次最多可使用 23 个名称；后续波次用重复的 `--exclude NAME` 排除已用代号。名额耗尽时应停止并报告。 |
| 并发不足 | 减少并行数量或分波次执行，遵守宿主真实并发限制。 |

## 开发验证

```sh
python -m unittest discover -s tests -v
```

测试包含名称唯一性、排除、错误输入、命令行 JSON 输出，以及复制到带空格路径后的运行检查。GitHub Actions 在 Windows、macOS、Linux 上运行 Python 3.11 和 3.13 测试；CI 不启动付费 Codex 会话，不能代替第 4 节的真实工具与界面验收。

仓库根目录就是 skill 根目录；`agents/openai.yaml` 是技能显示元数据，不是 `[agents]` 配置，也不能注册原生工具。

发布前本地检查（2026-10-22）：13 项测试通过，skill 结构校验通过；将包复制到全新、带空格的项目路径后，Codex CLI 0.163.0 的原生 `skills/list` 成功发现该 skill，读取显示名且状态为启用；隔离配置中打开两个 feature 后，环境检查通过。本次未启动模型执行完整双代理任务，也未对各平台桌面界面进行验收。
