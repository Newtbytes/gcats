from dataclasses import dataclass

import sys
import os.path
from typing import Optional
import string

import requests
from dotenv import load_dotenv
from joblib import Parallel, delayed
from yarl import URL
import json

from utils import requester


# directories that should be fullied synchronized
# e.g. if the deployment server has a file that isn't in the folder being deployed, it is removed
# for the mods folder for example, this prevents old versions of mods being kept
FULL_SYNC_DIRS = ["mods"]


def parse_conf_file(fn: str) -> dict:
    """Parse a key=value style config file."""

    with open(fn) as f:
        content = f.read()

    parsed: dict = {
        line[: line.find("=")]: line[line.find("=") + 1 :]
        for line in content.splitlines()
        if not line.startswith("#") and line.strip()
    }

    def is_str(s: str) -> bool:
        return (s.startswith('"') and s.endswith('"')) or (
            s.startswith("'") and s.endswith("'")
        )

    for k, v in list(parsed.items()):
        if is_str(v):
            for quote in ['"', "'"]:
                v.removeprefix(quote)
                v.removesuffix(quote)
            continue

        if v == "true" or v == "false":
            parsed[k] = bool(v)

        if v.isdecimal():
            parsed[k] = int(v)

    return parsed


@dataclass
class ExarotonFileInfo:
    path: str
    name: str
    isTextFile: bool
    isConfigFile: bool
    isDirectory: bool
    isLog: bool
    isReadable: bool
    isWritable: bool
    size: int
    children: Optional[list["ExarotonFileInfo"]]

    @classmethod
    def from_dict(cls, data: dict) -> "ExarotonFileInfo":
        assert data["isDirectory"] or (
            not data["isDirectory"] and data["children"] is None
        )

        if data["children"] is not None:
            data["children"] = [cls.from_dict(c) for c in data["children"]]

        return cls(**data)


class ExarotonServer:
    def __init__(
        self, id: str, token: str, base="https://api.exaroton.com/v1/"
    ) -> None:
        super().__init__()

        self.id = id
        self.base = URL(base)
        self.headers = {"Authorization": f"Bearer {token}"}

    @property
    def server_uri(self) -> URL:
        return self.base / "servers" / self.id

    @property
    def files_uri(self) -> URL:
        return self.server_uri / "files"

    @property
    def config_uri(self) -> URL:
        return self.files_uri / "config"

    def files_data_uri(self, path: str) -> str:
        return str(self.files_uri / "data" / path)

    def files_info_uri(self, path: str) -> str:
        return str(self.files_uri / "info" / path)

    @property
    @requester
    def version(self) -> str:
        url = str(self.server_uri)

        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()

        content = resp.json()

        if content["error"] is not None:
            raise Exception(content["error"])

        return content["data"]["software"]["version"]

    def is_conf_file(self, fn: str) -> bool:
        return fn.endswith("server.properties")

    def post_conf_file(self, data: dict, fn: str):
        url = str(self.config_uri / fn)

        resp = requests.post(
            url=url,
            headers={**self.headers, "Content-Type": "application/json"},
        )
        resp.raise_for_status()

        content = resp.json()

        if content["error"] is not None:
            raise ValueError(content["error"])

    def writable(self, fn: str) -> bool:
        return not any([fn.endswith(f) for f in ["server.jar", "eula.txt"]])

    @requester
    def mkdir(self, path: str):
        url = self.files_data_uri(path)

        parent = os.path.dirname(path)
        if parent and not self.exists(parent):
            self.mkdir(parent)

        headers = {"Content-Type": "inode/directory", **self.headers}
        requests.put(url, headers=headers, timeout=10).raise_for_status()

        print(f"+ {path}")

    @requester
    def file_info(self, path: str) -> Optional[ExarotonFileInfo]:
        url = self.files_info_uri(path)

        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()

        content = resp.json()

        if content["error"] is not None:
            raise FileNotFoundError(content["error"])

        return ExarotonFileInfo.from_dict(content["data"]) if content["data"] else None

    def listdir(self, path: str) -> list[ExarotonFileInfo]:
        match self.file_info(path):
            case None:
                return []
            case info:
                return [c for c in info.children] if info.children else []

    def isdir(self, path: str) -> bool:
        match self.file_info(path):
            case None:
                return False
            case info:
                return info.isDirectory

    def exists(self, path: str) -> bool:
        try:
            return self.file_info(path) is not None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise e

    @requester
    def remove(self, path: str):
        url = self.files_data_uri(path)

        if self.exists(path):
            requests.delete(url, headers=self.headers, timeout=10).raise_for_status()

        print(f"- {path}")

    @requester
    def write(self, src: str, dst: str):
        url = self.files_data_uri(dst)

        if not self.writable(dst):
            return

        if self.is_conf_file(dst):
            self.post_conf_file(parse_conf_file(src), dst)
        else:
            dst_dir = os.path.dirname(dst)
            if dst_dir and not self.exists(dst_dir):
                self.mkdir(dst_dir)

            if os.path.isdir(src):
                headers = {"Content-Type": "inode/directory", **self.headers}
                requests.put(url, headers=headers, timeout=10).raise_for_status()
            else:
                with open(src, "rb") as f:
                    requests.put(
                        url, data=f, headers=self.headers, timeout=10
                    ).raise_for_status()

        print(f"+ {dst}")


