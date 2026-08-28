# AIDA — Plugin Architecture

## 1. Plugin System Overview

AIDA's plugin system enables third-party extensions without modifying core code. Every extensible component (agents, tools, models, memory stores, knowledge sources) is a plugin.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PLUGIN SYSTEM                                │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │Discovery │──►│  Loader  │──►│Validator │──►│ Registry│──►│Runtime│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
│       │              │              │              │          │     │
│       ▼              ▼              ▼              ▼          ▼     │
│  File System    Python Import   Schema Check   DI Container   Sandbox│
│  Package Index  Dynamic Load   Security Scan  Version Mgmt   Monitor│
│  URL/Git        Isolation                                          │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Plugin Lifecycle

```
                    ┌─────────────┐
                    │  DISCOVERED │  (Found on filesystem, index, or URL)
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  LOADED     │  (Imported, metadata read)
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  VALIDATED  │  (Schema check, dependency check, security scan)
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  REGISTERED │  (Registered with container, wired with dependencies)
                    └──────┬──────┘
                           ▼
              ┌─────────────────────┐
              │  INITIALIZED        │  (initialize() called, ready for use)
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
         ┌───►│  ACTIVE             │  (Available for execution)
         │    └──────────┬──────────┘
         │               ▼
         │    ┌─────────────────────┐
         │    │  ERROR / DEGRADED   │  (Health check failed)
         │    └──────────┬──────────┘
         │               │
         └───────────────┘
                         ▼
              ┌─────────────────────┐
              │  SHUTTING DOWN      │  (shutdown() called, resources released)
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │  UNREGISTERED       │  (Removed from registry)
              └─────────────────────┘
```

## 3. Plugin Discovery

### Discovery Sources
| Source | Method | Priority | Use Case |
|---|---|---|---|
| Built-in | Code-level registration | Highest | Core agents, tools, providers |
| Local Directory | `plugins/` directory scan | High | Installed plugins |
| Python Package | pip-installed packages | Medium | Distributed plugins |
| Git Repository | Clone from URL | Low | Development plugins |
| Plugin Registry | Remote registry API | Lowest | Marketplace |

### Discovery Protocol
```python
class PluginDiscovery(ABC):
    """Discover plugins from various sources."""

    @abstractmethod
    async def discover(self) -> list[PluginManifest]:
        """Find available plugins. Returns list of manifests."""

    @abstractmethod
    async def fetch(self, manifest: PluginManifest) -> Path:
        """Download/fetch plugin to local cache. Returns path."""
```

### Manifest Format (plugin.yaml)
```yaml
id: aida-agent-code-reviewer
name: Code Reviewer Agent
version: 1.2.0
type: agent                     # agent | tool | model | memory | knowledge
author: Community Member
description: Automated code review agent

entry_point: plugin.main:CodeReviewerAgent
python_version: ">=3.10"
dependencies:
  - aida>=2.0.0
  - pylint>=3.0

permissions:
  - files:read                # Can read files
  - git:read                  # Can read git status/diff
  - network:http              # Can make HTTP calls

capabilities:
  - CODE_REVIEW
  - CODE_ANALYSIS

config:
  review_rules:               # Plugin-specific config schema
    type: array
    items:
      type: string
    default:
      - style
      - security
      - performance

health_check:
  timeout: 10s                # Health check timeout

resources:
  max_memory: 256MB           # Memory limit
  max_cpu: 0.5                # CPU cores limit
```

## 4. Plugin Loader

```python
class PluginLoader:
    """Loads plugins from discovered paths."""

    def __init__(self, sandbox: PluginSandbox, validator: PluginValidator):
        self._sandbox = sandbox
        self._validator = validator

    async def load(self, manifest: PluginManifest) -> PluginModule:
        """Load a plugin from its manifest.
        
        1. Check if plugin is already loaded (version compare)
        2. Verify dependencies are satisfied
        3. Import the entry point module
        4. Create sandboxed execution environment
        5. Return loaded module (before initialization)
        """

    async def load_batch(self, manifests: list[PluginManifest]) -> list[PluginModule]:
        """Load multiple plugins, respecting dependency order."""
```

