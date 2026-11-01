# legal-agent-skills

Three agent skills, meant to be used together.

Works on **Hermes, Claude Code, Cursor, Codex** and any other agent platform that supports skill files plus subagents or tool calls — the skills are plain Markdown with a few Python scripts, bound to no specific platform.

**中文：**[README.md](README.md)

| Skill | In one line |
|---|---|
| **[subagent-dispatch](subagent-dispatch/SKILL.md)** | To split or not to split: deciding whether a piece of work gets done in the main context or handed to a subagent. The core rule is "material stays whole; functions may split". |
| **[legal-case-workbench](legal-case-workbench/SKILL.md)** | A case analysis workbench: one long-lived workspace per case, where fact verification, legal research, analysis and drafting all happen. |
| **[workspace-boundary](workspace-boundary/SKILL.md)** | Workspace boundary: keep the agent reading and writing inside one folder you choose. Platform settings lock it in (a one-step script plus self-test for Claude Code); working rules make it ask instead of searching, and keep new files in each case's fixed folder. |

The first is a methodology; the second is one concrete implementation of it. Each works on its own, but they read better together — why the workbench uses three roles, and why evidence is never split, is answered in the rules.

Both are written for legal practice, but the dispatch rules are domain-neutral.

## The two problems they solve

**One: when should work go to a subagent?**

Wire a subagent tool into a single-session agent and two failures appear reliably. It never delegates — everything piles into the main context and slows down as it goes. Or it splits for the sake of splitting — the pieces don't reassemble, and the result looks complete while never having been verified.

`subagent-dispatch` turns "should I split this" from an in-the-moment judgment into a one-time structural decision: three task shapes, whether each stream can stand alone, three kinds of disguised serial dependency, the five costs of dispatch, how to collect and verify what comes back, when to cut a subagent off, and which work shouldn't go to an LLM at all.

**Two: a case runs for months and material keeps arriving. How do you stop the context from blowing up?**

`legal-case-workbench` keeps the case's memory in a folder instead of a conversation: a one-page case index, material register, timeline, deadline table, open items and disputes, issue files, material cards. Open a new conversation, read the index, and carry on.

There are exactly three roles. One **fact verifier** holds all the evidence — filing, cross-checking, answering factual questions. One **legal researcher** takes only abstract legal questions with party details stripped, and looks up statutes and cases. The **main dialogue** combines facts and law, drafts, and talks to the lawyer.

## Install

Drop them into your agent's skills directory — the path varies by platform; two examples:

```bash
cp -r subagent-dispatch legal-case-workbench workspace-boundary ~/.claude/skills/   # e.g. Claude Code
cp -r subagent-dispatch legal-case-workbench workspace-boundary ~/.hermes/skills/   # e.g. Hermes
```

Both are plain Markdown plus a few Python scripts (`legal-case-workbench/scripts/`) with no external dependencies.

To update later with `git pull`, clone the repo and symlink the skills into your skills directory:

```bash
git clone https://github.com/chupeter854-lang/legal-agent-skills.git
ln -s "$PWD/legal-agent-skills/legal-case-workbench" ~/.claude/skills/legal-case-workbench
ln -s "$PWD/legal-agent-skills/subagent-dispatch"    ~/.claude/skills/subagent-dispatch
ln -s "$PWD/legal-agent-skills/workspace-boundary"   ~/.claude/skills/workspace-boundary
```

## Getting started

The skill does not open new conversations by itself. Start a new conversation and say "给某某案建立案件工作台" (set up a case workbench for case X); each later session, open a new conversation and say "打开某某案" (open case X) — it reads the one-page case index and carries on. Reading material and looking up law are done by subagents it dispatches inside the current conversation; they are not separate sessions. See "怎么启动" in [legal-case-workbench/README.md](legal-case-workbench/README.md).

## Read/write boundary: the agent touches only the folder you choose

Agents differ widely in how they treat files; some will read the whole machine. **A prompt in a skill cannot stop that** — the real boundary comes from the platform's permission settings. `workspace-boundary` ships a one-step script for Claude Code: pick a cases root as the workspace, and both file tools and shell commands are locked inside it, with a self-test to confirm it actually holds. Each case gets one fixed folder under the root, named "party short name + cause of action + 案件_creation date" (e.g. "徐某某买卖合同纠纷案件_20261101") and created by the workbench; name the case and it knows where the files are, so you never pick a path.

## Four things to fill in before deploying

The skills bind no specific platform or service, but four items are environment-specific:

| Item | What to do |
|---|---|
| Confidentiality and de-identification rules | Copy `legal-case-workbench/references/本地配置.示例.md` to `本地配置.md` and fill in which cases get no workbench, your de-identification standard, where materials live, and which skills to hand off to. That file is in `.gitignore` and never committed; the skill reads it first every time. |
| Legal research source | Defaults to PKULaw MCP (seven tools under the service name `pkulaw`). Without it, swap in whatever database you have, or fall back to the official statute database. |
| Quota budget | One lookup and one verification each cost one call. Adjust the estimation factor to your account. |
| Subagent model | The axis is "would a wrong answer be visible", not "is the work hard". Never use the cheapest tier for legal research. |
| Cases root and boundary | Pick a dedicated folder as the cases root and run `workspace-boundary/scripts/setup_workspace.py` on it; keep private material and originals out of it. |

## One platform difference you must know: can a subagent be resumed?

- **Platforms that can resume a subagent** (e.g. Claude Code: send a message to a finished subagent with SendMessage and it carries on with its original context): send follow-up fact questions and the next batch of material to the same fact verifier.
- **Platforms where subagents are one-shot**: it finishes and ends. When new material arrives, spawn a fresh verifier and put this in the dispatch: "read the material register, timeline, deadline table and material cards first, then process this batch." To add something while it is running, use the platform's live channel.

Either way, the case files are the record of truth: anything a subagent remembers but did not write down does not count.

## Try it

`legal-case-workbench/examples/虚构买卖合同案/` is an entirely fictional sale-of-goods case (two batches, seven documents) with several contradictions that only cross-checking will catch — a ready-made test for the fact verifier. It lives inside the skill folder, so it installs with the skill; once installed, ask the agent to "用案件分析工作台自带的示例案件试跑一下" (do a trial run with the bundled sample case).

## Credits

The core propositions — that the split decision shouldn't rest on the model's in-the-moment judgment, the two-tier architecture, batching, and context organization — come from *Super-agent 设计探索：迈向更自主的 Agent 系统* ("Super-agent design exploration") by the DeepSeek Harness team (2026-10-31). Its ablation and stress-test data underpin several judgments here.

The skills follow the general conventions of Anthropic's agent skills format.

## License

MIT
