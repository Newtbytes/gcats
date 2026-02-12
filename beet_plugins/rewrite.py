import beet
from copy import deepcopy


def beet_default(ctx: beet.Context):
    tables_to_remove = []

    for key, table in ctx.data.loot_tables.items():
        if "rotten_flesh" not in str(table.data):
            tables_to_remove.append(key)
            continue

        for pool in table.data.get("pools", {}):
            new_entries = []

            for entry in pool.get("entries", []):
                if "rotten_flesh" in entry.get("name", ""):
                    new_entry = deepcopy(entry)
                    new_entry["name"] = "gcats:cloth"
                    new_entries.append(new_entry)

            pool["entries"] += new_entries

    for key in tables_to_remove:
        ctx.data.loot_tables.pop(key)
