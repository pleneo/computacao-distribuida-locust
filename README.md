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

### 8.2. Máquina 1 (Ryzen 5 9600X)

*Pendente:* executar os Passos 3 a 5 na Máquina 1 com `--maquina maquina_1`.

---

## 9. Análise e Conclusões (Máquina 2)

1. **Mais instâncias não aumentam a vazão quando todas dividem a mesma CPU.** Com a máquina saturada, o RPS **cai levemente** ao passar de 1 para 3 instâncias (cenário 1: 117 → 109 → 106 req/s) e a latência sobe (6,44 → 7,02 s com 800 usuários). Cada instância adiciona processos Apache/PHP que disputam os mesmos 8 threads, com custo extra de troca de contexto e memória (~1,7 GB por instância). A escalabilidade horizontal só traria ganho com as instâncias em hosts diferentes, ou com folga de CPU no host.

2. **A vazão máxima é fixa; mais usuários só aumentam a fila.** O RPS fica praticamente constante em cada cenário (~117, ~145 e ~185 req/s), enquanto o tempo de resposta cresce de forma linear com o número de usuários (lei de Little: tempo ≈ usuários / vazão). Por isso o limite da máquina é definido pela latência aceitável, ou seja, pelo timeout de 10 s.

3. **O tamanho e o tipo do conteúdo determinam o custo.** O post de 1 MB entrega ~117 req/s, o de texto de 400 KB ~145 req/s e o de 300 KB ~185 req/s. A latência com 800 usuários vai de 6,4 s (1 MB) a 3,9 s (300 KB).

4. **Dimensionar o recurso compartilhado é pré-requisito para escalar** (ver [Seção 6](#6-gargalos-encontrados-e-correções)). Com o `max_connections` padrão do MySQL, adicionar instâncias fazia a taxa de erro saltar de 0% para até 85%.

5. **Reprodutibilidade:** com `setup_wordpress.sh` e o orquestrador `run_all_benchmarks.py`, qualquer integrante reproduz os mesmos cenários e a mesma metodologia. Todos os CSVs brutos do Locust estão versionados em `results/`.
