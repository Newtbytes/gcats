from copy import deepcopy
import json
from jsonpatch import apply_patch, JsonPatchTestFailed

import beet


@beet.configurable
def add_entry_replacement_to_loot_tables(ctx: beet.Context, ops: dict):
    for key, table in ctx.data.loot_tables.items():
        if any(
            [
                ops["source"] not in str(table.data),
                any([skip in key for skip in ops.get("skip", [])]),
            ]
        ):
            continue

        for pool in table.data.get("pools", {}):
            new_entries = []

            for entry in pool.get("entries", []):
                if ops["source"] in entry.get("name", ""):
                    new_entry = deepcopy(entry)
                    new_entry["name"] = ops["target"]
                    new_entries.append(new_entry)

            pool["entries"] += new_entries


def apply_json_patch(ctx: beet.Context, key: str, patch: beet.File):
    ctx.query(extend=type(patch), match=key)

    for matches in ctx.query(extend=type(patch), match=key).values():
        for key, file in matches:
            try:
                file.set_content(
                    json.dumps(
                        apply_patch(
                            doc=json.loads(file.get_content()),
                            patch=patch.get_content(),
                        )
                    )
                )
            except JsonPatchTestFailed:
                continue


def json_patch(ctx: beet.Context):
    for matches in ctx.query(match="*.patch*").values():
        for key, file in matches:
            if not key.endswith(".patch"):
                continue

            key = key.removesuffix(".patch")

            apply_json_patch(ctx, key, file)
