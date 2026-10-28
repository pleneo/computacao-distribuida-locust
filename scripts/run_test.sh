#!/usr/bin/env bash
# ==============================================================================
# Executa um teste automatizado do Locust em modo headless (dentro do Docker)
# e salva o CSV de métricas na pasta results/<maquina>/.
#
# Uso:
#   ./scripts/run_test.sh <maquina> <cenario:1|2|3> <instancias:1|2|3> <usuarios> <spawn_rate> [duracao]
#
# Exemplo:
#   ./scripts/run_test.sh maquina_1 1 3 50 10 60s
#
# Opções extras do Locust podem ser passadas pela variável LOCUST_EXTRA_OPTS
# (ex: LOCUST_EXTRA_OPTS="--reset-stats").
# ==============================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MAQUINA="${1:-maquina_1}"
CENARIO="${2:-1}"
INSTANCIAS="${3:-3}"
USUARIOS="${4:-10}"
SPAWN_RATE="${5:-5}"
DURACAO="${6:-60s}"

OUT_DIR="results/${MAQUINA}"
mkdir -p "$OUT_DIR"

# A duração é a janela de medição: soma-se o tempo da rampa de spawn, que é
# descartado pelo --reset-stats (senão cargas altas ficariam com poucos segundos medidos)
case "$DURACAO" in
    *m) DURACAO_S=$(( ${DURACAO%m} * 60 )) ;;
    *s) DURACAO_S="${DURACAO%s}" ;;
    *)  DURACAO_S="$DURACAO" ;;
esac
RAMPA_S=$(( (USUARIOS + SPAWN_RATE - 1) / SPAWN_RATE ))
RUN_TIME="$(( DURACAO_S + RAMPA_S ))s"

CSV_PREFIX="/results/${MAQUINA}/cenario${CENARIO}_inst${INSTANCIAS}_users${USUARIOS}"

echo "=================================================================="
echo " Máquina:     $MAQUINA"
echo " Cenário:     $CENARIO"
echo " Instâncias:  $INSTANCIAS"
echo " Usuários:    $USUARIOS (Spawn rate: $SPAWN_RATE/s)"
echo " Duração:     $DURACAO de medição + ${RAMPA_S}s de rampa (run-time ${RUN_TIME})"
echo "=================================================================="

# 1. Ajusta o número de instâncias do WordPress e recarrega o Nginx
./scripts/set_instances.sh "$INSTANCIAS"

# 2. Para o container web interativo do Locust (se estiver rodando) para não concorrer na porta
docker compose stop locust >/dev/null 2>&1 || true

# 3. Executa o container do Locust na mesma rede da aplicação (conforme requisitos.txt)
#    O Locust sai com código 1 quando houve qualquer falha; isso não invalida o CSV.
LOCUST_EXIT=0
docker compose run --rm -T \
    -e ATTACKED_HOST="http://nginx" \
    -e LOCUST_FILE="locustfile_cenario${CENARIO}.py" \
    -e LOCUST_OPTS="--headless -u ${USUARIOS} -r ${SPAWN_RATE} --run-time ${RUN_TIME} --csv=${CSV_PREFIX} ${LOCUST_EXTRA_OPTS:-}" \
    locust || LOCUST_EXIT=$?

if [[ ! -f "${OUT_DIR}/cenario${CENARIO}_inst${INSTANCIAS}_users${USUARIOS}_stats.csv" ]]; then
    echo "[ERRO] O Locust terminou (código ${LOCUST_EXIT}) sem gerar o CSV de estatísticas."
    exit 1
fi
if [[ "$LOCUST_EXIT" != "0" ]]; then
    echo "[AVISO] O Locust terminou com código ${LOCUST_EXIT} (houve requisições com falha)."
fi

echo ""
echo "==> Resultados salvos em: ${OUT_DIR}/cenario${CENARIO}_inst${INSTANCIAS}_users${USUARIOS}_stats.csv"
