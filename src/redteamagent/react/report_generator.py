"""
report_generator.py — Structured engagement report for RedTeamLLM.
Generates JSON + Markdown reports at end of each engagement.
OpenClaw can read the JSON directly from ~/.redteamllm_reports/
"""
import json
from datetime import datetime
from pathlib import Path


def generate_report(engagement, log_path=None):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    target = engagement.target_ip or "unknown"

    objectives_done = [o for o in engagement.objectives if o.status == "DONE"]
    objectives_failed = [o for o in engagement.objectives if o.status == "FAILED"]
    objectives_pending = [o for o in engagement.objectives if o.status == "PENDING"]

    if not objectives_pending and not objectives_failed:
        outcome = "SUCCESS"
    elif objectives_done:
        outcome = "PARTIAL"
    else:
        outcome = "FAILED"

    finding_str = " ".join(engagement.key_findings).lower()
    credentials = [f for f in engagement.key_findings if any(k in f.lower() for k in ["credential","password","ssh","mysql","hash"])]
    flags = [f for f in engagement.key_findings if any(k in f.lower() for k in ["flag","content","proof"])]
    access = [f for f in engagement.key_findings if any(k in f.lower() for k in ["shell","sudo","root","access"])]

    vulns = []
    if "sudo (all) all" in finding_str:
        vulns.append("Unrestricted sudo (ALL) ALL — any user command can run as root")
    if "ssh access" in finding_str:
        vulns.append("SSH password authentication enabled with legacy weak algorithms")
    if "mysql" in finding_str:
        vulns.append("MySQL accessible — credentials found in web application config")
    if "flag/content" in finding_str:
        vulns.append("Sensitive files world-readable in /tmp")
    if not vulns:
        vulns.append("No specific vulnerabilities auto-detected — review findings manually")

    recs = []
    if "sudo (all) all" in finding_str:
        recs.append("Restrict sudo — replace (ALL) ALL with specific allowed commands only")
    if "ssh access" in finding_str:
        recs.append("Disable SSH password auth — enforce key-based authentication")
        recs.append("Disable legacy SSH algorithms: diffie-hellman-group1-sha1, ssh-rsa")
    if "mysql" in finding_str:
        recs.append("Set strong MySQL root password and remove credentials from config files")
    if not recs:
        recs.append("Review full findings for manual remediation guidance")

    report = {
        "meta": {
            "generated_at": now.isoformat(),
            "target_ip": target,
            "attacker_ip": engagement.attacker_ip,
            "phase_reached": engagement.phase,
            "outcome": outcome,
            "log_file": log_path or "not specified"
        },
        "objectives": {
            "total": len(engagement.objectives),
            "completed": len(objectives_done),
            "failed": len(objectives_failed),
            "pending": len(objectives_pending),
            "details": [{"id": i+1, "description": o.description, "status": o.status, "result": o.result} for i, o in enumerate(engagement.objectives)]
        },
        "findings": {
            "credentials": credentials,
            "flags_captured": flags,
            "access_confirmed": access,
            "all_findings": engagement.key_findings
        },
        "vulnerabilities": vulns,
        "recommendations": recs
    }

    report_dir = Path.home() / ".redteamllm_reports"
    report_dir.mkdir(exist_ok=True)
    json_path = report_dir / f"{timestamp}-{target}.json"
    md_path = report_dir / f"{timestamp}-{target}.md"
    json_path.write_text(json.dumps(report, indent=2))

    icons = {"SUCCESS": "SUCCESS", "PARTIAL": "PARTIAL", "FAILED": "FAILED"}
    md = [
        "# RedTeamLLM Engagement Report",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Target | {target} |",
        f"| Attacker | {engagement.attacker_ip} |",
        f"| Generated | {now.isoformat()} |",
        f"| Phase Reached | {engagement.phase} |",
        f"| Outcome | {outcome} |",
        "", "---", "", "## Objectives", "",
        f"**{len(objectives_done)}/{len(engagement.objectives)} completed**", ""
    ]
    for o in report["objectives"]["details"]:
        icon = {"DONE": "[DONE]", "FAILED": "[FAIL]", "PENDING": "[PEND]"}.get(o["status"], "[?]")
        md.append(f"- {icon} {o['id']}. {o['description']}")
        if o["result"]:
            md.append(f"  - Result: {o['result']}")
    md += ["", "---", "", "## Credentials Found", ""]
    for c in credentials or ["None found"]:
        md.append(f"- {c}")
    md += ["", "## Flags Captured", ""]
    for f in flags or ["None found"]:
        md.append(f"- {f}")
    md += ["", "## Access Confirmed", ""]
    for a in access or ["None"]:
        md.append(f"- {a}")
    md += ["", "---", "", "## Vulnerabilities Identified", ""]
    for v in vulns:
        md.append(f"- {v}")
    md += ["", "## Remediation Recommendations", ""]
    for r in recs:
        md.append(f"- {r}")
    md += ["", "---", "", "*Generated by RedTeamLLM — Biola University Research Fork*"]
    md_path.write_text("\n".join(md))

    print(f"\n[*] Report saved:")
    print(f"    JSON: {json_path}")
    print(f"    MD:   {md_path}")
    return report
