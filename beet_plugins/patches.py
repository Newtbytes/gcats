from copy import deepcopy

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
