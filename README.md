# Active OAuth2 Server

A complete OAuth2 Authorization Server implementation designed specifically for MCP (Model Context Protocol) clients. This server provides secure authentication and token management for AI assistants and MCP-enabled applications.

## 🚀 Features

- **Full OAuth2 Implementation**: Complete authorization code flow with PKCE support
- **MCP Integration**: Designed specifically for Model Context Protocol clients
- **JWT Token Management**: Secure access and refresh token generation
- **Client Management**: Support for multiple OAuth2 clients with different scopes
- **Token Validation**: Built-in endpoint for token verification
- **Web Interface**: User-friendly authorization interface
- **Cloud Ready**: Deployable on Railway, Heroku, and other platforms
- **Static Callback Page**: Integrated token display for easy integration

## 📁 Project Structure

```
active-oauth2-server/
├── LICENSE                    
├── auth.py                    # Main OAuth2 server implementation
├── requirements.txt           # Python dependencies
├── Procfile                   # Heroku deployment configuration
├── railway.toml               # Railway deployment configuration
└── static/
    └── oauth-callback.html    # OAuth callback page for token display
```

## 🛠️ OAuth2 Endpoints

### Authorization Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/authorize` | GET | OAuth2 authorization endpoint (user login) |
| `/authorize` | POST | Process authorization and generate code |
| `/token` | POST | Exchange authorization code for tokens |
| `/validate` | GET | Validate access token |
| `/.well-known/oauth-authorization-server` | GET | OAuth2 server metadata |

### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information and endpoints |
| `/static/oauth-callback.html` | GET | Token callback display page |

## 🔧 Installation & Setup

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/canertunc/active-oauth2-server.git
   cd active-oauth2-server
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables (optional):**
   ```bash
   export PORT=8000
   export HOST=0.0.0.0
   export OAUTH_USER=admin
   export OAUTH_PASS=your_password
   ```

4. **Start the server:**
   ```bash
   python auth.py
   ```

   Server will be available at `http://localhost:8000`

## 🌐 Cloud Deployment

### Railway Deployment
The project includes Railway configuration:
- `railway.toml`: Build and deployment settings

Deploy by connecting your GitHub repository to Railway.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `HOST` | Server host | `0.0.0.0` |
| `OAUTH_USER` | OAuth admin username | `admin` |
| `OAUTH_PASS` | OAuth admin password | `admin123` |

## 🔐 OAuth2 Configuration

### Supported Clients

The server comes pre-configured with the following OAuth2 client:

```python
"claude_desktop": {
    "client_secret": "claude_secret_key",
    "redirect_uris": [
        "https://caner-oauth-server.up.railway.app/callback",
        "mcp://oauth-callback",
        "https://caner-oauth-server.up.railway.app/static/oauth-callback.html"
    ],
    "scopes": ["mcp:read", "mcp:write", "mcp:admin"]
}
```

### Supported Scopes

- `mcp:read` - Read access to MCP resources
- `mcp:write` - Write access to MCP resources  
- `mcp:admin` - Administrative access to MCP resources

### Grant Types

- `authorization_code` - Standard OAuth2 authorization code flow
- `refresh_token` - Token refresh capability

## 🔄 OAuth2 Flow

### 1. Authorization Request
```
GET /authorize?client_id=claude_desktop&redirect_uri=CALLBACK_URL&response_type=code&scope=mcp:read mcp:write&state=xyz
```

### 2. User Authorization
User is presented with a login form to enter credentials and authorize the client.

### 3. Authorization Code
After successful login, user is redirected to callback URL with authorization code:
```
CALLBACK_URL?code=AUTHORIZATION_CODE&state=xyz
```

### 4. Token Exchange
```bash
curl -X POST https://caner-oauth-server.up.railway.app/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=claude_desktop" \
  -d "client_secret=claude_secret_key" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=CALLBACK_URL"
```

### 5. Token Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "scope": "mcp:read mcp:write"
}
```

## 🔍 Token Validation

Validate an access token:

```bash
curl "https://caner-oauth-server.up.railway.app/validate?token=YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "valid": true,
  "user": "admin",
  "client_id": "claude_desktop",
  "scopes": ["mcp:read", "mcp:write"],
  "repo_name": "caner/my-repo",
  "commit_message": "OAuth2 login added"
}
```

## 🧩 MCP Client Integration

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://your-mcp-server.railway.app/mcp",
        "--header",
        "ACCESS_TOKEN:${ACCESS_TOKEN}"
      ],
      "env": {
        "ACCESS_TOKEN": "your_oauth_access_token_here"
      }
    }
  }
}
```

### Getting Access Token

1. Visit: `https://caner-oauth-server.up.railway.app/authorize?client_id=claude_desktop&redirect_uri=https://caner-oauth-server.up.railway.app/static/oauth-callback.html&response_type=code&scope=mcp:read%20mcp:write&state=xyz`

2. Login with credentials (default: admin/admin123)

3. Copy the access token from the callback page

4. Use the token in your MCP client configuration

## 🧪 Testing

### Test Server Health
```bash
curl https://caner-oauth-server.up.railway.app/
```

### Test Authorization Endpoint
```bash
curl "https://caner-oauth-server.up.railway.app/authorize?client_id=claude_desktop&redirect_uri=https://caner-oauth-server.up.railway.app/static/oauth-callback.html&response_type=code&scope=mcp:read&state=test"
```

### Test Token Validation
```bash
curl "https://caner-oauth-server.up.railway.app/validate?token=YOUR_TOKEN"
```

## 📦 Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI applications
- **python-jose**: JWT token creation and validation
- **httpx**: Async HTTP client for external requests
- **requests**: HTTP library for API calls
- **mcp**: Model Context Protocol implementation

## 🔒 Security Features

- **JWT Tokens**: Cryptographically signed access tokens
- **Token Expiration**: Configurable token lifetime (60 minutes default)
- **Refresh Tokens**: Long-lived tokens for token renewal (30 days default)
- **Authorization Code Expiration**: Short-lived codes (10 minutes default)
- **Client Authentication**: Client secret verification
- **Redirect URI Validation**: Prevents authorization code interception

## 🔧 Configuration

### Token Lifetimes

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60        # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS = 30          # Refresh token lifetime
AUTHORIZATION_CODE_EXPIRE_MINUTES = 10  # Authorization code lifetime
```

### Security Settings

```python
SECRET_KEY = "your-secret-key-change-in-production"  # JWT signing key
ALGORITHM = "HS256"                                   # JWT algorithm
```

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🔗 Related Projects

- **[Active MCP Server](https://github.com/canertunc/active-mcp-server)** - MCP server that uses this OAuth2 server
- **[Active AI Commit Notifier Server](https://github.com/canertunc/active-ai-commit-notifier-server)** - Webhook processor for commit notifications

---
