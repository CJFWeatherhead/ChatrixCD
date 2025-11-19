# Evaluation: Webhooks, Webserver, and WebUI Migration

## Current Webhook Implementation Analysis

### Semaphore Webhook Plugin
The `semaphore_webhook` plugin uses **Gotify** as an intermediary:

```
Semaphore UI → Gotify → ChatrixCD (WebSocket client)
```

**Key Points:**
- ChatrixCD acts as a **WebSocket client** connecting to Gotify
- **No webserver needed** in ChatrixCD itself
- Gotify provides the webhook endpoint that Semaphore pushes to
- ChatrixCD listens for Gotify messages via WebSocket connection

### Current Architecture
```
┌─────────────────┐         ┌──────────┐         ┌───────────────┐
│  Semaphore UI   │──HTTP──>│  Gotify  │<--WS--->│  ChatrixCD    │
└─────────────────┘         └──────────┘         └───────────────┘
   (Sends hooks)             (Receives &           (Receives via
                              forwards)              WebSocket)
```

**Advantages:**
- No need for ChatrixCD to expose HTTP endpoint
- No need for public IP or port forwarding
- No need for SSL/TLS certificate management
- Gotify handles webhook security and authentication
- Gotify provides message persistence and retry logic

## Webhook Server Scenarios

### Scenario 1: Direct Webhook (No Gotify)

If we wanted direct webhooks from Semaphore to ChatrixCD:

```
Semaphore UI ──HTTP──> ChatrixCD (with HTTP server)
```

**Requirements:**
1. **HTTP Server**: Implement webhook endpoint in ChatrixCD
2. **Public Accessibility**: ChatrixCD needs to be reachable from Semaphore
3. **Port Forwarding**: If behind NAT/firewall
4. **SSL/TLS**: For HTTPS (recommended for security)
5. **Authentication**: Validate webhook signatures/tokens
6. **Reverse Proxy**: Nginx/Caddy for production (recommended)

**Implementation Approach:**
```python
# Using aiohttp for webhook server
from aiohttp import web

class WebhookServer:
    def __init__(self, bot, host='0.0.0.0', port=8080):
        self.bot = bot
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.router.add_post('/webhook/semaphore', self.handle_semaphore_webhook)
        self.app.router.add_get('/health', self.health_check)
    
    async def handle_semaphore_webhook(self, request):
        """Handle incoming webhook from Semaphore."""
        # Validate request
        # Parse webhook payload
        # Trigger task status update
        pass
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
```

**Considerations:**
- More complex deployment (networking, security)
- Requires exposing ChatrixCD to internet
- Better for high-frequency webhooks (lower latency)
- More control over webhook processing

### Scenario 2: Keep Gotify (Current)

**Recommendation**: Keep current Gotify approach because:
- ✅ No networking complexity
- ✅ No security concerns about exposed endpoints
- ✅ Works in any network environment
- ✅ Gotify provides additional features (persistence, UI)
- ✅ Simpler deployment

## WebUI vs TUI Analysis

### Current TUI
**Framework**: Textual (terminal-based)

**Advantages:**
- ✅ Lightweight, runs in terminal
- ✅ No browser required
- ✅ Fast, low resource usage
- ✅ Works over SSH
- ✅ No web server needed
- ✅ Secure (local only by default)

**Limitations:**
- ⚠️ Terminal-only access
- ⚠️ Limited UI capabilities
- ⚠️ Not remotely accessible (without SSH)
- ⚠️ Learning curve for terminal UI

### Proposed WebUI
**Framework Options**: Flask/FastAPI + React/Vue/Svelte

**Advantages:**
- ✅ Remote access via browser
- ✅ Rich UI capabilities
- ✅ Familiar web interface
- ✅ Multi-user access
- ✅ Better for mobile devices
- ✅ Integration with webhooks (shared server)

**Disadvantages:**
- ❌ Requires web server
- ❌ More complex deployment
- ❌ Higher resource usage
- ❌ Security concerns (authentication, HTTPS)
- ❌ Additional development effort

## WebUI Implementation Plan

### Architecture Decision: Hybrid Approach

**Recommendation**: Implement WebUI as **optional addon**, keep TUI as default

