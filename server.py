from fastmcp import FastMCP

mcp=FastMCP("Azure Calculator MCP")

@mcp.tool()
def add(a:int,b:int)->int:
    """ 
    Add two numbers
    """
    return a+b

app=mcp.http_app()