import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_DIR = Path(__file__).resolve().parent.parent
OUTPUT_GRAPH_FILE = REPO_DIR / "docs" / "project_graph.md"

TARGET_FOLDERS = ["core", "engine", "vision", "tools"]
IGNORE_DIRS = {".venv", "__pycache__", "dist", "build", ".git"}


def sanitize_id(name: str) -> str:
    """Converts file paths into clean, safe Mermaid IDs without markdown formatting conflicts."""
    return name.replace("/", "_").replace(".", "_").replace("-", "_").replace("__", "")


class CodeGraphScanner:
    """
    Parses Python AST into clean Mermaid flowchart nodes.
    Excludes __init__ to prevent markdown bold-tag collisions.
    """

    def __init__(self):
        self.nodes: Set[Tuple[str, str]] = set()
        self.edges: List[str] = []

    def scan_directory(self) -> None:
        for folder in TARGET_FOLDERS:
            folder_path = REPO_DIR / folder
            if not folder_path.exists():
                continue

            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(REPO_DIR)
                        self._parse_file(full_path, str(rel_path).replace("\\", "/"))

    def _parse_file(self, file_path: Path, mod_name: str) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return

        clean_mod = mod_name.replace(".py", "")
        source_id = sanitize_id(clean_mod)
        self.nodes.add((source_id, clean_mod))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    if pkg in TARGET_FOLDERS:
                        target_mod = node.module.replace(".", "/")
                        if not target_mod.endswith("__init__"):
                            target_id = sanitize_id(target_mod)
                            self.edges.append(f"    {source_id} --> {target_id}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    if pkg in TARGET_FOLDERS:
                        target_mod = alias.name.replace(".", "/")
                        if not target_mod.endswith("__init__"):
                            target_id = sanitize_id(target_mod)
                            self.edges.append(f"    {source_id} --> {target_id}")

    def generate_markdown(self) -> str:
        lines = [
            "# Project Architecture & Dependency Knowledge Graph",
            "",
            "> **Generated automatically for Google Gemini and Graphify.**",
            "> Maps every connected module node with zero token waste.",
            "",
            "```mermaid",
            "flowchart LR"
        ]

        layers = {
            "Core_Layer": ("Core Architecture", "core/"),
            "Vision_Pipeline": ("Vision Pipeline", "vision/"),
            "Engine_Layer": ("Engine & Controller", "engine/"),
            "Tools_Layer": ("Tools & Launchers", "tools/")
        }

        # Filter valid node IDs
        known_ids = {n[0] for n in self.nodes}

        for sub_id, (sub_title, prefix) in layers.items():
            lines.append(f'    subgraph {sub_id} ["{sub_title}"]')
            for node_id, display_label in sorted(self.nodes):
                if display_label.startswith(prefix):
                    lines.append(f'        {node_id}["{display_label}"]')
            lines.append("    end")

        lines.append("")
        lines.append("    %% Data Flow Connections")
        # Only include edges where both nodes exist
        for edge in sorted(set(self.edges)):
            parts = edge.strip().split(" --> ")
            if len(parts) == 2 and parts[0] in known_ids and parts[1] in known_ids:
                lines.append(f"    {parts[0]} --> {parts[1]}")

        lines.extend([
            "```",
            "",
            "---",
            "Run `python tools/generate_graph.py` anytime code changes to refresh this graph!",
            ""
        ])

        return "\n".join(lines)


def main():
    scanner = CodeGraphScanner()
    scanner.scan_directory()
    graph_md = scanner.generate_markdown()

    OUTPUT_GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_GRAPH_FILE.write_text(graph_md, encoding="utf-8")

    print("==================================================")
    print(" GRAPHIFY SCAN COMPLETE!")
    print(f" Generated valid visual node map: {OUTPUT_GRAPH_FILE}")
    print("==================================================")


if __name__ == "__main__":
    main()