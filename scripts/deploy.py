from abc import ABC, abstractmethod

import sys
import os.path

import requests
import backoff
from dotenv import load_dotenv
from yarl import URL


class Filesystem(ABC):
    @abstractmethod
    def write(self, fn: str, data): ...


class ExarotonServer(Filesystem):
    def __init__(
        self, id: str, token: str, base="https://api.exaroton.com/v2/"
    ) -> None:
        super().__init__()

        self.id = id
        self.token = token
        self.base = base

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
    def mkdir(self, fn: str):
        url = str(URL(self.base) / "servers" / self.id / "files" / "data" / fn)

        requests.put(url, headers={"Content-Type": "inode/directory"})

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
    def write(self, src: str, dst: str):
        url = str(URL(self.base) / "servers" / self.id / "files" / "data" / dst)

        if os.path.isdir(src):
            headers = {"Content-Type": "inode/directory"}
            requests.put(url, headers=headers)
        else:
            with open(src, "rb") as f:
                requests.put(url, data=f)


def collect_files(path: str) -> list[str]:
    """
    Return all files in a directory, recursively.
    Returned filenames are relative to the input directory.
    """

    files = []

    for subpath in os.listdir(path):
        if os.path.isdir(subpath):
            files += [os.path.join(subpath, fn) for fn in collect_files(subpath)]

        files.append(subpath)

    return files


# explicitly not abstract right now since there's no need
def write_folder(fs: ExarotonServer, src: str, dst: str):
    for fn in collect_files(src):
        fs.write(os.path.join(src, fn), os.path.join(dst, fn))


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

    for subdir in os.listdir(server_dir):
        dir = os.path.join(server_dir, subdir)

        if os.path.isdir(dir):
            write_folder(deploy_tgt, dir, subdir)


if __name__ == "__main__":
    main()
