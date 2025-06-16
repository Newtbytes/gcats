from functools import reduce
import io
from typing import Any, Optional
import zipfile
import tomllib as toml

import requests
import beet


def download_zip(url: str) -> zipfile.ZipFile:
    response = requests.get(url)
    response.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(response.content))


def get_one_pack(pack: dict[str, str]) -> Optional[beet.ResourcePack]:
    url = pack["url"]

    print(f"Downloading: {url}")
    try:
        zipped_pack = download_zip(url)
        return beet.ResourcePack(zipfile=zipped_pack)
    except Exception as e:
        print(f"Failed to download {url}: {e}")


def get_packs(conf: dict) -> list[beet.ResourcePack]:
    return [s for pack in conf["packs"] if (s := get_one_pack(pack))]


def parse_conf(conf_fn: str) -> dict[str, Any]:
    with open(conf_fn, "rb") as f:
        conf = toml.load(f)

    return conf


def merge_packs(
    pack_a: beet.ResourcePack, pack_b: beet.ResourcePack
) -> beet.ResourcePack:
    pack_a.merge(pack_b)
    return pack_a


def main(url_list_path, output_zip_path):
    conf = parse_conf(url_list_path)

    packs = get_packs(conf)
    packs.reverse()

    print(f"Merging {len(packs)} ZIPs into: {output_zip_path}")

    pack: beet.ResourcePack = reduce(
        merge_packs,
        packs,
    )

    pack.name = "pack"

    print("Done.")

    pack.save(output_zip_path, zipped=True, overwrite=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and merge ZIP files from a list of URLs."
    )
    parser.add_argument("conf", help="Path to pack configuration file")
    parser.add_argument("output_zip", help="Path to the output built pack")
    args = parser.parse_args()

    main(args.conf, args.output_zip)
