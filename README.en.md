# legal-agent-skills

Two agent skills, meant to be used together.

**中文：**[README.md](README.md)

| Skill | In one line |
|---|---|
| **[subagent-dispatch](subagent-dispatch/SKILL.md)** | To split or not to split: deciding whether a piece of work gets done in the main context or handed to a subagent. The core rule is "material stays whole; functions may split". |
| **[legal-case-workbench](legal-case-workbench/SKILL.md)** | A case analysis workbench: one long-lived workspace per case, where fact verification, legal research, analysis and drafting all happen. |

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

```bash
cp -r subagent-dispatch legal-case-workbench ~/.claude/skills/   # Claude Code
cp -r subagent-dispatch legal-case-workbench ~/.hermes/skills/   # Hermes
```

Or drop them into any agent's skills directory. Both are plain Markdown plus a few Python scripts (`legal-case-workbench/scripts/`) with no external dependencies.

## Four things to fill in before deploying

The skills bind no specific platform or service, but four items are environment-specific:

| Item | What to do |
|---|---|
| Confidentiality and de-identification rules | Step 0 of `legal-case-workbench` is intentionally blank — **hand your firm's rules to the AI and ask it to write them into that section**: which cases get no workbench, de-identification standard, external-release approval. |
| Legal research source | Defaults to PKULaw MCP (seven tools under the service name `pkulaw`). Without it, swap in whatever database you have, or fall back to the official statute database. |
| Quota budget | One lookup and one verification each cost one call. Adjust the estimation factor to your account. |
| Subagent model | The axis is "would a wrong answer be visible", not "is the work hard". Never use the cheapest tier for legal research. |

## One platform difference you must know

On most platforms a subagent is **one-shot**: it finishes and ends, and there is no "ask the same one again". What keeps it oriented is the files it writes. When new material arrives, spawn a fresh verifier and put this in the dispatch: "read the material register, timeline, deadline table and material cards first, then process this batch." If you need to add something while it is still running, use the platform's live channel (on Hermes that is `delegate_task` with `steer`).

## Credits

The core propositions — that the split decision shouldn't rest on the model's in-the-moment judgment, the two-tier architecture, batching, and context organization — come from *Super-agent 设计探索：迈向更自主的 Agent 系统* ("Super-agent design exploration") by the DeepSeek Harness team (2026-10-31). Its ablation and stress-test data underpin several judgments here.

The skills follow the general conventions of Anthropic's agent skills format.

## License

MIT
