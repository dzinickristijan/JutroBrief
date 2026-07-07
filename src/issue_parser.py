"""Parse and manipulate newsletter issue markdown (stories, B-lista, swap)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


EDITOR_SECTION_KEYS = ("subject", "b-lista", "b lista")
SKIP_SECTION_KEYS = EDITOR_SECTION_KEYS


@dataclass
class Story:
    section: str
    title: str
    body: str
    index: int = 0

    @property
    def markdown(self) -> str:
        return f"**{self.title}**\n{self.body.strip()}\n"


@dataclass
class BListItem:
    title: str
    url: str
    index: int = 0

    @property
    def markdown(self) -> str:
        return f"* {self.title} — [Izvor]({self.url})"

    def to_story(self, section: str = "🌍 SVIJET") -> Story:
        body = (
            "Sažetak treba dopuniti nakon zamjene s B-liste. "
            f"[Izvor]({self.url})"
        )
        return Story(section=section, title=self.title, body=body)


@dataclass
class IssueDocument:
    preamble: str = ""
    stories: list[Story] = field(default_factory=list)
    closing: str = ""
    b_list: list[BListItem] = field(default_factory=list)


def _is_editor_section(heading: str) -> bool:
    h = heading.strip().lower()
    return any(key in h for key in SKIP_SECTION_KEYS)


def _parse_b_line(line: str) -> BListItem | None:
    m = re.match(r"^\*\s+(.+?)\s+—\s+\[Izvor\]\(([^)]+)\)\s*$", line.strip())
    if not m:
        return None
    return BListItem(title=m.group(1).strip(), url=m.group(2).strip())


def _extract_source_url(body: str) -> str | None:
    m = re.search(r"\[Izvor\]\(([^)]+)\)", body)
    return m.group(1) if m else None


def parse_issue(text: str) -> IssueDocument:
    """Split issue markdown into preamble, stories, closing note and B-lista."""
    lines = text.splitlines()
    doc = IssueDocument()
    section = ""
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            heading = line[3:].strip()
            if _is_editor_section(heading):
                if "b-lista" in heading.lower() or "b lista" in heading.lower():
                    i += 1
                    while i < len(lines):
                        item = _parse_b_line(lines[i])
                        if item:
                            item.index = len(doc.b_list) + 1
                            doc.b_list.append(item)
                        i += 1
                    break
                i += 1
                continue
            section = heading
            i += 1
            continue

        if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            title = line.strip("*").strip()
            i += 1
            body_lines: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith("## ") or (
                    nxt.startswith("**") and nxt.endswith("**") and nxt.count("**") == 2
                ):
                    break
                body_lines.append(nxt)
                i += 1
            story = Story(section=section, title=title, body="\n".join(body_lines).strip())
            story.index = len(doc.stories) + 1
            doc.stories.append(story)
            continue

        if not doc.stories and not doc.b_list:
            doc.preamble += line + "\n"
        elif doc.stories and not doc.b_list:
            if line.strip().startswith("To je to za jutros"):
                doc.closing = line.strip()
                i += 1
                while i < len(lines) and not lines[i].startswith("## "):
                    if lines[i].strip():
                        doc.closing += "\n" + lines[i].strip()
                    i += 1
                continue
        i += 1

    doc.preamble = doc.preamble.strip()
    return doc


def serialize_issue(doc: IssueDocument) -> str:
    """Rebuild markdown from parsed structure."""
    parts: list[str] = []
    if doc.preamble:
        parts.append(doc.preamble)

    current_section = None
    for story in doc.stories:
        if story.section != current_section:
            current_section = story.section
            parts.append(f"\n## {current_section}\n")
        parts.append(story.markdown)

    if doc.closing:
        parts.append("\n" + doc.closing)

    if doc.b_list:
        parts.append("\n## B-LISTA\n")
        for item in doc.b_list:
            parts.append(item.markdown)

    return "\n".join(parts).strip() + "\n"


def swap_story(doc: IssueDocument, out_index: int, in_b_index: int) -> IssueDocument:
    """Replace story `out_index` with B-list item `in_b_index` (1-based)."""
    if out_index < 1 or out_index > len(doc.stories):
        raise ValueError(f"Priča #{out_index} ne postoji (ima {len(doc.stories)} priča).")
    if in_b_index < 1 or in_b_index > len(doc.b_list):
        raise ValueError(f"B-lista stavka #{in_b_index} ne postoji (ima {len(doc.b_list)}).")

    out_story = doc.stories[out_index - 1]
    in_item = doc.b_list[in_b_index - 1]

    url = _extract_source_url(out_story.body) or ""
    doc.b_list[in_b_index - 1] = BListItem(
        title=out_story.title,
        url=url,
        index=in_b_index,
    )

    replacement = in_item.to_story(section=out_story.section)
    doc.stories[out_index - 1] = replacement
    doc.stories[out_index - 1].index = out_index
    return doc


def list_stories(doc: IssueDocument) -> str:
    lines = ["Priče u izdanju:"]
    for s in doc.stories:
        lines.append(f"  {s.index:2}. [{s.section}] {s.title}")
    lines.append("\nB-lista:")
    for b in doc.b_list:
        lines.append(f"  {b.index:2}. {b.title}")
    return "\n".join(lines)
