#!/usr/bin/env python3
"""
UML Diagram Generator - Simplified MCP Server

A minimal MCP server for generating UML diagrams using FastMCP, Typer, and Rich.
"""

import os
import zlib
import base64
import logging
from typing import Dict, Any, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, PromptMessage, GetPromptResult

# Configure console and logging
console = Console()

# Configuration: Use PlantUML server (can be overridden with env var)
PLANTUML_SERVER = os.environ.get("PLANTUML_SERVER", "http://www.plantuml.com/plantuml")
OUTPUT_DIR = os.environ.get("UML_MCP_OUTPUT_DIR", "output")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
def setup_logging(debug: bool = False):
    """Configure logging for the simplified MCP server"""
    level = logging.DEBUG if debug else logging.INFO
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure handlers
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(level)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[console_handler]
    )
    
    return logging.getLogger(__name__)

# PlantUML encoding function
def encode_plantuml(text: str) -> str:
    """Encode PlantUML text using zlib and base64."""
    compressed = zlib.compress(text.encode("utf-8"))
    # Strip the first two and last four bytes per PlantUML spec
    return base64.urlsafe_b64encode(compressed[2:-4]).decode("utf-8")

# Function to generate diagrams
def generate_diagram(code: str, output_format: str = "svg", save_to_file: bool = True) -> Dict[str, Any]:
    """Generate a diagram URL using the PlantUML server."""
    # Ensure PlantUML markup is present if not provided
    if "@startuml" not in code:
        code = f"@startuml\n{code}\n@enduml"
    
    # Encode the PlantUML code
    encoded = encode_plantuml(code)
    url = f"{PLANTUML_SERVER}/{output_format}/{encoded}"
    
    result = {
        "url": url,
        "code": code,
        "format": output_format
    }
    
    if save_to_file:
        # Generate a filename based on the first line of code
        import hashlib
        import datetime
        
        # Create a hash of the code content to use in the filename
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"diagram_{timestamp}_{code_hash}.{output_format}"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        result["local_path"] = filepath
        # Note: In a real implementation, we would download the image from the URL
        # and save it to the local path, but for simplicity, we just record the path
    
    return result

# Create a FastMCP server instance
server = FastMCP("UML Diagram Generator")

# Register an MCP tool to generate a UML diagram
@server.tool(name="generate_uml", description="Generate a UML diagram using PlantUML")
def generate_uml(diagram_type: str, code: str, output_format: str = "svg") -> Dict[str, Any]:
    """
    Generate a UML diagram using PlantUML
    
    Args:
        diagram_type: Type of diagram (class, sequence, etc.)
        code: The PlantUML code
        output_format: Output format (svg, png)
        
    Returns:
        Dictionary containing URL and code
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating {diagram_type} diagram")
    
    return generate_diagram(code, output_format)

# Register a simple class diagram generation tool
@server.tool(name="generate_class_diagram", description="Generate a UML class diagram")
def generate_class_diagram(code: str, output_format: str = "svg") -> Dict[str, Any]:
    """
    Generate a UML class diagram using PlantUML
    
    Args:
        code: The PlantUML code for a class diagram
        output_format: Output format (svg, png)
        
    Returns:
        Dictionary containing URL and code
    """
    return generate_uml("class", code, output_format)

# Register an MCP resource to expose server info
@server.resource("uml://info")
def get_info() -> Dict[str, Any]:
    """Get server information"""
    return {
        "server": "UML Diagram Generator", 
        "version": "1.0",
        "plantuml_server": PLANTUML_SERVER,
        "output_dir": OUTPUT_DIR
    }

# Register a resource to expose diagram types
@server.resource("uml://types")
def get_diagram_types() -> Dict[str, Any]:
    """Get available diagram types"""
    return {
        "types": [
            "class",
            "sequence",
            "activity",
            "usecase",
            "state",
            "component",
            "object"
        ]
    }

# Register an MCP prompt with a simple template
@server.prompt(name="simple_prompt", description="Simple prompt for diagram generation")
def simple_prompt(context: Dict[str, Any]) -> PromptResult:
    """
    A simple prompt template for diagram generation
    
    Args:
        context: Context dictionary
        
    Returns:
        PromptResult containing messages
    """
    code = context.get("code", "@startuml\nAlice -> Bob: Hello\n@enduml")
    return GetPromptResult(
        description="Simple prompt for UML diagram",
        messages=[PromptMessage(role="user", content=TextContent(text=code))]
    )

# Set up the CLI using Typer
cli = typer.Typer(help="Simplified UML Diagram Generator MCP Server")

@cli.command()
def run(
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    transport: str = typer.Option("stdio", "--transport", help="Transport protocol (stdio or http)"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to when using HTTP transport"),
    port: int = typer.Option(8000, "--port", help="Port to bind to when using HTTP transport")
):
    """Run the MCP server using the specified transport."""
    logger = setup_logging(debug)
    console.print("[bold green]Starting UML Diagram Generator MCP Server...[/bold green]")
    
    # Display server configuration
    table = Table(title="Server Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Server Name", "UML Diagram Generator")
    table.add_row("Transport", transport)
    table.add_row("PlantUML Server", PLANTUML_SERVER)
    table.add_row("Output Directory", OUTPUT_DIR)
    
    if transport == "http":
        table.add_row("Host", host)
        table.add_row("Port", str(port))
    
    console.print(table)
    
    # Start the server
    try:
        if transport == "stdio":
            server.run()
        else:
            # Note: HTTP transport would need additional setup
            logger.info(f"Starting HTTP server on {host}:{port}")
            # This is a placeholder for HTTP transport implementation
            console.print("[yellow]HTTP transport not fully implemented in this simplified version[/yellow]")
            server.run()  # Fallback to stdio
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        logger.info("Server shut down")

@cli.command()
def info():
    """Display server information."""
    console = Console()
    table = Table(title="UML Diagram Generator Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Server", "UML Diagram Generator")
    table.add_row("Version", "1.0")
    table.add_row("PlantUML Server", PLANTUML_SERVER)
    table.add_row("Output Directory", OUTPUT_DIR)
    
    # Display supported diagram types
    diagram_types = get_diagram_types()["types"]
    table.add_row("Supported Diagram Types", ", ".join(diagram_types))
    
    # Display registered tools
    tools = ["generate_uml", "generate_class_diagram"]
    table.add_row("Registered Tools", ", ".join(tools))
    
    console.print(table)

if __name__ == "__main__":
    cli()