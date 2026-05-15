import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from dotenv import load_dotenv
import uvicorn

load_dotenv()

mcp = FastMCP("Azure Calculator MCP")

TENANT_ID = os.environ["AZURE_TENANT_ID"]
SERVER_URL = os.environ["SERVER_URL"]
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

async def oauth_protected_resource(request):
    return JSONResponse({
        "resource": SERVER_URL,
        "authorization_servers": [SERVER_URL]
    })

async def oauth_authorization_server(request):
    return JSONResponse({
        "issuer": SERVER_URL,
        "authorization_endpoint": f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize",
        "token_endpoint": f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        "registration_endpoint": f"{SERVER_URL}/register",
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
    })

async def oauth_register_client(request):
    return JSONResponse({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uris": [
            "http://localhost:6978/callback",
            "http://localhost:12570/callback",
            "http://localhost:8080/callback",
        ],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post"
    }, status_code=201)

class OAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in [
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-authorization-server",
            "/register"
        ]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{SERVER_URL}"'
                }
            )

        return await call_next(request)

mcp_app = mcp.http_app(path="/")

app = Starlette(
    lifespan=mcp_app.lifespan,
    routes=[
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource),
        Route("/.well-known/oauth-protected-resource/mcp", oauth_protected_resource),
        Route("/.well-known/oauth-authorization-server", oauth_authorization_server),
        Route("/register", oauth_register_client, methods=["POST"]),
        Mount("/mcp", app=mcp_app),
    ]
)

app.add_middleware(OAuthMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)