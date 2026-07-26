import requests
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RequestUsage:
    """Local, per-process request usage and the latest API limit information."""

    total: int = 0
    chat_completions: int = 0
    successful: int = 0
    failed: int = 0
    blocked: int = 0
    last_duration_ms: Optional[int] = None
    last_status_code: Optional[int] = None
    rate_limit_headers: Dict[str, str] = field(default_factory=dict)


class OpenRouterClient:
    def __init__(
        self, api_key: str, max_requests: int = 0, timeout: int = 30,
        management_api_key: Optional[str] = None
    ):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.max_requests = max_requests
        self.timeout = timeout
        self.management_api_key = management_api_key
        self.usage = RequestUsage()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/alexolinux/openrouter-cli", # Optional, for OpenRouter rankings
            "X-Title": "OpenRouter CLI",                                    # Optional
            "Content-Type": "application/json"
        }
        self.management_headers = {
            **self.headers,
            "Authorization": f"Bearer {self.management_api_key}"
        } if self.management_api_key else None

    def _can_make_request(self, count_toward_limit: bool) -> bool:
        if count_toward_limit and self.max_requests and self.usage.chat_completions >= self.max_requests:
            self.usage.blocked += 1
            print(
                f"Request blocked: session limit of {self.max_requests} chat-completion requests reached. "
                "Set OPENROUTER_MAX_REQUESTS=0 to remove the local limit."
            )
            return False
        return True

    def _record_response(self, response: requests.Response, duration_ms: int) -> None:
        self.usage.total += 1
        self.usage.last_duration_ms = duration_ms
        self.usage.last_status_code = response.status_code
        self.usage.rate_limit_headers = {
            key: value
            for key, value in response.headers.items()
            if "ratelimit" in key.lower() or key.lower() in {"retry-after", "x-request-id"}
        }
        if response.ok:
            self.usage.successful += 1
        else:
            self.usage.failed += 1

    @staticmethod
    def _auth_diagnostic(response: requests.Response) -> str:
        """Report header delivery without exposing the credential itself."""
        prepared_request = getattr(response, "request", None)
        headers = getattr(prepared_request, "headers", {})
        authorization = headers.get("Authorization", "")
        return "yes" if authorization.startswith("Bearer ") and len(authorization) > len("Bearer ") else "no"

    def _request(
        self, method: str, url: str, count_toward_limit: bool = False, **kwargs: Any
    ) -> Optional[requests.Response]:
        """Make one API request while recording local usage and server limit headers."""
        if not self._can_make_request(count_toward_limit):
            return None

        started = time.perf_counter()
        try:
            request_function = getattr(requests, method.lower())
            response = request_function(url, timeout=self.timeout, **kwargs)
            self._record_response(response, int((time.perf_counter() - started) * 1000))
            if count_toward_limit:
                self.usage.chat_completions += 1
            if response.status_code == 401:
                print(
                    "Authentication diagnostic: Authorization header sent by the CLI: "
                    f"{self._auth_diagnostic(response)}"
                )
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            # HTTP errors are already recorded above. Connection errors have no response.
            if getattr(error, "response", None) is None:
                self.usage.total += 1
                self.usage.failed += 1
                self.usage.last_duration_ms = int((time.perf_counter() - started) * 1000)
                self.usage.last_status_code = None
                if count_toward_limit:
                    self.usage.chat_completions += 1
            raise

    def get_usage(self) -> RequestUsage:
        """Return the current local session usage without changing it."""
        return self.usage

    @property
    def has_management_key(self) -> bool:
        """True when a management API key (and its headers) are configured."""
        return self.management_headers is not None

    def _ensure_management_headers(self) -> Dict[str, str]:
        """Return the management headers, raising a clear error when absent."""
        if not self.management_headers:
            raise RuntimeError(
                "This action requires OPENROUTER_MANAGEMENT_API_KEY to be set in your .env file."
            )
        return self.management_headers

    def list_keys(self, offset: int = 0) -> List[Dict[str, Any]]:
        """List the most recent API keys via the management API.

        Uses `offset` for pagination. See:
        https://openrouter.ai/docs/guides/overview/auth/management-api-keys
        """
        headers = self._ensure_management_headers()
        url = f"{self.base_url}/keys"
        if offset:
            url = f"{url}?offset={offset}"
        try:
            response = self._request("GET", url, headers=headers)
            if response is None:
                return []
            return response.json().get("data", [])
        except Exception as error:
            print(f"Error listing API keys: {error}")
            return []

    def create_key(
        self, name: str, limit: Optional[float] = None,
        limit_reset: Optional[str] = None,
        include_byok_in_limit: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new API key. Returns the key record; the plaintext key is
        exposed under the ``"key"`` field (OpenRouter returns it at the top
        level of the response, not nested inside ``data``).
        """
        headers = self._ensure_management_headers()
        url = f"{self.base_url}/keys"
        payload: Dict[str, Any] = {"name": name}
        if limit is not None:
            payload["limit"] = limit
        if limit_reset is not None:
            payload["limit_reset"] = limit_reset
        if include_byok_in_limit is not None:
            payload["include_byok_in_limit"] = include_byok_in_limit
        try:
            response = self._request(
                "POST", url, headers=headers, data=json.dumps(payload)
            )
            if response is None:
                return None
            body = response.json()
            data = dict(body.get("data") or {})
            plaintext = body.get("key")
            if plaintext and "key" not in data:
                data["key"] = plaintext
            return data
        except Exception as error:
            print(f"Error creating API key: {error}")
            return None

    def update_key(
        self, key_hash: str, name: Optional[str] = None,
        disabled: Optional[bool] = None, limit: Optional[float] = None,
        limit_reset: Optional[str] = None,
        include_byok_in_limit: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing API key identified by its hash."""
        headers = self._ensure_management_headers()
        url = f"{self.base_url}/keys/{key_hash}"
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if disabled is not None:
            payload["disabled"] = disabled
        if limit is not None:
            payload["limit"] = limit
        if limit_reset is not None:
            payload["limit_reset"] = limit_reset
        if include_byok_in_limit is not None:
            payload["include_byok_in_limit"] = include_byok_in_limit
        if not payload:
            print("Nothing to update: no key attributes were provided.")
            return None
        try:
            response = self._request(
                "PATCH", url, headers=headers, data=json.dumps(payload)
            )
            if response is None:
                return None
            return response.json().get("data")
        except Exception as error:
            print(f"Error updating API key: {error}")
            return None

    def delete_key(self, key_hash: str) -> bool:
        """Delete an API key by its hash. Returns True on success."""
        headers = self._ensure_management_headers()
        url = f"{self.base_url}/keys/{key_hash}"
        try:
            response = self._request("DELETE", url, headers=headers)
            if response is None:
                return False
            return True
        except Exception as error:
            print(f"Error deleting API key: {error}")
            return False

    def replace_primary_key(
        self, name: str, limit: Optional[float] = None
    ) -> Optional[str]:
        """Create a new key and, on success, switch the CLI's active key to it.

        Useful when the current free-tier key has run out of requests: create a
        fresh key via the management API and start using it immediately.
        Returns the new key string on success, or None on failure.
        """
        data = self.create_key(name=name, limit=limit)
        if not data:
            return None
        new_key = data.get("key")
        if not new_key:
            print("Management API did not return a key string for the new key.")
            return None
        # Switch to the new key for all subsequent calls.
        self.api_key = new_key
        self.headers["Authorization"] = f"Bearer {new_key}"
        return new_key

    def get_current_key_info(self) -> Optional[Dict[str, Any]]:
        """Fetch provider-authoritative usage and spending limits for this API key."""
        try:
            response = self._request("GET", f"{self.base_url}/key", headers=self.headers)
            if response is None:
                return None
            return response.json().get("data")
        except Exception as error:
            print(f"Error fetching API key usage: {error}")
            return None

    def get_account_requests_today(self) -> Optional[int]:
        """Return OpenRouter's account-wide AI request count for the current UTC day.

        The Analytics API is authoritative but requires a management API key.
        """
        if not self.management_headers:
            return None

        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        payload = {
            "metrics": ["request_count"],
            "time_range": {
                "start": start.isoformat().replace("+00:00", "Z"),
                "end": now.isoformat().replace("+00:00", "Z")
            }
        }
        try:
            response = self._request(
                "POST", f"{self.base_url}/analytics/query",
                headers=self.management_headers, data=json.dumps(payload)
            )
            if response is None:
                return None
            rows = response.json().get("data", {}).get("data", [])
            return sum(int(float(row.get("request_count", 0))) for row in rows)
        except Exception as error:
            print(f"Error fetching account request count: {error}")
            return None

    def get_free_models(self) -> List[Dict[str, Any]]:
        """
        Fetches all models and filters for those with zero pricing.
        """
        try:
            url = f"{self.base_url}/models"
            response = self._request("GET", url, headers=self.headers)
            if response is None:
                return []
            
            models = response.json().get('data', [])
            free_models = []
            
            for model in models:
                pricing = model.get('pricing', {})
                # Check if both prompt and completion are "0" (as strings or numbers)
                is_free = (
                    str(pricing.get('prompt')) == "0" and 
                    str(pricing.get('completion')) == "0"
                )
                if is_free:
                    free_models.append(model)
            
            return sorted(free_models, key=lambda x: x.get('name', ''))
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def chat_completion(self, model_id: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Sends a chat completion request to OpenRouter.
        """
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model_id,
                "messages": messages
            }
            
            response = self._request(
                "POST", url, count_toward_limit=True,
                headers=self.headers, data=json.dumps(payload)
            )
            if response is None:
                return None
            
            result = response.json()
            choices = result.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content')
            return None
        except Exception as e:
            print(f"\nError during chat completion: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Details: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
            return None