### Loading Strategy
```python
# Entry point resolution
entry_point = "plugin.main:CodeReviewerAgent"
# 1. Import plugin.main
# 2. Find CodeReviewerAgent class
# 3. Verify it implements the expected interface (BaseAgent)
# 4. Return uninitialized instance

# Isolation
# Each plugin runs with:
# - Restricted imports (cannot import aida.internal.*)
# - Limited resource access (CPU, memory, network)
# - Separate namespace
# - Timeout mechanism
```

## 5. Plugin Validator

```python
class PluginValidator:
    """Validates plugins before registration."""

    async def validate(self, manifest: PluginManifest, module: PluginModule) -> ValidationResult:
        """Run all validation checks.
        
        Checks:
        1. Schema validation — manifest matches expected schema
        2. Interface compliance — module implements required interface
        3. Dependency check — all plugin dependencies are satisfied
        4. Version compatibility — compatible with current AIDA version
        5. Security scan — no dangerous imports, no eval/exec, no shell injection
        6. Resource declaration — declared resources within limits
        """

    async def validate_runtime(self, plugin: Plugin) -> ValidationResult:
        """Runtime validation after initialization.
        
        Checks:
        1. Health check passes
        2. Resource usage within limits
        3. No unexpected side effects
        """
```

## 6. Plugin Registry

```python
class PluginRegistry:
    """Central registry for all loaded plugins."""

    def __init__(self):
        self._plugins: dict[str, PluginRegistration] = {}
        self._dependency_graph: DependencyGraph = {}

    async def register(self, plugin: Plugin, manifest: PluginManifest) -> None:
        """Register a plugin.
        
        1. Add to plugin dict
        2. Update dependency graph
        3. Call plugin.initialize()
        4. Set status to ACTIVE
        """

    async def unregister(self, plugin_id: str) -> None:
        """Unregister a plugin.
        
        1. Check if any other plugin depends on this one
        2. Call plugin.shutdown()
        3. Remove from registry
        4. Set status to UNREGISTERED
        """

    async def get(self, plugin_id: str) -> Plugin:
        """Get plugin by ID."""

    async def list(self, plugin_type: str | None = None) -> list[PluginRegistration]:
        """List all registered plugins, optionally filtered by type."""

    async def get_status(self, plugin_id: str) -> PluginStatus:
        """Get plugin status."""

    async def resolve_dependencies(self, plugin_id: str) -> list[str]:
        """Resolve dependency order for a plugin (topological sort)."""
```

### Registration Data
```python
@dataclass
class PluginRegistration:
    plugin: Plugin
    manifest: PluginManifest
    status: PluginStatus
    loaded_at: datetime
    health: PluginHealth
    metrics: PluginMetrics
    dependencies: list[str]
    dependents: list[str]  # plugins that depend on this one
```

## 7. Plugin Sandbox

```python
class PluginSandbox:
    """Sandboxed execution environment for plugins."""

    def __init__(self, config: SandboxConfig):
        self._config = config

    async def execute(self, plugin_id: str, fn: Callable, *args, **kwargs) -> Any:
        """Execute a plugin function in sandboxed environment.
        
        Enforces:
        - Timeout (configurable per plugin)
        - Memory limit (configurable per plugin)
        - CPU limit (configurable per plugin)
        - Restricted imports (no os.system, subprocess, etc.)
        - Network access control (whitelist/blacklist)
        - Filesystem access control (whitelist paths)
        """

    async def create_environment(self, manifest: PluginManifest) -> SandboxEnvironment:
        """Create a sandboxed environment for a plugin.
        
        For Python:
        - Custom import hook that blocks dangerous modules
        - Resource tracking wrapper
        - Network proxy with whitelist
        - Filesystem jail with allowed paths
        
        For Docker (future):
        - Container per plugin
        - Resource limits via cgroups
        - Network policy
        """

    async def destroy_environment(self, plugin_id: str) -> None:
        """Clean up sandbox environment."""
```

### Sandbox Security Model

