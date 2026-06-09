# -*- coding: utf-8 -*-
"""
LLM Client — Multi-Provider (Ollama + Gemini + OpenAI) — TEXT ONLY
Rate Limiting, Retry, Fallback, Chunking.

Providers suportados (ordem de prioridade com LLM_PROVIDER=auto):
  1. Ollama local (gemma4:12b, etc.) — R$0, dados nunca saem
  2. Google Gemini (gemini-2.5-flash-lite, etc.) — cloud
  3. OpenAI (gpt-4o-mini, etc.) — cloud

Configuração via .env:
  OLLAMA_URL           = http://localhost:11434 (padrão)
  OLLAMA_MODEL         = gemma4:12b (padrão)
  GEMINI_API_KEY       = chave Google AI Studio
  OPENAI_API_KEY       = chave OpenAI (opcional)
  LLM_PROVIDER         = ollama | gemini | openai | auto
  LLM_MODEL            = modelo override (qualquer provider)
"""
import json
import logging
import os
import re
import time
from collections import deque
from typing import Any, Dict, List, Optional

log = logging.getLogger("llm_client")


# ═══════════════════════════════════════════════════════════
# TOKEN ESTIMATOR
# ═══════════════════════════════════════════════════════════
class TokenEstimator:
    """Estima tokens sem dependência de tiktoken."""

    @staticmethod
    def count(text: str) -> int:
        """~4 chars per token (heurística aceita por Google/OpenAI)."""
        if not text:
            return 0
        return max(1, len(text) // 4)


# ═══════════════════════════════════════════════════════════
# RATE LIMITER — Token Bucket por Minuto
# ═══════════════════════════════════════════════════════════
class RateLimiter:
    """Controla tokens/minuto e requests/minuto."""

    def __init__(self, tpm: int = 500_000, rpm: int = 15):
        self.tpm = tpm
        self.rpm = rpm
        self._token_log: deque = deque()
        self._request_log: deque = deque()
        self._window = 60.0

    def _cleanup(self):
        now = time.time()
        cutoff = now - self._window
        while self._token_log and self._token_log[0][0] < cutoff:
            self._token_log.popleft()
        while self._request_log and self._request_log[0] < cutoff:
            self._request_log.popleft()

    def tokens_used(self) -> int:
        self._cleanup()
        return sum(t[1] for t in self._token_log)

    def requests_used(self) -> int:
        self._cleanup()
        return len(self._request_log)

    def can_send(self, token_count: int) -> bool:
        self._cleanup()
        return (self.tokens_used() + token_count <= self.tpm and
                self.requests_used() < self.rpm)

    def wait_if_needed(self, token_count: int) -> float:
        """Espera até poder enviar. Retorna segundos esperados."""
        total_waited = 0.0
        while not self.can_send(token_count):
            wait = 2.0
            log.info(f"Rate limit: aguardando {wait}s (TPM: {self.tokens_used()}/{self.tpm}, RPM: {self.requests_used()}/{self.rpm})")
            time.sleep(wait)
            total_waited += wait
            if total_waited > 120:
                raise TimeoutError("Rate limiter timeout: 120s esperando por quota")
        return total_waited

    def record(self, token_count: int):
        now = time.time()
        self._token_log.append((now, token_count))
        self._request_log.append(now)


# ═══════════════════════════════════════════════════════════
# PROVIDER: GEMINI (REST — sem SDK)
# Ref: https://ai.google.dev/gemini-api/docs/text-generation?lang=rest
# ═══════════════════════════════════════════════════════════
class GeminiProvider:
    """Google Gemini via REST API v1beta (suporta system_instruction)."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.name = f"Gemini/{model}"

    def call(self, system_prompt: str, user_content: str,
             temperature: float = 0.3, max_tokens: int = 8192) -> Dict[str, Any]:
        """Chama a API Gemini via REST."""
        import urllib.request
        import urllib.error

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_content}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                raise RateLimitError(f"Gemini 429: {error_body}")
            raise LLMError(f"Gemini HTTP {e.code}: {error_body}")
        except Exception as e:
            raise LLMError(f"Gemini request failed: {e}")

        # Extrair resposta
        candidates = body.get("candidates", [])
        if not candidates:
            raise LLMError(f"Gemini: sem candidates na resposta: {body}")

        parts_out = candidates[0].get("content", {}).get("parts", [])
        text_out = "".join(p.get("text", "") for p in parts_out)

        usage = body.get("usageMetadata", {})
        return {
            "text": text_out,
            "tokens_input": usage.get("promptTokenCount", 0),
            "tokens_output": usage.get("candidatesTokenCount", 0),
            "model": self.model,
            "provider": "gemini"
        }


# ═══════════════════════════════════════════════════════════
# PROVIDER: OPENAI (REST — sem SDK)
# ═══════════════════════════════════════════════════════════
class OpenAIProvider:
    """OpenAI via REST API — text only."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.name = f"OpenAI/{model}"

    def call(self, system_prompt: str, user_content: str,
             temperature: float = 0.3, max_tokens: int = 8192) -> Dict[str, Any]:
        """Chama a API OpenAI via REST."""
        import urllib.request
        import urllib.error

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.BASE_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                raise RateLimitError(f"OpenAI 429: {error_body}")
            raise LLMError(f"OpenAI HTTP {e.code}: {error_body}")
        except Exception as e:
            raise LLMError(f"OpenAI request failed: {e}")

        choices = body.get("choices", [])
        if not choices:
            raise LLMError(f"OpenAI: sem choices: {body}")

        text_out = choices[0].get("message", {}).get("content", "")
        usage = body.get("usage", {})

        return {
            "text": text_out,
            "tokens_input": usage.get("prompt_tokens", 0),
            "tokens_output": usage.get("completion_tokens", 0),
            "model": self.model,
            "provider": "openai"
        }


# ═══════════════════════════════════════════════════════════
# PROVIDER: OLLAMA (Local — Gemma 4, etc.)
# Zero custo, dados NUNCA saem da máquina
# ═══════════════════════════════════════════════════════════
class OllamaProvider:
    """Ollama local via REST API — 100% gratuito, 100% privado."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma4:12b", keep_alive: str = "30m"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.name = f"Ollama/{model}"

    def call(self, system_prompt: str, user_content: str,
             temperature: float = 0.3, max_tokens: int = 8192) -> Dict[str, Any]:
        """Chama Ollama local via REST API."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/chat"

        # Detectar se o prompt pede JSON
        wants_json = any(kw in system_prompt.lower() for kw in ["json", "retorne um json", "{\""])

        # CPU optimization: limitar contexto e output
        effective_max = min(max_tokens, 2048)  # CPU: limitar tokens de output

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "num_predict": effective_max,
                "num_ctx": 4096,
            }
        }
        if wants_json:
            payload["format"] = "json"

        prompt_size = len(system_prompt) + len(user_content)
        log.info(f"Ollama request: {prompt_size} chars, max_tokens={effective_max}, model={self.model}")

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise LLMError(f"Ollama indisponível ({self.base_url}): {e}")
        except Exception as e:
            raise LLMError(f"Ollama request failed: {e}")

        text_out = body.get("message", {}).get("content", "")
        if not text_out:
            raise LLMError(f"Ollama: resposta vazia: {body}")

        # Ollama retorna tokens no campo eval_count/prompt_eval_count
        return {
            "text": text_out,
            "tokens_input": body.get("prompt_eval_count", 0),
            "tokens_output": body.get("eval_count", 0),
            "model": self.model,
            "provider": "ollama",
            "duration_s": round(body.get("total_duration", 0) / 1e9, 2)
        }

    def warmup(self):
        """Envia request mínimo para pré-carregar o modelo na memória."""
        import urllib.request
        import urllib.error
        log.info(f"Ollama warmup: carregando {self.model} na memória (keep_alive={self.keep_alive})...")
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "oi"}],
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {"num_predict": 1}
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                load_s = round(body.get("load_duration", 0) / 1e9, 1)
                log.info(f"Ollama warmup OK: modelo carregado em {load_s}s (keep_alive={self.keep_alive})")
        except Exception as e:
            log.warning(f"Ollama warmup falhou: {e} — primeira request será mais lenta")


