from .act import Act,register
from .interactive_terminal import InteractiveProcess
import time
import subprocess








session = InteractiveProcess()

@register({
    "type": "function",
    "function": {
        "name": "exec_cmd",
        "description": "Execute a command on a linux not interactive terminal.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full command to be executed in the terminal, e.g 'echo toto', 'for e in 1 2 3; do echo $e; done', .... Be careful to make sure you're command is not interactive."
                },
            },
            "required": [
                "command",
            ],
            "additionalProperties": False
        },
        "strict": True
    }
},
Act
)
def exec_cmd(command:str):
    # res = subprocess.run(command,shell=True,capture_output=True)
    # return f"stdout = {res.stdout.decode('utf-8')}\nstderr={res.stderr.decode('utf-8')}"
    
    return session.run_or_send(command)
    
    
