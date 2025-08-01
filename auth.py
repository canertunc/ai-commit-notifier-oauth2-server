from fastapi import FastAPI, HTTPException, Form, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
import secrets
from urllib.parse import urlencode, parse_qs
from typing import Optional, List
import os
import uvicorn

app = FastAPI(title="OAuth2 Authorization Server for MCP")

# OAuth2 Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
AUTHORIZATION_CODE_EXPIRE_MINUTES = 10

# In-memory storage
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')
users = {
    os.getenv("OAUTH_USER", "admin"): os.getenv("OAUTH_PASS", "admin123")
}
oauth_clients = {
    "claude_desktop": {
        "client_secret": "claude_secret_key",
        "redirect_uris": ["https://caner-oauth-server.up.railway.app/callback", "mcp://oauth-callback","https://caner-oauth-server.up.railway.app/static/oauth-callback.html"],
        "scopes": ["mcp:read", "mcp:write", "mcp:admin"]
    }
}
authorization_codes = {}  # code: {client_id, user, scopes, expires}
access_tokens = {}  # token: {user, client_id, scopes, expires}
refresh_tokens = {}  # token: {user, client_id, scopes}

def generate_code() -> str:
    return secrets.token_urlsafe(32)

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def create_access_token(user: str, client_id: str, scopes: List[str]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user,
        "client_id": client_id,
        "scopes": scopes,
        "exp": expire,
        "token_type": "access"
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    access_tokens[token] = {
        "user": user,
        "client_id": client_id,
        "scopes": scopes,
        "expires": expire,
        "repo_name": "caner/my-repo",
        "commit_message": "OAuth2 login added"
    }
    return token

def create_refresh_token(user: str, client_id: str, scopes: List[str]) -> str:
    token = generate_token()
    refresh_tokens[token] = {
        "user": user,
        "client_id": client_id,
        "scopes": scopes
    }
    return token

def verify_client(client_id: str, client_secret: str = None) -> bool:
    client = oauth_clients.get(client_id)
    if not client:
        return False
    if client_secret and client["client_secret"] != client_secret:
        return False
    return True

def verify_redirect_uri(client_id: str, redirect_uri: str) -> bool:
    client = oauth_clients.get(client_id)
    if not client:
        return False
    return redirect_uri in client["redirect_uris"]

@app.get("/authorize")
async def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query(...),
    scope: str = Query(...),
    state: str = Query(None)
):
    """OAuth2 Authorization Endpoint"""
    
    # Validate client
    if not verify_client(client_id):
        raise HTTPException(400, "Invalid client_id")
    
    # Validate redirect URI
    if not verify_redirect_uri(client_id, redirect_uri):
        raise HTTPException(400, "Invalid redirect_uri")
    
    # Only support authorization code flow
    if response_type != "code":
        raise HTTPException(400, "Unsupported response_type")
    
    # Store authorization request
    auth_request = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state
    }
    
    # Return login form
    login_form = f"""
    <html>
    <head><title>OAuth2 Authorization</title></head>
    <body style="font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px;">
        <h2>🔐 MCP OAuth2 Authorization</h2>
        <p><strong>Client:</strong> {client_id}</p>
        <p><strong>Requested Scopes:</strong> {scope}</p>
        
        <form method="post" action="/authorize">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="scope" value="{scope}">
            <input type="hidden" name="state" value="{state or ''}">
            
            <div style="margin: 15px 0;">
                <label>Username:</label><br>
                <input type="text" name="username" required style="width: 100%; padding: 8px;">
            </div>
            
            <div style="margin: 15px 0;">
                <label>Password:</label><br>
                <input type="password" name="password" required style="width: 100%; padding: 8px;">
            </div>
            
            <button type="submit" style="background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                Authorize
            </button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=login_form)

@app.post("/authorize")
async def authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    state: str = Form(None),
    username: str = Form(...),
    password: str = Form(...)
):
    """Process authorization and return code"""
    
    # Validate user credentials
    if users.get(username) != password:
        raise HTTPException(401, "Invalid credentials")
    
    # Generate authorization code
    code = generate_code()
    expire_time = datetime.utcnow() + timedelta(minutes=AUTHORIZATION_CODE_EXPIRE_MINUTES)
    
    authorization_codes[code] = {
        "client_id": client_id,
        "user": username,
        "scopes": scope.split(),
        "expires": expire_time,
        "redirect_uri": redirect_uri
    }
    
    # Redirect back to client
    params = {"code": code}
    if state:
        params["state"] = state
        
    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url, status_code=303)

@app.post("/token")
async def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: str = Form(None),
    refresh_token: str = Form(None),
    redirect_uri: str = Form(None)
):
    """OAuth2 Token Endpoint"""
    
    # Verify client credentials
    if not verify_client(client_id, client_secret):
        raise HTTPException(401, "Invalid client credentials")
    
    if grant_type == "authorization_code":
        # Exchange authorization code for tokens
        if not code or code not in authorization_codes:
            raise HTTPException(400, "Invalid authorization code")
        
        auth_data = authorization_codes[code]
        
        # Check if code expired
        if datetime.utcnow() > auth_data["expires"]:
            del authorization_codes[code]
            raise HTTPException(400, "Authorization code expired")
        
        # Verify client and redirect URI
        if auth_data["client_id"] != client_id or auth_data["redirect_uri"] != redirect_uri:
            raise HTTPException(400, "Invalid client or redirect_uri")
        
        # Generate tokens
        access_token = create_access_token(auth_data["user"], client_id, auth_data["scopes"])
        refresh_token_value = create_refresh_token(auth_data["user"], client_id, auth_data["scopes"])
        
        # Remove used authorization code
        del authorization_codes[code]
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": refresh_token_value,
            "scope": " ".join(auth_data["scopes"])
        }
    
    elif grant_type == "refresh_token":
        # Refresh access token
        if not refresh_token or refresh_token not in refresh_tokens:
            raise HTTPException(400, "Invalid refresh token")
        
        refresh_data = refresh_tokens[refresh_token]
        
        # Verify client
        if refresh_data["client_id"] != client_id:
            raise HTTPException(400, "Invalid client")
        
        # Generate new access token
        access_token = create_access_token(refresh_data["user"], client_id, refresh_data["scopes"])
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(refresh_data["scopes"])
        }
    
    else:
        raise HTTPException(400, "Unsupported grant type")

@app.get("/validate")
async def validate_token(token: str):
    """Validate access token"""
    
    # Check if token exists and not expired
    token_data = access_tokens.get(token)
    if not token_data:
        raise HTTPException(401, "Invalid token")
    
    if datetime.utcnow() > token_data["expires"]:
        del access_tokens[token]
        raise HTTPException(401, "Token expired")
    
    return {
        "valid": True,
        "user": token_data["user"],
        "client_id": token_data["client_id"],
        "scopes": token_data["scopes"]
    }

@app.get("/")
async def root():
    return {
        "message": "OAuth2 Authorization Server for MCP",
        "authorization_endpoint": "/authorize",
        "token_endpoint": "/token",
        "validation_endpoint": "/validate"
    }

@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth2 Authorization Server Metadata"""
    return {
        "issuer": "https://caner-oauth-server.up.railway.app",
        "authorization_endpoint": "https://caner-oauth-server.up.railway.app/authorize",
        "token_endpoint": "https://caner-oauth-server.up.railway.app/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "scopes_supported": ["mcp:read", "mcp:write", "mcp:admin"]
    }

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    
    uvicorn.run(app, host=HOST, port=PORT)