# ═══════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════
class LLMError(Exception):
    pass

class RateLimitError(LLMError):
    pass


# ═══════════════════════════════════════════════════════════
# LLM CLIENT — Rate Limiter + Retry + Fallback
# ═══════════════════════════════════════════════════════════
class LLMClient:
    """
    Cliente universal multi-provider (text only):
    - Rate Limiting (token bucket/minuto)
    - Exponential Backoff (retry em 429)
    - Fallback automático entre providers
    - Chunking MAP-REDUCE para documentos grandes
    """

    RATE_LIMITS = {
        "ollama_local": {"tpm": 999_999_999, "rpm": 999_999},  # sem limites
        "gemini_free":  {"tpm": 800_000,  "rpm": 15},
        "gemini_paid":  {"tpm": 4_000_000, "rpm": 1000},
        "openai_tier1": {"tpm": 200_000,  "rpm": 500},
        "openai_tier2": {"tpm": 2_000_000, "rpm": 5000},
    }

    def __init__(self):
        self.providers: List = []
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.total_tokens_used = 0
        self.total_calls = 0
        self.total_cost_usd = 0.0
        self._configured = False

        self._load_config()

    def _load_config(self):
        """Carrega configuração do .env."""
        # ─── OLLAMA (local, gratuito) ───
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma4:12b").strip()
        ollama_enabled = os.getenv("OLLAMA_ENABLED", "true").lower() in ("true", "1", "yes")

        if ollama_enabled and ollama_url:
            # Verificar se Ollama está rodando (health check rápido)
            try:
                import urllib.request
                health = urllib.request.urlopen(ollama_url, timeout=2)
                if health.status == 200:
                    keep_alive = os.getenv("OLLAMA_KEEPALIVE", "30m").strip()
                    provider = OllamaProvider(ollama_url, ollama_model, keep_alive)
                    self.providers.append(provider)
                    limits = self.RATE_LIMITS["ollama_local"]
                    self.rate_limiters[provider.name] = RateLimiter(**limits)
                    log.info(f"Ollama LOCAL configurado: {ollama_model} @ {ollama_url} (keep_alive={keep_alive})")

                    # Warmup: pré-carregar modelo na memória
                    do_warmup = os.getenv("OLLAMA_WARMUP", "true").lower() in ("true", "1", "yes")
                    if do_warmup:
                        import threading
                        threading.Thread(target=provider.warmup, daemon=True).start()
            except Exception:
                log.info(f"Ollama não disponível em {ollama_url} — pulando")

        # ─── GEMINI (cloud) ───
        gemini_key = os.getenv("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY_TEXT", "")).strip()
        gemini_model = os.getenv("LLM_MODEL", os.getenv("LLM_MODEL_TEXT", "gemini-2.5-flash-lite"))

        if gemini_key:
            provider = GeminiProvider(gemini_key, gemini_model)
            self.providers.append(provider)
            rl_tier = os.getenv("GEMINI_TIER", "gemini_free")
            limits = self.RATE_LIMITS.get(rl_tier, self.RATE_LIMITS["gemini_free"])
            self.rate_limiters[provider.name] = RateLimiter(**limits)
            log.info(f"Gemini configurado: {gemini_model} (tier={rl_tier})")

        # ─── OPENAI (cloud) ───
        openai_key = os.getenv("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY_TEXT", "")).strip()
        openai_model = os.getenv("OPENAI_MODEL", os.getenv("OPENAI_MODEL_TEXT", "gpt-4o-mini"))

        if openai_key:
            provider = OpenAIProvider(openai_key, openai_model)
            self.providers.append(provider)
            rl_tier = os.getenv("OPENAI_TIER", "openai_tier1")
            limits = self.RATE_LIMITS.get(rl_tier, self.RATE_LIMITS["openai_tier1"])
            self.rate_limiters[provider.name] = RateLimiter(**limits)
            log.info(f"OpenAI configurado: {openai_model} (tier={rl_tier})")

        # ─── LLM_PROVIDER override ───
        preferred = os.getenv("LLM_PROVIDER", "auto").lower()
        if preferred == "ollama":
            self.providers = sorted(self.providers, key=lambda p: 0 if "Ollama" in p.name else 1)
        elif preferred == "gemini":
            self.providers = sorted(self.providers, key=lambda p: 0 if "Gemini" in p.name else 1)
        elif preferred == "openai":
            self.providers = sorted(self.providers, key=lambda p: 0 if "OpenAI" in p.name else 1)
        # auto: Ollama primeiro (já adicionado primeiro), depois Gemini, depois OpenAI

        self._configured = bool(self.providers)
        if self._configured:
            names = ", ".join(p.name for p in self.providers)
            log.info(f"LLM Client pronto: {names}")
        else:
            log.warning("LLM Client: nenhum provider configurado — usando ADK Robô")

    @property
    def is_available(self) -> bool:
        return self._configured

    def _call_with_retry(self, provider, system_prompt: str, user_content: str,
                         temperature: float = 0.3, max_tokens: int = 8192,
                         max_retries: int = 4) -> Dict[str, Any]:
        """Executa call com exponential backoff."""
        token_estimate = TokenEstimator.count(system_prompt) + TokenEstimator.count(user_content)
        rl = self.rate_limiters.get(provider.name)
        if rl:
            waited = rl.wait_if_needed(token_estimate)
            if waited > 0:
                log.info(f"Rate limiter: esperou {waited:.1f}s para {provider.name}")

        last_error = None
        for attempt in range(max_retries):
            try:
                result = provider.call(
                    system_prompt=system_prompt,
                    user_content=user_content,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                total_tokens = result.get("tokens_input", 0) + result.get("tokens_output", 0)
                if rl:
                    rl.record(total_tokens)
                self.total_tokens_used += total_tokens
                self.total_calls += 1
                self._estimate_cost(result)

                return result

            except RateLimitError as e:
                backoff = min(2 ** (attempt + 1), 32)
                log.warning(f"Rate limit ({provider.name}), retry {attempt+1}/{max_retries} em {backoff}s")
                time.sleep(backoff)
                last_error = e

            except LLMError as e:
                log.error(f"LLM error ({provider.name}): {e}")
                last_error = e
                break

        raise last_error or LLMError("Max retries exceeded")

    def _estimate_cost(self, result: Dict):
        """Estima custo em USD."""
        model = result.get("model", "")
        inp = result.get("tokens_input", 0)
        out = result.get("tokens_output", 0)

        # Ollama = gratuito
        if result.get("provider") == "ollama":
            return

        prices = {
            "gemini-2.5-flash-lite": (0.10, 0.40),
            "gemini-2.5-flash": (0.30, 2.50),
            "gemini-3.1-flash-lite": (0.25, 1.50),
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (2.50, 10.00),
        }
        price_in, price_out = prices.get(model, (1.0, 3.0))
        cost = (inp / 1_000_000 * price_in) + (out / 1_000_000 * price_out)
        self.total_cost_usd += cost

    # ═══════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════

    def analyze(self, system_prompt: str, user_content: str,
                temperature: float = 0.3, max_tokens: int = 8192) -> Dict[str, Any]:
        """
        Envia texto para análise via LLM.
        Tenta todos os providers em ordem, com fallback.
        """
        if not self.providers:
            raise LLMError("Nenhum provider configurado")

        last_error = None
        for provider in self.providers:
            try:
                log.info(f"Enviando para {provider.name} (~{TokenEstimator.count(user_content)} tokens)")
                return self._call_with_retry(
                    provider, system_prompt, user_content,
                    temperature=temperature, max_tokens=max_tokens
                )
            except (LLMError, TimeoutError) as e:
                log.warning(f"Falha em {provider.name}: {e}, tentando próximo...")
                last_error = e

        raise last_error or LLMError("Todos os providers falharam")

    # Alias para compatibilidade
    analyze_text = analyze
    smart_analyze = analyze

    def chunk_and_analyze(self, system_prompt: str, full_text: str,
                          chunk_size_tokens: int = 30_000,
                          overlap_tokens: int = 500,
                          temperature: float = 0.3,
                          max_tokens: int = 8192,
                          merge_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        MAP-REDUCE: divide texto grande em chunks, analisa cada um,
        depois faz merge dos resultados.
        """
        total_tokens = TokenEstimator.count(full_text)
        log.info(f"Chunk & Analyze: {total_tokens} tokens, chunk_size={chunk_size_tokens}")

        if total_tokens <= chunk_size_tokens:
            return self.analyze(system_prompt, full_text,
                                temperature=temperature, max_tokens=max_tokens)

        # MAP: dividir em chunks
        chunk_chars = chunk_size_tokens * 4
        overlap_chars = overlap_tokens * 4
        chunks = []
        pos = 0
        while pos < len(full_text):
            end = pos + chunk_chars
            if end < len(full_text):
                last_period = full_text.rfind(".", pos + chunk_chars - 200, end)
                if last_period > pos:
                    end = last_period + 1
            chunks.append(full_text[pos:end])
            pos = end - overlap_chars

        log.info(f"Dividido em {len(chunks)} chunks (~{chunk_chars} chars cada)")

        # MAP: analisar cada chunk
        partial_results = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"{system_prompt}\n\n[CHUNK {i+1}/{len(chunks)}] Analise este trecho do documento:"
            try:
                result = self.analyze(chunk_prompt, chunk,
                                      temperature=temperature, max_tokens=max_tokens)
                partial_results.append(result.get("text", ""))
                log.info(f"Chunk {i+1}/{len(chunks)} OK ({result.get('tokens_input', 0)} tokens)")
            except LLMError as e:
                log.error(f"Erro no chunk {i+1}: {e}")
                partial_results.append(f"[ERRO no chunk {i+1}: {e}]")

        # REDUCE: merge
        if not merge_prompt:
            merge_prompt = """Você recebeu análises parciais de diferentes trechos do mesmo documento.
Consolide todos os resultados em uma única análise coerente, sem duplicações.
Retorne um JSON com a análise consolidada."""

        merged_input = "\n\n---\n\n".join([
            f"=== Resultado Chunk {i+1} ===\n{r}" for i, r in enumerate(partial_results)
        ])

        final_result = self.analyze(merge_prompt, merged_input,
                                     temperature=temperature, max_tokens=max_tokens)
        final_result["chunks_processed"] = len(chunks)
        final_result["total_tokens_all_chunks"] = self.total_tokens_used

        return final_result

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso."""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_cost_brl": round(self.total_cost_usd * 5.8, 4),
            "providers": [p.name for p in self.providers],
            "rate_limiters": {
                name: {
                    "tokens_used": rl.tokens_used(),
                    "requests_used": rl.requests_used(),
                    "tpm_limit": rl.tpm,
                    "rpm_limit": rl.rpm
                }
                for name, rl in self.rate_limiters.items()
            }
        }

    def parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extrai JSON da resposta do LLM (lida com markdown code blocks)."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            brace_start = text.find("{")
            brace_end = text.rfind("}")
            if brace_start >= 0 and brace_end > brace_start:
                try:
                    return json.loads(text[brace_start:brace_end + 1])
                except json.JSONDecodeError:
                    pass
            log.warning(f"JSON parse failed: {text[:200]}...")
            return {"raw_response": text}
