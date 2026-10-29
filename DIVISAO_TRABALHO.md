# Divisão de Tarefas — Trabalho 3 (Testes de Carga com Locust e WordPress)

A infraestrutura, a metodologia, a **Máquina 1 (Ryzen 5 9600X)**, a **Máquina 2 (i7-1165G7)** e a **análise comparativa final** estão 100% concluídas e documentadas no repositório.

---

## ✅ O que já está pronto

- [x] `docker-compose.yml` com MySQL, 3 instâncias de WordPress, Nginx e Locust na mesma rede.
- [x] Correção dos gargalos: MySQL `max_connections=500`, Nginx com `worker_processes auto` / `worker_connections 8192` e `ulimit nofile 65535` no Nginx e no Locust.
- [x] Locustfiles com **timeout de 10 s** (requisição sem resposta em 10 s conta como erro).
- [x] `scripts/run_test.sh` mede **60 s após a rampa** de spawn e encerra contêineres de forma limpa.
- [x] `scripts/run_all_benchmarks.py` com os subcomandos `calibrar`, `matriz`, `exaustao` e `graficos`.
- [x] **Máquina 2 (Intel i7-1165G7, 4C/8T, 16 GB):** calibragem, matriz de 27 testes (todos dentro da regra), CSVs brutos, disputa de recursos e gráficos em `results/maquina_2/`.
- [x] **Máquina 1 (AMD Ryzen 5 9600X, 6C/12T, 32 GB):** calibragem (200 a 25.000 usuários), matriz de 27 testes (800 / 3000 / 8000, 0% erro em todos), disputa de recursos e gráficos em `results/maquina_1/`.
- [x] `README.md` completo com metodologia, gargalos encontrados, resultados de ambas as máquinas e análise comparativa de desempenho e escalabilidade horizontal.

---

## 📌 Regras do Professor (`requisitos.txt`)

1. **Calibragem da carga** (em vez de 10, 100 e 1000 fixos):
   - **Carga Baixa ($U_{min}$) e Carga Média ($U_{med}$):** **0% de erro**.
   - **Carga Máxima ($U_{max}$):** erro de até 10%, **nunca acima de 10%**.
   - A regra vale para **todas as 27 combinações** (3 cenários × 3 instâncias × 3 cargas).
2. **Pelo menos 2 máquinas** (uma forte e uma fraca).
3. **Locust no mesmo host da aplicação**, para analisar a disputa de recursos.

---

## 👥 Tarefas Executadas

### 👤 Pessoa 1 — Máquina 1 (Ryzen 5 9600X) ✅ Concluído
- Hardware: AMD Ryzen 5 9600X (6C/12T), 32 GB RAM DDR5, CachyOS Linux.
- Calibragem: 200 a 25.000 usuários testados sem erros. Cargas selecionadas: **800 / 3.000 / 8.000 usuários**.
- Matriz dos 27 testes executada com 0,0% de erro em todas as medições.
- Gráficos e dados de disputa de recursos gerados e versionados em `results/maquina_1/`.

### 👤 Pessoa 2 — Máquina 2 (Intel i7-1165G7) ✅ Concluído
- Hardware: Intel Core i7-1165G7 (4C/8T), 16 GB RAM, Zorin OS Linux.
- Calibragem: cargas de **200 / 400 / 800 usuários** (800 usuários atingiu 5,0% a 8,2% de erro).
- Matriz dos 27 testes executada e versionada em `results/maquina_2/`.

### 👤 Pessoa 3 — Análise comparativa e documentação ✅ Concluído
- Seções 4, 8.2 e 8.3 do `README.md` preenchidas com as tabelas de ambas as máquinas.
- Gráficos comparativos de tempo de resposta, RPS e disputa de recursos inseridos.
- Seção 9 consolidada com as 6 conclusões científicas sobre limites físicos, Lei de Little e escalabilidade horizontal.

---

## 📊 Resumo de Status

| Integrante | Responsabilidade | Status |
| :--- | :--- | :--- |
| **Pessoa 1** | Calibrar e testar na **Máquina 1 (Ryzen 5 9600X)** | ✅ Concluído |
| **Pessoa 2** | Calibrar e testar na **Máquina 2 (i7-1165G7)** | ✅ Concluído |
| **Pessoa 3** | Análise comparativa + fechamento do README | ✅ Concluído |
