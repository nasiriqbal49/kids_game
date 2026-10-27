import os
import sys
import re
from pathlib import Path

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}
DOC_FILE = Path("docs/project_directory_structure.md")


def build_tree(dir_path: Path, prefix: str = "") -> list:
    lines = []
    try:
        entries = sorted(
            [e for e in dir_path.iterdir() if e.name not in IGNORE_DIRS],
            key=lambda s: (s.is_file(), s.name.lower())
        )
    except PermissionError:
        return lines

    total = len(entries)
    for i, entry in enumerate(entries):
        is_last = (i == total - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            sub_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree(entry, sub_prefix))
    return lines


def print_or_update(update_doc: bool = False):
    root = Path(".")
    tree_lines = [f"{root.resolve().name}/"] + build_tree(root)
    tree_text = "\n".join(tree_lines)

    print("\n--- Current Project Structure ---")
    print(tree_text)
    print("---------------------------------\n")

    if not update_doc:
        return

    DOC_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = DOC_FILE.read_text(encoding="utf-8") if DOC_FILE.exists() else ""

    # Strategy 1: Match any heading containing 'Current Active Tree' followed by a code block
    pattern_heading = r"(#+\s*.*Current Active Tree.*?\s*```[a-zA-Z]*\s*\r?\n)(.*?)(\r?\n```)"
    # Strategy 2: Match the first code block in the file
    pattern_first_block = r"(```[a-zA-Z]*\s*\r?\n)(.*?)(\r?\n```)"

    if re.search(pattern_heading, content, flags=re.IGNORECASE | re.DOTALL):
        new_content = re.sub(
            pattern_heading,
            lambda m: f"{m.group(1)}{tree_text}{m.group(3)}",
            content,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )
    elif re.search(pattern_first_block, content, flags=re.DOTALL):
        new_content = re.sub(
            pattern_first_block,
            lambda m: f"{m.group(1)}{tree_text}{m.group(3)}",
            content,
            count=1,
            flags=re.DOTALL
        )
    else:
        # Fallback: Regenerate the clean full markdown structure
        new_content = (
            f"# Project Directory Structure\n\n"
            f"**Last Updated:** Phase A (Automated)\n\n"
            f"---\n\n"
            f"## Current Active Tree\n\n"
            f"```text\n{tree_text}\n```\n\n"
            f"---\n\n"
            f"## Target Project Tree (Full Build Roadmap)\n\n"
            f"```text\n"
            f"kids_game/\n"
            f"├── core/                          # Architecture foundation (Phase A)\n"
            f"│   ├── logger.py                  # Module 1: Logging\n"
            f"│   ├── config.py                  # Module 1: Settings\n"
            f"│   ├── events.py                  # Module 2: Event catalogue & dataclass\n"
            f"│   ├── event_bus.py               # Module 2: Pub/Sub message broker\n"
            f"│   └── input_keyboard.py          # Module 3: Keyboard input adapter\n"
            f"├── engine/                        # Game Engine & Mechanics (Phase B)\n"
            f"│   ├── display.py                 # Module 4: Pygame second-screen display & HUD\n"
            f"│   ├── audio.py                   # Module 5: Sound & music manager\n"
            f"│   ├── game_engine.py             # Module 6: State machine & fixed timestep loop\n"
            f"│   ├── mechanics/                 # Module 7: Reusable gameplay blocks\n"
            f"│   └── games/                     # Module 8 & 18: Runner, Lane Switch, Freeze Dance\n"
            f"├── vision/                        # Computer Vision & Tracking (Phase C & E)\n"
            f"├── identity/                      # Player Profiles & Calibration (Phase D)\n"
            f"├── projection/                    # Projector Output (Phase E)\n"
            f"├── assets/                        # Art, sounds and fonts\n"
            f"├── docs/                          # Comprehensive documentation & logs\n"
            f"├── tests/                         # Module unit tests\n"
            f"└── main.py                        # Game startup script\n"
            f"```\n"
        )

    DOC_FILE.write_text(new_content, encoding="utf-8")
    print(f"Successfully updated tree in {DOC_FILE}!")


if __name__ == "__main__":
    should_update = "--update" in sys.argv
    print_or_update(update_doc=should_update)