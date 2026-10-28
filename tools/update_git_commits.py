from pathlib import Path
import json
import subprocess


# ============================================================
# CONFIGURATION
# ============================================================

# Project root directory
REPO_DIR = Path(r"D:\kids_game")

# Output Markdown file
OUTPUT_FILE = REPO_DIR / "docs" / "git_commits.md"

# Git log scope:
# "all"     = commits reachable from all local branches and tags
# "current" = commits reachable from the currently checked-out branch
GIT_SCOPE = "all"

# Maximum number of commits to include.
# Set to 0 to include all commits.
MAX_COMMITS = 0

# Time format used for displaying commit timestamps.
# Git stores timestamps as Unix timestamps, so this format uses
# the original timezone offset recorded by Git.
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"

# ============================================================
# AVAILABLE COLUMNS
# ============================================================
#
# Add or remove column names from SELECTED_COLUMNS.
# Column order in this list determines the Markdown table order.
#
# Available columns:
#
# commit_number
# commit_hash
# short_hash
# tree_hash
# parent_hashes
# parent_count
# commit_date
# commit_time
# commit_datetime
# commit_timestamp
# commit_timezone_offset
# author_name
# author_email
# author_date
# author_timestamp
# author_timezone_offset
# committer_name
# committer_email
# committer_date
# committer_timestamp
# committer_timezone_offset
# subject
# full_message
# body
# decorations
# refs
# branches
# tags
# files_changed
# insertions
# deletions
# binary_files_changed
# changed_files
# signature_status
#
# Notes:
# - Some fields may be empty if Git has no corresponding data.
# - File statistics are calculated from each commit's diff against
#   its first parent. Root commits are compared against an empty tree.
# - Branches and tags are local references available in this clone.
# - Commit hashes are immutable identifiers; branch names are not.
# ============================================================

SELECTED_COLUMNS = [
    "commit_number",
    "commit_hash",
    "short_hash",
    "commit_datetime",
    "author_name",
    "author_email",
    "committer_name",
    "committer_email",
    "subject",
    "full_message",
    "parent_hashes",
    "tree_hash",
    "branches",
    "tags",
    "files_changed",
    "insertions",
    "deletions",
    "changed_files",
    "signature_status",
]


# Human-readable names displayed in the Markdown table.
COLUMN_HEADERS = {
    "commit_number": "No.",
    "commit_hash": "Full Commit Hash",
    "short_hash": "Short Hash",
    "tree_hash": "Tree Hash",
    "parent_hashes": "Parent Commit Hashes",
    "parent_count": "Parent Count",
    "commit_date": "Commit Date",
    "commit_time": "Commit Time",
    "commit_datetime": "Commit Date & Time",
    "commit_timestamp": "Commit Unix Timestamp",
    "commit_timezone_offset": "Commit Timezone Offset",
    "author_name": "Author Name",
    "author_email": "Author Email",
    "author_date": "Author Date & Time",
    "author_timestamp": "Author Unix Timestamp",
    "author_timezone_offset": "Author Timezone Offset",
    "committer_name": "Committer Name",
    "committer_email": "Committer Email",
    "committer_date": "Committer Date & Time",
    "committer_timestamp": "Committer Unix Timestamp",
    "committer_timezone_offset": "Committer Timezone Offset",
    "subject": "Commit Subject",
    "full_message": "Full Commit Message",
    "body": "Commit Message Body",
    "decorations": "Git Decorations",
    "refs": "References",
    "branches": "Local Branches",
    "tags": "Local Tags",
    "files_changed": "Files Changed",
    "insertions": "Lines Added",
    "deletions": "Lines Deleted",
    "binary_files_changed": "Binary Files Changed",
    "changed_files": "Changed File Paths",
    "signature_status": "Signature Status",
}


# ============================================================
# GIT HELPERS
# ============================================================

def run_git(*args, check=True):
    """Run a Git command inside the configured repository."""

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Git command failed:\n"
            f"git {' '.join(args)}\n"
            f"{result.stderr.strip()}"
        )

    return result


def validate_repository():
    """Ensure the configured directory is a Git working tree."""

    if not REPO_DIR.exists():
        raise FileNotFoundError(f"Repository directory not found: {REPO_DIR}")

    result = run_git("rev-parse", "--show-toplevel")

    actual_root = Path(result.stdout.strip()).resolve()

    if actual_root != REPO_DIR.resolve():
        raise RuntimeError(
            f"Configured directory is not the repository root.\n"
            f"Configured: {REPO_DIR}\n"
            f"Detected:   {actual_root}"
        )


def get_git_history():
    """Retrieve commit metadata using a NUL-delimited Git log format."""

    git_args = [
        "log",
        "--date=raw",
        "--format=%x1e%H%x00%h%x00%T%x00%P%x00%an%x00%ae%x00%aI%x00%at%x00%ai%x00%cn%x00%ce%x00%cI%x00%ct%x00%ci%x00%s%x00%b%x00%D%x00%G?%x00",
        "--numstat",
        "--no-renames",
    ]

    if GIT_SCOPE == "all":
        git_args.append("--all")
    elif GIT_SCOPE != "current":
        raise ValueError("GIT_SCOPE must be 'all' or 'current'.")

    if MAX_COMMITS > 0:
        git_args.append(f"--max-count={MAX_COMMITS}")

    result = run_git(*git_args)

    return result.stdout


