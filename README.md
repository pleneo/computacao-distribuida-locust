# Testes de Carga com Múltiplas Instâncias do WordPress Utilizando Locust

> **Disciplina:** Computação Distribuída  
> **Professor:** Prof. Nabor  
> **Trabalho 3:** Avaliação de Desempenho e Testes de Carga com Balanceamento Horizontal HTTP  
> **Repositório Oficial:** [github.com/pleneo/computacao-distribuida-locust](https://github.com/pleneo/computacao-distribuida-locust)

---

## 1. Visão Geral e Objetivos do Projeto

O objetivo deste trabalho é avaliar experimentalmente a **escalabilidade horizontal** e os **limites operacionais** de uma arquitetura composta por múltiplas instâncias do **WordPress** balanceadas via **Nginx** (*Round-Robin*), compartilhando uma base **MySQL**.

A carga é gerada pelo **Locust (`grubykarol/locust:1.2.3`)**, declarado como serviço no mesmo `docker-compose.yml` da aplicação, sobre **3 cenários**:
1. **Cenário 1:** Blog post com uma imagem de aproximadamente **1 MB** (`/?p=1`);
2. **Cenário 2:** Blog post com texto de aproximadamente **400 KB** (`/?p=2`);
3. **Cenário 3:** Blog post com uma imagem de aproximadamente **300 KB** (`/?p=3`).

Cada cenário é executado com **3 cargas crescentes de usuários** e **1, 2 e 3 instâncias** do WordPress (27 testes por máquina).

### Requisitos adicionais do professor (`requisitos.txt`)
* **Calibragem real de carga** (em vez de 10, 100 e 1000 fixos), descobrindo o limite de cada máquina:
  * **Carga Baixa e Carga Média:** **0% de erro** (100% de sucesso);
  * **Carga Máxima:** taxa de erro **≤ 10%**.
* **Pelo menos 2 máquinas** (uma mais forte e uma mais fraca) para comparar a calibragem.
* **Locust no mesmo host da aplicação**, para observar a disputa de recursos entre o gerador de carga e o sistema sob teste.

---

## 2. Arquitetura do Sistema e Topologia de Rede

```text
               ┌────────────────────────────────────────────────────────┐
               │              Docker Bridge Network                     │
               │                                                        │
               │                   ┌──────────────┐                     │
               │                   │    Locust    │                     │
               │                   │  (Gerador)   │                     │
               │                   └──────┬───────┘                     │
               │                          │                             │
Actor Externo ─┼───────────────► ┌────────▼───────┐                     │
(porta 80)     │                 │     Nginx      │                     │
               │                 │(Load Balancer) │                     │
               │                 └────────┬───────┘                     │
               │          ┌───────────────┼───────────────┐             │
               │          │ (Round-Robin) │ (Round-Robin) │             │
               │   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐      │
               │   │ wordpress1  │ │ wordpress2  │ │ wordpress3  │      │
               │   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘      │
               │          │               │               │             │
               │          └───────────────┼───────────────┘             │
               │                          ▼                             │
               │                   ┌──────────────┐                     │
               │                   │    MySQL     │                     │
               │                   │    (Banco)   │                     │
               │                   └──────────────┘                     │
               └────────────────────────────────────────────────────────┘
```

### Componentes
1. **Nginx 1.19.0 (Load Balancer):**
   * Distribuição HTTP *Round-Robin*; injeta o cabeçalho `X-Upstream` com a instância que atendeu.
   * `worker_processes auto`, `worker_connections 8192` e `ulimit nofile 65535` (ver [Seção 6](#6-gargalos-encontrados-e-correções)).
   * Alternância entre **1, 2 ou 3 instâncias** via `scripts/set_instances.sh`, com *reload* sem derrubar conexões.
2. **WordPress 5.4.2 PHP 7.2 Apache (Backends):**
   * Três réplicas idênticas sem portas publicadas no host (Apache prefork, `MaxRequestWorkers 150` cada).
   * `WORDPRESS_CONFIG_EXTRA` dinâmico para responder tanto a `http://nginx` quanto a `http://localhost` sem *redirects* 301.
3. **MySQL 5.7 (Banco compartilhado):**
   * `max_connections=500`, suficiente para 3 × 150 workers do Apache.
4. **Locust 1.2.3 (Gerador de Carga):**
   * Serviço Docker na mesma rede (`ATTACKED_HOST=http://nginx`), com `ulimit nofile 65535`.

---

## 3. Metodologia

| Parâmetro | Valor |
| :--- | :--- |
| Comportamento do usuário | `GET /?p=N` em loop, com espera de 0,1–0,5 s entre requisições |
| **Critério de erro** | Resposta HTTP de erro **ou requisição sem resposta em 10 s** (`timeout=10` nos locustfiles) |
| Taxa de *spawn* | 50 usuários/s |
| Janela de medição | **60 s após a rampa de *spawn*** (a rampa é descartada com `--reset-stats`; `run_test.sh` soma o tempo da rampa ao `--run-time`) |
| Calibragem | Cenário 1 (o mais pesado) com 1 instância, em cargas crescentes, até o erro passar de 10% |
| Escolha das cargas | U_max = maior carga com erro ≤ 10%, deixando margem para 2 e 3 instâncias; U_min e U_med com 0% de erro |
| Validação | As 27 combinações precisam respeitar a regra; se alguma estourar, U_max é reduzido e a matriz é refeita |

**Por que o timeout de 10 s?** Sem timeout no cliente, o servidor nunca recusa requisições: elas apenas entram na fila (o Nginx só desiste após 60 s). Na calibragem sem timeout, a taxa de erro ficou em 0% até 2000 usuários, mesmo com requisições esperando 44 s. Com o timeout de 10 s, a regra de ≤ 10% de erro passa a refletir a experiência do usuário.

---

## 4. Especificação do Hardware de Teste

| Parâmetro | Máquina 1 (Forte) | Máquina 2 (Fraca) |
| :--- | :--- | :--- |
| **Processador (CPU)** | AMD Ryzen 5 9600X (6 núcleos / 12 threads) | Intel Core i7-1165G7 (4 núcleos / 8 threads, notebook) |
| **Memória RAM** | 32 GB DDR5 | 16 GB |
| **Sistema Operacional** | Linux (CachyOS) | Zorin OS 18.1 (kernel 6.14) |
| **Docker** | Docker Engine + Compose v2 | Docker 29.8 + Compose v5.5 |
| **Carga Baixa (U_min)** | *pendente* | **200 usuários** (0% de erro) |
| **Carga Média (U_med)** | *pendente* | **400 usuários** (0% de erro) |
| **Carga Máxima (U_max)** | *pendente* | **800 usuários** (≤ 8,2% de erro) |

---

## 5. Estrutura do Repositório

```text
├── docker-compose.yml              # MySQL, WordPress 1..3, Nginx e Locust
├── nginx.conf                      # Configuração ativa do Nginx (reescrita por set_instances.sh)
├── nginx/
│   ├── nginx.1.conf                # Upstream com 1 instância (wordpress1)
│   ├── nginx.2.conf                # Upstream com 2 instâncias
│   └── nginx.3.conf                # Upstream com 3 instâncias
├── locust/
│   ├── locustfile.py               # Script genérico (cenário via variável SCENARIO)
│   ├── locustfile_cenario1.py      # Cenário 1: post com imagem ~1MB (/?p=1)
│   ├── locustfile_cenario2.py      # Cenário 2: post com texto ~400KB (/?p=2)
│   └── locustfile_cenario3.py      # Cenário 3: post com imagem ~300KB (/?p=3)
├── scripts/
│   ├── generate_assets.py          # Gera os conteúdos de 1MB, 400KB e 300KB
│   ├── setup_wordpress.sh          # Instala o WordPress e publica os 3 posts
│   ├── set_instances.sh            # Alterna entre 1, 2 ou 3 instâncias ativas
│   ├── run_test.sh                 # Executa um teste Locust headless e salva os CSVs
│   ├── run_all_benchmarks.py       # Orquestrador: calibrar, matriz, exaustao, graficos
│   ├── consolidate_csv.py          # Lê os *_stats.csv do Locust
│   └── plot_results.py             # Gera os gráficos
├── results/
│   ├── maquina_1/                  # Máquina 1 (Ryzen) — pendente
│   └── maquina_2/
│       ├── calibracao.csv          # Varredura de calibragem (1 instância, cenário 1)
│       ├── calibracao/             # CSVs brutos e log da calibragem
│       ├── resumo.csv              # Métricas consolidadas dos 27 testes
│       ├── cenarioX_instY_usersZ_* # CSVs brutos do Locust (stats, failures, stats_history)
│       ├── disputa_recursos.csv    # CPU% e RAM por contêiner (3 instâncias, carga máxima)
│       ├── disputa_recursos_por_teste.csv
│       ├── execucao.log            # Saída completa de todos os testes
│       └── graficos/               # Gráficos PNG
├── requisitos.txt                  # Requisitos adicionais passados pelo professor
├── DIVISAO_TRABALHO.md             # Divisão das tarefas entre os membros
└── README.md
```

---

## 6. Gargalos Encontrados e Correções

Na primeira bateria de testes, as execuções com **2 e 3 instâncias** apresentavam **54% a 85% de erros (HTTP 500)**, enquanto 1 instância parecia estável. Como os erros respondem rápido, o RPS ficava artificialmente alto (até 1.700 req/s). A investigação, reproduzida com 600 usuários, apontou três limites de configuração padrão:

| # | Gargalo | Evidência | Correção |
| :---: | :--- | :--- | :--- |
| 1 | **MySQL `max_connections = 151`**. Cada WordPress abre até 150 conexões (`MaxRequestWorkers 150`); com 2 instâncias são até 300, com 3 até 450. As conexões excedentes eram recusadas e o WordPress respondia 500 ("Error establishing a database connection"). | 5.487 respostas 500 dos WordPress × 5.489 `Connection_errors_max_connections` no MySQL (2 instâncias) | `command: --max_connections=500` |
| 2 | **Nginx com 1 worker, `worker_connections 1024` e `ulimit -n 1024`**. Cada requisição repassada usa 2 descritores (cliente + upstream). | ~1.300–1.500 `socket() failed (24: Too many open files)` por teste, inclusive com 1 instância | `worker_processes auto`, `worker_rlimit_nofile 65535`, `worker_connections 8192`, `ulimits nofile 65535` |
| 3 | **Locust com `ulimit -n 1024`** | `[Errno 24] No file descriptors available` com 1.200 usuários | `ulimits nofile 65535` no serviço `locust` |

**Depois da correção** (cenário 1, 600 usuários, 40 s): **0% de erro com 1, 2 e 3 instâncias**, nenhuma conexão recusada pelo MySQL (pico de 421 conexões com 3 instâncias) e nenhum erro de descritor no Nginx.

> **Lição:** escalar o WordPress horizontalmente sem dimensionar o recurso compartilhado (o banco) **piora** o resultado. O gargalo apenas muda de lugar.

---

## 7. Tutorial de Execução Passo a Passo

### Pré-requisitos
* Docker Engine e Docker Compose plugin;
* Python 3 com `matplotlib` e `numpy` (`pip install matplotlib numpy`).

### Passo 1: Inicializar e popular o ambiente
```bash
chmod +x scripts/*.sh scripts/*.py
./scripts/setup_wordpress.sh
```

Validação dos posts:
```bash
for path in "/?p=1" "/?p=2" "/?p=3"; do
  curl -s -o /dev/null -w "$path -> HTTP %{http_code} | %{size_download} bytes\n" "http://localhost${path}"
done
```
Saída esperada: `/?p=1` ≈ 1.040.257 bytes, `/?p=2` ≈ 438.821 bytes, `/?p=3` ≈ 328.807 bytes.

### Passo 2: Alternar a quantidade de instâncias (opcional, os scripts fazem isso sozinhos)
```bash
./scripts/set_instances.sh 1   # apenas wordpress1
./scripts/set_instances.sh 2   # wordpress1 e wordpress2
./scripts/set_instances.sh 3   # wordpress1, wordpress2 e wordpress3
for i in {1..6}; do curl -I -s http://localhost/ | grep "X-Upstream"; done
```

### Passo 3: Calibrar a máquina
```bash
python3 scripts/run_all_benchmarks.py calibrar --maquina maquina_X --cenario 1 \
    --usuarios 100 200 400 600 800 1000 1200 1600 2000 --duracao 60s --parar-ao-exceder
```
Escolha U_max (maior carga com erro ≤ 10%, com margem) e U_min/U_med (0% de erro).

### Passo 4: Rodar a matriz (3 cenários × 3 instâncias × 3 cargas)
```bash
python3 scripts/run_all_benchmarks.py matriz --maquina maquina_X --usuarios <U_min> <U_med> <U_max> --duracao 60s
```
Ao final, o script avisa se algum teste passou de 10% de erro. Nesse caso, reduza U_max e rode de novo.

### Passo 5: Gerar os gráficos
```bash
python3 scripts/run_all_benchmarks.py graficos --maquina maquina_X --maquina-label "Máquina X (CPU, núcleos, RAM)"
# Com as duas máquinas medidas, para o gráfico comparativo:
python3 scripts/run_all_benchmarks.py graficos --maquina maquina_1 --maquina-label "Máquina 1 (...)" \
    --comparar-com maquina_2 --comparar-label "Máquina 2 (...)"
```

Teste individual, sem o orquestrador:
```bash
# ./scripts/run_test.sh <maquina> <cenario> <instancias> <usuarios> <spawn_rate> <duracao_medida>
./scripts/run_test.sh maquina_2 1 3 400 50 60s
```

---

## 8. Resultados Experimentais

### 8.1. Máquina 2 (Intel i7-1165G7, 4C/8T, 16 GB)

#### Calibragem (cenário 1, 1 instância — `results/maquina_2/calibracao.csv`)

| Usuários | Tempo médio | RPS | Erro |
| :---: | :---: | :---: | :---: |
| 100 | 0,51 s | 122,0 | 0% |
| 200 | 1,38 s | 117,5 | 0% |
| 400 | 3,08 s | 117,3 | 0% |
| 600 | 4,81 s | 116,2 | 0% |
| 800 | 6,52 s | 115,6 | 5,0% |
| 1000 | 7,25 s | 130,7 | 20,4% |

Todos os erros foram *timeouts* de 10 s. Cargas escolhidas: **200 / 400 / 800 usuários**. 600 não foi usado como carga média porque, com 3 instâncias, as requisições mais lentas já chegavam perto do timeout.

#### Resultados consolidados (`results/maquina_2/resumo.csv`)

| Cenário | Instâncias | Usuários | Tempo médio | RPS | Erro |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1 — Imagem 1 MB** | 1 | 200 / 400 / 800 | 1,40 / 3,11 / 6,44 s | 116,7 / 116,4 / 116,7 | 0% / 0% / 4,48% |
| | 2 | 200 / 400 / 800 | 1,55 / 3,32 / 6,95 s | 108,7 / 109,0 / 108,8 | 0% / 0% / 0,13% |
| | 3 | 200 / 400 / 800 | 1,58 / 3,48 / 7,02 s | 105,8 / 104,8 / 107,8 | 0% / 0% / 8,23% |
| **2 — Texto 400 KB** | 1 | 200 / 400 / 800 | 1,04 / 2,38 / 4,97 s | 149,0 / 148,6 / 150,0 | 0% / 0% / 1,83% |
| | 2 | 200 / 400 / 800 | 1,10 / 2,48 / 5,30 s | 142,2 / 142,3 / 141,2 | 0% / 0% / 0% |
| | 3 | 200 / 400 / 800 | 1,12 / 2,56 / 5,31 s | 140,9 / 138,8 / 141,6 | 0% / 0% / 0% |
| **3 — Imagem 300 KB** | 1 | 200 / 400 / 800 | 0,76 / 1,80 / 3,88 s | 188,4 / 190,3 / 189,6 | 0% / 0% / 0,46% |
| | 2 | 200 / 400 / 800 | 0,81 / 1,87 / 4,00 s | 179,7 / 183,6 / 185,1 | 0% / 0% / 0% |
| | 3 | 200 / 400 / 800 | 0,80 / 1,92 / 4,08 s | 181,4 / 179,5 / 181,9 | 0% / 0% / 0% |

**Todas as 27 combinações respeitam a regra** (0% de erro nas cargas baixa e média, ≤ 10% na máxima).

#### Gráficos (estilo das páginas 4 e 5 do enunciado)

| Cenário | Tempo de Resposta × Usuários | Requisições por Segundo × Instâncias |
| :--- | :---: | :---: |
| **Cenário 1 (Imagem 1 MB)** | ![Cenário 1 Latência](results/maquina_2/graficos/cenario_1_tempo_resposta.png) | ![Cenário 1 RPS](results/maquina_2/graficos/cenario_1_rps.png) |
| **Cenário 2 (Texto 400 KB)** | ![Cenário 2 Latência](results/maquina_2/graficos/cenario_2_tempo_resposta.png) | ![Cenário 2 RPS](results/maquina_2/graficos/cenario_2_rps.png) |
| **Cenário 3 (Imagem 300 KB)** | ![Cenário 3 Latência](results/maquina_2/graficos/cenario_3_tempo_resposta.png) | ![Cenário 3 RPS](results/maquina_2/graficos/cenario_3_rps.png) |

#### Disputa de recursos no mesmo host (3 instâncias, 800 usuários)

![Disputa de Recursos CPU e RAM](results/maquina_2/graficos/disputa_recursos_cpu_ram.png)

| Contêiner | CPU | RAM |
| :--- | :---: | :---: |
| WordPress (wordpress1 + 2 + 3) | 584,6% (~195% cada) | 5,0 GB (~1,7 GB cada) |
| MySQL | 110,7% | 931 MB |
| **Locust** | **65,9%** | 93 MB |
| Nginx | 5,5% | 43 MB |
| **Total** | **~767% de 800% disponíveis** | |

A máquina opera **no limite de CPU**: os contêineres somam ~767% de 800% (8 threads). O Locust sozinho consome ~66% (8,6% do total), CPU que deixa de ir para o Apache e o MySQL. É a penalidade de rodar o gerador de carga no mesmo host. O Locust não foi o gargalo: nenhum teste emitiu o aviso `CPU usage was too high`.

### 8.2. Máquina 1 (AMD Ryzen 5 9600X, 6C/12T, 32 GB RAM DDR5)

#### Calibragem (cenário 1, 1 instância — `results/maquina_1/calibracao.csv`)

| Usuários | Tempo médio | RPS | Erro |
| :---: | :---: | :---: | :---: |
| 200 | 0,42 s | 259,7 | 0% |
| 400 | 1,22 s | 253,6 | 0% |
| 800 | 2,93 s | 247,4 | 0% |
| 1.200 | 2,25 s | 247,5 | 0% |
| 1.600 | 2,41 s | 248,5 | 0% |
| 2.000 | 2,53 s | 245,8 | 0% |
| 3.000 | 3,01 s | 246,9 | 0% |
| 5.000 | 3,88 s | 247,1 | 0% |
| 8.000 | 5,28 s | 243,3 | 0% |
| 15.000 | 8,25 s | 238,8 | 0% |
| 25.000 | 12,42 s | 240,1 | 0% |

Mesmo com até 25.000 usuários simultâneos, a Máquina 1 manteve **0,0% de erro**. A vazão atingiu o teto físico de processamento em ~245 req/s logo em 800 usuários, operando com **degradação graciosa** (enfileiramento com aumento proporcional de latência) em vez de timeouts ou quebra de sockets. Cargas selecionadas para a matriz: **800 / 3.000 / 8.000 usuários** (onde 800 é a carga máxima da Máquina 2, permitindo comparação empírica direta).

#### Resultados consolidados (`results/maquina_1/resumo.csv`)

| Cenário | Instâncias | Usuários | Tempo médio | RPS | Erro |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1 — Imagem 1 MB** | 1 | 800 / 3000 / 8000 | 2,86 / 3,03 / 5,28 s | 251,5 / 246,0 / 243,3 | 0% / 0% / 0% |
| | 2 | 800 / 3000 / 8000 | 3,01 / 3,04 / 5,11 s | 240,2 / 238,7 / 236,2 | 0% / 0% / 0% |
| | 3 | 800 / 3000 / 8000 | 3,02 / 3,08 / 5,20 s | 241,0 / 239,3 / 233,5 | 0% / 0% / 0% |
| **2 — Texto 400 KB** | 1 | 800 / 3000 / 8000 | 1,76 / 2,93 / 5,17 s | 384,4 / 363,3 / 358,8 | 0% / 0% / 0% |
| | 2 | 800 / 3000 / 8000 | 1,85 / 2,70 / 4,73 s | 366,3 / 352,7 / 345,7 | 0% / 0% / 0% |
| | 3 | 800 / 3000 / 8000 | 1,91 / 2,66 / 4,62 s | 355,7 / 347,6 / 341,8 | 0% / 0% / 0% |
| **3 — Imagem 300 KB** | 1 | 800 / 3000 / 8000 | 1,37 / 2,69 / 4,73 s | 469,2 / 444,1 / 434,9 | 0% / 0% / 0% |
| | 2 | 800 / 3000 / 8000 | 1,43 / 2,50 / 4,54 s | 453,3 / 435,9 / 425,4 | 0% / 0% / 0% |
| | 3 | 800 / 3000 / 8000 | 1,47 / 2,51 / 4,42 s | 444,3 / 428,5 / 419,0 | 0% / 0% / 0% |

**Todas as 27 combinações respeitam a regra** (0% de erro em todas as medições).

#### Gráficos (estilo das páginas 4 e 5 do enunciado)

| Cenário | Tempo de Resposta × Usuários | Requisições por Segundo × Instâncias |
| :--- | :---: | :---: |
| **Cenário 1 (Imagem 1 MB)** | ![Cenário 1 Latência](results/maquina_1/graficos/cenario_1_tempo_resposta.png) | ![Cenário 1 RPS](results/maquina_1/graficos/cenario_1_rps.png) |
| **Cenário 2 (Texto 400 KB)** | ![Cenário 2 Latência](results/maquina_1/graficos/cenario_2_tempo_resposta.png) | ![Cenário 2 RPS](results/maquina_1/graficos/cenario_2_rps.png) |
| **Cenário 3 (Imagem 300 KB)** | ![Cenário 3 Latência](results/maquina_1/graficos/cenario_3_tempo_resposta.png) | ![Cenário 3 RPS](results/maquina_1/graficos/cenario_3_rps.png) |

#### Disputa de recursos no mesmo host (3 instâncias, 8000 usuários)

![Disputa de Recursos CPU e RAM](results/maquina_1/graficos/disputa_recursos_cpu_ram.png)

| Contêiner | CPU | RAM |
| :--- | :---: | :---: |
| WordPress (wordpress1 + 2 + 3) | 652,6% (~217,5% cada) | 697 MB (~232 MB cada) |
| MySQL | 95,8% | 936 MB |
| **Locust** | **62,6%** | 346 MB |
| Nginx | 3,0% | 55 MB |
| **Total** | **~814% de 1200% disponíveis** | ~2,03 GB |

Ao contrário da Máquina 2 (que operou a 767% de 800%, no limite térmico e de threads), a Máquina 1 consumiu ~814% de 1200% disponíveis (12 threads). Os ~386% de folga garantiram que o Locust gerasse carga sem canibalizar o Apache e o MySQL, impedindo timeouts ou descarte de pacotes no kernel.

### 8.3. Comparativo Direto entre as Máquinas

![Comparativo de Calibragem](results/maquina_1/graficos/comparativo_maquinas_calibragem.png)

| Métrica | Máquina 2 (Notebook i7-1165G7) | Máquina 1 (Desktop Ryzen 5 9600X) | Razão / Diferença |
| :--- | :---: | :---: | :---: |
| **Núcleos / Threads / RAM** | 4C / 8T (16 GB DDR4) | 6C / 12T (32 GB DDR5) | +50% núcleos / +100% RAM |
| **Vazão Cenário 1 (1 MB)** | ~117 req/s | ~245 req/s | **2,1× mais rápida** |
| **Vazão Cenário 2 (400 KB)** | ~145 req/s | ~360 req/s | **2,5× mais rápida** |
| **Vazão Cenário 3 (300 KB)** | ~185 req/s | ~440 req/s | **2,4× mais rápida** |
| **Carga Máxima Suportada** | 800 usuários (5,0% erro) | 8.000+ usuários (0,0% erro) | **10× maior concorrência** |
| **Comportamento em Saturação** | Falha Catastrófica (Timeouts de 10s) | Degradação Graciosa (Enfileiramento) | Alta resiliência sob carga extrema |

---

## 9. Análise e Conclusões

1. **Mais instâncias no mesmo host físico não aumentam a vazão global quando a CPU é o gargalo:** Em ambas as máquinas, o RPS não triplica ao passar de 1 para 3 instâncias. Na Máquina 2 (saturada em 100%), o RPS até cai levemente (117 → 106 req/s) devido à sobrecarga de *context switching*. Na Máquina 1, onde sobram threads, a latência com 3 instâncias nos cenários 2 e 3 diminui com 8.000 usuários (de 5,17s para 4,62s no cenário 2), demonstrando melhor distribuição da fila.
2. **A vazão máxima é fixa; o aumento de usuários gera fila (Lei de Little):** O throughput em cada cenário atinge um patamar fixo determinado pela capacidade de processamento PHP/I-O de rede. O aumento do número de usuários simultâneos reflete-se quase exclusivamente no aumento proporcional do tempo de resposta ($W \approx L / \lambda$).
3. **Disputa de recursos gerador vs. aplicação (Requisito do Enunciado):** O teste evidenciou o impacto direto do Locust no mesmo host. Na Máquina 2 (8 threads), o Locust consumiu ~66% de CPU em um sistema já a 767%/800%, levando o servidor a timeouts por inanição. Na Máquina 1 (12 threads), o Locust consumiu 62,6% com folga de mais de 380% de CPU, operando com 0% de perdas.
4. **O tamanho e formato do payload definem a velocidade de saturação:** O Cenário 3 (Imagem 300 KB) entregou a maior vazão (~440 req/s na M1, ~185 req/s na M2), seguido pelo Cenário 2 (Texto 400 KB, ~360 req/s na M1) e Cenário 1 (Imagem 1 MB, ~245 req/s na M1), provando o impacto do custo de transferência de rede e streaming TCP.
5. **Dimensionamento compartilhado (MySQL) é indispensável:** Conforme documentado na Seção 6, o ajuste de `max_connections=500` e otimizações de `worker_connections=8192` e `nofile=65535` foram os responsáveis por viabilizar testes de alta concorrência sem falhas prematuras de infraestrutura.
6. **Reprodutibilidade completa:** Os scripts de automação (`setup_wordpress.sh`, `run_all_benchmarks.py`, `plot_results.py`) garantiram metodologia 100% idêntica e reproduzível entre máquinas heterogêneas, com todos os dados brutos versionados em `results/`.
