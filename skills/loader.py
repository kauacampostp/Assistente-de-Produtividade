import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent


def get_skill_catalog():
    """Descobre as Skills disponíveis e retorna seus metadados."""

    catalog = []

    for skill_file in SKILLS_DIR.glob("*/SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")

        metadata = re.search(
            r"\A---\s*\n(.*?)\n---",
            content,
            re.DOTALL,
        )

        if not metadata:
            continue

        frontmatter = metadata.group(1)

        name = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
        description = re.search(
            r"^description:\s*(.+)$",
            frontmatter,
            re.MULTILINE,
        )

        if name and description:
            catalog.append(
                {
                    "name": name.group(1).strip(),
                    "description": description.group(1).strip(),
                    "path": skill_file,
                }
            )

    return catalog


def load_skill(skill_name: str):
    """Carrega o conteúdo de uma Skill pelo nome."""

    for skill in get_skill_catalog():
        if skill["name"] == skill_name:
            return skill["path"].read_text(encoding="utf-8")

    raise ValueError(f"Skill não encontrada: {skill_name}")