def collect_files(root: str, collect_directories=True) -> list[str]:
    """
    Return all files in a directory, recursively.
    Returned filenames are relative to the input directory.
    """

    files = []

    for subpath in os.listdir(root):
        path = os.path.join(root, subpath)

        if os.path.isdir(path):
            files += [
                os.path.join(subpath, fn)
                for fn in collect_files(path, collect_directories)
            ]

        if not os.path.isdir(path) or collect_directories:
            files.append(subpath)

    return files


def is_versioned_file(fn: str):
    return (
        any([d in fn for d in string.digits])
        and fn.count(".") > 1
        and len(fn) > len("server.jar")
    )


def _write_file_task(
    fs: ExarotonServer, src: str, dst: str, fn: str, server_files_names: list[str]
):
    """Helper function for parallelized file writing."""
    if fn in server_files_names and is_versioned_file(fn):
        print(f"  {fn}")
        return

    fs.write(os.path.join(src, fn), os.path.join(dst, fn))


# explicitly not abstract right now since there's no need
def write_folder(fs: ExarotonServer, src: str, dst: str):
    files = os.listdir(src)
    server_files = fs.listdir(dst) if fs.exists(dst) else []
    server_files_names = [f.name for f in server_files]

    if dst in FULL_SYNC_DIRS:
        for file_info in server_files:
            if file_info.name not in files:
                fs.remove(file_info.path.removeprefix("/"))

    Parallel(n_jobs=4)(
        delayed(_write_file_task)(fs, src, dst, fn, server_files_names)
        for fn in files
        if not os.path.isdir(os.path.join(src, fn))
    )

    for subdir in files:
        path = os.path.join(src, subdir)

        if not os.path.isdir(path):
            continue

        write_folder(fs, path, os.path.join(dst, subdir))


def main():
    if len(sys.argv) == 1:
        print("usage:")
        print(f"    python {os.path.basename(__file__)} SERVER_DIR")
        return

    load_dotenv("secrets.env")

    deploy_tgt = ExarotonServer(
        os.getenv("EXAROTON_SERVER_ID", ""), os.getenv("EXAROTON_TOKEN", "")
    )

    server_dir = sys.argv[1]

    lockfile = json.load(open("pakku-lock.json"))

    supported_versions = [
        f"{ver} ({lockfile['loaders']['fabric']})" for ver in lockfile["mc_versions"]
    ]
    if deploy_tgt.version not in supported_versions:
        print(
            f"WARNING: Server version {deploy_tgt.version} not in lockfile versions {supported_versions}"
        )

    write_folder(deploy_tgt, server_dir, "")


if __name__ == "__main__":
    main()
