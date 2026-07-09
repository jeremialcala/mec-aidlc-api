"""Tests del núcleo de scoring MEC-AIDLC (sin red)."""
import pytest

from mec_aidlc_api.domain import scoring
from mec_aidlc_api.domain.models import COMPETENCIA_A_DOMINIO, Estadio


def _comps(d1=1, d2=1, d3=1, d4=1):
    """Construye las 16 competencias con un valor uniforme (entero 1–4) por dominio."""
    valor_por_dom = {"D1": d1, "D2": d2, "D3": d3, "D4": d4}
    return {k: valor_por_dom[dom.value] for k, dom in COMPETENCIA_A_DOMINIO.items()}


def _comps_por_dominio(items_por_dom):
    """Asigna 4 ítems explícitos por dominio (para promedios fraccionarios)."""
    idx = {"D1": 0, "D2": 0, "D3": 0, "D4": 0}
    out = {}
    for k, dom in COMPETENCIA_A_DOMINIO.items():
        out[k] = items_por_dom[dom.value][idx[dom.value]]
        idx[dom.value] += 1
    return out


def test_hay_16_competencias_repartidas_4x4():
    assert len(COMPETENCIA_A_DOMINIO) == 16
    conteo: dict[str, int] = {}
    for dom in COMPETENCIA_A_DOMINIO.values():
        conteo[dom.value] = conteo.get(dom.value, 0) + 1
    assert conteo == {"D1": 4, "D2": 4, "D3": 4, "D4": 4}


def test_promedios_por_dominio():
    p = scoring.calcular_promedios(_comps(d1=4, d2=2, d3=3, d4=1))
    assert (p.d1, p.d2, p.d3, p.d4) == (4.0, 2.0, 3.0, 1.0)


def test_igv_pondera_d2_y_d3_mas():
    # Mismo "total" de puntos, pero cargados en D2/D3 → IGV mayor que si van en D1/D4.
    p_social = scoring.calcular_promedios(_comps(d1=1, d2=4, d3=4, d4=1))
    p_tecnico = scoring.calcular_promedios(_comps(d1=4, d2=1, d3=1, d4=4))
    # 0.20*1 + 0.30*4 + 0.30*4 + 0.20*1 = 2.8
    assert scoring.calcular_igv(p_social) == 2.8
    assert scoring.calcular_igv(p_social) > scoring.calcular_igv(p_tecnico)


def test_normalizacion_igv_a_porcentaje():
    assert scoring.normalizar_igv_pct(1.0) == 0.0
    assert scoring.normalizar_igv_pct(2.5) == 50.0
    assert scoring.normalizar_igv_pct(4.0) == 100.0


def test_generador_de_valor_requiere_todos_los_umbrales():
    # Todos los dominios en B (3.0): IGV=3.0 y cada umbral se cumple.
    res = scoring.evaluar(_comps(d1=3, d2=3, d3=3, d4=3))
    assert res.estadio == Estadio.GENERADOR_DE_VALOR


def test_d3_alto_pero_d2_bajo_no_es_generador():
    # Colabora excelente pero sin resultados: no debe ser Generador de Valor.
    res = scoring.evaluar(_comps(d1=3, d2=1, d3=4, d4=3))
    assert res.estadio != Estadio.GENERADOR_DE_VALOR


def test_experto_aislado():
    # D1 alto (>=B) y D3 bajo (<=C): fuerte técnico, débil colaboración.
    res = scoring.evaluar(_comps(d1=4, d2=2, d3=1, d4=2))
    assert "aislado" in res.patron_diagnostico.lower()


def test_contribuidor_individual_por_defecto():
    res = scoring.evaluar(_comps(d1=1, d2=1, d3=1, d4=1))
    assert res.estadio == Estadio.CONTRIBUIDOR_INDIVIDUAL


def test_patron_orquestador_sin_criterio_tecnico():
    # D3 alto (>=B) con D1 bajo (<=C): coordina sin profundidad técnica.
    res = scoring.evaluar(_comps(d1=2, d2=3, d3=3, d4=3))
    assert "orquestador" in res.patron_diagnostico.lower()


def test_patron_ejecutor_individual():
    # D2 alto (>=B) con D3 bajo (<=C): entrega resultados, poco integrado al equipo.
    res = scoring.evaluar(_comps(d1=2, d2=3, d3=2, d4=3))
    assert "ejecutor" in res.patron_diagnostico.lower()


def test_patron_team_player_en_desarrollo():
    # Perfil equilibrado en ~2.5 sin picos ni déficits: Team Player sin patrón de desbalance.
    comps = _comps_por_dominio(
        {"D1": [2, 3, 2, 3], "D2": [2, 3, 2, 3], "D3": [2, 3, 2, 3], "D4": [3, 3, 3, 3]}
    )
    res = scoring.evaluar(comps)
    assert res.estadio == Estadio.TEAM_PLAYER
    assert "team player" in res.patron_diagnostico.lower()


def test_patron_contribuidor_sin_desbalance():
    # Bajo parejo pero sin gatillar 'rígido' (D4 suficiente): patrón por defecto de CI.
    res = scoring.evaluar(_comps(d1=2, d2=2, d3=2, d4=3))
    assert res.estadio == Estadio.CONTRIBUIDOR_INDIVIDUAL
    assert "contribuidor individual" in res.patron_diagnostico.lower()


def test_evaluar_rechaza_competencias_incompletas():
    # Un dict parcial haría a _promedio dividir por cero: debe fallar claro (no ZeroDivisionError).
    comps = _comps()
    comps.pop("colaboracion")
    with pytest.raises(ValueError, match="faltan"):
        scoring.evaluar(comps)


def test_evaluar_rechaza_competencias_desconocidas():
    comps = _comps()
    comps["competencia_inventada"] = 3
    with pytest.raises(ValueError, match="sobran"):
        scoring.evaluar(comps)
