import sys
import re

if __name__ == "__main__":
    diff_md = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

    with open(diff_md, "r") as f:
        diff = f.read()

    prj_name_pat = r"[a-zA-Z0-9_-]+"

    diff = re.sub(rf"! ({prj_name_pat})", r"change(mods): Update mod \1", diff)
    diff = re.sub(rf"\+ ({prj_name_pat})", r"feat(mods): Add mod \1", diff)
    diff = re.sub(rf"- ({prj_name_pat})", r"remove(mods): Remove mod \1", diff)

    diff = diff.strip().removeprefix("```diff").removesuffix("```").strip()

    if out:
        with open(out, "w") as f:
            f.write(diff)
    else:
        print(diff)
