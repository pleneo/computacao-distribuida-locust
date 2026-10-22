#!/usr/bin/env bash
# ==============================================================================
# Alterna o ambiente entre 1, 2 ou 3 instâncias ativas do WordPress.
# Uso: ./scripts/set_instances.sh <1|2|3>
# ==============================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

N="${1:-3}"

if [[ "$N" != "1" && "$N" != "2" && "$N" != "3" ]]; then
    echo "Uso: $0 <1|2|3>"
    exit 1
fi

echo "==> Configurando arquitetura para $N instância(s) do WordPress..."

# 1. Garante que as instâncias necessárias estão rodando e para as excedentes
if [[ "$N" == "1" ]]; then
    docker compose up -d mysql wordpress1 nginx
    docker compose stop wordpress2 wordpress3
elif [[ "$N" == "2" ]]; then
    docker compose up -d mysql wordpress1 wordpress2 nginx
    docker compose stop wordpress3
elif [[ "$N" == "3" ]]; then
    docker compose up -d mysql wordpress1 wordpress2 wordpress3 nginx
fi

# 2. Atualiza o conteúdo de nginx.conf preservando o inode (para bind mount do Docker)
cat "nginx/nginx.${N}.conf" > nginx.conf

# 3. Recarrega o Nginx sem derrubar conexões
docker exec nginx nginx -s reload

echo "==> Pronto! Nginx balanceando para $N instância(s) do WordPress."
docker compose ps
