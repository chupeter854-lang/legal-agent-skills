# legal-agent-skills

三个 agent 技能，配套使用。

适用于 **Hermes、Claude Code、Cursor、Codex** 等任何支持「技能文件 + 子代理 / 工具调用」的 agent 平台——技能本身是纯 Markdown 加几个 Python 脚本。两处例外以 Claude Code 为准：模型名（sonnet、haiku）和读写边界的一键脚本；其他平台按对应说明自行换算、配置。

**English:** [README.en.md](README.en.md)

| 技能 | 一句话 |
|---|---|
| **[subagent-dispatch](subagent-dispatch/SKILL.md)** | 拆不拆：决定一项工作自己做完，还是分派给子代理。核心判据是「材料不拆，职能可拆」。 |
| **[legal-case-workbench](legal-case-workbench/SKILL.md)** | 案件分析工作台：每个案件一个长期保存的工作空间，完成事实梳理与核实、法律检索、分析与起草。 |
| **[workspace-boundary](workspace-boundary/SKILL.md)** | 工作区边界：让 agent 只在指定的一个文件夹里读写。平台层用权限与沙箱设置锁死（Claude Code 有一键脚本和自测），技能层规定找不到就问、新文件放进对应案件的固定文件夹。 |

`subagent-dispatch` 是方法论，`legal-case-workbench` 是按它写死的一个具体实现，`workspace-boundary` 是底下的安全层（agent 只碰指定的文件夹）。三者可以单独用，但一起看更清楚——工作台里为什么要分三个角色、为什么证据不拆，答案在分派规则里。

## 三个技能解决的三个问题

**一、什么时候该派子代理？**

给单会话 agent 配上子代理工具后，会出现两种稳定失败：什么都不敢派（全挤在主上下文里，越做越慢），或者为了拆而拆（回来拼不起来，看着完整实际没核过）。

`subagent-dispatch` 把「要不要分工」从模型的临场判断改成一次性结构性判定：任务形状三分类、每条流能否独立自洽、三种伪装成独立的串行依赖、分派的五项代价、结果回收与验收、失败止损、哪些活根本不该交给 LLM。

**二、案件跟几个月，材料不断进来，怎么不被上下文撑爆？**

`legal-case-workbench` 的做法是把案件的记忆存在文件夹里而不是对话里：一页案件索引、材料登记、时间线、期限表、待办与争点、议题、材料卡。新开对话读完索引就能接着干。

分工只有三个角色：一个事实核查员掌握全部证据材料（入卷、交叉比对、回答事实问题）；一个法律检索员只拿去掉当事人信息的抽象法律问题去查法规和案例；主对话负责把事实和法律结合起来分析、起草、和律师沟通。

**三、agent 会不会到处读我电脑里的文件？**

不同 agent 对文件的处理差别很大，有的只在启动它的文件夹里读写，有的会读整台电脑。**技能里的提示词挡不住它**，真正的边界要靠平台的权限设置。`workspace-boundary` 分两层：平台层把文件工具和 shell 命令锁在一个“案件根目录”里（Claude Code 有一键脚本和自测脚本）；技能层规定 agent 找不到就问、不在外面搜、被挡住就报告。每个案件在根目录下有一个固定文件夹，按“当事人简称＋案由＋案件_建立日期”命名（如“徐某某买卖合同纠纷案件_20261101”），由工作台自动建；你说案件名，它就知道文件在哪里，不用每次选路径。

## 安装

放进你的 agent 技能目录即可，各平台路径不同，下面是两个例子：

```bash
cp -r subagent-dispatch legal-case-workbench workspace-boundary ~/.claude/skills/   # 例：Claude Code
cp -r subagent-dispatch legal-case-workbench workspace-boundary ~/.hermes/skills/   # 例：Hermes
```

三个都是纯 Markdown，另有少量 Python 脚本（`legal-case-workbench/scripts/`、`workspace-boundary/scripts/`），只用标准库，无外部依赖。

想以后用 `git pull` 更新，可以把仓库克隆到本地，再用软链接接进技能目录：

```bash
git clone https://github.com/chupeter854-lang/legal-agent-skills.git
ln -s "$PWD/legal-agent-skills/legal-case-workbench" ~/.claude/skills/legal-case-workbench
ln -s "$PWD/legal-agent-skills/subagent-dispatch"    ~/.claude/skills/subagent-dispatch
ln -s "$PWD/legal-agent-skills/workspace-boundary"   ~/.claude/skills/workspace-boundary
```

## 怎么启动

技能不会自己开新对话。先设好案件根目录（见下表最后一项），以它为工作文件夹新建一个对话，说“给徐某某买卖合同纠纷建个档”；以后每次新开对话说“打开徐某某的案子”，它读一页案件索引就接着干。读材料、查法条的活由它在当前对话里派子代理完成，子代理不是新会话。详见 [legal-case-workbench/README.md](legal-case-workbench/README.md) 的“怎么启动”。

## 部署前要改的五处

技能不绑定具体平台和服务，但有几处必须按你的环境填：

| 项 | 说明 |
|---|---|
| 保密与脱敏要求 | 复制 `legal-case-workbench/references/本地配置.示例.md` 为 `本地配置.md`，写入哪些案件不建档、脱敏标准、材料目录约定、要衔接的技能。该文件已写入 `.gitignore`，不会被提交；技能每次先读它 |
| 法律检索渠道 | 默认用北大法宝 MCP（工具名 `pkulaw` 下的七个工具）。没有的，改成你手上的数据库，或降级到官方法规库 |
| 额度预算 | 检索一次、复核一次各算一次调用；按你的账户调整估算系数 |
| 子代理模型 | 分层轴是「错了能不能被发现」，不是「活难不难」。法律检索不要用最便宜的档 |
| 案件根目录与读写边界 | 选一个专用文件夹作为案件根目录，运行 `workspace-boundary/scripts/setup_workspace.py` 设好边界；私密材料、原件不放进去 |

## 一个必须知道的平台差异：能不能续用子代理

- **能续用的平台**（例如 Claude Code：用 SendMessage 给已经结束的子代理发消息，它带着原来的上下文接着干）：同一次工作里的事实追问和下一批材料，都交给同一个事实核查员。
- **子代理一次性的平台**：跑完即结束。新材料入卷时新派一个，派单里写明「先读材料登记、时间线、期限表、材料卡，再处理本批」；运行中要补话，用平台的插话通道。

两种情况下，案卷文件都是记忆的正本：子代理记得但没写进文件的，不算数。

## 试跑

`legal-case-workbench/examples/虚构买卖合同案/` 是一个全部虚构的买卖合同案件（两批 7 份材料），故意埋了几处要靠交叉比对才能发现的矛盾，可以用来检验事实核查员。它在技能文件夹里，随技能一起安装；装好后对 agent 说“用案件分析工作台自带的示例案件试跑一下”即可。

## 来源

核心命题——分工不该由模型临场判断、双层架构与订阅直通、批处理与上下文组织——来自 DeepSeek Harness 团队《Super-agent 设计探索：迈向更自主的 Agent 系统》（2026-10-31），其中的消融实验和压力测试数据是本仓库多处判断的依据。

Agent Skills 的通用写法参考了 Anthropic 的 agent skills 约定。

## License

MIT
