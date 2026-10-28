# Divisão de Tarefas — Trabalho 3 (Testes de Carga com Locust e WordPress)

A infraestrutura, a metodologia e a **Máquina 2 (fraca)** estão prontas. **Falta medir a Máquina 1 (Ryzen 5 9600X)** e fechar a análise comparativa entre as duas máquinas.

> ⚠️ **Antes de testar, atualize o repositório (`git pull`).** A versão anterior tinha limites de configuração que geravam 54% a 85% de erros com 2 e 3 instâncias (ver seção 6 do `README.md`). Resultados obtidos com o código antigo **não servem** e não são comparáveis com os da Máquina 2.

---

## ✅ O que já está pronto

- [x] `docker-compose.yml` com MySQL, 3 instâncias de WordPress, Nginx e Locust na mesma rede.
- [x] Correção dos gargalos: MySQL `max_connections=500`, Nginx com `worker_processes auto` / `worker_connections 8192` e `ulimit nofile 65535` no Nginx e no Locust.
- [x] Locustfiles com **timeout de 10 s** (requisição sem resposta em 10 s conta como erro).
- [x] `scripts/run_test.sh` mede **60 s após a rampa** de spawn.
- [x] `scripts/run_all_benchmarks.py` com os subcomandos `calibrar`, `matriz`, `exaustao` e `graficos`.
- [x] **Máquina 2 (Intel i7-1165G7, 4C/8T, 16 GB):** calibragem, matriz de 27 testes (todos dentro da regra), CSVs brutos, disputa de recursos e gráficos em `results/maquina_2/`.
- [x] `README.md` com metodologia, gargalos encontrados, resultados e análise da Máquina 2.

---

## 📌 Regras do Professor (`requisitos.txt`)

1. **Calibragem da carga** (em vez de 10, 100 e 1000 fixos):
   - **Carga Baixa ($U_{min}$) e Carga Média ($U_{med}$):** **0% de erro**.
   - **Carga Máxima ($U_{max}$):** erro perto de 10%, **nunca acima de 10%**.
   - A regra vale para **todas as 27 combinações** (3 cenários × 3 instâncias × 3 cargas).
2. **Pelo menos 2 máquinas** (uma forte e uma fraca).
3. **Locust no mesmo host da aplicação**, para analisar a disputa de recursos.

---

## 👥 O que falta fazer

### 👤 Pessoa 1 — Testes na Máquina 1 (Ryzen 5 9600X)

1. **Atualizar o repositório e subir o ambiente:**
   ```bash
   git pull
   ./scripts/setup_wordpress.sh
   ```
   Se o ambiente já existia, recrie MySQL e Nginx para aplicar a configuração nova:
   ```bash
   docker compose up -d --force-recreate mysql nginx
   ```
2. **Anotar o hardware:** CPU (núcleos/threads), RAM, sistema operacional e versão do Docker.
3. **Calibrar** (cenário 1, 1 instância; a varredura para sozinha quando o erro passa de 10%):
   ```bash
   python3 scripts/run_all_benchmarks.py calibrar --maquina maquina_1 --cenario 1 \
       --usuarios 200 400 800 1200 1600 2000 2500 3000 --duracao 60s --parar-ao-exceder
   ```
   - Se o erro passar de 10% logo no início, refine com cargas intermediárias.
   - **U_max:** a maior carga com erro ≤ 10%, **com folga**. Com 3 instâncias a latência é um pouco maior. Na Máquina 2, o erro com 800 usuários foi de 5,0% com 1 instância e 8,2% com 3.
   - **U_min e U_med:** cargas com 0% de erro (ex.: ~25% e ~50% de U_max).
4. **Rodar a matriz (27 testes, ~45 min):**
   ```bash
   python3 scripts/run_all_benchmarks.py matriz --maquina maquina_1 --usuarios <U_min> <U_med> <U_max> --duracao 60s
   ```
   Se no final aparecer o aviso **"acima de 10% de erro"**, reduza U_max e rode a matriz de novo.
5. **Gerar os gráficos** (o segundo comando também gera o comparativo entre as máquinas):
   ```bash
   python3 scripts/run_all_benchmarks.py graficos --maquina maquina_1 \
       --maquina-label "Máquina 1 (Ryzen 5 9600X, 6C/12T, 32 GB)" \
       --comparar-com maquina_2 --comparar-label "Máquina 2 (i7-1165G7, 4C/8T, 16 GB)"
   ```
6. **Subir tudo de `results/maquina_1/`** (inclusive os CSVs brutos `cenario*_stats.csv`, `*_failures.csv`, `*_stats_history.csv` e o `execucao.log`) e as especificações do hardware.

> Durante os testes, deixe a máquina sem outras cargas pesadas (navegador com muitas abas, jogos, builds), porque elas disputam CPU com a aplicação.

---

### 👤 Pessoa 2 — Máquina 2 ✅ concluída

Resultados em `results/maquina_2/`: cargas de **200 / 400 / 800 usuários** e as 27 combinações dentro da regra.

---

### 👤 Pessoa 3 — Análise comparativa e fechamento do README

Depois que a Máquina 1 estiver no repositório:

1. Preencher no `README.md`:
   - **Seção 4:** a calibragem da Máquina 1 (U_min / U_med / U_max) e a confirmação das especificações do hardware.
   - **Seção 8.2:** a tabela de resultados da Máquina 1 (do `results/maquina_1/resumo.csv`), os gráficos e a disputa de recursos.
   - **Gráfico comparativo** entre as máquinas (`results/maquina_1/graficos/comparativo_maquinas_calibragem.png`).
2. Escrever a **análise Máquina 1 × Máquina 2** na seção 9:
   - quanto a máquina mais forte aumenta a carga máxima e o RPS;
   - se, com mais núcleos, 2 e 3 instâncias passam a ganhar vazão. Na Máquina 2 não ganham, porque a CPU satura (~767% de 800%);
   - o peso do Locust na CPU de cada máquina.
3. Conferir se todos os números do README batem com os `resumo.csv`.

---

## 📊 Resumo

| Integrante | Responsabilidade | Status |
| :--- | :--- | :--- |
| **Pessoa 1** | Calibrar e testar na **Máquina 1 (Ryzen)** | ⏳ Pendente |
| **Pessoa 2** | Calibrar e testar na **Máquina 2 (i7-1165G7)** | ✅ Concluído |
| **Pessoa 3** | Análise comparativa + fechamento do README | ⏳ Depende da Máquina 1 |
