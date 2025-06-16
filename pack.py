import io
from typing import Any
import zipfile
import requests
import tomllib as toml


def download_zip(url):
    response = requests.get(url)
    response.raise_for_status()
    return io.BytesIO(response.content)


def merge_zips(zip_streams, output_path):
    seen_files = set()
    with zipfile.ZipFile(output_path, "w") as output_zip:
        for zip_stream in zip_streams:
            with zipfile.ZipFile(zip_stream) as zip_file:
                for name in zip_file.namelist():
                    if name in seen_files or name.endswith("/"):
                        continue  # Skip duplicates and directories
                    seen_files.add(name)
                    data = zip_file.read(name)
                    output_zip.writestr(name, data)


def build_pack(pack: dict[str, str]):
    url = pack["url"]

    print(f"Downloading: {url}")
    try:
        return download_zip(url)
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def get_pack_streams(conf: dict):
    streams = []

    for pack in conf["packs"]:
        s = build_pack(pack)

        if s:
            streams.append(s)

    return streams


def parse_conf(conf_fn: str) -> dict[str, Any]:
    with open(conf_fn, "rb") as f:
        conf = toml.load(f)

    return conf


def main(url_list_path, output_zip_path):
    conf = parse_conf(url_list_path)

    zip_streams = get_pack_streams(conf)

    print(f"Merging {len(zip_streams)} ZIPs into: {output_zip_path}")
    merge_zips(zip_streams, output_zip_path)
    print("Done.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and merge ZIP files from a list of URLs."
    )
    parser.add_argument("url_list", help="Path to text file containing ZIP URLs")
    parser.add_argument("output_zip", help="Path to output merged ZIP file")
    args = parser.parse_args()

    main(args.url_list, args.output_zip)
