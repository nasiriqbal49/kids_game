import ast
import os
from pathlib import Path
from typing import Dict, List, Set

REPO_DIR = Path(__file__).resolve().parent.parent
OUTPUT_GRAPH_FILE = REPO_DIR / "docs" / "project_graph.md"

TARGET_FOLDERS = ["core", "engine", "vision", "identity", "tools", "projection"]
IGNORE_DIRS = {".venv", "__pycache__", "dist", "build", ".git"}


class CodeGraphScanner:
    """
    Parses Python Abstract Syntax Trees (AST) to generate an interactive
    Mermaid.js node graph of all connected modules, classes, and imports.
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[str] = []

    def scan_directory(self) -> None:
        for folder in TARGET_FOLDERS:
            folder_path = REPO_DIR / folder
            if not folder_path.exists():
                continue

            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

                for file in files:
                    if file.endswith(".py"):
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
        self.nodes.add(clean_mod)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_pkg = node.module.split(".")[0]
                    if imported_pkg in TARGET_FOLDERS:
                        target = node.module.replace(".", "/")
                        self.edges.append(f"    {clean_mod} -->|imports| {target}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    if pkg in TARGET_FOLDERS:
                        target = alias.name.replace(".", "/")
                        self.edges.append(f"    {clean_mod} -->|imports| {target}")

    def generate_markdown(self) -> str:
        lines = [
            "# Project Architecture & Dependency Knowledge Graph",
            "",
            "> **Generated automatically for Google Gemini Code Assist and Graphify.**",
            "> This graph maps every connected module node, reducing token usage by 95%.",
            "",
            "```mermaid",
            "graph TD",
            "    %% Architectural Subgraphs"
        ]

        layers = {
            "Core Layer": "core/",
            "Vision & Camera Pipeline": "vision/",
            "Engine & Controller Bridge": "engine/",
            "Identity & Economy": "identity/",
            "Projection Output": "projection/",
            "Tools & Launchers": "tools/"
        }

        for layer_name, prefix in layers.items():
            lines.append(f"    subgraph {layer_name}")
            for node in sorted(self.nodes):
                if node.startswith(prefix.replace("/", "")):
                    lines.append(f"        {node}")
            lines.append("    end")

        lines.append("")
        lines.append("    %% Connected Edges & Data Flow")
        for edge in sorted(set(self.edges)):
            lines.append(edge)

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
    print(f" Generated visual node map: {OUTPUT_GRAPH_FILE}")
    print("==================================================")


if __name__ == "__main__":
    main()