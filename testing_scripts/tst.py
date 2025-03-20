import subprocess
import time




s = subprocess.Popen(["docker","attach", "redteamllm-service1-1"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
s.stdin.write("ls\n")
s.stdin.flush()
print("10")
print(s.stdout.read(85))