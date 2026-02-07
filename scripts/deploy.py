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
        self, id: str, token: str, base="https://api.exaroton.com/v1/"
    ) -> None:
        super().__init__()

        self.id = id
        self.base = URL(base)
        self.headers = {"Authorization": f"Bearer {token}"}

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
    def mkdir(self, fn: str):
        print(fn)

        url = str(self.base / "servers" / self.id / "files" / "data" / fn)

        headers = {"Content-Type": "inode/directory", **self.headers}
        requests.put(url, headers=headers, timeout=10).raise_for_status()

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
    def write(self, src: str, dst: str):
        print(dst)

        url = str(self.base / "servers" / self.id / "files" / "data" / dst)

        if os.path.isdir(src):
            headers = {"Content-Type": "inode/directory", **self.headers}
            requests.put(url, headers=headers, timeout=10).raise_for_status()
        else:
            with open(src, "rb") as f:
                requests.put(
                    url, data=f, headers=self.headers, timeout=10
                ).raise_for_status()


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


# explicitly not abstract right now since there's no need
def write_folder(fs: ExarotonServer, src: str, dst: str):
    for fn in collect_files(src, collect_directories=False):
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
