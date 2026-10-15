"""Repositorio de consulta: predios, estadísticas, banderas y puntos.

Solo usa `public_id` en las respuestas de la API; `parcel_source_id`
(numero_predial real) jamás se expone fuera de la base privada.
"""

import sqlite3

SORT_ALLOWLIST = {
    "destino_economico": "destino_economico",
    "area": "area_terreno_catastral_m2",
    "subzona": "subzona",
    "latitud": "latitud",
    "longitud": "longitud",
    "public_id": "public_id",
}

LIST_COLUMNS = (
    "public_id, destino_economico, area_terreno_catastral_m2, area_zhf_m2, "
    "area_construida_m2, latitud, longitud, subzona, coincide_zhf, "
    "cantidad_intersecciones, cantidad_zonas_zhg, tiene_alertas_calidad, "
    "n_alertas_calidad"
)

DETAIL_COLUMNS = LIST_COLUMNS


def list_parcels(
    conn: sqlite3.Connection,
    destino: str | None = None,
    subzona: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    min_lat: float | None = None,
    min_lon: float | None = None,
    max_lat: float | None = None,
    max_lon: float | None = None,
    public_id_prefix: str | None = None,
    sort: str = "public_id",
    sort_desc: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ["1=1"]
    params: list = []
    if destino:
        where.append("destino_economico = ?")
        params.append(destino)
    if subzona:
        where.append("subzona = ?")
        params.append(subzona)
    if public_id_prefix:
        where.append("public_id LIKE ? || '%'")
        params.append(public_id_prefix)
    if min_area is not None:
        where.append("area_terreno_catastral_m2 >= ?")
        params.append(min_area)
    if max_area is not None:
        where.append("area_terreno_catastral_m2 <= ?")
        params.append(max_area)
    if min_lat is not None:
        where.append("latitud >= ?")
        params.append(min_lat)
    if min_lon is not None:
        where.append("longitud >= ?")
        params.append(min_lon)
    if max_lat is not None:
        where.append("latitud <= ?")
        params.append(max_lat)
    if max_lon is not None:
        where.append("longitud <= ?")
        params.append(max_lon)

    where_sql = " AND ".join(where)
    total = conn.execute(
        f"SELECT COUNT(*) FROM parcels WHERE {where_sql}", params
    ).fetchone()[0]

    order = SORT_ALLOWLIST.get(sort, "public_id")
    direction = "DESC" if sort_desc else "ASC"
    rows = conn.execute(
        f"SELECT {LIST_COLUMNS} FROM parcels WHERE {where_sql} "
        f"ORDER BY {order} {direction} LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    return [dict(r) for r in rows], total


def get_parcel(conn: sqlite3.Connection, public_id: str) -> dict | None:
    row = conn.execute(
        f"SELECT {DETAIL_COLUMNS} FROM parcels WHERE public_id = ?",
        (public_id,),
    ).fetchone()
    if row is None:
        return None
    parcel = dict(row)
    features = conn.execute(
        "SELECT * FROM parcel_features WHERE public_id = ?", (public_id,)
    ).fetchone()
    parcel["features"] = dict(features) if features else {}
    flags = conn.execute(
        "SELECT code FROM quality_flags WHERE public_id = ? ORDER BY code",
        (public_id,),
    ).fetchall()
    parcel["quality_flags"] = [f["code"] for f in flags]
    return parcel


def overview_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM parcels").fetchone()[0]
    destino = conn.execute(
        "SELECT destino_economico AS key, COUNT(*) AS n FROM parcels "
        "GROUP BY destino_economico ORDER BY n DESC"
    ).fetchall()
    subzona = conn.execute(
        "SELECT subzona AS key, COUNT(*) AS n FROM parcels "
        "WHERE subzona IS NOT NULL GROUP BY subzona ORDER BY n DESC"
    ).fetchall()
    construccion = conn.execute(
        "SELECT SUM(area_construida_m2 > 0) AS con, "
        "SUM(area_construida_m2 = 0) AS sin FROM parcels"
    ).fetchone()
    alertas = conn.execute(
        "SELECT COUNT(*) FROM parcels WHERE tiene_alertas_calidad = 1"
    ).fetchone()[0]
    area = conn.execute(
        "SELECT COUNT(*) AS n, MIN(area_terreno_catastral_m2) AS min_m2, "
        "MAX(area_terreno_catastral_m2) AS max_m2, "
        "AVG(area_terreno_catastral_m2) AS mean_m2, "
        "SUM(area_terreno_catastral_m2) AS total_m2 FROM parcels"
    ).fetchone()
    coords = conn.execute(
        "SELECT COUNT(*) AS con_coordenadas FROM parcels "
        "WHERE latitud IS NOT NULL AND longitud IS NOT NULL"
    ).fetchone()[0]
    return {
        "total_predios": total,
        "por_destino_economico": [dict(r) for r in destino],
        "por_subzona": [dict(r) for r in subzona],
        "con_construccion": construccion["con"] or 0,
        "sin_construccion": construccion["sin"] or 0,
        "con_alertas_calidad": alertas,
        "area": {
            "n": area["n"],
            "min_m2": area["min_m2"],
            "max_m2": area["max_m2"],
            "media_m2": round(area["mean_m2"], 2) if area["mean_m2"] else None,
            "total_m2": area["total_m2"],
        },
        "predios_con_coordenadas": coords,
    }


def distribution(conn: sqlite3.Connection, field: str) -> dict:
    if field == "area_terreno_catastral_m2":
        bins = [0, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1e9]
        labels = ["<=0.5 ha", "0.5-1 ha", "1-2 ha", "2-5 ha", "5-10 ha",
                  "10-20 ha", "20-50 ha", "50-100 ha", "100-200 ha",
                  "200-500 ha", ">500 ha"]
        counts = []
        for label, low, high in zip(labels, bins, bins[1:], strict=False):
            n = conn.execute(
                "SELECT COUNT(*) FROM parcels WHERE area_terreno_catastral_m2 "
                "> ? AND area_terreno_catastral_m2 <= ?",
                (low * 10000, high * 10000),
            ).fetchone()[0]
            counts.append({"rango": label, "n": n})
        return {"field": field, "bins": counts}
    if field in ("destino_economico", "subzona"):
        rows = conn.execute(
            f"SELECT {field} AS valor, COUNT(*) AS n FROM parcels "
            f"WHERE {field} IS NOT NULL GROUP BY {field} ORDER BY n DESC"
        ).fetchall()
        return {"field": field, "bins": [dict(r) for r in rows]}
    raise ValueError(f"campo de distribución no soportado: {field}")


def map_points(
    conn: sqlite3.Connection,
    min_lat: float | None, min_lon: float | None,
    max_lat: float | None, max_lon: float | None,
    limit: int,
) -> list[dict]:
    where = ["latitud IS NOT NULL", "longitud IS NOT NULL"]
    params: list = []
    for value, column in (
        (min_lat, "latitud"), (min_lon, "longitud"),
    ):
        if value is not None:
            where.append(f"{column} >= ?")
            params.append(value)
    for value, column in (
        (max_lat, "latitud"), (max_lon, "longitud"),
    ):
        if value is not None:
            where.append(f"{column} <= ?")
            params.append(value)
    rows = conn.execute(
        "SELECT public_id, latitud, longitud, destino_economico, subzona "
        f"FROM parcels WHERE {' AND '.join(where)} LIMIT ?",
        params + [limit],
    ).fetchall()
    return [dict(r) for r in rows]


def area_percentiles(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT MIN(area_terreno_catastral_m2) AS min_m2, "
        "MAX(area_terreno_catastral_m2) AS max_m2 FROM parcels"
    ).fetchone()
    return {"min_m2": row["min_m2"], "max_m2": row["max_m2"]}


def get_zhg_zones(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT zone_code, value_cop_ha, source_column, source_file "
        "FROM zhg_zones ORDER BY zone_code"
    ).fetchall()
    return [dict(r) for r in rows]


def parcel_exists(conn: sqlite3.Connection, public_id: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM parcels WHERE public_id = ?", (public_id,)
    ).fetchone() is not None


def get_parcel_zhg(conn: sqlite3.Connection, public_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT zone_code, value_cop_ha, area_intersection_m2, share_pct, "
        "coverage_status, source_file "
        "FROM parcel_zhg_references WHERE public_id = ? ORDER BY zone_code",
        (public_id,),
    ).fetchall()
    return [dict(r) for r in rows]
