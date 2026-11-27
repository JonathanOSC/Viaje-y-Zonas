"""Configuración del servicio MID de Viajes (iniciar/finalizar viaje).

Consume APIs de Cuentas y Flota a través del gateway.
No almacena datos propios de usuarios, billeteras ni vehículos.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Persistencia (el MID también puede leer viajes/zonas si necesita)
    database_url: str
    database_ssl_mode: str = "prefer"
    app_env: str = "local"
    api_mid_port: int = 8101

    # Reglas de negocio
    saldo_minimo: int = 5000
    bateria_minima: int = 15
    tarifa_desbloqueo: int = 1000
    tarifa_por_minuto: int = 350
    recargo_zona_pct: int = 20
    descuento_primer_viaje_pct: int = 50

    # API Gateway
    gateway_url: str = "https://gateway.example.test"
    gateway_client_id: str = "viajes-mid-client"
    gateway_client_secret: str = "replace-me"
    gateway_secret: str = "replace-me"
    gateway_token_url: str = "https://gateway.example.test/token"
    token_scope: str = "zonas:leer,vehiculos:leer,vehiculos:escribir,usuarios:leer,billetera:escribir"

    # APIs integradas (a través del gateway)
    cuentas_url: str = "https://gateway.example.test/cuentas"
    flota_url: str = "https://gateway.example.test/flota"
    zonas_url: str = "https://gateway.example.test/viajes"

    @property
    def connect_args(self) -> dict:
        args: dict = {}
        if self.database_ssl_mode:
            args["sslmode"] = self.database_ssl_mode
        return args


settings = Settings()
