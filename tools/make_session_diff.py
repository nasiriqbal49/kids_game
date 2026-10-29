import sys
import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def run_cmd(cmd):
    result = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip()


def main():
    # 1. Get recent tags
    tags = run_cmd(["git", "tag", "--sort=-creatordate"]).splitlines()

    base_tag = sys.argv[1] if len(sys.argv) > 1 else (tags[0] if tags else None)

    print(f"Generating session diff against tag: {base_tag}")

    change_file = REPO_DIR / "docs" / "change.md"
    change_text = change_file.read_text(encoding="utf-8") if change_file.exists() else ""

    # 2. Extract recent entries from change.md
    recent_changes = "\n".join(change_text.splitlines()[:60])

    # 3. Generate git diff excluding large commit logs
    diff_text = ""
    if base_tag:
        diff_text = run_cmd([
            "git", "diff", f"{base_tag}..HEAD",
            "--", ".",
            ":(exclude)docs/git_commits.md",
            ":(exclude)docs/project_directory_structure.md"
        ])

    output = f"=== RECENT SESSION LOGS (docs/change.md) ===\n{recent_changes}\n\n=== CODE & DOCS DIFF SINCE {base_tag} ===\n{diff_text}\n"

    out_file = REPO_DIR / "session_diff.txt"
    out_file.write_text(output, encoding="utf-8")

    char_count = len(output)
    est_tokens = char_count // 4
    print(f"Success! Output written to {out_file.name}")
    print(f"Size: {char_count:,} characters (~{est_tokens:,} tokens). Compare that to 95,000 tokens!")


if __name__ == "__main__":
    main()