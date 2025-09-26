from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

import requests
from requests import Session

from .config import get_client_config
from .models import AuthResponse, Bet, User


class ApiClientError(Exception):
    pass


class ApiConnectionError(ApiClientError):
    pass


class ApiClient:
    def __init__(self) -> None:
        self.config = get_client_config()
        self.session = Session()
        self.session.headers.update({"Accept": "application/json"})
        self._token: Optional[str] = None

    def set_auth(self, auth: Optional[AuthResponse]) -> None:
        if auth is None:
            self._token = None
            self.session.headers.pop("Authorization", None)
            return
        self._token = auth.access_token
        self.session.headers["Authorization"] = f"Bearer {auth.access_token}"

    def register(self, email: str, password: str, full_name: Optional[str] = None) -> AuthResponse:
        payload = {"email": email, "password": password, "full_name": full_name}
        data = self._request("POST", "/auth/register", json=payload)
        auth = AuthResponse.from_dict(data)
        self.set_auth(auth)
        return auth

    def login(self, email: str, password: str) -> AuthResponse:
        payload = {"email": email, "password": password}
        data = self._request("POST", "/auth/login", json=payload)
        auth = AuthResponse.from_dict(data)
        self.set_auth(auth)
        return auth

    def fetch_profile(self) -> User:
        data = self._request("GET", "/auth/me")
        return User.from_dict(data)

    def list_bets(self, start: Optional[str] = None, end: Optional[str] = None) -> List[Bet]:
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        data = self._request("GET", "/bets", params=params)
        return [Bet.from_dict(item) for item in data]

    def create_bet(self, bet: Bet) -> Bet:
        payload = bet.to_payload()
        data = self._request("POST", "/bets", json=payload)
        return Bet.from_dict(data)

    def update_bet(self, bet_id: str, payload: dict) -> Bet:
        data = self._request("PATCH", f"/bets/{bet_id}", json=payload)
        return Bet.from_dict(data)

    def delete_bet(self, bet_id: str) -> None:
        self._request("DELETE", f"/bets/{bet_id}")

    def sync(self, since: Optional[datetime]) -> dict:
        params = {}
        if since:
            params["since"] = since.isoformat()
        return self._request("GET", "/sync", params=params)

    def _request(self, method: str, path: str, **kwargs):
        url = self._build_url(path)
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as exc:
            raise ApiConnectionError(str(exc)) from exc
        if response.status_code >= 400:
            message = self._extract_error(response)
            raise ApiClientError(message)
        if response.status_code == 204:
            return None
        if response.content:
            return response.json()
        return None

    def _build_url(self, path: str) -> str:
        base = self.config.api_url.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        return base + path

    @staticmethod
    def _extract_error(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"HTTP {response.status_code}: {response.text}"
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        return f"HTTP {response.status_code}: {detail}"


__all__ = ["ApiClient", "ApiClientError", "ApiConnectionError"]
