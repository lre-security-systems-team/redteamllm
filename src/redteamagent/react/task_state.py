from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class Objective:
    description: str
    status: str = "PENDING"
    result: str = ""

class EngagementState:
    def __init__(self):
        self.target_ip = None
        self.attacker_ip = None
        self.objectives = []
        self.phase = "recon"
        self.key_findings = []
        self._initialized = False

    def init(self, target_ip, attacker_ip):
        self.target_ip = target_ip
        self.attacker_ip = attacker_ip
        self._initialized = True

    def add_objective(self, description):
        self.objectives.append(Objective(description=description))

    def mark_done(self, index, result=""):
        if 0 <= index < len(self.objectives):
            self.objectives[index].status = "DONE"
            self.objectives[index].result = result

    def mark_failed(self, index, reason=""):
        if 0 <= index < len(self.objectives):
            self.objectives[index].status = "FAILED"
            self.objectives[index].result = reason

    def add_finding(self, finding):
        if finding not in self.key_findings:
            self.key_findings.append(finding)

    def set_phase(self, phase):
        self.phase = phase

    def validate_target_ip(self, command):
        if not self.target_ip:
            return None
        found_ips = re.findall(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', command)
        for ip in found_ips:
            if ip != self.target_ip and ip != self.attacker_ip and ip != "127.0.0.1":
                return ip
        return None

    def status_block(self):
        if not self._initialized:
            return ""
        lines = [
            "=" * 60,
            "ENGAGEMENT STATE — READ THIS BEFORE EVERY DECISION",
            "=" * 60,
            f"TARGET IP (IMMUTABLE): {self.target_ip}",
            f"ATTACKER IP:           {self.attacker_ip}",
            f"CURRENT PHASE:         {self.phase}",
            "",
            "OBJECTIVES:",
        ]
        for i, obj in enumerate(self.objectives):
            icon = {"PENDING": "[ ]", "IN_PROGRESS": "[>]",
                    "DONE": "[✓]", "FAILED": "[✗]"}.get(obj.status, "[ ]")
            line = f"  {icon} {i+1}. {obj.description}"
            if obj.result:
                line += f"\n       -> {obj.result}"
            lines.append(line)
        if self.key_findings:
            lines.append("")
            lines.append("KEY FINDINGS SO FAR:")
            for f in self.key_findings[-8:]:
                lines.append(f"  * {f}")
        lines += [
            "=" * 60,
            "RULE: Never send traffic to any IP other than TARGET IP above.",
            "RULE: If an objective is [OK] DONE, move to the next PENDING one.",
            "RULE: Do not re-run commands already marked FAILED.",
            "=" * 60,
        ]
        return "\n".join(lines)

    def parse_objectives_from_task(self, task):
        matches = re.findall(r'\((\d+)\)\s+([^,()\n]+?)(?=\s*[,()\n]|$)', task)
        if matches:
            for _, desc in matches:
                desc = desc.strip()
                if len(desc) > 5:
                    self.add_objective(desc)
        else:
            matches = re.findall(r'(?:step\s*)?\d+[.):\s]+([^\n.]+)', task, re.IGNORECASE)
            for m in matches:
                m = m.strip()
                if len(m) > 5:
                    self.add_objective(m)

    def auto_update_from_result(self, command, result):
        for pattern in [r'[A-Za-z0-9_]+\{[^}]+\}', r'TESTCONTENT']:
            match = re.search(pattern, result)
            if match:
                self.add_finding(f"FLAG/CONTENT: {match.group(0)}")
        if 'uid=' in result and 'gid=' in result:
            self.add_finding(f"Shell access: {command[:60]}")
        if '(all) all' in result.lower():
            self.add_finding("sudo (ALL) ALL confirmed")
        if 'insert into' in result.lower() and 'md5(' in result.lower():
            self.add_finding(f"Credentials in: {command[:60]}")

engagement = EngagementState()
