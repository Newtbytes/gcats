"""
Test that the server runs without crashing due to mod conflicts, failure to load datapacks, etc.
"""

import pytest

from dataclasses import dataclass
import json
from zipfile import ZipFile
import os.path

from utils.server import MinecraftServer


@dataclass
class ServerRun:
    returncode: int | None
    crashed: bool
    log: str


@pytest.fixture
def server() -> MinecraftServer:
    return MinecraftServer(server_dir="build/server/")


@pytest.fixture
def full_server_run(server: MinecraftServer) -> ServerRun:
    stopped = False

    while True:
        if server.started() and not stopped:
            server.run("stop")

            stopped = True

        if server.done():
            break

    return ServerRun(server.returncode, server.crashed(), server.log())


@pytest.fixture
def pakku_lock() -> dict:
    with open("pakku-lock.json") as f:
        return json.load(f)


@pytest.fixture
def pakku_conf() -> dict:
    with open("pakku.json") as f:
        return json.load(f)


def test_server_runs(full_server_run: ServerRun):
    """test that the server initializes correctly without crashing"""

    assert full_server_run.returncode == 0 and not full_server_run.crashed


def get_mod_metadata(fn: str):
    with ZipFile(fn) as z:
        with z.open("fabric.mod.json") as f:
            return json.load(f)


def test_mods_loaded(full_server_run: ServerRun, pakku_lock: dict, pakku_conf: dict):
    log = full_server_run.log
    target = pakku_lock["target"]

    for project in pakku_lock["projects"]:
        side: str = project["side"]
        ty: str = project["type"]
        slug: str = project["slug"][target].strip()
        name: str = project["name"][target].strip()
        files: list[dict] = project["files"]

        export: bool = project["export"] if "export" in project else True
        export = export and len(files) > 0

        probably_client_side = side == "CLIENT"
        if slug in pakku_conf["projects"]:
            if "side" in pakku_conf["projects"][slug]:
                probably_client_side = (
                    probably_client_side
                    or pakku_conf["projects"][slug]["side"] == "SERVER"
                )

        if side == "SERVER" and not probably_client_side and ty == "MOD" and export:
            filename = os.path.join("build/server/mods", files[0]["file_name"])

            assert os.path.exists(filename)

            meta = get_mod_metadata(filename)

            assert meta["id"] in log, (
                f"mod '{name}' doesn't seem to have been loaded when running the server"
            )