```
┌────────────────────────────────────────┐
│           ChatrixCD Core               │
│  ┌────────────┐      ┌──────────────┐ │
│  │    Bot     │      │Plugin Manager│ │
│  └────────────┘      └──────────────┘ │
│         │                    │         │
│    ┌────┴────────────────────┴─────┐  │
│    │      Management Interface     │  │
│    └───────────┬───────────────────┘  │
│                │                       │
│       ┌────────┴────────┐             │
│       │                 │             │
│   ┌───▼───┐       ┌────▼────┐        │
│   │  TUI  │       │ WebUI   │        │
│   │(Local)│       │(Remote) │        │
│   └───────┘       └─────────┘        │
└────────────────────────────────────────┘
```

### Phase 1: Web Server Foundation

#### 1.1 Choose Framework
**Recommendation**: **FastAPI** (modern, async, automatic OpenAPI docs)

```python
# chatrixcd/webserver.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn

class ChatrixWebServer:
    """Optional web interface for ChatrixCD."""
    
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.app = FastAPI(title="ChatrixCD Web Interface")
        self.setup_routes()
        self.setup_auth()
    
    def setup_routes(self):
        # API routes
        self.app.get("/api/status")(self.get_status)
        self.app.get("/api/plugins")(self.get_plugins)
        self.app.post("/api/plugins/{name}/reload")(self.reload_plugin)
        self.app.get("/api/rooms")(self.get_rooms)
        self.app.post("/api/rooms/{room_id}/message")(self.send_message)
        
        # Webhook endpoint
        self.app.post("/webhook/semaphore")(self.handle_webhook)
        
        # Static files (frontend)
        self.app.mount("/", StaticFiles(directory="webui", html=True))
    
    async def get_status(self):
        """Get bot status."""
        return {
            "status": "online",
            "version": self.bot.version,
            "uptime": self.bot.get_uptime(),
            "metrics": self.bot.metrics
        }
    
    async def get_plugins(self):
        """Get plugin status."""
        if not hasattr(self.bot, 'plugin_manager'):
            return []
        return self.bot.plugin_manager.get_all_plugins_status()
```

#### 1.2 Configuration
```json
// config.json
{
  "webui": {
    "enabled": false,
    "host": "127.0.0.1",
    "port": 8080,
    "auth_token": "your-secret-token",
    "ssl_cert": "",
    "ssl_key": "",
    "cors_origins": ["http://localhost:3000"],
    "rate_limit": "100/minute"
  }
}
```

### Phase 2: Frontend Development

#### 2.1 Technology Stack
**Recommendation**: **React** with **TypeScript**

- React: Component-based, mature ecosystem
- TypeScript: Type safety, better tooling
- TailwindCSS: Utility-first styling
- Vite: Fast build tool

#### 2.2 Key Components
```typescript
// webui/src/components/Dashboard.tsx
interface DashboardProps {
  botStatus: BotStatus;
  plugins: Plugin[];
}

const Dashboard: React.FC<DashboardProps> = ({ botStatus, plugins }) => {
  return (
    <div className="dashboard">
      <StatusCard status={botStatus} />
      <PluginList plugins={plugins} />
      <RoomList rooms={botStatus.rooms} />
      <MetricsChart metrics={botStatus.metrics} />
    </div>
  );
};

// webui/src/components/PluginManager.tsx
const PluginManager: React.FC = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  
  const reloadPlugin = async (name: string) => {
    await api.post(`/api/plugins/${name}/reload`);
    // Refresh list
  };
  
  return (
    <div className="plugin-manager">
      {plugins.map(plugin => (
        <PluginCard
          key={plugin.name}
          plugin={plugin}
          onReload={reloadPlugin}
        />
      ))}
    </div>
  );
};
```

### Phase 3: Authentication & Security

