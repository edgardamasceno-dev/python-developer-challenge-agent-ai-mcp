"""
Utilitários de UI para a CLI MCP Client, usando Rich.
Inclui funções para exibir tabelas, markdown e mensagens.
"""
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

console = Console()

def print_table(headers, rows, title=None):
    table = Table(title=title)
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)

def print_markdown(md_text):
    md = Markdown(md_text)
    console.print(md)

def print_status(msg):
    console.print(f"[bold green]{msg}[/bold green]")

def print_error(msg):
    console.print(f"[bold red]{msg}[/bold red]") 