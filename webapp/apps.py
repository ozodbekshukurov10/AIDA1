import logging
import threading
from django.apps import AppConfig

logger = logging.getLogger("webapp")


class WebappConfig(AppConfig):
    name = 'webapp'

    def ready(self):
        """Django to'liq yuklangandan so'ng serverlarni avtomatik ishga tushiradi."""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        def _auto_start():
            try:
                from server_manager import ServerManager
                mgr = ServerManager()
                logger.info("[AutoStart] Serverlarni ishga tushirish...")
                result = mgr.start_all_servers()
                logger.info(f"[AutoStart] Ollama: {result['ollama']}, LM Studio: {result['lmstudio']}")
            except Exception as e:
                logger.warning(f"[AutoStart] Serverlarni ishga tushirishda xatolik: {e}")

        thread = threading.Thread(target=_auto_start, daemon=True)
        thread.start()
