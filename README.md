# Testes de Carga com Múltiplas Instâncias do WordPress Utilizando o Locust

> **Disciplina:** Computação Distribuída  
> **Professor:** Prof. Nabor  
> **Trabalho 3:** Avaliação de Desempenho e Testes de Carga com Locust  

---

## 1. Arquitetura do Ambiente

Este repositório expande a arquitetura do **Trabalho 2** (Nginx como *Load Balancer* em *Round-Robin* + até 3 instâncias do WordPress + MySQL 5.7), adicionando o contêiner do **Locust (`grubykarol/locust`)** na mesma rede Docker para geração de carga nos 3 cenários especificados:

```text
locust ──► nginx ──┬──► wordpress1 ──┬──► mysql
                   ├──► wordpress2 ──┤
                   └──► wordpress3 ──┘
```

### Cenários de Teste Configurados Automaticamente:
1. **Cenário 1 (`/?p=1`):** Blog post com uma imagem de aproximadamente **1 MB** (`/wp-content/uploads/img_1mb.bmp`).
2. **Cenário 2 (`/?p=2`):** Blog post com um texto de aproximadamente **400 KB**.
3. **Cenário 3 (`/?p=3`):** Blog post com uma imagem de aproximadamente **300 KB** (`/wp-content/uploads/img_300kb.bmp`).

---

## 2. Estrutura do Repositório

```text
├── docker-compose.yml              # Orquestração: MySQL, WordPress (1..3), Nginx e Locust
├── nginx.conf                      # Configuração ativa do Nginx
├── nginx/
│   ├── nginx.1.conf                # Upstream com 1 instância (wordpress1)
│   ├── nginx.2.conf                # Upstream com 2 instâncias (wordpress1, wordpress2)
│   └── nginx.3.conf                # Upstream com 3 instâncias (wordpress1, wordpress2, wordpress3)
├── locust/
│   ├── locustfile.py               # Script dinâmico (seleciona cenário via env SCENARIO=1|2|3)
│   ├── locustfile_cenario1.py      # Script exclusivo para o Cenário 1 (Imagem ~1MB)
│   ├── locustfile_cenario2.py      # Script exclusivo para o Cenário 2 (Texto ~400KB)
│   └── locustfile_cenario3.py      # Script exclusivo para o Cenário 3 (Imagem ~300KB)
├── scripts/
│   ├── generate_assets.py          # Gera as imagens de 1MB e 300KB e o texto de 400KB
│   ├── setup_wordpress.sh          # Instala o WordPress via WP-CLI e cria os 3 posts automaticamente
│   ├── set_instances.sh            # Alterna entre 1, 2 ou 3 instâncias do WordPress
│   ├── run_test.sh                 # Executa um teste do Locust em modo headless e salva CSV
│   ├── consolidate_csv.py          # Consolida os CSVs do Locust em um único resumo.csv
│   └── plot_results.py             # Gera os gráficos no padrão exigido pelo PDF
├── results/
│   ├── maquina_1/                  # Dados e gráficos coletados na Máquina 1
│   └── maquina_2/                  # Dados e gráficos coletados na Máquina 2
└── DIVISAO_TRABALHO.md             # Guia de divisão de tarefas entre os 3 integrantes
```

---

## 3. Como Executar do Zero (Em Qualquer Máquina)

### Passo 1: Preparar e Popular o WordPress Automaticamente
Não é necessário abrir o navegador para instalar o WordPress nem criar posts manualmente. Basta executar:
```bash
chmod +x scripts/*.sh scripts/*.py
./scripts/setup_wordpress.sh
```
Esse script:
1. Gera a imagem de `1MB`, o texto de `400KB` e a imagem de `300KB` na pasta `assets/`;
2. Sobe `mysql`, `wordpress1`, `wordpress2`, `wordpress3` e `nginx`;
3. Usa o contêiner oficial `wordpress:cli` para instalar o WordPress e criar os posts `/?p=1`, `/?p=2` e `/?p=3`.

### Passo 2: Alternar entre 1, 2 ou 3 Instâncias do WordPress
Para mudar a quantidade de instâncias ativas no balanceador de carga Nginx:
```bash
./scripts/set_instances.sh 1   # Apenas wordpress1 ativo
./scripts/set_instances.sh 2   # wordpress1 e wordpress2 ativos
./scripts/set_instances.sh 3   # wordpress1, wordpress2 e wordpress3 ativos
```

### Passo 3: Calibrar a Carga via Interface Web do Locust
Para descobrir os 3 níveis de carga da máquina (Carga Baixa e Média com **0% de erro**, e Carga Máxima com **até 10% de erro**):
```bash
SCENARIO=1 docker compose up -d locust
```
Acesse **`http://localhost:8089`** no navegador, informe o número de usuários (*Number of users to simulate*) e a taxa de entrada (*Hatch rate*), e observe a coluna **Failures (%)**.

### Passo 4: Rodar Testes Automatizados e Gerar Gráficos
Após descobrir as 3 cargas da máquina (ex: `20`, `60` e `120` usuários), execute:
```bash
# Uso: ./scripts/run_test.sh <maquina> <cenario:1|2|3> <instancias:1|2|3> <usuarios> <spawn_rate> <duracao>
./scripts/run_test.sh maquina_1 1 3 20 5 60s
```
Em seguida, consolide os resultados e gere os gráficos:
```bash
python3 scripts/consolidate_csv.py results/maquina_1
python3 scripts/plot_results.py results/maquina_1/resumo.csv --output-dir results/maquina_1/graficos --maquina-label "Máquina 1"
```
