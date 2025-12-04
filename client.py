#!/usr/bin/env python3
"""
MOSS Browser CLI — Client
-------------------------
- Renderizado Markdown con Rich
- Paginación (lynx-style)
- Cabecera fija en la parte superior
- Ancho fijo estilo gopher
- Margen lateral
- Enlaces numerados como en tu versión original
- Conexión automática a localhost:1987
"""

import requests
import re
import os
import json
from urllib.parse import urljoin
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()

# ================================
# CONFIG
# ================================
WIDTH = 78          # ancho estilo gopher
LEFT_MARGIN = 4     # margen izquierdo
PAGE_LINES = console.size.height - 10   # resto para cabecera + footer

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1987
DEFAULT_PATH = "index.md"


# ================================
# UTILS
# ================================
def request(path: str):
    """Hace GET a http://localhost:1987/path"""
    url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return "20 OK", resp.text
        return f"40 HTTP {resp.status_code}", resp.text
    except Exception as e:
        return "40 ERROR", str(e)


def extract_links(md_text: str):
    """Extrae enlaces markdown [texto](archivo.md)"""
    pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
    return re.findall(pattern, md_text)


def normalize_path(current_path: str, link_path: str):
    if link_path.startswith("/"):
        return link_path.lstrip("/")
    base = os.path.dirname(current_path)
    return os.path.normpath(os.path.join(base, link_path))


def insert_inline_numbers_and_style(md_text: str):
    """Reemplaza enlaces por texto coloreado y numerado. Mantiene tu estilo exacto."""
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


# =========================================
# PAGINACIÓN CON MARKDOWN CORRECTO
# =========================================
def paginate_markdown(md_text):
    """
    Renderiza Markdown → líneas visibles, sin usar width en render_lines().
    Compatible con versiones antiguas de Rich.
    """
    md = Markdown(md_text)

    # Renderizamos a un buffer temporal para capturar el output procesado
    from rich.console import Console
    from io import StringIO

    temp_console = Console(width=WIDTH, file=StringIO(), force_terminal=True)
    temp_console.print(md)
    rendered = temp_console.file.getvalue()

    # Convertimos a lista de líneas reales (sin saltos extra)
    return rendered.splitlines()

# =========================================
# PINTAR UNA PÁGINA COMPLETA
# =========================================
def draw_screen(author_info, current_path, page_lines, page_index, total_pages):
    console.clear()

    # -------- CABECERA FIJA --------
    header = Text()
    if author_info:
        header.append(f"Author: {author_info.get('name','Unknown')}\n", style="bold cyan")
        if "email" in author_info:
            header.append(f"Contact: {author_info['email']}\n", style="cyan")

    header.append(f"Node: {DEFAULT_HOST}:{DEFAULT_PORT}\n", style="bold cyan")
    header.append(f"Document: {current_path}\n", style="bold cyan")

    console.print(header)
    console.print("-" * WIDTH)

    # -------- CONTENIDO (PAGINADO) --------
    for line in page_lines:
        console.print(" " * LEFT_MARGIN + line)

    console.print("-" * WIDTH)

    # -------- FOOTER --------
    console.print(
        f"[bold green](b) Back  |  (q) Quit  |  Page {page_index + 1}/{total_pages} | (n) Next page | (p) Prev page[/bold green]"
    )


# =========================================
# MAIN
# =========================================
def main():
    current_path = DEFAULT_PATH
    history = []

    # Carga author.json si existe
    try:
        _, author_body = request("author.json")
        author_info = json.loads(author_body)
    except Exception:
        author_info = None

    while True:
        header, body = request(current_path)

        if not header.startswith("20"):
            console.print(f"[bold red]Error loading {current_path}: {header}[/bold red]")
            cmd = console.input(">> ")
            if cmd == "q":
                break
            continue

        # Formateo de enlaces (estilo previo)
        rendered_body, links = insert_inline_numbers_and_style(body)

        # Poner títulos más pequeños
        rendered_body = rendered_body.replace("# ", "## ")

        # Paginado real con markdown
        md_lines = paginate_markdown(rendered_body)
        total_pages = max(1, (len(md_lines) + PAGE_LINES - 1) // PAGE_LINES)
        page_index = 0

        # ========== LOOP DE PAGINA ==========
        while True:
            start = page_index * PAGE_LINES
            end = start + PAGE_LINES
            page_lines = md_lines[start:end]

            draw_screen(author_info, current_path, page_lines, page_index, total_pages)

            cmd = console.input(">> ").strip().lower()

            # SALIR
            if cmd == "q":
                return

            # ATRÁS
            elif cmd == "b":
                if history:
                    current_path = history.pop()
                break

            # PAGE NAVIGATION
            elif cmd == "n":
                if page_index < total_pages - 1:
                    page_index += 1

            elif cmd == "p":
                if page_index > 0:
                    page_index -= 1

            # NAVEGAR POR NÚMERO DE ENLACE
            elif cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(links):
                    history.append(current_path)
                    link_path = links[idx][1]
                    current_path = normalize_path(current_path, link_path)
                    break
                else:
                    console.print("[red]Invalid link number[/red]")

            else:
                console.print("[red]Unknown command[/red]")


if __name__ == "__main__":
    main()
