import re
import sys
import os.path

from dataclasses import dataclass
from collections import defaultdict
from enum import StrEnum

from typing import Any, Callable
from urllib.parse import urlparse, urljoin, ParseResult as URL
import json


class ToMarkdown:
    def to_md(self) -> str:
        raise NotImplementedError


class ProjectProvider(StrEnum):
    MODRINTH = "modrinth"
    CURSEFORGE = "curseforge"

    def to_url(self) -> URL:
        match self:
            case ProjectProvider.MODRINTH:
                return urlparse("https://modrinth.com")
            case ProjectProvider.CURSEFORGE:
                return urlparse("https://curseforge.com")

    def to_md(self) -> str:
        title = ""

        match self:
            case ProjectProvider.CURSEFORGE:
                title = "CurseForge"
            case _:
                title = self.value.title()

        return f"*{title}*"


class ProjectSide(StrEnum):
    SERVER = "server"
    CLIENT = "client"
    BOTH = "both"

    def to_md(self) -> str:
        return f"{self.value.capitalize()}{'-side' if not self == ProjectSide.BOTH else ''}"


class ProjectType(StrEnum):
    MOD = "mod"
    DATAPACK = "datapack"
    RESOURCEPACK = "resourcepack"

    def to_md(self) -> str:
        md = self.value.replace("pack", " pack")
        md = md.title()

        return f"*{md}*"


@dataclass
class ProjectURL(ToMarkdown):
    provider: ProjectProvider
    project_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectURL":
        # {
        #     <provider>: <id>
        # }

        provider, id = list(data.items())[0]

        return cls(ProjectProvider(provider), id)

    def to_url(self):
        url = self.provider.to_url()

        match self.provider:
            case ProjectProvider.MODRINTH:
                url = urlparse(urljoin(url.geturl(), "/project/" + self.project_id))
            case ProjectProvider.CURSEFORGE:
                raise NotImplementedError

        return url.geturl()

    def to_md(self) -> str:
        return f"[{self.to_url()}]({self.to_url()})"


@dataclass
class ProjectInfo(ToMarkdown):
    name: str
    ty: ProjectType
    side: ProjectSide
    url: ProjectURL

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectInfo":
        return cls(
            name=data["name"].get("modrinth", data["name"].get("curseforge")),
            ty=ProjectType(data["type"].lower()),
            side=ProjectSide(data["side"].lower()),
            url=ProjectURL.from_dict(data["id"]),
        )

    def to_md(self) -> str:
        return f"***{self.name.strip()}***: " + self.url.to_md()


def fmt_row(*values: str) -> str:
    return f"| {' | '.join(values)} |"


def fmt_table_header(*headers: str) -> str:
    out = fmt_row(*headers) + "\n"
    out += fmt_row(*["-------------" for _ in range(len(headers))])
    return out


def fmt_project_table(projects: list[ProjectInfo]) -> str:
    out = fmt_table_header("Name", "URL") + "\n"

    out += "\n".join(
        [fmt_row(project.name, project.url.to_md()) for project in projects]
    )

    return out


def fmt_modlist(projects: list[ProjectInfo]):
    def group_by_field(
        projects: list[ProjectInfo], key: Callable[[ProjectInfo], Any]
    ) -> dict[Any, list[ProjectInfo]]:
        grouped = defaultdict(list)

        for project in projects:
            grouped[key(project)].append(project)

        return grouped

    def first_header(
        s: str,
    ) -> str:
        return f"# {s}"

    def second_header(
        s: str,
    ) -> str:
        return f"## {s}"

    out = []

    sections = {
        ty: group_by_field(prjs, lambda prj: prj.side)
        for ty, prjs in group_by_field(projects, lambda prj: prj.ty).items()
    }

    for ty, project_of_ty in sections.items():
        ty: ProjectType
        project_of_ty: dict[ProjectSide, list[ProjectInfo]]

        out.append(first_header(f"*{str(ty).capitalize()}s*"))
        for side, projects in project_of_ty.items():
            out.append(second_header(side.to_md()))
            out.append(fmt_project_table(projects))

    return "\n".join(out)


def replace_modlist(doc: str, replacement: str):
    modlist_pat = re.compile(
        r"^# \*?Mods\*?\b[\s\S]*?(?=^# |\Z)",
        flags=re.MULTILINE,
    )

    return re.sub(modlist_pat, replacement, doc)


def main():
    if len(sys.argv) == 1:
        print("usage:")
        print(f"    python {os.path.basename(__file__)} LOCK_FILE README")
        return

    lock_file = json.loads(open(sys.argv[1], "r").read())

    projects = [
        ProjectInfo.from_dict(project_data) for project_data in lock_file["projects"]
    ]

    modlist = fmt_modlist(projects)

    print(modlist)

    readme_fn = sys.argv[2]

    if os.path.exists(readme_fn):
        new_readme = replace_modlist(open(readme_fn, "r").read(), modlist)
        readme_file = open(readme_fn, "w")
    else:
        new_readme = modlist
        readme_file = open(readme_fn, "x")

    readme_file.write(new_readme)
    readme_file.close()


if __name__ == "__main__":
    main()