#### 3.1 Authentication
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token."""
    if credentials.credentials != config.get('webui.auth_token'):
        raise HTTPException(status_code=403, detail="Invalid token")
    return credentials.credentials
```

#### 3.2 Security Headers
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get('webui.cors_origins'),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
```

### Phase 4: Integration with Existing Features

#### 4.1 Plugin Integration
```python
# WebUI as a plugin
class WebUIPlugin(Plugin):
    """Web interface plugin."""
    
    async def initialize(self):
        self.server = ChatrixWebServer(self.bot, self.config)
        return True
    
    async def start(self):
        # Start web server in background
        asyncio.create_task(self.server.run())
        return True
    
    async def stop(self):
        await self.server.shutdown()
```

#### 4.2 Real-time Updates
```python
# Using WebSockets for real-time updates
from fastapi import WebSocket

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            status = await bot.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
```

### Phase 5: Feature Parity with TUI

#### Features to Implement:
1. ✅ Dashboard (status, metrics)
2. ✅ Plugin management (view, reload)
3. ✅ Room management (list, send messages)
4. ✅ Task monitoring (view active tasks)
5. ✅ Configuration editing
6. ✅ Logs viewer
7. ⚠️ Device verification (complex, may need Matrix widget)
8. ⚠️ Alias management
9. ⚠️ Message customization

## Deployment Considerations

### Option 1: Standalone WebUI
```bash
# Separate process
chatrixcd --webui-only --port 8080
```

### Option 2: Embedded WebUI
```bash
# Runs alongside bot
chatrixcd --enable-webui
```

### Option 3: Docker with WebUI
```dockerfile
FROM python:3.12-alpine

# Install dependencies
RUN pip install chatrixcd[webui]

# Expose ports
EXPOSE 8080

CMD ["chatrixcd", "--enable-webui"]
```

### Option 4: Reverse Proxy Setup
```nginx
# Nginx configuration
server {
    listen 443 ssl;
    server_name chatrixcd.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Migration Strategy

### Stage 1: Prototype (1-2 weeks)
1. Basic web server with API
2. Simple dashboard frontend
3. Plugin viewer
4. Proof of concept

### Stage 2: MVP (2-3 weeks)
1. Authentication
2. Real-time updates
3. Plugin management
4. Room management
5. Basic configuration

### Stage 3: Feature Complete (3-4 weeks)
1. Full feature parity with TUI
2. Mobile responsive design
3. Advanced configuration
4. Webhook integration
5. Comprehensive testing

### Stage 4: Production Ready (1-2 weeks)
1. Security hardening
2. Performance optimization
3. Documentation
4. Deployment guides

## Effort Estimation

### WebUI Development
- Backend API: 3-4 days
- Frontend Dashboard: 4-5 days
- Plugin Management UI: 2-3 days
- Room Management UI: 2-3 days
- Configuration UI: 2-3 days
- Authentication & Security: 2-3 days
- Real-time Updates: 1-2 days
- Testing: 3-4 days
- Documentation: 2-3 days
- **Total**: 21-30 days (4-6 weeks)

### Maintenance Burden
- **High**: Separate frontend requires ongoing maintenance
- Need to maintain API compatibility
- Security updates for web components
- Cross-browser testing
- Mobile compatibility

## Recommendations

### Short Term (Current PR)
- ✅ Keep Gotify-based webhook approach
- ✅ No webserver needed for core functionality
- ✅ Focus on TUI plugin awareness

### Medium Term (Next 3-6 months)
1. Implement TUI plugin management (2-3 weeks)
2. Migrate aliases to plugin (1 week)
3. Migrate messages to plugin (1 week)
4. Stabilize plugin system

### Long Term (6-12 months)
1. Consider WebUI as **optional addon**
2. Start with minimal API for monitoring
3. Gradually add management features
4. Keep TUI as primary interface
5. Position WebUI as "remote management" tool

### Decision Tree

```
Do you need remote access?
├─ No → Use TUI (current, recommended)
└─ Yes
   ├─ Via SSH → Use TUI over SSH
   └─ Via Browser
      ├─ Read-only monitoring → Simple web dashboard
      └─ Full management → Full WebUI
```

## Conclusion

### Webhook Server
**Not required** - Current Gotify approach is optimal for webhook handling. Only consider direct webhook server if:
- Need lower latency (< 1 second)
- Cannot deploy Gotify
- Have specific security requirements

### WebUI Development
**Recommended approach**: 
1. **Keep TUI as primary interface** (lightweight, secure, works everywhere)
2. **Develop WebUI as optional plugin** (for remote access scenarios)
3. **Phase development** (start with read-only dashboard, add management features gradually)
4. **Don't deprecate TUI** (different use cases, both valuable)

### Priority
1. **High**: TUI plugin awareness (immediate value, low effort)
2. **Medium**: Alias/message plugin migration (architectural improvement)
3. **Low**: WebUI development (nice-to-have, high effort, maintenance burden)

The TUI serves most use cases well. WebUI should be positioned as an **optional enhancement** for specific remote management scenarios, not a replacement for TUI.