| Restriction | Python Plugin | Docker Plugin (future) |
|---|---|---|
| Import blacklist | `os.system`, `subprocess`, `ctypes`, `socket`, `requests` (unguarded) | Container isolation |
| Filesystem | Project directory only | Mounted volume |
| Network | Whitelisted domains only | Network policy |
| CPU | `threading` limit, no `multiprocessing` | cgroup CPU quota |
| Memory | GC monitoring, allocation limit | cgroup memory limit |
| Timeout | `signal.alarm` / `threading.Timer` | Container timeout |
| Disk | Write size limit | Container disk quota |

## 8. Plugin Permissions

```python
class PluginPermissions:
    """Permission management for plugins."""

    # Permission categories
    FILES_READ = "files:read"
    FILES_WRITE = "files:write"
    FILES_DELETE = "files:delete"
    NETWORK_HTTP = "network:http"
    NETWORK_WS = "network:websocket"
    GIT_READ = "git:read"
    GIT_WRITE = "git:write"
    SHELL_EXECUTE = "shell:execute"
    CODE_EXECUTE = "code:execute"
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"
    USER_DATA_READ = "user_data:read"
    USER_DATA_WRITE = "user_data:write"
    SECURITY_OVERRIDE = "security:override"  # Requires admin approval

    @dataclass
    class PermissionRequest:
        plugin_id: str
        permission: str
        reason: str
        resource: str | None = None

    async def request(self, request: PermissionRequest) -> bool:
        """Request a permission. Returns approved/rejected."""

    async def grant(self, plugin_id: str, permission: str) -> None:
        """Grant a permission to a plugin."""

    async def revoke(self, plugin_id: str, permission: str) -> None:
        """Revoke a permission."""

    async def check(self, plugin_id: str, permission: str, resource: str | None = None) -> bool:
        """Check if plugin has a permission."""
```

### Permission Levels

| Level | Scope | Examples | Requires |
|---|---|---|---|
| **Built-in** | Full access | Core agents, tools | Source inclusion |
| **Trusted** | All standard | Known plugins | Manifest signature |
| **Standard** | Declared only | Most plugins | User approval |
| **Restricted** | Minimal | Untrusted plugins | Sandbox enforced |
| **Sandboxed** | None | Unknown sources | Full sandbox |

## 9. Plugin Versioning

```python
@dataclass
class PluginVersion:
    """Semantic version for plugins."""
    major: int
    minor: int
    patch: int
    pre_release: str | None = None

    def is_compatible_with(self, aida_version: str) -> bool:
        """Check if plugin is compatible with this AIDA version.
        
        Rules:
        - Plugin's 'aida>=X.Y.Z' requirement must be satisfied
        - Major version 0 means breaking changes possible
        - Pre-release plugins are not loaded in production
        """

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
```

### Dependency Resolution
```python
class PluginDependencyResolver:
    """Resolves plugin dependencies with version constraints."""

    async def resolve(self, plugins: list[PluginManifest]) -> DependencyGraph:
        """Topological sort of plugin dependency graph.
        
        Raises:
        - DependencyNotFoundError: required plugin not found
        - VersionConflictError: incompatible version requirements
        - CircularDependencyError: circular dependency detected
        """

    async def verify(self, manifest: PluginManifest, installed: dict[str, PluginManifest]) -> bool:
        """Verify all dependencies of a manifest are satisfied."""
```

## 10. Plugin Lifecycle Manager

