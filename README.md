# RedTeamLLM — Biola University Research Fork

> An agentic AI framework for autonomous penetration testing, extended with ten architectural improvements for reliability and safety.

This is a research fork of [RedTeamLLM](https://github.com/lre-security-systems-team/redteamllm) by Brian Challita and Pierre Parrend (arXiv:2505.06913), maintained by the AI and Cybersecurity Research Group at Biola University. The original framework proposes a ReAct-based agentic architecture for autonomous penetration testing. This fork implements targeted architectural improvements that address failure modes observed during empirical testing against VulnHub CTF targets.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [What Changed from the Original](#2-what-changed-from-the-original)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Configuration Guide](#5-configuration-guide)
6. [Network Setup](#6-network-setup)
7. [Running an Engagement](#7-running-an-engagement)
8. [Task Prompt Guide](#8-task-prompt-guide)
9. [Understanding the Output](#9-understanding-the-output)
10. [Engagement Persistence](#10-engagement-persistence)
11. [Report Generation](#11-report-generation)
12. [Pre-scan Workflow for Blue Team Exercises](#12-pre-scan-workflow-for-blue-team-exercises)
13. [Benchmark Targets](#13-benchmark-targets)
14. [Troubleshooting](#14-troubleshooting)
15. [Research Notes & Citation](#15-research-notes--citation)

---

## 1. Architecture Overview

RedTeamLLM uses a ReAct (Reason + Act) loop where a reasoning module plans each step and an action module executes terminal commands. This fork adds a persistent engagement state layer and a suite of safety mechanisms around that core loop.

```
User prompt
     │
     ▼
  main()
     ├── Detect attacker IP automatically
     ├── Lock target IP into EngagementState
     ├── Parse numbered objectives from task string
     └── Check for saved state → prompt to resume or restart
     │
     ▼
  ReAct.exec_task()
     │
     ├── Reason.reason_n_times()
     │       Input:  state_block + failed_commands + last_execution
     │       Output: reasoning string (phase, priority, next step)
     │
     └── Act.send_process_messages()
             │
             ▼
         exec_cmd(command)
             ├── validate_target_ip()       block if wrong IP
             ├── _sanitize_command()        block if interactive
             ├── session.run_or_send()      execute with 30s timeout
             ├── _record_command()          log result status
             └── auto_update_from_result()  update findings & objectives
             │
             ▼
         loop until no tool call or max_iterations reached
             │
             ▼
         generate_report() → JSON + Markdown in ~/.redteamllm_reports/
```

**Key source files:**

| File | Role |
|---|---|
| `react/react.py` | Main loop, startup, engagement initialization, state injection |
| `react/task_state.py` | Engagement state — objectives, findings, IP lock |
| `react/act/act_tools.py` | `exec_cmd`, IP validator, command sanitizer, failed-command tracker |
| `react/act/interactive_terminal.py` | PTY process manager with 30-second timeout killer |
| `react/reason/reason.py` | Strategic reasoning module |
| `react/summarizer/summarizer.py` | Engagement-aware output summarizer |
| `react/report_generator.py` | JSON and Markdown report generation |
| `config/config.json` | Runtime configuration (gitignored — use `config.example.json` as template) |

---

## 2. What Changed from the Original

The original paper identified four open challenges: memory management, plan correction, context window constraint, and generality vs. specialization. Memory management and plan correction were described as "less mature, and not evaluated." This fork addresses those gaps with ten concrete patches.

| # | File | Change | Failure Mode Solved |
|---|---|---|---|
| 1 | `interactive_terminal.py` | 30-second timeout killer via PTY + strace | Infinite hangs on interactive prompts (ssh, mysql, sudo) |
| 2 | `act_tools.py` | Command sanitizer blocks bare `ssh` and `mysql -p` | Agent hanging on password prompts mid-engagement |
| 3 | `act_tools.py` | Failed command tracker records every command status | Agent retrying the same dead-end commands in loops |
| 4 | `react.py` | Failed commands injected into reasoning context | Command loop prevention — reason module sees past failures |
| 5 | `task_state.py` | New persistent `EngagementState` object with objectives, findings, and phase | Objective drift and target forgetting over long sessions |
| 6 | `act_tools.py` | Target IP validator blocks any command targeting a non-authorized IP | IP hallucination — agent scanning the wrong host |
| 7 | `react.py` | Full state block re-injected into every reasoning cycle | Target IP and objectives lost in long conversations |
| 8 | `react.py` | Engagement serialized to `~/.redteamllm_engagement.json` with resume prompt | Complete state loss on crash or manual restart |
| 9 | `config.json` | Engagement-aware summarizer prompt preserving credentials, flags, and port data | Critical findings silently dropped by aggressive summarization |
| 10 | `config.json` | `max_history_messages` raised from 6 to 12 | Premature context pruning causing the agent to forget recent actions |

### The Task State Block

At every reasoning cycle the agent sees the following block prepended to its input, ensuring objectives and identity are never forgotten regardless of conversation length:

```
============================================================
ENGAGEMENT STATE — READ THIS BEFORE EVERY DECISION
============================================================
TARGET IP (IMMUTABLE): 192.168.88.240
ATTACKER IP:           192.168.88.241
CURRENT PHASE:         exploitation

OBJECTIVES:
  [✓] 1. Read /tmp/test.txt as root
         -> TESTCONTENT
  [ ] 2. Dump the ehks database contents

KEY FINDINGS SO FAR:
  * Shell access confirmed
  * sudo (ALL) ALL confirmed
============================================================
RULE: Never send traffic to any IP other than TARGET IP above.
RULE: If an objective is DONE, move to the next PENDING one.
RULE: Do not re-run commands already marked FAILED.
============================================================
```

---

## 3. Prerequisites

**Attacker machine:** Kali Linux (tested on Kali 2024+) on VMware Fusion or VMware Workstation.

**Target machines:** VulnHub CTF VMs on the same isolated host-only network as Kali.

**Anthropic API key:** Obtain one at [https://console.anthropic.com](https://console.anthropic.com).

Install required system tools on Kali:

```bash
sudo apt install -y git python3 python3-pip python3-venv \
  sshpass nmap gobuster nikto sqlmap john hashcat strace
```

Verify `strace` is present — the 30-second timeout mechanism depends on it:

```bash
which strace
```

---

## 4. Installation

```bash
git clone -b cost-optimizations \
  https://github.com/Josephaaan/RedTeamLLM-Modification.git \
  /opt/redteamllm

cd /opt/redteamllm
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify the install:

```bash
python3 -c "from src.redteamagent.react.react import ReAct; print('Install OK')"
```

---

## 5. Configuration Guide

### Initial Setup

Copy the example config and open it for editing:

```bash
cp src/redteamagent/config/config.example.json \
   src/redteamagent/config/config.json

nano src/redteamagent/config/config.json
```

The file is gitignored by default — your API key will never be accidentally committed.

### Configuration Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `api_key` | string | *(required)* | Your Anthropic API key. Never commit this to version control. |
| `model_name` | string | `claude-haiku-4-5-20251001` | Model to use. See model selection guidance below. |
| `reason_time` | int | `1` | Number of reasoning calls per cycle. **Must be 1** — setting to 0 disables all state injection and defeats improvements #4, #7. |
| `activate_summary` | bool | `true` | Summarize long command output to prevent context bloat. Disable only for debugging. |
| `max_history_messages` | int | `12` | Rolling conversation window size. Raised from the original 6 to reduce premature pruning. |
| `max_iterations` | int | `30` | Hard stop after this many ReAct cycles. Prevents runaway token spend. |

### Model Selection

| Model | Use Case | Notes |
|---|---|---|
| `claude-haiku-4-5-20251001` | Most engagements, cost-sensitive research | Fast and cheap; sufficient for well-defined CTF targets |
| `claude-sonnet-4-6` | Harder targets, blind engagements, novel CVEs | Stronger reasoning; higher cost per token |

To switch models mid-project, edit `model_name` in `config.json` and restart the engagement.

### Tuning the Prompts

All system prompts are stored in `config.json` as string fields. You can edit them directly:

| Prompt Field | Controls | When to Edit |
|---|---|---|
| `base_system_prompt` | Shared identity, scope discipline, honesty principle, prompt injection defense | Add target-specific constraints or change the research framing |
| `act_system_prompt` | Command execution discipline, phase summary format, end-of-engagement summary | Tune output filtering patterns or add new `grep` preferences |
| `reason_system_prompt` | Strategic reasoning framing, anti-rabbit-hole check, phase awareness | Adjust how aggressively the agent pivots between attack vectors |
| `summarizer_system_prompt` | Which output to keep vs. discard during summarization | Add new patterns to preserve (e.g., new flag formats or credential formats) |
| `planner_system_prompt` | Task decomposition logic | Relevant only if using the planning module, not the ReAct module |

**Important:** Preserve the `\n` escape sequences when editing prompts in JSON. Use a JSON validator before saving.

### Verifying Configuration

```bash
python3 -c "
from src.redteamagent.config.config import configuration
print('Model:', configuration.model_name)
print('Reason time:', configuration.reason_time)
print('Max history:', configuration.max_history_messages)
print('Summary active:', configuration.activate_summary)
"
```

---

## 6. Network Setup

Kali and all target VMs must share the same isolated host-only network in VMware. They should **not** have internet access from that interface.

Assign an IP to your Kali interface if not auto-assigned:

```bash
sudo ip addr add 192.168.88.241/24 dev eth0
sudo ip link set eth0 up
ping 192.168.88.240
```

Confirm network isolation — the agent will block any command targeting an IP outside the authorized target, but network-level isolation is your backstop.

---

## 7. Running an Engagement

```bash
mkdir -p ~/logs
cd /opt/redteamllm
source .venv/bin/activate

python3 -u -m src.redteamagent.react.react 2>&1 \
  | tee ~/logs/engagement-$(date +%Y%m%d-%H%M).log
```

At startup you will be prompted for:

1. **Target IP** — the single authorized target. Locked into `EngagementState` for the entire session.
2. **Task** — your engagement description with numbered objectives (see Task Prompt Guide below).

If a saved state exists for this target IP you will be asked whether to resume it.

---

## 8. Task Prompt Guide

Use numbered parenthetical format for objectives — they are automatically parsed into the objective tracker and displayed in the state block at every reasoning cycle.

**From scratch with no credentials:**

```
Target: 192.168.88.240. No credentials known.
Objectives: (1) enumerate all open services, (2) gain initial shell,
(3) escalate to root, (4) capture the root flag.
Scope: 192.168.88.240 only.
```

**With known SSH credentials on a legacy target:**

```
Target: 192.168.88.240. SSH credentials: dstevens:ilike2surf (admins group).
Use sshpass for all SSH:
  sshpass -p "ilike2surf" ssh -o StrictHostKeyChecking=no
    -o KexAlgorithms=+diffie-hellman-group1-sha1
    -o HostKeyAlgorithms=+ssh-rsa -o MACs=hmac-sha1
    dstevens@192.168.88.240 "COMMAND"
For sudo: echo 'ilike2surf' | sudo -S COMMAND
For mysql: mysql -uUSER -pPASSWORD (no space after -p)
Objectives: (1) read /tmp/test.txt as root, (2) dump the ehks database.
Scope: 192.168.88.240 only.
```

**Tips for writing good task prompts:**

- Always state the scope explicitly — the IP validator uses it to block rogue traffic.
- Include known credentials and their correct non-interactive invocation patterns upfront — this avoids the agent needing to discover them and reduces wasted iterations.
- Number objectives with the `(N) description` format so they are parsed correctly into the tracker.
- Keep the scope line last so it is easy to find when reviewing logs.

---

## 9. Understanding the Output

| Color | Source | Meaning |
|---|---|---|
| Yellow | Reasoning module | Phase analysis, priority ranking, next-step rationale |
| Blue | User/task input | The task or user message being processed |
| Red (with black bg) | Command dispatch | The exact command being sent to the terminal |
| Red | Command result | Raw or summarized output from the terminal |
| White | Act module text | Assistant prose between tool calls |

**Expected messages during normal operation:**

```
[TIMEOUT: command killed after 30s — command was likely waiting for interactive input.]
```
This is working as intended. The sanitizer should have blocked it; this is the PTY-level backstop.

```
COMMAND BLOCKED: targets 172.25.0.5 which is NOT the authorized target (192.168.88.240).
```
The IP validator caught a hallucinated target IP. The agent will receive this as feedback and self-correct.

```
PREVIOUSLY FAILED COMMANDS (do not retry these):
  [TIMEOUT] nmap -A 192.168.88.240
  [ERROR]   mysql -u root -p
```
Injected into the reasoning context to break retry loops.

**Cost summary printed at end of every run:**

```
========== ENGAGEMENT COST SUMMARY ==========
Act    — in: 45,231  out: 3,847
Reason — in: 12,104  out: 2,193
TOTAL TOKENS: 63,375
ESTIMATED COST: $0.0523
==============================================
```

---

## 10. Engagement Persistence

State is automatically serialized to `~/.redteamllm_engagement.json` at the end of every run. On next launch against the same target IP:

```
[*] Found saved engagement state for 192.168.88.240
    [OK] 1. Read /tmp/test.txt as root
    [  ] 2. Dump the ehks database contents
[?] Resume previous engagement? (y/n):
```

Answer `y` to restore all objectives, findings, phase, and key results. Answer `n` to start fresh (the state file is deleted).

Always use `n` when benchmarking to ensure clean, reproducible runs.

**Manually clear saved state:**

```bash
rm ~/.redteamllm_engagement.json
```

---

## 11. Report Generation

At the end of every engagement two files are written to `~/.redteamllm_reports/`:

| File | Format | Purpose |
|---|---|---|
| `YYYYMMDD-HHMMSS-TARGET.json` | Machine-readable JSON | Direct ingestion by OpenClaw or other tooling |
| `YYYYMMDD-HHMMSS-TARGET.md` | Human-readable Markdown | Blue team remediation report |

The report includes: outcome (SUCCESS / PARTIAL / FAILED), all objectives with results, credentials found, flags captured, access confirmed, vulnerabilities identified, and remediation recommendations automatically inferred from findings.

**Useful commands:**

```bash
# View the latest Markdown report
cat $(ls -t ~/.redteamllm_reports/*.md | head -1)

# View the latest JSON report
cat $(ls -t ~/.redteamllm_reports/*.json | head -1)

# List all reports
ls -lt ~/.redteamllm_reports/
```

---

## 12. Pre-scan Workflow for Blue Team Exercises

RedTeamLLM is designed to serve as an automated pre-scanner before a blue team exercise, generating structured findings for the blue team to remediate before a human red teamer attacks.

```
Kali VM (RedTeamLLM)               Vulnerable VMs
192.168.88.241                     192.168.88.240, .242, .243
  │                                  │
  ├── autonomous scan, target 1 ───► │
  ├── generates report 1             │
  ├── autonomous scan, target 2 ───► │
  └── generates report 2             │
  │
  ▼
Blue team reads Markdown reports
  │
  ▼
Blue team patches identified vulnerabilities
  │
  ▼
Red teamer attacks manually to test whether patches held
  │
  ▼
OpenClaw ingests JSON reports to coordinate follow-on actions
```

**Workflow steps:**

1. Run RedTeamLLM autonomously against each vulnerable VM in sequence.
2. JSON and Markdown reports are generated in `~/.redteamllm_reports/`.
3. Blue team reads the Markdown report and patches all identified vulnerabilities.
4. Human red teamer attacks after remediation to validate patch effectiveness.
5. OpenClaw ingests the JSON reports directly for programmatic coordination.

---

## 13. Benchmark Targets

Validated against the same five VulnHub VMs used in the original paper:

| VM | VulnHub Link | Walkthrough Reference |
|---|---|---|
| LampSecurity CTF4 | [vulnhub.com/entry/lampsecurity-ctf4,83](https://www.vulnhub.com/entry/lampsecurity-ctf4,83/) | [hackingarticles.in](https://www.hackingarticles.in/hack-the-lampsecurity-ctf4-ctf-challenge/) |
| CewlKid | [vulnhub.com/entry/cewlkid-1,775](https://www.vulnhub.com/entry/cewlkid-1,775/) | [hackingarticles.in](https://www.hackingarticles.in/cewlkid-1-vulnhub-walkthrough/) |
| Sar | [vulnhub.com/entry/sar-1,760](https://www.vulnhub.com/entry/sar-1,760/) | [hackingarticles.in](https://www.hackingarticles.in/sar-vulnhub-walkthrough/) |
| Victim1 | [vulnhub.com/entry/victim-1,505](https://www.vulnhub.com/entry/victim-1,505/) | [hackingarticles.in](https://www.hackingarticles.in/victim1-vulnhub-walkthrough/) |
| Westwild | [vulnhub.com/entry/westwild-11,756](https://www.vulnhub.com/entry/westwild-11,756/) | [hackingarticles.in](https://www.hackingarticles.in/westwild-1-1-vulnhub-walkthorugh/) |

---

## 14. Troubleshooting

**State block not appearing in reasoning output — `reason_time` is 0:**

```bash
python3 -c "
import json
p = 'src/redteamagent/config/config.json'
c = json.load(open(p))
c['reason_time'] = 1
json.dump(c, open(p, 'w'), indent=4)
print('Fixed — reason_time set to 1')
"
```

**Agent hangs and timeout does not fire — `strace` missing:**

```bash
sudo apt install -y strace
which strace   # should return /usr/bin/strace
```

**Virtual environment not active (ImportError on launch):**

```bash
source /opt/redteamllm/.venv/bin/activate
python3 -c "from src.redteamagent.react.react import ReAct; print('OK')"
```

**John the Ripper lock file stuck during hash cracking:**

```bash
rm -f ~/.john/john.rec
```

**XRDP clipboard not syncing between Windows host and Kali:**

```bash
killall xrdp-chansrv 2>/dev/null; xrdp-chansrv &
```

**Agent loses target IP mid-engagement — verify patches are applied:**

```bash
grep "validate_target_ip" src/redteamagent/react/act/act_tools.py
ls src/redteamagent/react/task_state.py
```

Both should return results. If `task_state.py` is missing, pull the latest commit from the `cost-optimizations` branch.

**Config validation error on startup:**

All fields in `config.json` are required. The config loader will raise an exception naming the missing field. Compare your `config.json` against `config.example.json` to identify gaps.

---

## 15. Research Notes & Citation

This fork is part of a comparative study at Biola University evaluating RedTeamLLM against PentestGPT (USENIX Security 2024) on VulnHub LAMPSecurity CTF targets.

**Benchmark metrics recorded per run:**

| Metric | Description |
|---|---|
| Completion | Root access achieved (yes/no) |
| Cost | Total tokens consumed and estimated USD |
| Efficiency | Wasted iterations after flag capture |
| Reliability | Timeout count, blocked IP count, target loss events |

**Citing the original work:**

```bibtex
@article{challita2025redteamllm,
  title   = {RedTeamLLM: an Agentic AI framework for offensive security},
  author  = {Challita, Brian and Parrend, Pierre},
  journal = {arXiv preprint arXiv:2505.06913},
  year    = {2025}
}
```

---

*Biola University AI and Cybersecurity Research Group*
*github.com/Josephaaan/RedTeamLLM-Modification*
