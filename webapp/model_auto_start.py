"""
Model Auto-Start System for AIDA
Automatically detects, starts, and manages Ollama and LM Studio servers.
Provides intelligent model management and health monitoring.
"""

import os
import sys
import json
import time
import socket
import subprocess
import platform
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading


class ModelProvider(Enum):
    """Available model providers."""
    OLLAMA = "ollama"
    LM_STUDIO = "lmstudio"
    GEMINI = "gemini"
    LOCAL = "local"


class ProviderStatus(Enum):
    """Status of model providers."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"
    STARTING = "starting"


@dataclass
class ProviderConfig:
    """Configuration for a model provider."""
    name: ModelProvider
    default_url: str
    default_model: str
    executable_path: str = ""
    install_command: str = ""
    start_command: str = ""
    health_check_endpoint: str = ""
    auto_start: bool = True
    priority: int = 0


@dataclass
class ProviderHealth:
    """Health status of a provider."""
    provider: ModelProvider
    status: ProviderStatus
    url: str
    response_time: float = 0.0
    available_models: List[str] = field(default_factory=list)
    error_message: str = ""
    last_check: float = 0.0


class ModelAutoStart:
    """
    Automatic model provider management system.
    Detects, starts, and monitors Ollama and LM Studio.
    """
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.config_file = self.project_path / ".model_config.json"
        self.providers: Dict[ModelProvider, ProviderConfig] = {}
        self.health_status: Dict[ModelProvider, ProviderHealth] = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Initialize provider configurations
        self._init_providers()
        
        # Load saved configuration
        self._load_config()
    
    def _init_providers(self):
        """Initialize provider configurations based on platform."""
        system = platform.system()
        
        # Ollama configuration
        ollama_executable = self._find_ollama_executable()
        ollama_start_cmd = "ollama serve" if ollama_executable else ""
        
        self.providers[ModelProvider.OLLAMA] = ProviderConfig(
            name=ModelProvider.OLLAMA,
            default_url="http://localhost:11434",
            default_model="llama3.2",
            executable_path=ollama_executable,
            install_command=self._get_ollama_install_command(system),
            start_command=ollama_start_cmd,
            health_check_endpoint="/api/tags",
            auto_start=True,
            priority=1
        )
        
        # LM Studio configuration
        lmstudio_executable = self._find_lmstudio_executable()
        lmstudio_start_cmd = self._get_lmstudio_start_command(system, lmstudio_executable)
        
        self.providers[ModelProvider.LM_STUDIO] = ProviderConfig(
            name=ModelProvider.LM_STUDIO,
            default_url="http://localhost:1234",
            default_model="local-model",
            executable_path=lmstudio_executable,
            install_command=self._get_lmstudio_install_command(system),
            start_command=lmstudio_start_cmd,
            health_check_endpoint="/v1/models",
            auto_start=False,  # LM Studio is usually started manually
            priority=2
        )
        
        # Gemini configuration (no auto-start needed)
        self.providers[ModelProvider.GEMINI] = ProviderConfig(
            name=ModelProvider.GEMINI,
            default_url="https://generativelanguage.googleapis.com",
            default_model="gemini-2.0-flash-exp",
            executable_path="",
            install_command="",
            start_command="",
            health_check_endpoint="",
            auto_start=False,
            priority=3
        )
    
    def _find_ollama_executable(self) -> str:
        """Find Ollama executable in the system."""
        possible_paths = []
        
        if platform.system() == "Windows":
            possible_paths = [
                "C:\\Users\\{}\\AppData\\Local\\Programs\\Ollama\\ollama.exe".format(os.getenv("USERNAME", "")),
                "ollama.exe",
            ]
        else:
            possible_paths = [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                "ollama",
            ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # Check if ollama is in PATH
        try:
            result = subprocess.run(
                ["which", "ollama"] if platform.system() != "Windows" else ["where", "ollama"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass
        
        return ""
    
    def _find_lmstudio_executable(self) -> str:
        """Find LM Studio executable in the system."""
        possible_paths = []
        
        if platform.system() == "Windows":
            possible_paths = [
                "C:\\Users\\{}\\AppData\\Local\\LM-Studio\\LM Studio.exe".format(os.getenv("USERNAME", "")),
                "C:\\Program Files\\LM Studio\\LM Studio.exe",
            ]
        elif platform.system() == "Darwin":  # macOS
            possible_paths = [
                "/Applications/LM Studio.app/Contents/MacOS/LM Studio",
            ]
        else:  # Linux
            possible_paths = [
                "/opt/lm-studio/LM Studio",
            ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        return ""
    
    def _get_ollama_install_command(self, system: str) -> str:
        """Get Ollama installation command for the platform."""
        if system == "Windows":
            return "powershell -c \"irm https://ollama.com/install.ps1 | iex\""
        elif system == "Darwin":  # macOS
            return "brew install ollama"
        else:  # Linux
            return "curl -fsSL https://ollama.com/install.sh | sh"
    
    def _get_lmstudio_install_command(self, system: str) -> str:
        """Get LM Studio installation command."""
        return "Download from https://lmstudio.ai/"
    
    def _get_lmstudio_start_command(self, system: str, executable: str) -> str:
        """Get LM Studio start command."""
        if not executable:
            return ""
        
        if system == "Windows":
            return f'"{executable}"'
        elif system == "Darwin":
            return f'open -a "LM Studio"'
        else:
            return executable
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                for provider_name, provider_config in config_data.get("providers", {}).items():
                    provider = ModelProvider(provider_name)
                    if provider in self.providers:
                        self.providers[provider].auto_start = provider_config.get("auto_start", True)
                        self.providers[provider].default_url = provider_config.get("default_url", self.providers[provider].default_url)
            except Exception as e:
                print(f"Error loading config: {str(e)}")
    
    def _save_config(self):
        """Save configuration to file."""
        config_data = {
            "providers": {}
        }
        
        for provider, config in self.providers.items():
            config_data["providers"][provider.value] = {
                "auto_start": config.auto_start,
                "default_url": config.default_url,
                "default_model": config.default_model,
            }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    def check_provider_health(self, provider: ModelProvider) -> ProviderHealth:
        """
        Check health status of a provider.
        
        Args:
            provider: Provider to check
        
        Returns:
            ProviderHealth with current status
        """
        config = self.providers[provider]
        
        # Check if executable exists for local providers
        if provider in [ModelProvider.OLLAMA, ModelProvider.LM_STUDIO]:
            if not config.executable_path and provider != ModelProvider.LM_STUDIO:
                return ProviderHealth(
                    provider=provider,
                    status=ProviderStatus.NOT_INSTALLED,
                    url=config.default_url,
                    error_message=f"{provider.value} not found in system"
                )
        
        # Check if server is running
        if provider == ModelProvider.GEMINI:
            # Gemini is a cloud service, just check API key
            api_key = os.getenv("GOOGLE_API_KEY", "")
            if not api_key:
                return ProviderHealth(
                    provider=provider,
                    status=ProviderStatus.ERROR,
                    url=config.default_url,
                    error_message="GOOGLE_API_KEY not set"
                )
            return ProviderHealth(
                provider=provider,
                status=ProviderStatus.RUNNING,
                url=config.default_url,
                available_models=["gemini-2.0-flash-exp", "gemini-1.5-pro"]
            )
        
        # Check server availability
        start_time = time.time()
        try:
            health_url = f"{config.default_url}{config.health_check_endpoint}"
            req = urllib.request.Request(
                health_url,
                headers={"Content-Type": "application/json"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                response_time = time.time() - start_time
                result = json.loads(response.read().decode("utf-8"))
                
                # Extract available models
                available_models = []
                if provider == ModelProvider.OLLAMA:
                    available_models = [model["name"] for model in result.get("models", [])]
                elif provider == ModelProvider.LM_STUDIO:
                    available_models = [model["id"] for model in result.get("data", [])]
                
                return ProviderHealth(
                    provider=provider,
                    status=ProviderStatus.RUNNING,
                    url=config.default_url,
                    response_time=response_time,
                    available_models=available_models,
                    last_check=time.time()
                )
                
        except urllib.error.URLError as e:
            return ProviderHealth(
                provider=provider,
                status=ProviderStatus.STOPPED,
                url=config.default_url,
                error_message=f"Cannot connect to {config.default_url}",
                last_check=time.time()
            )
        except Exception as e:
            return ProviderHealth(
                provider=provider,
                status=ProviderStatus.ERROR,
                url=config.default_url,
                error_message=str(e),
                last_check=time.time()
            )
    
    def start_provider(self, provider: ModelProvider) -> bool:
        """
        Start a model provider.
        
        Args:
            provider: Provider to start
        
        Returns:
            True if successful, False otherwise
        """
        config = self.providers[provider]
        
        if provider == ModelProvider.GEMINI:
            print("Gemini is a cloud service and doesn't need to be started")
            return True
        
        if not config.executable_path:
            print(f"Executable not found for {provider.value}")
            return False
        
        if not config.start_command:
            print(f"No start command configured for {provider.value}")
            return False
        
        try:
            print(f"Starting {provider.value}...")
            
            # Start the process
            if platform.system() == "Windows":
                # Use STARTUPINFO to hide window on Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = subprocess.Popen(
                    config.start_command,
                    shell=True,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    config.start_command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Wait a bit for the server to start
            time.sleep(3)
            
            # Check if it's running
            health = self.check_provider_health(provider)
            if health.status == ProviderStatus.RUNNING:
                print(f"{provider.value} started successfully")
                self.health_status[provider] = health
                return True
            else:
                print(f"Failed to start {provider.value}: {health.error_message}")
                return False
                
        except Exception as e:
            print(f"Error starting {provider.value}: {str(e)}")
            return False
    
    def stop_provider(self, provider: ModelProvider) -> bool:
        """
        Stop a model provider.
        
        Args:
            provider: Provider to stop
        
        Returns:
            True if successful, False otherwise
        """
        if provider == ModelProvider.GEMINI:
            print("Gemini is a cloud service and cannot be stopped")
            return True
        
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "ollama.exe"],
                    capture_output=True
                )
            else:
                subprocess.run(
                    ["pkill", "-f", provider.value],
                    capture_output=True
                )
            
            print(f"{provider.value} stopped")
            return True
        except Exception as e:
            print(f"Error stopping {provider.value}: {str(e)}")
            return False
    
    def auto_start_providers(self) -> Dict[ModelProvider, bool]:
        """
        Automatically start all configured providers.
        
        Returns:
            Dictionary with provider names and start status
        """
        results = {}
        
        for provider, config in self.providers.items():
            if config.auto_start:
                health = self.check_provider_health(provider)
                
                if health.status == ProviderStatus.RUNNING:
                    print(f"{provider.value} is already running")
                    results[provider] = True
                elif health.status == ProviderStatus.STOPPED:
                    print(f"Starting {provider.value}...")
                    success = self.start_provider(provider)
                    results[provider] = success
                else:
                    print(f"{provider.value} status: {health.status} - {health.error_message}")
                    results[provider] = False
        
        return results
    
    def get_best_provider(self) -> Optional[ModelProvider]:
        """
        Get the best available provider based on health and priority.
        
        Returns:
            Best available provider or None
        """
        available_providers = []
        
        for provider, config in self.providers.items():
            health = self.check_provider_health(provider)
            if health.status == ProviderStatus.RUNNING:
                available_providers.append((provider, config.priority, health.response_time))
        
        if not available_providers:
            return None
        
        # Sort by priority (lower is better) and response time
        available_providers.sort(key=lambda x: (x[1], x[2]))
        
        return available_providers[0][0]
    
    def start_monitoring(self, interval: int = 30):
        """
        Start background monitoring of providers.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_active:
            print("Monitoring is already active")
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                for provider in self.providers:
                    health = self.check_provider_health(provider)
                    self.health_status[provider] = health
                
                time.sleep(interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
        print(f"Started monitoring providers (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("Stopped monitoring providers")
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Get comprehensive status report of all providers.
        
        Returns:
            Status report with provider information
        """
        report = {
            "timestamp": time.time(),
            "providers": {}
        }
        
        for provider, config in self.providers.items():
            health = self.check_provider_health(provider)
            
            report["providers"][provider.value] = {
                "status": health.status.value,
                "url": health.url,
                "response_time": health.response_time,
                "available_models": health.available_models,
                "error_message": health.error_message,
                "auto_start": config.auto_start,
                "priority": config.priority,
                "executable_found": bool(config.executable_path)
            }
        
        return report
    
    def install_provider(self, provider: ModelProvider) -> bool:
        """
        Install a provider if not already installed.
        
        Args:
            provider: Provider to install
        
        Returns:
            True if successful, False otherwise
        """
        config = self.providers[provider]
        
        if not config.install_command:
            print(f"No automatic installation available for {provider.value}")
            return False
        
        print(f"Installing {provider.value}...")
        print(f"Running: {config.install_command}")
        
        try:
            if platform.system() == "Windows":
                subprocess.run(config.install_command, shell=True)
            else:
                subprocess.run(config.install_command, shell=True, check=True)
            
            print(f"{provider.value} installation completed")
            
            # Refresh configuration
            self._init_providers()
            
            return True
        except Exception as e:
            print(f"Error installing {provider.value}: {str(e)}")
            return False


# Convenience functions
def setup_auto_start(project_path: str = None) -> ModelAutoStart:
    """Setup and configure auto-start system."""
    auto_start = ModelAutoStart(project_path)
    auto_start.auto_start_providers()
    return auto_start


def check_all_providers(project_path: str = None) -> Dict[str, Any]:
    """Check status of all providers."""
    auto_start = ModelAutoStart(project_path)
    return auto_start.get_status_report()


def get_available_provider(project_path: str = None) -> Optional[str]:
    """Get the best available provider."""
    auto_start = ModelAutoStart(project_path)
    provider = auto_start.get_best_provider()
    return provider.value if provider else None


if __name__ == "__main__":
    # Test model auto-start
    print("Testing Model Auto-Start System...")
    
    # Create auto-start instance
    auto_start = ModelAutoStart()
    
    # Check all providers
    print("\n=== Provider Status ===")
    report = auto_start.get_status_report()
    print(json.dumps(report, indent=2))
    
    # Get best provider
    print("\n=== Best Provider ===")
    best = auto_start.get_best_provider()
    print(f"Best available provider: {best.value if best else 'None'}")
    
    # Auto-start providers
    print("\n=== Auto-Starting Providers ===")
    results = auto_start.auto_start_providers()
    for provider, success in results.items():
        print(f"{provider.value}: {'✓' if success else '✗'}")
    
    # Start monitoring
    print("\n=== Starting Monitoring ===")
    auto_start.start_monitoring(interval=10)
    
    # Keep running for a bit
    time.sleep(15)
    
    # Stop monitoring
    auto_start.stop_monitoring()
    
    print("\nTest completed!")