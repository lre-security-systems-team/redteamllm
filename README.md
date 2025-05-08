# RedTeamAgent / ReAct – Quick‑Start Guide

This README shows you **two ways** to launch the agent:

1. **Docker** – completely sandboxed (recommended)
2. **Native install** – full control, but **the agent can run arbitrary shell commands**.

---

## 1  Prepare your configuration

The configuration file lives at

```
src/redteamagent/config/config.json
```

It is already populated with the exact values used in the paper’s experiments—**only `api_key` is left empty**.  You may also tweak `activate_summary`, `reason_time`, `model_name`, or any other field, but **all keys must be present**.

| Field                      | Type   | Meaning                                                          |
| -------------------------- | ------ | ---------------------------------------------------------------- |
| `api_key`                  | `str`  | Your LLM provider key (OpenAI, Anthropic…)                       |
| `model_name`               | `str`  | Model shared by every component (e.g. `gpt-4o`)                  |
| `activate_summary`         | `bool` | `true` → post‑summarise long outputs, `false` → keep full text   |
| `reason_time`              | `int`  | `0` = no reasoning; `>0` = number of times to reason             |
| `base_system_prompt`       | `str`  | Base prompt (overridden by the component‑specific prompts below) |
| `act_system_prompt`        | `str`  | Prompt used by the **ACT** component                             |
| `reason_system_prompt`     | `str`  | Prompt used by the **REASON** component                          |
| `summarizer_system_prompt` | `str`  | Prompt used by the **SUMMARISER** component                      |
| `planner_system_prompt`    | `str`  | Prompt used by the **PLANNER** component                         |

---

## 2  Run with Docker (recommended)

```bash
# build the image from the repository root
$ docker build -t redteamagent .

# launch an interactive session
$ docker run -it --rm redteamagent
```

Edit `src/redteamagent/config/config.json` **before** building if you need custom values.

---

## 3  Run natively (advanced / risky)

> **Danger:** The agent can execute arbitrary shell commands. Only run locally if you’re sure you want that.

### 3.1  Build & install

```bash
# prerequisites
python3 -m pip install --upgrade build pip

# from the repo root
python3 -m build .          # creates dist/*.whl and *.tar.gz
pip install dist/*.whl      # install into your environment
```

### 3.2  Launch

```bash
# Main demo used in the paper
ReAct

# Experimental recursive planner (beta)
RedTeamAgent
```

---

## 4  What happens when you run **ReAct**?

* A folder named `saved_<N>` is created (`N` increments on each run).
* The folder contains three text logs:

  * **`Act.txt`** – actions executed by the ACT component
  * **`Reason.txt`** – chain‑of‑thought produced during reasoning
  * **`Summarizer.txt`** – summaries of long outputs
* Each file shows token usage, the active config snapshot, metadata about the component, **and the complete conversation of every LLM session**.

These artefacts are exactly what we used to generate the figures in the paper.

---

## 5  Inspecting published results

The `results/` directory already contains all benchmark artefacts cited in the paper:

```
results/
├── Cewlkid
├── Cewlkid.json
├── ctf4
├── ctf4.json
├── extract.py
├── extract_stop.py
├── json_results
├── json_results.json
├── output_data.xlsx
├── sar
├── sar.json
├── stop_reason.yaml
├── stop_reson.json
├── victim1
├── victim1.json
├── westside
└── westside.json
```

Explore them freely!
