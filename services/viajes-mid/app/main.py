"""Aplicación FastAPI del servicio MID de Viajes (iniciar/finalizar viaje).

Consume Cuentas y Flota a través del gateway.
No almacena datos propios de usuarios, billeteras ni vehículos.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que el directorio app/ esté en el path para importaciones absolutas
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from fastapi import FastAPI

from api.routers import viajes_router

app = FastAPI(
    title="Viajes y zonas — MID",
    description="MID de Viajes: iniciar y finalizar viaje (consume Cuentas y Flota).",
    version="1.0.0",
)

app.include_router(viajes_router)