```python
class PluginLifecycleManager:
    """Manages the complete lifecycle of all plugins."""

    def __init__(self, discovery: PluginDiscovery, loader: PluginLoader,
                 validator: PluginValidator, registry: PluginRegistry,
                 sandbox: PluginSandbox):
        self._discovery = discovery
        self._loader = loader
        self._validator = validator
        self._registry = registry
        self._sandbox = sandbox

    async def discover_and_load_all(self) -> list[PluginRegistration]:
        """Full pipeline: discover → load → validate → register → initialize."""
        manifests = await self._discovery.discover()
        # Sort by dependencies (dependents last)
        sorted_manifests = await self._resolve_dependency_order(manifests)
        
        loaded = []
        for manifest in sorted_manifests:
            module = await self._loader.load(manifest)
            validation = await self._validator.validate(manifest, module)
            if not validation.passed:
                self._handle_validation_failure(manifest, validation)
                continue
            registration = await self._registry.register(module.plugin, manifest)
            loaded.append(registration)
        return loaded

    async def shutdown_plugin(self, plugin_id: str) -> None:
        """Gracefully shut down a plugin.
        
        1. Check for dependents — if any, reject shutdown
        2. Remove from routing tables (no new tasks)
        3. Wait for in-flight tasks to complete (with timeout)
        4. Call plugin.shutdown()
        5. Destroy sandbox environment
        6. Unregister from registry
        """

    async def reload_plugin(self, plugin_id: str) -> PluginRegistration:
        """Hot-reload a plugin without restarting AIDA.
        
        1. Shutdown old version
        2. Load new version
        3. Validate
        4. Register
        5. Initialize
        """

    async def health_check_all(self) -> dict[str, PluginHealth]:
        """Run health checks on all active plugins."""
```

## 11. Plugin Marketplace (Future)

```python
class PluginMarketplace:
    """Remote plugin registry for community plugins."""

    async def search(self, query: str, plugin_type: str | None = None) -> list[PluginListing]:
        """Search for plugins in the marketplace."""

    async def install(self, plugin_id: str, version: str | None = None) -> PluginRegistration:
        """Install a plugin from the marketplace.
        
        1. Download plugin package
        2. Verify signature
        3. Run security scan
        4. Check dependencies
        5. Install via pip / filesystem copy
        6. Load and register
        """

    async def publish(self, manifest: PluginManifest, package_path: Path) -> PluginListing:
        """Publish a plugin to the marketplace.
        
        Requirements:
        - Signed manifest
        - Passed security review
        - Documentation included
        """

    async def update(self, plugin_id: str) -> PluginRegistration:
        """Check for and apply updates to a plugin."""
```

## 12. Plugin Development Guide

### Creating a Plugin (Step by Step)

```python
# 1. Create plugin directory
# my_plugin/
# ├── __init__.py
# ├── main.py
# ├── plugin.yaml
# └── requirements.txt

# 2. Define the plugin manifest (plugin.yaml)
"""
id: my-company-custom-tool
name: My Custom Tool
version: 1.0.0
type: tool
entry_point: main:MyCustomTool
dependencies:
  - aida>=2.0.0
permissions:
  - files:read
  - network:http
"""

# 3. Implement the plugin (main.py)
from aida.plugins.interfaces import ToolPlugin
from aida.domain.entities import ToolSpec, ToolResult

class MyCustomTool(ToolPlugin):
    @property
    def id(self) -> str:
        return "my-company-custom-tool"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return []

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="custom_tool",
            description="Does something custom",
            parameters={"input": {"type": "string"}},
        )

    async def initialize(self, container):
        # Plugin setup — called when registered
        self._api_key = container.config.get("my_plugin.api_key")
        self._client = HTTPClient(base_url="https://api.example.com")

    async def execute(self, args, context=None):
        result = await self._client.post("/process", json=args)
        return ToolResult(success=True, output=result.json())

    async def validate(self, args):
        errors = []
        if "input" not in args:
            errors.append("input is required")
        return errors

    async def shutdown(self):
        await self._client.close()

    async def health_check(self):
        try:
            await self._client.get("/health")
            return True
        except Exception:
            return False
```

## 13. Plugin System Constraints

| Constraint | Reason |
|---|---|
| Maximum plugins | 100 simultaneous | Resource limits |
| Plugin timeout | 30s initialization | Prevent hangs |
| Plugin size | < 100MB | Storage limits |
| Network per plugin | 10 req/s | Fair usage |
| Memory per plugin | 512MB max | Prevent memory leaks |
| CPU per plugin | 1 core max | Prevent starvation |
| Disk per plugin | 1GB max | Storage limits |
| API version compat | Semver major match | Prevent breaking changes |
