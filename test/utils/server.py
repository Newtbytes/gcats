from typing import Optional, Union

import signal
import subprocess
import threading
import os.path

import re


def _agree_eula(server_dir: Union[str, None]):
    fn = "eula.txt"

    if server_dir is not None:
        fn = os.path.join(server_dir, fn)

    with open(fn, mode="w") as f:
        f.write("eula=true")


class MinecraftServer:
    """
    Control a Minecraft server subprocess programmatically from Python.

    Note: by running ServerProcess.__init__ you agree to the Minecraft: Java Edition EULA
    as __init__ creates a "eula.txt" with the contents "eula=true".
    """

    _process: subprocess.Popen[str]

    _output: str
    _output_thread: threading.Thread

    def __init__(self, server_dir: Optional[str], server_jar="server.jar") -> None:
        _agree_eula(server_dir)

        self._process = subprocess.Popen(
            ["java", "-jar", server_jar, "nogui"],
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        self._output = ""

        self._output_thread = threading.Thread(target=self.poll_log)
        self._output_thread.start()

    @classmethod
    def _agree_eula(cls, server_dir: str):
        with open(os.path.join(server_dir, "eula.txt"), mode="w") as f:
            f.write("eula=true")

    def poll_log(self):
        while True:
            if self.done():
                break

            if self._process.stdout is not None:
                c = self._process.stdout.read(1)

                self._output += c

                if c == "\n":
                    print(self._output.splitlines()[-1])

    def log(self) -> str:
        return self._output

    def check_regex(self, pat: str) -> bool:
        return re.match(pat, self.log()) is not None

    def started(self) -> bool:
        return (
            not self.done()
            and 'For help, type "help"\n' in self.log()
            and "Done (" in self.log()
        )

    def crashed(self) -> bool:
        return "Minecraft Crash Report" in self.log()

    def run(self, command: str):
        if self._process.stdin is not None:
            self._process.stdin.write(command + "\n")
            self._process.stdin.flush()

    @property
    def returncode(self) -> Optional[int]:
        return self._process.returncode

    def done(self) -> bool:
        self._process.poll()

        if self.crashed() and self.returncode is None:
            self._process.send_signal(signal.CTRL_C_EVENT)
            self._process.wait()

        return self.returncode is not None