def parse_history(raw_history):
    """Parse Git's structured commit output and per-commit numstat."""

    commits = []

    # Each record begins with ASCII record separator (0x1e).
    records = raw_history.split("\x1e")

    for record in records:
        if not record.strip():
            continue

        metadata, separator, stats_text = record.partition("\n")

        fields = metadata.split("\x00")

        if len(fields) < 18:
            continue

        (
            commit_hash,
            short_hash,
            tree_hash,
            parent_hashes,
            author_name,
            author_email,
            author_iso_date,
            author_timestamp,
            author_raw_date,
            committer_name,
            committer_email,
            committer_iso_date,
            committer_timestamp,
            committer_raw_date,
            subject,
            body,
            decorations,
            signature_status,
        ) = fields[:18]

        stats = parse_numstat(stats_text if separator else "")

        commit_datetime, commit_timezone_offset = split_iso_datetime(
            committer_iso_date
        )

        committer_datetime = commit_datetime

        author_datetime, author_timezone_offset = split_iso_datetime(
            author_iso_date
        )


        refs = split_decorations(decorations)

        branches = [
            ref.removeprefix("HEAD -> ")
            for ref in refs
            if ref.startswith("HEAD -> ")
            or (
                not ref.startswith("tag: ")
                and not ref.startswith("HEAD")
                and "/" not in ref
            )
        ]

        tags = [
            ref[5:]
            for ref in refs
            if ref.startswith("tag: ")
        ]

        commits.append({
            "commit_number": len(commits) + 1,
            "commit_hash": commit_hash,
            "short_hash": short_hash,
            "tree_hash": tree_hash,
            "parent_hashes": parent_hashes,
            "parent_count": len(parent_hashes.split()) if parent_hashes else 0,
            "commit_date": commit_datetime.split(" ")[0],
            "commit_time": (
                commit_datetime.split(" ")[1]
                if " " in commit_datetime
                else ""
            ),
            "commit_datetime": commit_datetime,
            "commit_timestamp": committer_timestamp,
            "commit_timezone_offset": commit_timezone_offset,
            "author_name": author_name,
            "author_email": author_email,
            "author_date": author_datetime,
            "author_timestamp": author_timestamp,
            "author_timezone_offset": author_timezone_offset,
            "committer_name": committer_name,
            "committer_email": committer_email,
            "committer_date": committer_datetime,
            "committer_timestamp": committer_timestamp,
            "committer_timezone_offset": commit_timezone_offset,
            "subject": subject,
            "full_message": build_full_message(subject, body),
            "body": body,
            "decorations": decorations,
            "refs": refs,
            "branches": branches,
            "tags": tags,
            "files_changed": stats["files_changed"],
            "insertions": stats["insertions"],
            "deletions": stats["deletions"],
            "binary_files_changed": stats["binary_files_changed"],
            "changed_files": stats["changed_files"],
            "signature_status": signature_status,
        })

    return commits


def parse_numstat(stats_text):
    """Parse per-file additions and deletions from Git numstat output."""

    result = {
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
        "binary_files_changed": 0,
        "changed_files": [],
    }

    for line in stats_text.splitlines():
        parts = line.split("\t", 2)

        if len(parts) != 3:
            continue

        additions, deletions, filename = parts

        result["files_changed"] += 1
        result["changed_files"].append(filename)

        if additions == "-" or deletions == "-":
            result["binary_files_changed"] += 1
        else:
            result["insertions"] += int(additions)
            result["deletions"] += int(deletions)

    return result


def split_iso_datetime(value):
    """Separate an ISO timestamp into a readable datetime and UTC offset."""

    if not value:
        return "", ""

    if len(value) >= 6 and value[-6] in ("+", "-"):
        return value[:-6].replace("T", " "), value[-6:]

    return value.replace("T", " "), ""


def split_decorations(value):
    """Parse Git's ref decorations."""

    if not value:
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


def build_full_message(subject, body):
    """Reconstruct the commit message for display."""

    if body:
        return f"{subject}\n\n{body}"

    return subject


# ============================================================
# MARKDOWN GENERATION
# ============================================================

def markdown_escape(value):
    """Escape characters that could break a Markdown table."""

    if value is None:
        return ""

    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)

    value = str(value)

    # Prevent newlines and pipes from breaking table cells.
    value = value.replace("\\", "\\\\")
    value = value.replace("|", "\\|")
    value = value.replace("\r\n", "<br>")
    value = value.replace("\n", "<br>")
    value = value.replace("\r", "<br>")

    return value


def generate_markdown(commits):
    """Build the complete Markdown document."""

    headers = [
        COLUMN_HEADERS.get(column, column)
        for column in SELECTED_COLUMNS
    ]

    lines = [
        "# Git Commit History",
        "",
        f"- **Repository:** `{REPO_DIR}`",
        f"- **Total commits included:** {len(commits)}",
        f"- **History scope:** `{GIT_SCOPE}`",
        "- **Generated automatically from local Git history.**",
        "",
        "> Run `python tools/update_git_commits.py` to regenerate this document.",
        "",
    ]

    if not commits:
        lines.extend([
            "No commits were found in the selected Git history.",
            "",
        ])
        return "\n".join(lines)

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for commit in commits:
        row = [
            markdown_escape(commit.get(column, ""))
            for column in SELECTED_COLUMNS
        ]

        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():
    validate_repository()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    raw_history = get_git_history()
    commits = parse_history(raw_history)

    markdown = generate_markdown(commits)

    OUTPUT_FILE.write_text(
        markdown,
        encoding="utf-8",
        newline="\n",
    )

    print("=" * 60)
    print("Git commit history generated successfully.")
    print(f"Repository : {REPO_DIR}")
    print(f"Output     : {OUTPUT_FILE}")
    print(f"Commits    : {len(commits)}")
    print(f"Columns    : {len(SELECTED_COLUMNS)}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise