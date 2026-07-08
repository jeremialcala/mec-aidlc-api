"""Tests del núcleo de scoring MEC-AIDLC (sin red)."""
from mec_aidlc_api.domain import scoring
from mec_aidlc_api.domain.models import COMPETENCIA_A_DOMINIO, Estadio


def _comps(d1=1, d2=1, d3=1, d4=1):
    """Construye las 16 competencias con un valor uniforme (entero 1–4) por dominio."""
    valor_por_dom = {"D1": d1, "D2": d2, "D3": d3, "D4": d4}
    return {k: valor_por_dom[dom.value] for k, dom in COMPETENCIA_A_DOMINIO.items()}


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
