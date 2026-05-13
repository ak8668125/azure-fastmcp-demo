from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.auth.providers.bearer import RSAKeyPair

# Generate a key pair (do this once, save the keys)
key_pair = RSAKeyPair.generate()

auth = BearerAuthProvider(
    public_key=key_pair.public_key,
    issuer="https://login.microsoftonline.com/e813a119-6748-433d-b576-931933d91666/v2.0",
    audience="590a2365-a8b7-450f-875b-4133f5dd80c6",
)

mcp = FastMCP("Azure Calculator MCP", auth=auth)

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

app = mcp.http_app()