from .act import Act,register
import subprocess



@register({
    "type": "function",
    "function": {
        "name": "exec_cmd",
        "description": "Execute a command on a linux terminal with all the rights. Be careful to use -y to not block the command.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full command to be executed in the terminal, e.g 'echo toto', 'for e in 1 2 3; do echo $e; done', ..."
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
def exec_cmd(command):
    res = subprocess.run(command,shell=True,capture_output=True)

    return f"stdout = {res.stdout.decode('utf-8')}\nstderr={res.stderr.decode('utf-8')}"
