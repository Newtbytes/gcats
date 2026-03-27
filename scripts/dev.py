import random
import uuid
import subprocess
import argparse

import minecraft_launcher_lib

from tests.utils.server import MinecraftServer

parser = argparse.ArgumentParser()

parser.add_argument("-v", "--version", default="latest")
parser.add_argument("--quickPlayMultiplayer")
args = parser.parse_args()

version = args.version

if version == "latest":
    version = minecraft_launcher_lib.utils.get_latest_version()["release"]

minecraft_directory = ".minecraft"
minecraft_launcher_lib.install.install_minecraft_version(
    version, minecraft_directory, callback={"setStatus": print}
)

username = f"Player{random.randrange(100, 1000)}"

options = minecraft_launcher_lib.types.MinecraftOptions(
    username=username,
    uuid=str(uuid.uuid4()),
    token="",
)
if args.quickPlayMultiplayer:
    options["quickPlayMultiplayer"] = args.quickPlayMultiplayer

minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
    version, minecraft_directory, options
)

SERVER_DIR = "build/server/"
server = MinecraftServer(server_dir=SERVER_DIR)
client = None

with open(SERVER_DIR + "/server.properties", "r") as f:
    props = f.read()

if "online-mode" in props:
    props = props.replace("online-mode=true", "online-mode=false")
else:
    props += "\nonline-mode=false"

with open(SERVER_DIR + "/server.properties", "w") as f:
    f.write(props)

while True:
    if server.started() and client is None:
        client = subprocess.Popen(minecraft_command)
        server.run(f"op {username}")
        server.run(f"gamemode creative {username}")

    if client is None:
        continue

    if server.done() or client.poll():
        if server.done() and not client.poll():
            client.kill()

        if client.poll() and not server.done():
            server.run("stop")

    if server.done() and client.poll():
        break
