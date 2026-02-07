import sys
import os.path

import requests
import backoff
from dotenv import load_dotenv
from yarl import URL


def fatal_code(e):
    return 400 <= e.response.status_code < 500


requester = backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_time=300,
    giveup=fatal_code,
)


class ExarotonServer:
    def __init__(
        self, id: str, token: str, base="https://api.exaroton.com/v1/"
    ) -> None:
        super().__init__()

        self.id = id
        self.base = URL(base)
        self.headers = {"Authorization": f"Bearer {token}"}

    def files_data_uri(self, path: str) -> str:
        return str(self.base / "servers" / self.id / "files" / "data" / path)

    def files_info_uri(self, path: str) -> str:
        return str(self.base / "servers" / self.id / "files" / "info" / path)

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
    def file_info(self, path: str) -> dict:
        url = self.files_info_uri(path)

        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()

        return resp.json()

    def isdir(self, path: str) -> bool:
        return self.file_info(path)["isDirectory"]

    def exists(self, path: str) -> bool:
        try:
            return self.file_info(path)["success"]
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
            deploy_tgt.remove(subdir)
            write_folder(deploy_tgt, dir, subdir)


if __name__ == "__main__":
    main()
