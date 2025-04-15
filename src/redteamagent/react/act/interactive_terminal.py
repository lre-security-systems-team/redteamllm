import os
import pty
import select
import subprocess
import sys
import time
import re

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

            # Use strace to check if the child might be waiting
            if self._is_waiting_for_input():
                # Just in case there's a tiny bit of output left in the buffer,
                # we do one more immediate non-blocking read before returning.
                # This helps catch partial lines that arrived while we were stracing.
                ready, _, _ = select.select([self.fd], [], [], 0.05)
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
        Use a brief strace call to see if the process might be waiting on input.
        We trace multiple syscalls: read,write,ioctl,poll,select,epoll_wait.
        
        Return True if:
          - We see any sign of read(0,...) OR
          - poll({fd=0, ... => indicates the process is polling FD=0
          - select or epoll waiting on FD=0
          - or any other clue that the program is blocked waiting for user input.
          
        NOTE: This is still heuristic. Some programs don't wait in these syscalls.
        """
        if not self._is_process_alive():
            return False

        # We'll trace multiple syscalls in case the program is using them to wait.
        # The '-f' means follow children if the process spawns them.
        # The 'timeout' is set to 0.5s, but you can increase if you keep missing the call.
        cmd = [
            "timeout", "0.5",
            "strace",
            "-p", str(self.pid),
            "-f",
            "-e", "trace=read,write,ioctl,poll,select,epoll_wait"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Returncode 124 => timed out, so we won't rely on that alone.
        # We'll scan stderr for patterns that indicate waiting on FD=0.
        # Examples:
        #   read(0, ...
        #   poll([{fd=0, ...
        #   select(1, [0], ...
        #   epoll_wait(...) where fd=0 is in the wait set (less common)
        #
        # For a more robust approach, you could do a more advanced parse
        # to see if the "fd=..." matches 0 or not. We'll do a simple search for now.
        
        output = result.stderr.lower()
        print(result)  # For debug; remove if not needed

        # Basic checks for "read(0," or "poll([{fd=0," or "select(...[0],..."
        patterns = [
            r"read\(0,",         # read(0,...
            r"poll\(\{\{fd=0,",  # poll({fd=0,
            r"select\(\d+, \[0", # select(..., [0 ...
            r"epoll_wait"        # Some apps do epoll_wait on FD sets that include 0
        ]

        for pat in patterns:
            if re.search(pat, output):
                return True

        return False

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
        user_cmd = input()
        out = a.run_or_send(user_cmd)
        print(out, end="")
