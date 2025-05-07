import os
import pty
import select
import subprocess
import sys
import time

class InteractiveProcess:
    def __init__(self):
        """
        Manages a single interactive child process in a pseudo-terminal,
        capturing output as a string rather than printing it.
        """
        self.pid = None
        self.fd = None
        self.active = False

    def _spawn_process(self, cmd: str):
        """
        Spawn a child process running `cmd` in a pseudo-terminal.
        """
        pid, fd = pty.fork()
        if pid == 0:
            # Child process
            os.execvp("bash", ["bash", "-c", cmd])
        else:
            # Parent process: store references
            self.pid = pid
            self.fd = fd
            self.active = True
            # Make the file descriptor non-blocking so we can repeatedly read
            # until no more data is available.
            os.set_blocking(self.fd, False)

    def _read_output_loop(self, poll_interval=0.2):
        """
        Continuously read any available output from the child until:
          - The process indicates it's waiting for input (via strace), or
          - The process exits (fd closes).
        
        Returns all captured output as a string.
        """
        output_buffer = []

        while True:
            # Wait up to `poll_interval` for the child fd to be ready
            ready, _, _ = select.select([self.fd], [], [], poll_interval)

            if self.fd in ready:
                # Read everything available until BlockingIOError
                while True:
                    try:
                        chunk = os.read(self.fd, 4096)
                        if not chunk:
                            # Child closed the fd -> process ended
                            self.active = False
                            return "".join(output_buffer)
                        else:
                            output_buffer.append(chunk.decode(errors="ignore"))
                    except BlockingIOError:
                        # Nothing more to read this instant
                        break
                    except OSError:
                        # Some other error, assume process ended
                        self.active = False
                        return "".join(output_buffer)

            # Check if process ended
            if not self._is_process_alive():
                self.active = False
                return "".join(output_buffer)

            # Use strace to check if the child is waiting on stdin
            if self._is_waiting_for_input():
                ready, _, _ = select.select([self.fd], [], [], poll_interval)

                if self.fd in ready:
                    # Read everything available until BlockingIOError
                    while True:
                        try:
                            chunk = os.read(self.fd, 4096)
                            if not chunk:
                                # Child closed the fd -> process ended
                                self.active = False
                                return "".join(output_buffer)
                            else:
                                output_buffer.append(chunk.decode(errors="ignore"))
                        except BlockingIOError:
                            # Nothing more to read this instant
                            break
                        except OSError:
                            # Some other error, assume process ended
                            self.active = False
                            return "".join(output_buffer)
                return "".join(output_buffer)

    def _is_process_alive(self) -> bool:
        """
        Check if the child process is still alive without blocking.
        """
        if self.pid is None:
            return False
        try:
            pid_done, _ = os.waitpid(self.pid, os.WNOHANG)
            return pid_done == 0
        except ChildProcessError:
            return False

    def _is_waiting_for_input(self) -> bool:
        """
        Use a brief strace call to see if the process is blocked on reading stdin (FD=0).
        Returns True if 'read(0,' is found in strace output, implying it awaits input.
        
        NOTE: This is a heuristic; it may need adjustment for certain applications.
        """
        if not self._is_process_alive():
            return False

        cmd = [
            "timeout", "0.1",
            "strace", "-p", str(self.pid),
            "-e", "trace=read"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # print(result)
        return ("read(" in result.stderr)

    def run_or_send(self, cmd_or_input: str) -> str:
        """
        Main interaction method:
          - If no active child, spawn one with `cmd_or_input` as the command.
            Then read output until the process is waiting or exits, and return it.
          
          - If there's an active child (presumably waiting for input),
            write `cmd_or_input` to it, then read output until waiting again or exit.
            
        Returns the text output that was collected during the read loop.
        """
        if not self.active:
            # Spawn a new process
            self._spawn_process(cmd_or_input)
            return self._read_output_loop(0.2)
        else:
            # Send input to an existing process
            user_input = cmd_or_input if cmd_or_input.endswith("\n") else cmd_or_input + "\n"
            os.write(self.fd, user_input.encode())
            
            # A tiny sleep helps the child app read the data before we poll again
            time.sleep(0.05)
            
            # Collect and return any resulting output
            return self._read_output_loop(0.2)
    



if __name__ == "__main__":
    a = InteractiveProcess()

    while True:
        print(a.run_or_send(input()),end="")