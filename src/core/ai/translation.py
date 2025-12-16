"""
Translation Service with multiple provider support.
Supports: Google Translate (free), Gemini Pro (API key required)
"""
import os
from typing import Optional
from abc import ABC, abstractmethod


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    def __init__(self, provider: str, message: str = ""):
        self.provider = provider
        self.message = message or f"{provider} API rate limit exceeded"
        super().__init__(self.message)


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""
    
    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        """Translate text to target language."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name."""
        pass


class GoogleTranslateProvider(TranslationProvider):
    """Free Google Translate via deep-translator with Chinese handling."""
    
    def get_name(self) -> str:
        return "Google Translate"
    
    def _detect_chinese(self, text: str) -> str:
        """Detect if text is Chinese and return appropriate source code."""
        if not text:
            return "auto"
        # Check for Chinese characters
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        if has_chinese:
            # Check for Traditional Chinese specific characters
            traditional_chars = set('臺灣國語這裡說話車輛電話時間東西開關嗎們個為還會點對沒過從門發過問題經與應該無過後來現這麼頭個')
            has_traditional = any(char in traditional_chars for char in text)
            return "zh-TW" if has_traditional else "zh-CN"
        return "auto"
    
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        if not text or not text.strip():
            return text
        
        try:
            from deep_translator import GoogleTranslator
            
            # Auto-detect Chinese source
            if source_lang == "auto":
                source_lang = self._detect_chinese(text)
            
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            
            # If translation returned same text, try with explicit Chinese
            if result == text and source_lang == "auto":
                for src in ["zh-TW", "zh-CN"]:
                    try:
                        translator = GoogleTranslator(source=src, target=target_lang)
                        result = translator.translate(text)
                        if result and result != text:
                            return result
                    except:
                        continue
            
            return result or text
            
        except Exception as e:
            print(f"⚠️ Google Translate error: {e}")
            return text
    
    def translate_batch(self, texts: list, target_lang: str, source_lang: str = "auto") -> list:
        """Batch translation for Google Translate - individual calls but with retry."""
        results = []
        for text in texts:
            results.append(self.translate(text, target_lang, source_lang))
        return results


class GeminiProProvider(TranslationProvider):
    """Gemini Pro translation via Google AI API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._model = None
    
    def get_name(self) -> str:
        return "Gemini Pro"
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._model = None  # Reset model
    
    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel('gemini-2.0-flash')
        return self._model
    
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        if not text or not text.strip():
            return text
        
        if not self.api_key:
            print("⚠️ Gemini API key not set. Using Google Translate fallback.")
            return GoogleTranslateProvider().translate(text, target_lang, source_lang)
        
        try:
            model = self._get_model()
            lang_names = {
                "vi": "Vietnamese", "en": "English", "zh": "Chinese",
                "zh-CN": "Simplified Chinese", "zh-TW": "Traditional Chinese",
                "ja": "Japanese", "ko": "Korean", "fr": "French",
                "de": "German", "es": "Spanish",
            }
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"""Translate to {target_name}. Output ONLY the translation, no explanations:
{text}"""
            
            response = model.generate_content(
                prompt,
                generation_config={"max_output_tokens": 500}  # Limit output
            )
            return response.text.strip() or text
            
        except Exception as e:
            error_str = str(e)
            # Check for rate limit (429) error
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                raise RateLimitError("Gemini Pro", error_str)
            print(f"⚠️ Gemini Pro error: {e}")
            return GoogleTranslateProvider().translate(text, target_lang, source_lang)
    
    def translate_batch(self, texts: list, target_lang: str, source_lang: str = "auto") -> list:
        """Translate multiple texts in one API call - MUCH faster!"""
        if not texts:
            return []
        
        if not self.api_key:
            print("⚠️ Gemini API key not set. Using Google Translate fallback.")
            return [GoogleTranslateProvider().translate(t, target_lang, source_lang) for t in texts]
        
        try:
            model = self._get_model()
            lang_names = {
                "vi": "Vietnamese", "en": "English", "zh": "Chinese",
                "ja": "Japanese", "ko": "Korean",
            }
            target_name = lang_names.get(target_lang, target_lang)
            
            # Format texts with numbers for batch processing
            numbered_texts = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])
            
            prompt = f"""Translate to {target_name}. Rules:
- Return ONLY translations
- Keep same number format (1. 2. 3.)
- No explanations or notes

