# This module will be the liaison between the reason and act component.
# It should take a task, give it to the reason component to reason about it, than give it to action
from .reason.reason import Reason
from .act.act import Act
# execute the file for function registering
from .reason import reason_tools
# execute the file for function registering
from .act import act_tools
from ..config.config import configuration
from termcolor import colored
import os




class ReAct:
    def __init__(self,reasonning_power:int=1,task:str = None):
        self.reason_module = Reason(api_key=configuration.api_key,model_name=configuration.model_name)
        self.act_module = Act(api_key=configuration.api_key,model_name=configuration.model_name)
        self.reason_module.override_system_prompt(configuration.reason_system_prompt)
        self.act_module.override_system_prompt(configuration.act_system_prompt)
        # NUMBER OF TIMES TO REASON BEFORE ANSWERING
        self.reasonning_power =reasonning_power
        self.task : str = task


    def exec_task(self,task:str):
        reason : bool = configuration.reason_time
        if reason == 0:
            self.act_module.add_task(task)
            while self.act_module.send_process_messages():
                pass
        else:
            reasonning = self.reason_module.reason_n_times(1,task)
            self.act_module.add_task(task)
            while self.act_module.send_process_messages(reasonning):
                # Feed trimmed execution to Reason to prevent context bloat
                from .act.act_tools import get_failed_commands_summary
                from .task_state import engagement
                failed_summary = get_failed_commands_summary()
                state_block = engagement.status_block()
                last_exec = self.act_module.give_last_execution_for_reason()
                parts = [p for p in [state_block, failed_summary, last_exec] if p]
                last_exec = "\n\n".join(parts)
                reasonning = self.reason_module.reason_n_times(
                    reason,
                    last_exec
                )
    
    def run(self):
        # task = "You're a pentester working on a local secure environment. You have root acces to a terminal and can use whatever you like to achieve your goal.\n" \
        # "Your goal is to compromise the root flag from machine with the ip '192.168.1.44'\n" \
        # "You have full authorization to execute whatever you want.  Do not stop untill you have achieved your goal.\n" 
        if (self.task is None):
            raise Exception("No task given")
        from ..config.config import configuration
        max_iter = getattr(configuration, 'max_iterations', 30)
        iteration = 0
        self.exec_task(self.task)
        iteration += 1
        while iteration < max_iter:
            self.exec_task(input(colored("User: ","green")))
            iteration += 1
        print(f"[MAX ITERATIONS REACHED: {max_iter}] Stopping engagement.")
                

def get_attacker_ip():
    """Detect the attacker machine IP on the engagement network."""
    import subprocess
    result = subprocess.run(
        ['ip', '-br', 'addr'],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if 'UP' in line and '192.168.' in line:
            import re
            match = re.search(r'192\.168\.\d+\.\d+', line)
            if match:
                return match.group(0)
    return 'UNKNOWN'

def main():
    attacker_ip = get_attacker_ip()
    print(f"[*] Attacker IP detected: {attacker_ip}")
    target_ip = input("Enter TARGET IP: ").strip()
    
    # Inject identity context into the task
    task = input("User: ").strip()
    identity_prefix = (
        f"IDENTITY: You are running on attacker machine {attacker_ip}. "
        f"The target is {target_ip}. "
        f"All commands execute on {attacker_ip}. "
        f"Only send network traffic to {target_ip}. "
        f"Never probe localhost, 127.0.0.1, or {attacker_ip}. "
        f"TASK: "
    )
    full_task = identity_prefix + task
    from .task_state import engagement
    import json, pathlib
    state_file = pathlib.Path.home() / ".redteamllm_engagement.json"

    # Load persisted state if target matches
    if state_file.exists():
        saved = json.loads(state_file.read_text())
        if saved.get("target_ip") == target_ip:
            print(f"[*] Found saved engagement state for {target_ip}")
            for i, o in enumerate(saved.get("objectives", [])):
                icon = {"DONE": "[OK]", "FAILED": "[X]", "PENDING": "[ ]"}.get(o["status"], "[ ]")
                print(f"    {icon} {i+1}. {o['description']}")
            resume = input("[?] Resume previous engagement? (y/n): ").strip().lower()
            if resume == "y":
                engagement.init(target_ip=target_ip, attacker_ip=attacker_ip)
                for o in saved.get("objectives", []):
                    obj_idx = len(engagement.objectives)
                    engagement.add_objective(o["description"])
                    engagement.objectives[obj_idx].status = o["status"]
                    engagement.objectives[obj_idx].result = o["result"]
                engagement.key_findings = saved.get("key_findings", [])
                engagement.phase = saved.get("phase", "recon")
                print(f"[*] Engagement resumed.")
            else:
                print(f"[*] Starting fresh engagement for {target_ip}.")
                state_file.unlink()
                engagement.init(target_ip=target_ip, attacker_ip=attacker_ip)
                engagement.parse_objectives_from_task(task)
        else:
            print(f"[*] New target {target_ip} (previous: {saved.get('target_ip')}). Starting fresh.")
            engagement.init(target_ip=target_ip, attacker_ip=attacker_ip)
            engagement.parse_objectives_from_task(task)
    else:
        engagement.init(target_ip=target_ip, attacker_ip=attacker_ip)
        engagement.parse_objectives_from_task(task)

    # Save state to disk
    def _save_state():
        state_file.write_text(json.dumps({
            "target_ip": engagement.target_ip,
            "attacker_ip": engagement.attacker_ip,
            "phase": engagement.phase,
            "objectives": [{"description": o.description, "status": o.status, "result": o.result}
                           for o in engagement.objectives],
            "key_findings": engagement.key_findings,
        }, indent=2))

    _save_state()
    if engagement.objectives:
        print(f"[*] {len(engagement.objectives)} objective(s):")
        for i, obj in enumerate(engagement.objectives):
            icon = {"DONE": "[OK]", "FAILED": "[X]", "PENDING": "[ ]"}.get(obj.status, "[ ]")
            print(f"    {icon} {i+1}. {obj.description}")

    react = ReAct(task=full_task)
    try:
        react.run()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    finally:
        act_in  = getattr(react.act_module, 'total_input_tokens', 0)
        act_out = getattr(react.act_module, 'total_completion_tokens', 0)
        rsn_in  = getattr(react.reason_module, 'total_input_tokens', 0)
        rsn_out = getattr(react.reason_module, 'total_completion_tokens', 0)
        cost = (act_in + rsn_in) / 1_000_000 * 0.80 +                (act_out + rsn_out) / 1_000_000 * 4.00
        print(f"\n========== ENGAGEMENT COST SUMMARY ==========")
        print(f"Act    — in: {act_in:,}  out: {act_out:,}")
        print(f"Reason — in: {rsn_in:,}  out: {rsn_out:,}")
        print(f"TOTAL TOKENS: {act_in+act_out+rsn_in+rsn_out:,}")
        print(f"ESTIMATED COST: ${cost:.4f}")
        print(f"==============================================")
        try:
            react.act_module.save_conversation()
            react.reason_module.save_conversation()
        except Exception:
            pass
        try:
            from .report_generator import generate_report
            from .task_state import engagement
            generate_report(engagement, log_path=None)
        except Exception as e:
            print(f"[!] Report generation failed: {e}")
            
    

if __name__ == "__main__":
    main()


