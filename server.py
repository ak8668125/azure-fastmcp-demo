import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from dotenv import load_dotenv
import uvicorn

load_dotenv()

mcp = FastMCP("Azure Calculator MCP")

TENANT_ID = os.environ["AZURE_TENANT_ID"]
SERVER_URL = os.environ["SERVER_URL"]

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

async def oauth_protected_resource(request):
    return JSONResponse({
        "resource": SERVER_URL,
        "authorization_servers": [
            f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        ]
    })

async def oauth_authorization_server(request):
    base = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize",
        "token_endpoint": f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
    })

mcp_app = mcp.http_app()

app = Starlette(
    lifespan=mcp_app.lifespan,  # ← this was missing
    routes=[
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource),
        Route("/.well-known/oauth-authorization-server", oauth_authorization_server),
        Mount("/", app=mcp_app),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)