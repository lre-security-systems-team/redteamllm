import subprocess





def exec_cmd(command):
    res = subprocess.run(command,shell=True,capture_output=True)

    return f"stdout = {res.stdout.decode('utf-8')}\nstderr={res.stderr.decode('utf-8')}"

