import os
import pty
import select
import subprocess
import sys
import time

COMMAND_TIMEOUT = 30  # seconds before killing a hung command

class InteractiveProcess:
    def __init__(self):
        self.pid = None
        self.fd = None
        self.active = False

    def _spawn_process(self, cmd: str):
        pid, fd = pty.fork()
        if pid == 0:
            os.execvp("bash", ["bash", "-c", cmd])
        else:
            self.pid = pid
            self.fd = fd
            self.active = True
            os.set_blocking(self.fd, False)

    def _read_output_loop(self, poll_interval=0.2, timeout=COMMAND_TIMEOUT):
        output_buffer = []
        start_time = time.time()

        while True:
            # --- TIMEOUT CHECK ---
            if time.time() - start_time > timeout:
                # Kill the hung process
                try:
                    import signal
                    os.kill(self.pid, signal.SIGKILL)
                    os.waitpid(self.pid, 0)
                except Exception:
                    pass
                self.active = False
                self.pid = None
                self.fd = None
                return "".join(output_buffer) + f"\n[TIMEOUT: command killed after {timeout}s — command was likely waiting for interactive input. Use non-interactive alternatives (e.g. sshpass, sudo -S, mysql -p<password>)]"

            ready, _, _ = select.select([self.fd], [], [], poll_interval)

            if self.fd in ready:
                while True:
                    try:
                        chunk = os.read(self.fd, 4096)
                        if not chunk:
                            self.active = False
                            return "".join(output_buffer)
                        else:
                            output_buffer.append(chunk.decode(errors="ignore"))
                    except BlockingIOError:
                        break
                    except OSError:
                        self.active = False
                        return "".join(output_buffer)

            if not self._is_process_alive():
                self.active = False
                return "".join(output_buffer)

            if self._is_waiting_for_input():
                ready, _, _ = select.select([self.fd], [], [], poll_interval)
                if self.fd in ready:
                    while True:
                        try:
                            chunk = os.read(self.fd, 4096)
                            if not chunk:
                                self.active = False
                                return "".join(output_buffer)
                            else:
                                output_buffer.append(chunk.decode(errors="ignore"))
                        except BlockingIOError:
                            break
                        except OSError:
                            self.active = False
                            return "".join(output_buffer)
                return "".join(output_buffer)

    def _is_process_alive(self) -> bool:
        if self.pid is None:
            return False
        try:
            pid_done, _ = os.waitpid(self.pid, os.WNOHANG)
            return pid_done == 0
        except ChildProcessError:
            return False

    def _is_waiting_for_input(self) -> bool:
        if not self._is_process_alive():
            return False
        cmd = ["timeout", "0.1", "strace", "-p", str(self.pid), "-e", "trace=read"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return ("read(" in result.stderr)

    def run_or_send(self, cmd_or_input: str) -> str:
        if not self.active:
            self._spawn_process(cmd_or_input)
            return self._read_output_loop(0.2)
        else:
            user_input = cmd_or_input if cmd_or_input.endswith("\n") else cmd_or_input + "\n"
            os.write(self.fd, user_input.encode())
            time.sleep(0.05)
            return self._read_output_loop(0.2)


if __name__ == "__main__":
    a = InteractiveProcess()
    while True:
        print(a.run_or_send(input()), end="")
