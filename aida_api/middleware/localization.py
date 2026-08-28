"""
Localization Middleware — Til sozlash.
"""
from django.utils import translation


class LocalizationMiddleware:
    """
    Accept-Language header asosida tilni aniqlash.
    
    Qo'llab-quvvatlanadigan tillar:
    - uz (O'zbek) — default
    - en (Ingliz)
    - ru (Rus)
    
    Header: Accept-Language: uz
    """

    SUPPORTED_LANGUAGES = ["uz", "en", "ru"]
    DEFAULT_LANGUAGE = "uz"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Accept-Language header dan tilni aniqlash
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")

        if accept_language:
            # Birinchi tilni olish
            lang = accept_language.split(",")[0].split("-")[0].strip().lower()
            if lang in self.SUPPORTED_LANGUAGES:
                request.LANGUAGE_CODE = lang
                translation.activate(lang)
            else:
                request.LANGUAGE_CODE = self.DEFAULT_LANGUAGE
                translation.activate(self.DEFAULT_LANGUAGE)
        else:
            request.LANGUAGE_CODE = self.DEFAULT_LANGUAGE
            translation.activate(self.DEFAULT_LANGUAGE)

        response = self.get_response(request)

        # Response header ga til qo'shish
        response["Content-Language"] = request.LANGUAGE_CODE

        return response
