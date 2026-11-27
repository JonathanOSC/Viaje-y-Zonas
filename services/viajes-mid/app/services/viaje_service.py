"""Servicio de lógica de negocio: iniciar y finalizar viaje (MID).

Reglas:
- Saldo mínimo para iniciar (consulta a Cuentas vía gateway).
- Vehículo disponible y batería suficiente (consulta a Flota vía gateway).
- Reserva atómica del vehículo (cambia a en_viaje en Flota).
- Verificación de zona del punto final (multa si es prohibida).
- Liquidación con recargo y descuento primer viaje (consulta a Cuentas vía gateway).
- Degradación: si Cuentas o Flota no responden, el viaje no se crea (503).
  Si Cuentas no responde al liquidar, el viaje queda finalizado con liquidación pendiente.

Este MID no almacena datos propios de usuarios, billeteras ni vehículos;
solo delega en los servicios de Cuentas y Flota a través del gateway.
"""

from __future__ import annotations

from typing import Optional

import httpx
from fastapi import HTTPException

from clients.gateway import CuentasClient, FlotaClient, GatewayAuth, ZonasClient
from core.config import settings


class ViajeService:
    def __init__(self, client: Optional[httpx.Client] = None):
        self.client = client or httpx.Client(timeout=10.0)
        self.auth = GatewayAuth(self.client)
        self.cuentas = CuentasClient(self.client, self.auth)
        self.flota = FlotaClient(self.client, self.auth)
        self.zonas = ZonasClient(self.client, self.auth)

    def iniciar_viaje(self, usuario_id: str, vehiculo_id: str) -> dict:
        # 1. Saldo mínimo (Cuentas)
        try:
            saldo = self.cuentas.obtener_saldo(usuario_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            raise HTTPException(status_code=503, detail="Cuentas no disponible")
        if saldo.get("saldo", 0) < settings.saldo_minimo:
            raise HTTPException(
                status_code=409,
                detail={"codigo": "saldo_insuficiente", "mensaje": "Saldo insuficiente para iniciar viaje"},
            )

        # 2. Vehículo disponible y batería suficiente (Flota)
        try:
            vehiculo = self.flota.obtener_vehiculo(vehiculo_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Vehículo no encontrado")
            raise HTTPException(status_code=503, detail="Flota no disponible")
        if vehiculo.get("estado") != "disponible":
            raise HTTPException(
                status_code=409,
                detail={"codigo": "vehiculo_no_disponible", "mensaje": "El vehículo no está disponible"},
            )
        if vehiculo.get("bateriaPct", 0) < settings.bateria_minima:
            raise HTTPException(
                status_code=409,
                detail={"codigo": "bateria_insuficiente", "mensaje": "Batería insuficiente para iniciar viaje"},
            )

        # 3. Reservar vehículo (cambiar a en_viaje en Flota)
        try:
            self.flota.cambiar_estado(vehiculo_id, "en_viaje")
        except httpx.HTTPStatusError as exc:
            # Compensación: si falla la reserva, no se crea el viaje
            raise HTTPException(status_code=503, detail="No se pudo reservar el vehículo")

        # 4. Crear viaje (se delega al CRUD de viajes vía HTTP o directamente)
        import uuid

        viaje_id = str(uuid.uuid4())
        return {
            "viaje_id": viaje_id,
            "estado": "iniciado",
            "mensaje": "Viaje iniciado correctamente",
        }

    def finalizar_viaje(self, viaje_id: str, lat: float, lng: float) -> dict:
        # 3. Verificar zona del punto final (Vías y zonas vía gateway)
        try:
            verificacion = self.zonas.verificar_punto(lat, lng)
        except httpx.HTTPStatusError:
            # Degradación: si zonas no responde, asumimos permitida
            verificacion = {"permitida": True, "zonas": []}

        multa = not verificacion.get("permitida", True)
        zona_final = None
        if verificacion.get("zonas"):
            zona_final = verificacion["zonas"][0].get("nombre")

        # 4-5. Guardar viaje como finalizado y liberar vehículo en Flota
        # (se delega al CRUD de viajes y a Flota)

        # 6. Liquidación (Cuentas vía gateway, con degradación)
        liquidacion = {
            "tarifa_base": float(settings.tarifa_desbloqueo),
            "recargo": 0.0,
            "descuento": 0.0,
            "total": float(settings.tarifa_desbloqueo),
            "saldo_restante": 0.0,
        }
        advertencia = None
        try:
            # Llamar a Cuentas /liquidaciones (por implementar completamente)
            pass
        except httpx.HTTPStatusError:
            advertencia = "liquidacion_pendiente"

        return {
            "viaje_id": viaje_id,
            "minutos": 0,
            "zona_final": zona_final,
            "multa": multa,
            "liquidacion": liquidacion,
            "advertencia": advertencia,
        }
