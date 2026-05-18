import os
import time
import logging
import asyncio
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GeminiKey:
    def __init__(self, key: str, index: int):
        self.key = key
        self.index = index
        self.client = None
        self.is_active = True
        self.fail_count = 0
        self.cooldown_until = 0.0
        self.last_used = 0.0

    def init_client(self):
        if not self.client:
            self.client = genai.Client(api_key=self.key)
        return self.client

class GeminiPool:
    def __init__(self):
        self.keys: List[GeminiKey] = []
        self._load_keys()
        self.current_index = 0
        self.cooldown_seconds = 60

    def _load_keys(self):
        for i in range(1, 6):
            key_val = os.getenv(f"GEMINI_API_KEY_{i}")
            if key_val:
                self.keys.append(GeminiKey(key_val, i))
        
        # Fallback to standard GEMINI_API_KEY if no pool keys found
        if not self.keys:
            key_val = os.getenv("GEMINI_API_KEY")
            if key_val:
                self.keys.append(GeminiKey(key_val, 0))

    def _get_next_available_key(self) -> Optional[GeminiKey]:
        now = time.time()
        start_index = self.current_index
        
        for _ in range(len(self.keys)):
            k = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            if k.cooldown_until and now >= k.cooldown_until:
                k.is_active = True
                k.cooldown_until = 0.0
                k.fail_count = 0
                
            if k.is_active:
                return k
                
        return None

    def mark_key_failed(self, key: GeminiKey):
        key.fail_count += 1
        key.is_active = False
        key.cooldown_until = time.time() + self.cooldown_seconds
        logger.warning(f"Gemini Key {key.index} marked failed. Cooldown until {key.cooldown_until}")

    async def generate_content_async(self, prompt: str, system_instruction: str, model: str = "gemini-2.5-flash"):
        """Async wrapper around the blocking Gemini API with retry and failover"""
        if not self.keys:
            raise RuntimeError("No Gemini API keys configured in the pool.")

        # Try up to len(keys) times for failover
        for attempt in range(len(self.keys)):
            key = self._get_next_available_key()
            if not key:
                logger.error("All Gemini keys are currently in cooldown.")
                # Force wait if all keys are down
                await asyncio.sleep(2)
                key = self.keys[0] # Try first key anyway
                
            client = key.init_client()
            key.last_used = time.time()
            
            cfg = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
            
            try:
                # Assuming genai SDK generates synchronously, we run in an executor
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=cfg
                    )
                )
                return {"response": response.text, "provider": f"gemini_key_{key.index}"}
            except (ServerError, ClientError) as e:
                code = getattr(e, "code", None)
                logger.error(f"Gemini Error on Key {key.index}: {str(e)} Code: {code}")
                # 429: Too Many Requests, 500/503: Server Errors
                if code in (429, 500, 503) or 'quota' in str(e).lower() or 'exhausted' in str(e).lower():
                    self.mark_key_failed(key)
                    continue
                # If it's a 400 Bad Request (e.g. safety blocks), don't retry, just raise
                raise
            except Exception as e:
                logger.error(f"Unexpected error on Key {key.index}: {str(e)}")
                self.mark_key_failed(key)
                continue
                
        raise RuntimeError("All Gemini API requests failed after multiple failover attempts.")

gemini_pool = GeminiPool()