{numbered_texts}"""
            
            # Estimate max tokens: ~2x input for translation + some buffer
            max_tokens = min(4000, len(numbered_texts) * 3)
            
            response = model.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens}
            )
            result_text = response.text.strip()
            
            # Parse numbered results
            lines = result_text.split("\n")
            results = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Remove number prefix like "1. " or "1) "
                import re
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    results.append(cleaned)
            
            # If parsing failed, pad with original texts
            while len(results) < len(texts):
                results.append(texts[len(results)])
            
            return results[:len(texts)]
            
        except RateLimitError:
            # Re-raise rate limit errors for UI to handle
            raise
        except Exception as e:
            error_str = str(e)
            # Check for rate limit (429) error
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                raise RateLimitError("Gemini Pro", error_str)
            # DON'T fallback to individual translations - that causes 20x more requests!
            # Just return original texts and log error
            print(f"⚠️ Gemini batch error: {e}. Keeping original texts.")
            return texts  # Return originals instead of calling individual translations


class OpenAIProvider(TranslationProvider):
    """OpenAI GPT-5/GPT-5 mini translation provider."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-5"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._client = None
    
    def get_name(self) -> str:
        model_names = {
            "gpt-5": "GPT-5",
            "gpt-5-mini": "GPT-5 mini",
            "gpt-5-nano": "GPT-5 nano",
            "gpt-4o": "GPT-4o",
        }
        return model_names.get(self.model, self.model)
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._client = None  # Reset client
    
    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        if not text or not text.strip():
            return text
        
        if not self.api_key:
            print("⚠️ OpenAI API key not set. Using Google Translate fallback.")
            return GoogleTranslateProvider().translate(text, target_lang, source_lang)
        
        try:
            client = self._get_client()
            lang_names = {
                "vi": "Vietnamese", "en": "English", "zh": "Chinese",
                "ja": "Japanese", "ko": "Korean",
            }
            target_name = lang_names.get(target_lang, target_lang)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate to {target_name}. Output ONLY the translation, nothing else."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500  # Limit output tokens
            )
            return response.choices[0].message.content.strip() or text
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                raise RateLimitError(self.get_name(), error_str)
            print(f"⚠️ OpenAI error: {e}")
            return GoogleTranslateProvider().translate(text, target_lang, source_lang)
    
    def translate_batch(self, texts: list, target_lang: str, source_lang: str = "auto") -> list:
        """Translate multiple texts using OpenAI - batch in single prompt."""
        if not texts:
            return []
        
        if not self.api_key:
            return [GoogleTranslateProvider().translate(t, target_lang, source_lang) for t in texts]
        
        try:
            client = self._get_client()
            lang_names = {
                "vi": "Vietnamese", "en": "English", "zh": "Chinese",
                "ja": "Japanese", "ko": "Korean",
            }
            target_name = lang_names.get(target_lang, target_lang)
            
            # Format texts with numbers
            numbered_texts = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])
            
            # Estimate max tokens: roughly 2-3x input for translations
            estimated_tokens = len(numbered_texts.split()) * 3
            max_tokens = min(4000, max(500, estimated_tokens))
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate each numbered line to {target_name}. Rules:\n- Keep numbering (1. 2. 3.)\n- Output ONLY translations\n- No explanations or notes"},
                    {"role": "user", "content": numbered_texts}
                ],
                max_tokens=max_tokens
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse numbered results
            import re
            lines = result_text.split("\n")
            results = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    results.append(cleaned)
            
            # Pad with originals if needed
            while len(results) < len(texts):
                results.append(texts[len(results)])
            
            return results[:len(texts)]
            
        except RateLimitError:
            raise
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                raise RateLimitError(self.get_name(), error_str)
            print(f"⚠️ OpenAI batch error: {e}")
            return texts


class TranslationService:
    """Translation service with configurable provider."""
    
    PROVIDER_GOOGLE = "google"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_GPT5 = "gpt5"
    PROVIDER_GPT5_MINI = "gpt5_mini"
    PROVIDER_GPT5_NANO = "gpt5_nano"
    
    def __init__(self):
        self.providers = {
            self.PROVIDER_GOOGLE: GoogleTranslateProvider(),
            self.PROVIDER_GEMINI: GeminiProProvider(),
            self.PROVIDER_GPT5: OpenAIProvider(model="gpt-5"),
            self.PROVIDER_GPT5_MINI: OpenAIProvider(model="gpt-5-mini"),
            self.PROVIDER_GPT5_NANO: OpenAIProvider(model="gpt-5-nano"),
        }
        self.current_provider = self.PROVIDER_GOOGLE
    
    def set_provider(self, provider: str):
        """Set active translation provider."""
        if provider in self.providers:
            self.current_provider = provider
            print(f"🌐 Translation provider set to: {self.get_provider_name()}")
    
    def get_provider_name(self) -> str:
        """Get current provider name."""
        return self.providers[self.current_provider].get_name()
    
    def set_gemini_api_key(self, api_key: str):
        """Set Gemini API key."""
        if isinstance(self.providers[self.PROVIDER_GEMINI], GeminiProProvider):
            self.providers[self.PROVIDER_GEMINI].set_api_key(api_key)
    
    def set_openai_api_key(self, api_key: str):
        """Set OpenAI API key for GPT-5 providers."""
        for provider_key in [self.PROVIDER_GPT5, self.PROVIDER_GPT5_MINI, self.PROVIDER_GPT5_NANO]:
            if isinstance(self.providers[provider_key], OpenAIProvider):
                self.providers[provider_key].set_api_key(api_key)
    
    def translate(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        """Translate text using current provider."""
        provider = self.providers[self.current_provider]
        return provider.translate(text, target_lang, source_lang)
    
    def translate_batch(self, texts: list, target_lang: str, source_lang: str = "auto") -> list:
        """Translate multiple texts - uses batch API if provider supports it."""
        provider = self.providers[self.current_provider]
        
        # Use batch method if available (Gemini Pro has it)
        if hasattr(provider, 'translate_batch'):
            return provider.translate_batch(texts, target_lang, source_lang)
        
        # Fallback to individual translation
        return [provider.translate(t, target_lang, source_lang) for t in texts]


# Global instance
translation_service = TranslationService()
