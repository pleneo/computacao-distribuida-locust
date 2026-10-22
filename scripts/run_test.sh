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

CSV_PREFIX="/results/${MAQUINA}/cenario${CENARIO}_inst${INSTANCIAS}_users${USUARIOS}"

echo "=================================================================="
echo " Máquina:     $MAQUINA"
echo " Cenário:     $CENARIO"
echo " Instâncias:  $INSTANCIAS"
echo " Usuários:    $USUARIOS (Spawn rate: $SPAWN_RATE/s)"
echo " Duração:     $DURACAO"
echo "=================================================================="

# 1. Ajusta o número de instâncias do WordPress e recarrega o Nginx
./scripts/set_instances.sh "$INSTANCIAS"

# 2. Para o container web interativo do Locust (se estiver rodando) para não concorrer na porta
docker compose stop locust >/dev/null 2>&1 || true

# 3. Executa o container do Locust na mesma rede da aplicação (conforme requisitos.txt)
docker compose run --rm \
    -e ATTACKED_HOST="http://nginx" \
    -e LOCUST_FILE="locustfile_cenario${CENARIO}.py" \
    -e LOCUST_OPTS="--no-web -c ${USUARIOS} -r ${SPAWN_RATE} --run-time ${DURACAO} --csv=${CSV_PREFIX}" \
    locust

echo ""
echo "==> Resultados salvos em: ${OUT_DIR}/cenario${CENARIO}_inst${INSTANCIAS}_users${USUARIOS}_requests.csv"
