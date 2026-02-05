from copy import deepcopy
from dataclasses import dataclass, field
from typing import Iterator, Optional, Type
from urllib.parse import ParseResult as ParsedURL
from abc import ABC, abstractmethod


class Node(ABC):
    @abstractmethod
    def __str__(self) -> str: ...


@dataclass
class Text(Node):
    value: str | list[Node]

    def __str__(self) -> str:
        return (
            self.value
            if isinstance(self.value, str)
            else "".join(str(n) for n in self.value)
        )


@dataclass
class Line(Node):
    value: Node

    def __str__(self) -> str:
        return f"{self.value}\n"

    @classmethod
    def empty(cls) -> "Line":
        return cls(Text(""))


def collapse_double_lines(lines: Iterator[Line]) -> Iterator[Line]:
    lines_buffer = list(lines)  # Convert to list for random access

    for i, curr_line in enumerate(lines_buffer):
        next_line = lines_buffer[i + 1] if i < len(lines_buffer) - 1 else None

        if curr_line == Line.empty() and next_line == Line.empty():
            continue
        else:
            yield curr_line


@dataclass
class Heading(Node):
    value: Node
    n: int

    def __str__(self) -> str:
        return f"{'#' * self.n} {self.value}"


def separate_headings(lines: Iterator[Line]) -> Iterator[Line]:
    """
    Ensure that all headings are surrounded by empty lines.
    """
    lines_buffer = list(lines)  # Convert to list for random access

    for i, curr_line in enumerate(lines_buffer):
        last_line = lines_buffer[i - 1] if i > 0 else None
        next_line = lines_buffer[i + 1] if i < len(lines_buffer) - 1 else None

        if isinstance(curr_line.value, Heading):
            if last_line and last_line.value != Text(""):
                yield Line.empty()

            yield curr_line

            if next_line and next_line.value != Text(""):
                yield Line.empty()
        else:
            yield curr_line


def text_wrapper(wrap_with: str) -> Type:
    @dataclass
    class TextWrapper(Node):
        value: Node

        def __str__(self) -> str:
            return f"{wrap_with}{self.value}{wrap_with}"

    return TextWrapper


Italics = text_wrapper("*")
Bold = text_wrapper("**")


@dataclass
class URL(Node):
    url: Text | ParsedURL
    text: Optional[Node] = field(default=None)

    def __str__(self) -> str:
        text = self.text if self.text is not None else self.url

        url = self.url
        if isinstance(url, ParsedURL):
            url = url.geturl()

        return f"[{text}]({url})"


@dataclass
class Row(Node):
    values: list[Node]

    def __getitem__(self, i: int) -> Node:
        return self.values[i]

    def __len__(self) -> int:
        return len(self.values)

    def __str__(self) -> str:
        return f"| {' | '.join([str(v) for v in self])} |"


@dataclass
class Table(Node):
    headers: Row
    rows: list[Row]

    def __str__(self):
        return ""


def process_tables(lines: Iterator[Line]) -> Iterator[Line]:
    for line in lines:
        if isinstance(line.value, Table):
            table = line.value

            yield Line(table.headers)
            yield Line(Row([Text("-------------") for _ in range(len(table.headers))]))
            for row in table.rows:
                yield Line(row)
        else:
            yield line


@dataclass
class Document(Node):
    lines: list[Line]

    _processors = [
        separate_headings,
        process_tables,
        collapse_double_lines,
    ]

    def _process_step(self):
        lines = iter(self.lines)

        for processor in Document._processors:
            lines = processor(lines)

        self.lines = list(lines)

    def process(self):
        for _ in range(100):
            before = deepcopy(self.lines)
            self._process_step()

            if before == self.lines:
                break

    def __getitem__(self, i: int) -> Line:
        return self.lines[i]

    def get(self, i: int) -> Optional[Line]:
        if 0 <= i and i < len(self):
            return self[i]

        return None

    def add(self, line: Line | Node):
        self.lines.append(Line(line) if isinstance(line, Node) else line)

    def __str__(self) -> str:
        self.process()
        return "".join(str(li) for li in self.lines)

    def __len__(self) -> int:
        return len(self.lines)


class ToMarkdown:
    def to_md(self) -> Node:
        raise NotImplementedError
