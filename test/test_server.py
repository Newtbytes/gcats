"""
Test that the server runs without crashing due to mod conflicts, failure to load datapacks, etc.
"""

from utils.server import MinecraftServer


def test_server_runs():
    """test that the server initializes correctly without crashing"""
    server = MinecraftServer(server_dir="build/server/")

    stopped = False

    while True:
        if server.started() and not stopped:
            server.run("stop")

            stopped = True

        if server.done():
            break

    # for debug purposes in case of failure
    print(server.log())

    assert server.returncode == 0 and not server.crashed()
