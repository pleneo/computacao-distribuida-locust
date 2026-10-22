#!/usr/bin/env bash
# ==============================================================================
# Inicializa automaticamente o WordPress e cria os 3 cenários de teste:
#   - /?p=1 -> Cenário 1: Post com imagem de ~1MB
#   - /?p=2 -> Cenário 2: Post com texto de ~400KB
#   - /?p=3 -> Cenário 3: Post com imagem de ~300KB
# ==============================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> 1. Gerando arquivos dos 3 cenários (1MB img, 400KB txt, 300KB img)..."
python3 scripts/generate_assets.py

echo "==> 2. Subindo containers base (mysql, wordpress1..3, nginx)..."
docker compose up -d mysql wordpress1 wordpress2 wordpress3 nginx

echo "==> 3. Aguardando o MySQL ficar pronto..."
until docker exec mysql mysqladmin ping -h"localhost" -u"wordpress" -p"wordpresspassword" --silent >/dev/null 2>&1; do
    printf "."
    sleep 2
done
echo " MySQL pronto!"

echo "==> 4. Copiando arquivos para /var/www/html/wp-content/uploads/..."
docker exec wordpress1 mkdir -p /var/www/html/wp-content/uploads
docker cp assets/img_1mb.bmp wordpress1:/var/www/html/wp-content/uploads/img_1mb.bmp
docker cp assets/img_300kb.bmp wordpress1:/var/www/html/wp-content/uploads/img_300kb.bmp
docker cp assets/post1_1mb.html wordpress1:/var/www/html/wp-content/uploads/post1_1mb.html
docker cp assets/texto_400kb.html wordpress1:/var/www/html/wp-content/uploads/texto_400kb.html
docker cp assets/post3_300kb.html wordpress1:/var/www/html/wp-content/uploads/post3_300kb.html
docker exec wordpress1 chown -R www-data:www-data /var/www/html/wp-content/uploads

WP_CLI="docker run --rm --user 33:33 --volumes-from wordpress1 --network container:wordpress1 wordpress:cli"

echo "==> 5. Instalando e configurando o WordPress via WP-CLI..."
if ! $WP_CLI wp core is-installed 2>/dev/null; then
    $WP_CLI wp core install \
        --url="http://localhost" \
        --title="Sistemas Distribuidos" \
        --admin_user="admin" \
        --admin_password="adminpassword" \
        --admin_email="admin@example.com" \
        --skip-email
fi

# Configura permalinks simples (/?p=1, /?p=2, /?p=3) para evitar redirects 301
$WP_CLI wp option update permalink_structure ""

echo "==> 6. Configurando os 3 posts dos cenários (/?p=1, /?p=2, /?p=3)..."

# Cenário 1: Post ID 1 (Imagem de ~1MB)
$WP_CLI wp post update 1 \
    --post_type=post \
    --post_status=publish \
    --post_title="Cenário 1: Blog Post com Imagem de 1MB" \
    /var/www/html/wp-content/uploads/post1_1mb.html

# Cenário 2: Post ID 2 (Texto de ~400KB)
$WP_CLI wp post update 2 \
    --post_type=post \
    --post_status=publish \
    --post_title="Cenário 2: Blog Post com Texto de 400KB" \
    /var/www/html/wp-content/uploads/texto_400kb.html

# Cenário 3: Post ID 3 (Imagem de ~300KB)
$WP_CLI wp post update 3 \
    --post_type=post \
    --post_status=publish \
    --post_title="Cenário 3: Blog Post com Imagem de 300KB" \
    /var/www/html/wp-content/uploads/post3_300kb.html

echo ""
echo "=================================================================="
echo " Setup concluído com sucesso!"
echo " - Cenário 1 (Imagem 1MB):   http://localhost/?p=1"
echo " - Cenário 2 (Texto 400KB):  http://localhost/?p=2"
echo " - Cenário 3 (Imagem 300KB): http://localhost/?p=3"
echo " - Painel Web do Locust:     http://localhost:8089"
echo "=================================================================="
