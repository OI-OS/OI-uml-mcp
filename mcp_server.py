#!/usr/bin/env python3
"""
UML Diagram Generator - Simplified MCP Server

A minimal MCP server for generating UML diagrams using FastMCP, Typer, and Rich.
"""

import os
import zlib
import base64
from typing import Dict, Any

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from fastmcp import FastMCP
from mcp.types import TextContent, PromptMessage, GetPromptResult

# Configuration: Use PlantUML server (can be overridden with env var)
PLANTUML_SERVER = os.environ.get("PLANTUML_SERVER", "http://www.plantuml.com/plantuml")


def _encode6bit(b: int) -> str:
    """Encode 6 bits into a single character using PlantUML's custom encoding."""
    if b < 10:
        return chr(48 + b)  # 0-9
    b -= 10
    if b < 26:
        return chr(65 + b)  # A-Z
    b -= 26
    if b < 26:
        return chr(97 + b)  # a-z
    b -= 26
    if b == 0:
        return '-'
    return '_' if b == 1 else '?'

def _encode3bytes(b1: int, b2: int, b3: int) -> str:
    """Encode 3 bytes into 4 characters using PlantUML's encoding."""
    c1 = (b1 >> 2) & 0x3F
    c2 = ((b1 & 0x3) << 4) | ((b2 >> 4) & 0x3F)
    c3 = ((b2 & 0xF) << 2) | ((b3 >> 6) & 0x3F)
    c4 = b3 & 0x3F
    return _encode6bit(c1) + _encode6bit(c2) + _encode6bit(c3) + _encode6bit(c4)

def encode_plantuml(text: str) -> str:
    """Encode PlantUML text using DEFLATE compression and PlantUML's custom 6-bit encoding.
    
    PlantUML uses a custom encoding scheme (not standard base64):
    1. Compress text using zlib.compress (DEFLATE algorithm)
    2. Strip first 2 bytes (zlib header) and last 4 bytes (checksum)
    3. Encode using PlantUML's custom 6-bit character set (0-9, A-Z, a-z, -, _)
    """
    # Compress using DEFLATE
    compressed = zlib.compress(text.encode("utf-8"))
    # Strip zlib header (2 bytes) and checksum (4 bytes)
    data = compressed[2:-4]
    
    # Encode using PlantUML's custom 6-bit encoding
    result = ""
    for i in range(0, len(data), 3):
        if i + 2 < len(data):
            # 3 bytes -> 4 characters
            result += _encode3bytes(data[i], data[i + 1], data[i + 2])
        elif i + 1 < len(data):
            # 2 bytes -> 3 characters (pad with 0)
            result += _encode3bytes(data[i], data[i + 1], 0)
        else:
            # 1 byte -> 2 characters (pad with 0)
            result += _encode3bytes(data[i], 0, 0)
    
    return result


def generate_diagram(code: str, fmt: str = "svg") -> Dict[str, Any]:
    """Generate a diagram URL using the PlantUML server."""
    encoded = encode_plantuml(code)
    url = f"{PLANTUML_SERVER}/{fmt}/{encoded}"
    return {"url": url, "code": code}


# Create a FastMCP server instance
server = FastMCP("UML Diagram Generator")


# Register an MCP tool to generate a UML diagram
@server.tool(name="generate_uml", description="Generate a UML diagram using PlantUML")
def generate_uml(diagram_type: str, code: str) -> Dict[str, Any]:
    # For simplicity, the diagram_type parameter is not used.
    return generate_diagram(code)


# Register an MCP resource to expose server info
@server.resource("uml://info")
def get_info() -> Dict[str, Any]:
    return {"server": "UML Diagram Generator", "version": "1.0"}


# Register an MCP prompt with a simple template
@server.prompt(name="simple_prompt", description="Simple prompt for diagram generation")
def simple_prompt(context: Dict[str, Any]) -> GetPromptResult:
    code = context.get("code", "@startuml\nAlice -> Bob: Hello\n@enduml")
    return GetPromptResult(
        description="Simple prompt for UML diagram",
        messages=[PromptMessage(role="user", content=TextContent(text=code))]
    )


# Set up the CLI using Typer and Rich
cli = typer.Typer()


@cli.command()
def run():
    """Run the MCP server using stdio transport."""
    console = Console()
    console.print("[bold green]Starting UML Diagram Generator MCP Server...[/bold green]")
    server.run()


@cli.command()
def info():
    """Display server information."""
    console = Console()
    table = Table("Property", "Value")
    table.add_row("Server", "UML Diagram Generator")
    table.add_row("Version", "1.0")
    console.print(table)


if __name__ == "__main__":
    cli()
