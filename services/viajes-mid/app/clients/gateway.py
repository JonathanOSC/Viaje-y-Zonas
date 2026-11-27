"""Clientes HTTP síncronos para consumir APIs de Cuentas y Flota a través del gateway.

Cada cliente obtiene y renueva un token OAuth2 client credentials del gateway.
Maneja 401 (renueva y reintenta una vez), 403, 404 y 503.
"""

from __future__ import annotations

from typing import Optional

import httpx
from core.config import settings


class GatewayAuth:
    """Obtiene y renueva tokens del gateway (client credentials)."""

    def __init__(self, client: httpx.Client):
        self.client = client
        self._token: Optional[str] = None

    def get_token(self) -> str:
        if self._token:
            return self._token
        resp = self.client.post(
            settings.gateway_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.gateway_client_id,
                "client_secret": settings.gateway_client_secret,
                "scope": settings.token_scope,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def invalidar(self) -> None:
        self._token = None


class CuentasClient:
    """Cliente para la API de Cuentas (usuarios y billetera)."""

    def __init__(self, client: httpx.Client, auth: GatewayAuth):
        self.client = client
        self.auth = auth

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "X-Gateway-Secret": settings.gateway_secret,
        }

    def obtener_saldo(self, usuario_id: str) -> dict:
        """Consulta el saldo de un usuario."""
        token = self.auth.get_token()
        resp = self.client.get(
            f"{settings.cuentas_url}/usuarios/{usuario_id}/billetera",
            headers=self._headers(token),
            timeout=10.0,
        )
        if resp.status_code == 401:
            self.auth.invalidar()
            token = self.auth.get_token()
            resp = self.client.get(
                f"{settings.cuentas_url}/usuarios/{usuario_id}/billetera",
                headers=self._headers(token),
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()

    def registrar_debito(self, usuario_id: str, monto: float, referencia: str) -> dict:
        """Registra un débito en la billetera del usuario."""
        token = self.auth.get_token()
        resp = self.client.post(
            f"{settings.cuentas_url}/billeteras/{usuario_id}/movimientos",
            headers=self._headers(token),
            json={"tipo": "debito", "monto": monto, "referencia": referencia},
            timeout=10.0,
        )
        if resp.status_code == 401:
            self.auth.invalidar()
            token = self.auth.get_token()
            resp = self.client.post(
                f"{settings.cuentas_url}/billeteras/{usuario_id}/movimientos",
                headers=self._headers(token),
                json={"tipo": "debito", "monto": monto, "referencia": referencia},
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()


class FlotaClient:
    """Cliente para la API de Flota (vehículos)."""

    def __init__(self, client: httpx.Client, auth: GatewayAuth):
        self.client = client
        self.auth = auth

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "X-Gateway-Secret": settings.gateway_secret,
        }

    def obtener_vehiculo(self, vehiculo_id: str) -> dict:
        """Obtiene el estado y ubicación de un vehículo."""
        token = self.auth.get_token()
        resp = self.client.get(
            f"{settings.flota_url}/vehiculos/{vehiculo_id}",
            headers=self._headers(token),
            timeout=10.0,
        )
        if resp.status_code == 401:
            self.auth.invalidar()
            token = self.auth.get_token()
            resp = self.client.get(
                f"{settings.flota_url}/vehiculos/{vehiculo_id}",
                headers=self._headers(token),
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()

    def cambiar_estado(
        self,
        vehiculo_id: str,
        estado: str,
        ubicacion: Optional[dict] = None,
        bateria: Optional[int] = None,
    ) -> dict:
        """Cambia el estado de un vehículo (operación atómica en Flota)."""
        token = self.auth.get_token()
        body: dict = {"estado": estado}
        if ubicacion is not None:
            body["ubicacion"] = ubicacion
        if bateria is not None:
            body["bateriaPct"] = bateria
        resp = self.client.patch(
            f"{settings.flota_url}/vehiculos/{vehiculo_id}/estado",
            headers=self._headers(token),
            json=body,
            timeout=10.0,
        )
        if resp.status_code == 401:
            self.auth.invalidar()
            token = self.auth.get_token()
            resp = self.client.patch(
                f"{settings.flota_url}/vehiculos/{vehiculo_id}/estado",
                headers=self._headers(token),
                json=body,
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()


class ZonasClient:
    """Cliente para consultar zonas a través del gateway (Viajes y zonas)."""

    def __init__(self, client: httpx.Client, auth: GatewayAuth):
        self.client = client
        self.auth = auth

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "X-Gateway-Secret": settings.gateway_secret,
        }

    def verificar_punto(self, lat: float, lng: float) -> dict:
        """Consulta si un punto está dentro de alguna zona."""
        token = self.auth.get_token()
        resp = self.client.get(
            f"{settings.zonas_url}/zonas/verificar",
            params={"lat": lat, "lng": lng},
            headers=self._headers(token),
            timeout=10.0,
        )
        if resp.status_code == 401:
            self.auth.invalidar()
            token = self.auth.get_token()
            resp = self.client.get(
                f"{settings.zonas_url}/zonas/verificar",
                params={"lat": lat, "lng": lng},
                headers=self._headers(token),
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()
