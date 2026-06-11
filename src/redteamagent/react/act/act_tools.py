from .act import Act, register
from .interactive_terminal import InteractiveProcess
import time
import subprocess
import re

session = InteractiveProcess()

# Tracks commands that already ran and their outcome (success/fail/timeout)
_command_history: list[dict] = []

def _sanitize_command(command: str) -> str:
    """
    Intercept known interactive patterns and fix them before execution.
    Returns the sanitized command and a warning if changes were made.
    """
    original = command

    # Fix: mysql -p (bare, interactive password prompt) → reject and explain
    if re.search(r'mysql\b.*\s-p\s*$', command) or re.search(r'mysql\b.*\s-p\s+"', command):
        return (
            f"echo 'COMMAND BLOCKED: mysql with bare -p will hang waiting for a password. "
            f"Use inline password instead: mysql -u USER -pPASSWORD (no space between -p and password). "
            f"Original command was: {original}'"
        )

    # Fix: ssh without sshpass on legacy target patterns
    if re.search(r'\bssh\b', command) and 'sshpass' not in command and \
       re.search(r'192\.168\.\d+\.\d+', command):
        return (
            f"echo 'COMMAND BLOCKED: bare ssh will hang waiting for a password. "
            f"Use: sshpass -p PASSWORD ssh -o StrictHostKeyChecking=no "
            f"-o KexAlgorithms=+diffie-hellman-group1-sha1 "
            f"-o HostKeyAlgorithms=+ssh-rsa -o MACs=hmac-sha1 USER@HOST COMMAND. "
            f"Original command was: {original}'"
        )

    # Fix: sudo without -S (will hang for password)
    if re.search(r'\bsudo\b', command) and '-S' not in command and \
       'echo' not in command.split('sudo')[0]:
        # Only fix if it looks like a remote sudo (inside ssh quotes)
        # Local sudo is fine if user handles it
        pass

    return command


def _record_command(command: str, result: str):
    """Track command history for the failed-commands memory injection."""
    status = "timeout" if "TIMEOUT" in result else \
             "blocked" if "COMMAND BLOCKED" in result else \
             "error" if any(e in result.lower() for e in [
                 "no such file", "permission denied", "access denied",
                 "command not found", "error 1045", "usage:"
             ]) else "ok"
    _command_history.append({
        "command": command[:120],  # truncate long commands
        "status": status,
        "snippet": result[:200]
    })


def get_failed_commands_summary() -> str:
    """
    Returns a summary of previously tried commands that failed/timed out.
    Injected into reasoning context to prevent loops.
    """
    failed = [h for h in _command_history if h["status"] in ("timeout", "error", "blocked")]
    if not failed:
        return ""
    lines = ["PREVIOUSLY FAILED COMMANDS (do not retry these):"]
    for h in failed[-10:]:  # last 10 failures max
        lines.append(f"  [{h['status'].upper()}] {h['command']}")
    return "\n".join(lines)


@register({
    "type": "function",
    "function": {
        "name": "exec_cmd",
        "description": (
            "Execute a command on a non-interactive Linux terminal. "
            "IMPORTANT: Never use commands that wait for input — "
            "no bare 'ssh' (use sshpass), no 'mysql -p' (use -pPASSWORD inline), "
            "no 'sudo' without piping the password via 'echo PASSWORD | sudo -S'. "
            "Commands that hang will be killed after 30 seconds."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "The full non-interactive command to execute. "
                        "For SSH: use sshpass -p PASSWORD ssh -o StrictHostKeyChecking=no ... HOST 'COMMAND'. "
                        "For sudo: use echo 'PASSWORD' | sudo -S COMMAND. "
                        "For mysql: use mysql -u USER -pPASSWORD (no space after -p)."
                    )
                },
            },
            "required": ["command"],
            "additionalProperties": False
        },
        "strict": True
    }
},
Act
)
def exec_cmd(command: str):
    from ..task_state import engagement
    rogue_ip = engagement.validate_target_ip(command)
    if rogue_ip:
        msg = (f"COMMAND BLOCKED: targets {rogue_ip} which is NOT the authorized "
               f"target ({engagement.target_ip}). Fix the IP and retry.")
        _record_command(command, msg)
        return msg
    sanitized = _sanitize_command(command)
    result = session.run_or_send(sanitized)
    _record_command(command, result)
    engagement.auto_update_from_result(command, result)
    return result
