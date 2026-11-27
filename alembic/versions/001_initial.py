"""Primera migración: extensión PostGIS, tablas zonas y viajes, índices.

Reproducible desde una BD vacía.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# Identificadores de revisión de Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Extensión PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 2. Tabla zonas
    op.create_table(
        "zonas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column(
            "tipo",
            sa.String(20),
            nullable=False,
            comment="prohibida | recargo | parqueo",
        ),
        sa.Column("poligono", sa.Text(), nullable=True),  # GeoJSON texto, SRID 4326
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_check_constraint(
        "chk_zonas_tipo_valido",
        "zonas",
        "tipo IN ('prohibida', 'recargo', 'parqueo')",
    )
    op.create_index("idx_zonas_tipo", "zonas", ["tipo"])

    # 3. Tabla viajes
    op.create_table(
        "viajes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("usuario_id", sa.String(36), nullable=False, index=True),
        sa.Column("vehiculo_id", sa.String(36), nullable=False, index=True),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            index=True,
            comment="iniciado | finalizado | cancelado",
        ),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("origen", sa.Text(), nullable=True),  # GeoJSON texto [lng, lat], SRID 4326
        sa.Column("destino", sa.Text(), nullable=True),  # GeoJSON texto [lng, lat], SRID 4326
        sa.Column("minutos", sa.Integer(), nullable=True),
        sa.Column("multa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_check_constraint(
        "chk_viajes_estado_valido",
        "viajes",
        "estado IN ('iniciado', 'finalizado', 'cancelado')",
    )
    op.create_check_constraint(
        "chk_viajes_minutos_positivos",
        "viajes",
        "minutos IS NULL OR minutos >= 0",
    )
    op.create_check_constraint(
        "chk_viajes_fin_despues_de_inicio",
        "viajes",
        "fin_en IS NULL OR fin_en >= inicio_en",
    )
    op.create_index("idx_viajes_usuario_estado", "viajes", ["usuario_id", "estado"])
    op.create_index("idx_viajes_estado_inicio", "viajes", ["estado", sa.text("inicio_en DESC")])


def downgrade() -> None:
    op.drop_index("idx_viajes_estado_inicio")
    op.drop_index("idx_viajes_usuario_estado")
    op.drop_table("viajes")
    op.drop_index("idx_zonas_tipo")
    op.drop_table("zonas")
    op.execute("DROP EXTENSION IF EXISTS postgis")
