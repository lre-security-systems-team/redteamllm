RedTeam Agent & ReAct

Status: ReAct = stable (paper‑ready) • RedTeamAgent = beta / under active development

This repository ships two command‑line agents that share a common configuration file:

Entry‑point

Description

ReAct

Exact implementation used in the accompanying paper. Each run is logged under saved_<n>/.

RedTeamAgent

Experimental recursive planner; shows the evolving plan tree in real time.

1  Clone & Configure

Clone the repo or extract the release.

Edit src/redteamagent/config/config.yaml (already populated with the values used for the paper). Every key is required; only the first four usually need changing:

Key

Type

Purpose

api_key

str

Your OpenAI (or compatible) key.

model_name

str

LLM used everywhere (e.g. gpt‑4o-mini).

activate_summary

bool

true → summarise long outputs before the next reasoning step.

reason_time

int

0 = no reasoning • >0 = reason for n seconds.

base_system_prompt

str

Prepended globally; overridden by specialised prompts below.

act_system_prompt

str

System prompt for the Act component.

reason_system_prompt

str

System prompt for the Reason component.

summarizer_system_prompt

str

System prompt for the Summarizer.

planner_system_prompt

str

System prompt for the Planner (RedTeamAgent only).

You may export the key instead:

export OPENAI_API_KEY="<your‑key>"   # overrides `api_key` in YAML

2  Run in Docker (Recommended)

# Build the image (from repo root)
docker build -t redteamagent .

# Launch an interactive container
docker run -it --rm \
  -e OPENAI_API_KEY="<your‑key>" \
  redteamagent

Inside the container, both ReAct and RedTeamAgent are on the $PATH.

3  Run Locally (Unsafe – full shell access)

The agent can execute arbitrary commands. Use an isolated VM or throw‑away environment.

python3 -m venv .venv            # optional but strongly advised
source .venv/bin/activate

pip install --upgrade build
python -m build .                # produces dist/*.whl
pip install dist/*.whl

Now simply type:

ReAct           # paper agent
# or
RedTeamAgent    # recursive planner (beta)

4  Outputs & Logs

Each ReAct run writes a timestamped directory saved_<n>/ containing the full conversation of Act, Reason and Summarizer components.

RedTeamAgent streams its plan tree to the terminal and stores artefacts in the working directory.

The results/ folder ships every benchmark referenced in the paper:

results/
├── CewlKid/
├── ctf4/
├── json_results/
├── sar/
├── victim1/
└── westside/

You will find prompts, intermediate thoughts, and evaluation reports exactly as they appeared in the manuscript.

5  Troubleshooting

Symptom

Fix

FileNotFoundError: config.json

Ensure you edited config.yaml in place or mounted it into Docker.

No API key provided

Set api_key in YAML or OPENAI_API_KEY env‑var.

Permission errors locally

The agent is trying to touch files/exec; re‑run inside Docker if uncomfortable.

6  Citing This Work

If you use ReAct or RedTeamAgent in academic work, please cite the accompanying paper:

@inproceedings{YourBibKey2025,
  title     = {RedTeamAgent: …},
  author    = {Author A and Author B},
  booktitle = {Proceedings of …},
  year      = {2025}
}

7  License

Distributed under the MIT License. See LICENSE for details.

