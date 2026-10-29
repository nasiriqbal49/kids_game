import sys
import re
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def extract_module(module_num: int):
    plan_file = REPO_DIR / "docs" / "full_game_plan.md"
    cat_file = REPO_DIR / "docs" / "use_case_catalogue.md"

    plan_text = plan_file.read_text(encoding="utf-8")
    cat_text = cat_file.read_text(encoding="utf-8")

    # 1. Extract from full_game_plan.md
    plan_match = re.search(rf"(###\s*{module_num}\..*?)(?=###\s*\d+\.|\Z)", plan_text, re.DOTALL)
    plan_section = plan_match.group(1).strip() if plan_match else f"Module {module_num} section not found in plan."

    # 2. Extract from use_case_catalogue.md
    mod_str = f"{module_num:02d}" if module_num < 10 else str(module_num)
    cat_match = re.search(rf"(##\s*6\.{module_num}\s*Module\s*{module_num}.*?)(?=##\s*6\.|\Z)", cat_text, re.DOTALL | re.IGNORECASE)
    cat_section = cat_match.group(1).strip() if cat_match else f"Module {module_num} use cases not found in catalogue."

    output = f"# Module {module_num} Specification\n\n## Game Plan Section\n{plan_section}\n\n## Use Case Catalogue\n{cat_section}\n"

    out_file = REPO_DIR / f"module_{module_num}_spec.md"
    out_file.write_text(output, encoding="utf-8")
    print(f"Generated {out_file.name} ({len(output):,} chars, ~{len(output)//4:,} tokens).")


if __name__ == "__main__":
    mod = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    extract_module(mod)