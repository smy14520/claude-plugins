from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LEGACY_SLICE_CHECKBOX_RE = re.compile(r"^- \[[ x\-]\] S-\d{3}", re.MULTILINE)
SLICE_SECTION_RE = re.compile(r"^## Slices\b.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
SLICE_BLOCK_RE = re.compile(
    r"^### (S-\d{3}):\s*(.*?)\s*$\n?(.*?)(?=^### S-\d{3}:|^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
SLICE_ID_RE = re.compile(r"\bS-\d{3}\b")
MARKER_ID_RE = re.compile(r"\bS-\d{3}(?:\.\d+)?\b")
SLICE_SCAFFOLD_TOKENS = (
    "<walking skeleton 或第一个独立可验证的契约/功能>",
    "<walking skeleton 或第一个独立可验证的行为>",
    "<扩展某个契约/功能/行为/状态转换>",
    "<下一个独立可验证的行为>",
    "<回归 / 边界 / 自检切片>",
    "<完成后多了什么可独立验证的契约/功能/行为>",
    "Impl 只更新 [ ] / [-] / [x]",
)

_FIELD_ALIASES = {
    "完成标志": ("完成标志",),
    "代码锚点": ("代码锚点",),
    "数据/schema": ("数据/schema", "数据", "schema", "Schema"),
    "测试": ("测试",),
}


@dataclass(frozen=True)
class PrdSlice:
    id: str
    title: str
    body: str
    completion_markers: tuple[str, ...]
    code_anchors: str
    data_schema: str
    tests: str

    @property
    def completion_marker(self) -> str:
        """Back-compat: return joined markers as a single string."""
        return "; ".join(self.completion_markers)

    def marker_ids(self) -> list[str]:
        """Return deterministic marker ids.

        - 1 marker  → ['S-NNN']        (back-compat)
        - N markers → ['S-NNN.1', 'S-NNN.2', ...]
        """
        if len(self.completion_markers) <= 1:
            return [self.id]
        return [f"{self.id}.{i}" for i in range(1, len(self.completion_markers) + 1)]


def parse_prd_slices(prd_text: str) -> tuple[list[PrdSlice], list[str]]:
    errors: list[str] = []
    section_match = SLICE_SECTION_RE.search(prd_text)
    if not section_match:
        return [], ["missing `## Slices` section"]

    section = section_match.group(0)
    blocks = list(SLICE_BLOCK_RE.finditer(section))
    if not blocks:
        errors.append("`## Slices` must contain at least one `### S-NNN:` slice header")
        return [], errors

    slices: list[PrdSlice] = []
    seen: set[str] = set()
    for match in blocks:
        slice_id = match.group(1)
        title = match.group(2).strip()
        body = match.group(3).strip()
        if slice_id in seen:
            errors.append(f"duplicate slice id: {slice_id}")
        seen.add(slice_id)
        markers = _completion_markers(body)
        if not markers:
            errors.append(f"slice {slice_id} missing non-empty `完成标志` marker")
        slices.append(
            PrdSlice(
                id=slice_id,
                title=title,
                body=body,
                completion_markers=tuple(markers),
                code_anchors=_field_value(body, _FIELD_ALIASES["代码锚点"]),
                data_schema=_field_value(body, _FIELD_ALIASES["数据/schema"]),
                tests=_field_value(body, _FIELD_ALIASES["测试"]),
            )
        )
    return slices, errors


def validate_prd_slice_structure(prd_text: str, strict_scaffold: bool = False) -> list[str]:
    slices, errors = parse_prd_slices(prd_text)
    if LEGACY_SLICE_CHECKBOX_RE.search(prd_text):
        errors.append("PRD uses legacy `- [ ] S-NNN` checkbox format; migrate to `### S-NNN:` structured slices")
    if strict_scaffold:
        scaffold_hits = [token for token in SLICE_SCAFFOLD_TOKENS if token in prd_text]
        if scaffold_hits:
            errors.append("PRD contains unfilled slice scaffold tokens: " + ", ".join(scaffold_hits))
    if slices:
        ids = [item.id for item in slices]
        duplicates = sorted({slice_id for slice_id in ids if ids.count(slice_id) > 1})
        for slice_id in duplicates:
            duplicate_error = f"duplicate slice id: {slice_id}"
            if duplicate_error not in errors:
                errors.append(duplicate_error)
    return errors


def collect_slice_ids_from_text(text: str) -> set[str]:
    return set(SLICE_ID_RE.findall(text))


def collect_marker_ids_from_text(text: str) -> set[str]:
    """Extract both slice ids (S-NNN) and marker ids (S-NNN.M) mentioned in text."""
    return set(MARKER_ID_RE.findall(text))


def _completion_markers(body: str) -> list[str]:
    """Parse the `- 完成标志：` field as either inline text or a sublist.

    Inline:  `- 完成标志：阻止重复报名`            → ['阻止重复报名']
    Sublist: `- 完成标志：\n  - 代报名\n  - 取消`  → ['代报名', '取消']
    Mixed:   `- 完成标志：总述\n  - 细节 A\n  - 细节 B`
             → if head has content, treat as one + sublist items, keeping all
    """
    label_pattern = "|".join(re.escape(label) for label in _FIELD_ALIASES["完成标志"])
    match = re.search(
        rf"^\s*-\s*(?:\*\*)?(?:{label_pattern})(?:\*\*)?\s*[：:][ \t]*(.*?)(?=^\s*-\s*(?:\*\*)?(?!\s)[^\n：:]+(?:\*\*)?\s*[：:]|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []

    block = match.group(1)
    lines = block.splitlines()
    if not lines:
        return []

    head = lines[0].strip()
    sub_items: list[str] = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # sub-bullet: must start with '-' or '*' and be indented
        if re.match(r"^(-|\*)\s+", stripped) and re.match(r"^\s+", line):
            sub_items.append(re.sub(r"^(-|\*)\s+", "", stripped))
        else:
            # non-bullet continuation line; append to previous or head
            if sub_items:
                sub_items[-1] = f"{sub_items[-1]} {stripped}"
            elif head:
                head = f"{head} {stripped}"

    if sub_items:
        # If head is empty (pure sublist), markers = sub_items
        # If head is non-empty, prepend it (mixed: head is an overall claim +细节)
        return [head, *sub_items] if head else sub_items
    if head:
        return [head]
    return []


def _field_value(body: str, labels: tuple[str, ...]) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"^\s*-\s*(?:\*\*)?(?:{label_pattern})(?:\*\*)?\s*[：:]\s*(.*?)(?=^\s*-\s*(?:\*\*)?[^\n：:]+(?:\*\*)?\s*[：:]|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


_TASK_ACCEPTANCE_RE = re.compile(r"^## Acceptance\b", re.MULTILINE)
_TASK_VERIFICATION_RE = re.compile(r"^## Verification\b", re.MULTILINE)
_VERIFICATION_HEADING_RE = re.compile(r"^##+\s+Verification\s*$", re.IGNORECASE)
_HEADING_LINE_RE = re.compile(r"^##+\s+")
_VERIFICATION_TAG_RE = re.compile(r"^\[([a-z]+)\]\s+(.+)$", re.DOTALL)

# Check kind is declared by brainstorm in the slice task file, never inferred
# by the CLI: kind decides whether the gate demands run-check evidence, which
# is a policy decision, not a parsing heuristic.
VERIFICATION_KINDS = {"build", "test", "typecheck", "lint", "docker", "api", "browser", "manual"}


def parse_verification_items(text: str) -> list[tuple[str | None, str]]:
    """Parse `## Verification` bullets into (kind, description) pairs.

    Expected item format: `- [test] python -m pytest tests/`. Items without a
    `[kind]` tag come back with kind=None; callers decide whether that is an
    error (finalize and derive both reject untagged items).
    """
    items: list[tuple[str | None, str]] = []
    in_verification = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if _HEADING_LINE_RE.match(line):
            if in_verification:
                break
            in_verification = bool(_VERIFICATION_HEADING_RE.match(line))
            continue
        if not in_verification or not line.startswith("- "):
            continue
        item = line[2:].strip()
        if not item:
            continue
        tag_match = _VERIFICATION_TAG_RE.match(item)
        if tag_match and tag_match.group(1) in VERIFICATION_KINDS:
            items.append((tag_match.group(1), tag_match.group(2).strip()))
        else:
            items.append((None, item))
    return items


def validate_slice_tasks(root: Path, package_name: str, slice_ids: list[str]) -> list[str]:
    """Validate that each slice has a corresponding task file with required sections.

    Returns errors if slice task files are missing, lack required sections, or
    contain Verification items without an explicit `[kind]` tag. When the PRD
    defines slices but the slices/ directory does not exist, returns an error
    requiring brainstorm to create the task files first.
    """
    from .fs import package_dir

    errors: list[str] = []
    pkg_dir = package_dir(root, package_name)
    slices_dir = pkg_dir / "slices"

    if not slices_dir.exists():
        if slice_ids:
            errors.append(f"slices/ directory does not exist but PRD defines {len(slice_ids)} slices; create slice task files before finalize")
        return errors

    kinds = "/".join(sorted(VERIFICATION_KINDS))
    for slice_id in slice_ids:
        task_file = slices_dir / f"{slice_id}.md"
        if not task_file.exists():
            errors.append(f"slice {slice_id} missing task file at slices/{slice_id}.md")
            continue
        content = task_file.read_text(encoding="utf-8")
        if not _TASK_ACCEPTANCE_RE.search(content):
            errors.append(f"slices/{slice_id}.md missing ## Acceptance section")
        if not _TASK_VERIFICATION_RE.search(content):
            errors.append(f"slices/{slice_id}.md missing ## Verification section")
            continue
        verification_items = parse_verification_items(content)
        if not verification_items:
            errors.append(f"slices/{slice_id}.md Verification must contain at least one `- [kind] ...` bullet")
            continue
        for kind, description in verification_items:
            if kind is None:
                errors.append(
                    f"slices/{slice_id}.md Verification 项缺少 [kind] 标签: \"{description}\"；"
                    f"写成 `- [test] ...` 形式，合法 kind: {kinds}"
                )

    return errors
