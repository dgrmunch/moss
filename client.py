#!/usr/bin/env python3
"""
MiniGem Client Navigator (fixed to your specs)
----------------------------------------------
- Enlaces con números inline en texto negrita+subrayado color cyan (igual que Path)
- Sin pausa tras introducir número (navega directo)
- Entrada host/port vía consola (sin argumentos CLI)
- Muestra datos de author.json si existe en el servidor
"""

import requests
import re
import os
import json
from urllib.parse import urljoin
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def request(host: str, port: int, path: str) -> tuple[str, str]:
    if port == 443:
        scheme = "https"
    else:
        scheme = "http"

    # Construye URL
    if path.startswith("/"):
        path = path[1:]

    url = f"{scheme}://{host}:{port}/{path}"

    try:
        resp = requests.get(url, timeout=10)
    except Exception as e:
        return "40 ERROR", f"Request failed: {e}"

    if resp.status_code != 200:
        return f"40 HTTP {resp.status_code}", resp.text

    return "20 OK", resp.text



def extract_links(md_text: str) -> list[tuple[str, str]]:
    pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
    return re.findall(pattern, md_text)


def normalize_path(current_path: str, link_path: str) -> str:
    if link_path.startswith("/"):
        return link_path.lstrip("/")
    base_dir = os.path.dirname(current_path)
    return os.path.normpath(os.path.join(base_dir, link_path))


def insert_inline_numbers_and_style(md_text: str):
    import re
    pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
    matches = re.findall(pattern, md_text)

    numbered = md_text
    links = []

    MAGENTA = "\033[35m"

    for i, (text, link) in enumerate(matches, start=1):
        links.append((text, link))
        decorated = f"**{MAGENTA}{text} ({i}){MAGENTA}**"
        original = f"[{text}]({link})"
        numbered = numbered.replace(original, decorated, 1)

    return numbered, links



def main():
    console.print("[bold green]MiniGem Navigator[/bold green]")

    host = console.input("Server hostname/IP (default localhost): ").strip() or "localhost"
    port_str = console.input("Server port (default 80): ").strip()
    port = int(port_str) if port_str.isdigit() else 80

    history = []
    current_path = "index.md"

    author_info = None

    # Intenta cargar author.json
    try:
        _, author_body = request(host, port, "author.json")
        author_info = json.loads(author_body)
    except Exception:
        author_info = None


    while True:
        console.clear()

        if author_info:
            author_str = f"[bold cyan]Author:[/bold cyan] [magenta]{author_info.get('name', 'Unknown')}[/magenta]"
            if "email" in author_info:
                author_str += f"\n[bold cyan]Contact:[/bold cyan] [magenta]{author_info['email']}[/magenta]"
            console.print(author_str)

        console.print(f"[bold cyan]Node:[/bold cyan][magenta]{host}:{port}[/magenta]")
        console.print(f"[bold cyan]Document:[/bold cyan] [magenta]{current_path}[/magenta]")

        header, body = request(host, port, current_path)

        if header.lower().startswith("error") or header.startswith("40"):
            console.print(f"[bold red]Error loading {current_path}: {header}[/bold red]")
        else:
            rendered_body, links = insert_inline_numbers_and_style(body)

            rendered_body = rendered_body.replace("# ", "## ")
            console.print(Markdown(rendered_body))

            console.print("\n (b) Back | (q) Quit")
            cmd = console.input(">> ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "b":
                if history:
                    host, port, current_path = history.pop()
                else:
                    console.print("[italic]No history.[/italic]")
            elif cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(links):
                    history.append((host, port, current_path))
                    _, link = links[idx]

                    moss_match = re.match(r"moss://([^:/]+):(\d+)(/.+)", link)
                    if moss_match:
                        host = moss_match.group(1)
                        port = int(moss_match.group(2))
                        current_path = moss_match.group(3).lstrip("/")
                    else:
                        current_path = normalize_path(current_path, link)
                else:
                    console.print("[red]Invalid link number[/red]")
            else:
                console.print("[red]Unknown command[/red]")



if __name__ == "__main__":
    main()
