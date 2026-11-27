"""Endpoints MID: iniciar y finalizar viaje.

Aplica reglas de negocio consumiendo Cuentas y Flota a través del gateway.
No almacena datos propios de usuarios, billeteras ni vehículos.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError

from clients.gateway import CuentasClient, FlotaClient, GatewayAuth, ZonasClient
from core.config import settings
from schemas import (
    FinalizarViajeRequest,
    FinalizarViajeResponse,
    IniciarViajeRequest,
    IniciarViajeResponse,
    LiquidacionResumen,
)
from services.viaje_service import ViajeService

router = APIRouter(tags=["viajes-mid"])


def get_service() -> ViajeService:
    return ViajeService()


@router.post("/viajes/iniciar", response_model=IniciarViajeResponse, status_code=status.HTTP_201_CREATED)
def iniciar_viaje(datos: IniciarViajeRequest, service: ViajeService = Depends(get_service)):
    """Inicia un viaje:
    1. Valida saldo del usuario (Cuentas).
    2. Valida disponibilidad y batería del vehículo (Flota).
    3. Reserva el vehículo (cambia a en_viaje).
    4. Crea el viaje en estado iniciado.
    """
    try:
        return service.iniciar_viaje(datos.usuario_id, datos.vehiculo_id)
    except HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        if exc.response.status_code == 409:
            raise HTTPException(status_code=409, detail=exc.response.json().get("detalle", "Conflicto"))
        if exc.response.status_code == 503:
            raise HTTPException(status_code=503, detail="Servicio no disponible")
        raise HTTPException(status_code=502, detail="Error de integración")


@router.post("/viajes/{viaje_id}/finalizar", response_model=FinalizarViajeResponse)
def finalizar_viaje(
    viaje_id: str,
    datos: FinalizarViajeRequest,
    service: ViajeService = Depends(get_service),
):
    """Finaliza un viaje:
    1. Valida que el viaje exista y esté iniciado.
    2. Calcula minutos.
    3. Verifica zona del punto final (multa si es prohibida).
    4. Guarda viaje como finalizado.
    5. Libera el vehículo en Flota.
    6. Dispara liquidación en Cuentas.
    """
    try:
        return service.finalizar_viaje(viaje_id, datos.lat, datos.lng)
    except HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Viaje no encontrado")
        if exc.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Viaje ya finalizado")
        if exc.response.status_code == 503:
            raise HTTPException(status_code=503, detail="Servicio no disponible")
        raise HTTPException(status_code=502, detail="Error de integración")
