"""
Model Management API Views for AIDA
Provides endpoints for managing model providers (Ollama, LM Studio, CodeLLaMA, etc.)
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from webapp.model_auto_start import ModelAutoStart, ModelProvider, ProviderStatus
    MODEL_AUTO_START_AVAILABLE = True
except ImportError:
    MODEL_AUTO_START_AVAILABLE = False

try:
    from webapp.codellama_provider import CodeLLaMAProvider
    CODELLAMA_AVAILABLE = True
except ImportError:
    CODELLAMA_AVAILABLE = False


def get_auto_start_instance():
    """Get or create ModelAutoStart instance."""
    if not MODEL_AUTO_START_AVAILABLE:
        return None
    
    # Get project path (AIDA root)
    project_path = Path(__file__).resolve().parent.parent
    return ModelAutoStart(str(project_path))


@csrf_exempt
@require_http_methods(["GET"])
def api_models_status(request):
    """
    Get status of all model providers.
    
    Returns:
        JSON response with provider statuses
    """
    try:
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available",
                "providers": []
            }, status=503)
        
        report = auto_start.get_status_report()
        
        # Format providers for frontend
        formatted_providers = []
        for provider_name, provider_data in report["providers"].items():
            # Map status to frontend format
            status_map = {
                "running": "running",
                "stopped": "stopped", 
                "error": "error",
                "not_installed": "not_installed"
            }
            
            # Get icon based on provider
            icon_map = {
                "ollama": "Database",
                "lmstudio": "Cpu",
                "gemini": "Globe",
                "codellama": "Zap",
                "local": "Cpu"
            }
            
            formatted_providers.append({
                "name": provider_name,
                "displayName": provider_name.replace("_", " ").title(),
                "status": status_map.get(provider_data.get("status", "unknown"), "unknown"),
                "url": provider_data.get("url", ""),
                "responseTime": provider_data.get("response_time", 0),
                "availableModels": provider_data.get("available_models", []),
                "errorMessage": provider_data.get("error_message", ""),
                "autoStart": provider_data.get("auto_start", False),
                "priority": provider_data.get("priority", 0),
                "icon": icon_map.get(provider_name, "Cpu")
            })
        
        return JsonResponse({
            "timestamp": report["timestamp"],
            "providers": formatted_providers
        })
        
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "providers": []
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_models_start(request, provider_name):
    """
    Start a specific model provider.
    
    Args:
        provider_name: Name of the provider to start
    
    Returns:
        JSON response with start result
    """
    try:
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available"
            }, status=503)
        
        # Map provider name to enum
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
            "gemini": ModelProvider.GEMINI,
            "codellama": ModelProvider.OLLAMA,  # CodeLLaMA uses Ollama
            "local": ModelProvider.LOCAL
        }
        
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({
                "error": f"Unknown provider: {provider_name}"
            }, status=400)
        
        # Start the provider
        success = auto_start.start_provider(provider)
        
        if success:
            # Get updated status
            health = auto_start.check_provider_health(provider)
            return JsonResponse({
                "success": True,
                "provider": provider_name,
                "status": health.status.value,
                "message": f"{provider_name} started successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "provider": provider_name,
                "error": f"Failed to start {provider_name}"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_models_stop(request, provider_name):
    """
    Stop a specific model provider.
    
    Args:
        provider_name: Name of the provider to stop
    
    Returns:
        JSON response with stop result
    """
    try:
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available"
            }, status=503)
        
        # Map provider name to enum
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
            "gemini": ModelProvider.GEMINI,
            "codellama": ModelProvider.OLLAMA,
            "local": ModelProvider.LOCAL
        }
        
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({
                "error": f"Unknown provider: {provider_name}"
            }, status=400)
        
        # Stop the provider
        success = auto_start.stop_provider(provider)
        
        if success:
            return JsonResponse({
                "success": True,
                "provider": provider_name,
                "message": f"{provider_name} stopped successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "provider": provider_name,
                "error": f"Failed to stop {provider_name}"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_models_switch(request, provider_name):
    """
    Switch to a specific model provider.
    
    Args:
        provider_name: Name of the provider to switch to
    
    Returns:
        JSON response with switch result
    """
    try:
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available"
            }, status=503)
        
        # Map provider name to enum
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
            "gemini": ModelProvider.GEMINI,
            "codellama": ModelProvider.OLLAMA,
            "local": ModelProvider.LOCAL
        }
        
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({
                "error": f"Unknown provider: {provider_name}"
            }, status=400)
        
        # Check if provider is running, start if needed
        health = auto_start.check_provider_health(provider)
        
        if health.status == ProviderStatus.STOPPED:
            # Try to start the provider
            start_success = auto_start.start_provider(provider)
            if not start_success:
                return JsonResponse({
                    "success": False,
                    "provider": provider_name,
                    "error": f"Failed to start {provider_name}"
                }, status=500)
        
        # Return success
        return JsonResponse({
            "success": True,
            "provider": provider_name,
            "status": "running",
            "message": f"Switched to {provider_name} successfully"
        })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_models_list(request):
    """
    List available models for a provider.
    
    Query params:
        provider: Provider name (ollama, lmstudio, etc.)
    
    Returns:
        JSON response with available models
    """
    try:
        provider_name = request.GET.get("provider", "ollama")
        
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available",
                "models": []
            }, status=503)
        
        # Map provider name to enum
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
            "gemini": ModelProvider.GEMINI,
            "codellama": ModelProvider.OLLAMA,
        }
        
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({
                "error": f"Unknown provider: {provider_name}",
                "models": []
            }, status=400)
        
        # Get provider health (includes available models)
        health = auto_start.check_provider_health(provider)
        
        return JsonResponse({
            "provider": provider_name,
            "models": health.available_models,
            "status": health.status.value
        })
            
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "models": []
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_models_install(request, provider_name):
    """
    Install a model provider if not already installed.
    
    Args:
        provider_name: Name of the provider to install
    
    Returns:
        JSON response with install result
    """
    try:
        auto_start = get_auto_start_instance()
        if not auto_start:
            return JsonResponse({
                "error": "Model auto-start system not available"
            }, status=503)
        
        # Map provider name to enum
        provider_map = {
            "ollama": ModelProvider.OLLAMA,
            "lmstudio": ModelProvider.LM_STUDIO,
            "gemini": ModelProvider.GEMINI,
        }
        
        provider = provider_map.get(provider_name.lower())
        if not provider:
            return JsonResponse({
                "error": f"Unknown provider: {provider_name}"
            }, status=400)
        
        # Install the provider
        success = auto_start.install_provider(provider)
        
        if success:
            return JsonResponse({
                "success": True,
                "provider": provider_name,
                "message": f"{provider_name} installation completed"
            })
        else:
            return JsonResponse({
                "success": False,
                "provider": provider_name,
                "error": f"Failed to install {provider_name}"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_models_pull(request):
    """
    Pull a specific model for a provider.
    
    Request body:
        provider: Provider name
        model: Model name to pull
    
    Returns:
        JSON response with pull result
    """
    try:
        data = json.loads(request.body)
        provider_name = data.get("provider", "ollama")
        model_name = data.get("model", "llama3.2")
        
        if provider_name == "codellama" and CODELLAMA_AVAILABLE:
            # Use CodeLLaMA provider to pull model
            from webapp.codellama_provider import create_codellama_provider
            provider = create_codellama_provider()
            success = provider.pull_model(model_name)
            
            if success:
                return JsonResponse({
                    "success": True,
                    "provider": provider_name,
                    "model": model_name,
                    "message": f"Model {model_name} pulled successfully"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "provider": provider_name,
                    "model": model_name,
                    "error": f"Failed to pull model {model_name}"
                }, status=500)
        else:
            return JsonResponse({
                "error": f"Model pulling not supported for {provider_name}"
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)