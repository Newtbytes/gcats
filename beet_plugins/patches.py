import beet
from copy import deepcopy


@beet.configurable
def add_entry_to_loot_tables(ctx: beet.Context, ops: dict):
    tables_to_remove = []

    for key, table in ctx.data.loot_tables.items():
        if any(
            [
                ops["source"] not in str(table.data),
                any([skip in key for skip in ops.get("skip", [])]),
            ]
        ):
            tables_to_remove.append(key)
            continue

        for pool in table.data.get("pools", {}):
            new_entries = []

            for entry in pool.get("entries", []):
                if ops["source"] in entry.get("name", ""):
                    new_entry = deepcopy(entry)
                    new_entry["name"] = ops["target"]
                    new_entries.append(new_entry)

            pool["entries"] += new_entries

    for key in tables_to_remove:
        ctx.data.loot_tables.pop(key)
