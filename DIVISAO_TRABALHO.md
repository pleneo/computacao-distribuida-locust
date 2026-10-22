# Divisão de Tarefas — Trabalho 3 (Testes de Carga com Locust e WordPress)

Como toda a **fundação de código e infraestrutura** (`docker-compose.yml`, configs do Nginx para 1/2/3 instâncias, scripts de criação automática dos 3 cenários no WordPress, scripts do Locust e gerador de gráficos) **já está pronta neste repositório**, o trabalho restante consiste na **execução experimental (calibragem + coleta nas máquinas)** e na **análise dos resultados (gráficos + relatório)**.

Abaixo está a divisão justa do que **falta fazer agora** entre as 3 pessoas.

---

## ✅ O que JÁ está pronto no repositório (Fundação)

- [x] `docker-compose.yml` com MySQL, 3 instâncias de WordPress, Nginx e Locust na mesma rede.
- [x] `nginx/nginx.1.conf`, `nginx.2.conf`, `nginx.3.conf` + `scripts/set_instances.sh` para alternar entre 1, 2 e 3 instâncias.
- [x] `scripts/generate_assets.py` e `scripts/setup_wordpress.sh` que instalam o WordPress e criam sozinhos os 3 posts (`/?p=1` com 1MB, `/?p=2` com 400KB de texto, `/?p=3` com 300KB).
- [x] Scripts do Locust (`locust/locustfile_cenario1.py`, `2` e `3`) e executor automatizado (`scripts/run_test.sh`).
- [x] Consolidador de CSV (`scripts/consolidate_csv.py`) e gerador dos gráficos do PDF (`scripts/plot_results.py`).

---

## 📌 Regras do Professor para os Testes (`requisitos.txt`)

1. **Calibragem da Carga (em vez de usar 10, 100 e 1000 fixos):**
   - Descobrir o limite real da máquina testada (usando 1 instância do WordPress como base).
   - **Carga Máxima ($U_{max}$):** Quantidade de usuários onde a **taxa de erro chega perto de 10% (nunca passando de 10%)**.
   - **Carga Baixa ($U_{min}$) e Carga Média ($U_{med}$):** Quantidades menores de usuários onde a **taxa de erro é 0% ($100\%$ de acerto)**.
2. **Pelo menos 2 máquinas diferentes:**
   - Rodar em uma máquina mais forte e outra mais fraca para comparar a diferença de calibragem.
3. **Locust rodando dentro do Docker junto com a aplicação:**
   - Já configurado no `docker-compose.yml` para avaliar no relatório a disputa de recursos (CPU/RAM) entre o Locust e o WordPress/Nginx/MySQL.

---

## 👥 O que cada pessoa vai fazer agora

### 👤 Pessoa 1 — Publicação do Repo + Calibragem e Testes na Máquina 1
**Foco:** Subir o repositório no GitHub, validar o setup inicial e executar toda a bateria de testes na **Máquina 1** (ex: máquina mais potente ou principal).

1. **Criar o repositório no GitHub** e fazer `git push` desta estrutura.
2. **Anotar o hardware da Máquina 1:** Modelo da CPU (núcleos/threads), quantidade de RAM e Sistema Operacional.
3. **Subir e inicializar o ambiente:**
   ```bash
   ./scripts/setup_wordpress.sh
   ```
4. **Calibrar as 3 cargas da Máquina 1:**
   - Rodar `./scripts/set_instances.sh 1` e `SCENARIO=1 docker compose up -d locust`.
   - Abrir `http://localhost:8089` e testar quantidades de usuários até achar:
     - **Carga Máxima ($U_{max}$):** Taxa de falha (*Failures*) $> 0\%$ e $\le 10\%$.
     - **Carga Média ($U_{med}$):** ~50% da carga máxima, com **0% de falha**.
     - **Carga Baixa ($U_{min}$):** ~20% da carga máxima, com **0% de falha**.
5. **Rodar a bateria automatizada na Máquina 1 (3 cenários × 3 instâncias × 3 cargas):**
   ```bash
   # Substitua 20, 60 e 120 pelos valores (U_min, U_med, U_max) descobertos na Máquina 1:
   for cenario in 1 2 3; do
     for inst in 1 2 3; do
       for users in 20 60 120; do
         ./scripts/run_test.sh maquina_1 $cenario $inst $users 10 60s
       done
     done
   done

   python3 scripts/consolidate_csv.py results/maquina_1
   ```
6. **Subir os resultados (`results/maquina_1/resumo.csv`) e as specs da Máquina 1 no GitHub.**

---

### 👤 Pessoa 2 — Calibragem e Testes na Máquina 2 (Hardware Diferente)
**Foco:** Clonar o repositório pronto em uma **segunda máquina** (preferencialmente mais fraca ou de configuração diferente da Máquina 1), calibrar os limites dela e coletar os resultados.

1. **Clonar o repositório na Máquina 2** e anotar o hardware (CPU, núcleos/threads, RAM, SO).
2. **Subir e inicializar o ambiente com 1 comando:**
   ```bash
   ./scripts/setup_wordpress.sh
   ```
3. **Calibrar as 3 cargas específicas da Máquina 2:**
   - Rodar `./scripts/set_instances.sh 1` e `SCENARIO=1 docker compose up -d locust`.
   - Acessar `http://localhost:8089` e encontrar os valores de **$U'_{min}$ (0% erro)**, **$U'_{med}$ (0% erro)** e **$U'_{max}$ ($\le 10\%$ erro)** para a Máquina 2.
4. **Rodar a bateria automatizada na Máquina 2:**
   ```bash
   # Substitua 10, 30 e 60 pelos valores (U'_min, U'_med, U'_max) descobertos na Máquina 2:
   for cenario in 1 2 3; do
     for inst in 1 2 3; do
       for users in 10 30 60; do
         ./scripts/run_test.sh maquina_2 $cenario $inst $users 5 60s
       done
     done
   done

   python3 scripts/consolidate_csv.py results/maquina_2
   ```
5. **Subir os resultados (`results/maquina_2/resumo.csv`) e as specs da Máquina 2 no GitHub.**

---

### 👤 Pessoa 3 — Geração dos Gráficos, Análise dos Dados e Relatório Final
**Foco:** Processar os dados das Máquinas 1 e 2, gerar os gráficos exigidos pelo PDF e escrever a análise técnica e conclusões do trabalho (e opcionalmente rodar em uma Máquina 3 se quiserem 3 pontos de comparação).

1. **Gerar todos os gráficos das Máquinas 1 e 2** usando o script pronto:
   ```bash
   pip install matplotlib numpy

   python3 scripts/plot_results.py results/maquina_1/resumo.csv \
       --output-dir results/maquina_1/graficos \
       --maquina-label "Máquina 1"

   python3 scripts/plot_results.py results/maquina_2/resumo.csv \
       --output-dir results/maquina_2/graficos \
       --maquina-label "Máquina 2"
   ```
   *(Serão gerados 6 gráficos por máquina: Tempo de Resposta e RPS para os Cenários 1, 2 e 3, idênticos ao modelo das páginas 4 e 5 do PDF).*
2. **Redigir o Relatório / Documentação Final de Resultados contendo:**
   - **Tabela de Calibragem (Máquina 1 vs. Máquina 2):** Comparando o hardware das duas máquinas e qual foi a carga mínima, média e máxima ($\le 10\%$ erro) suportada por cada uma.
   - **Análise dos 3 Cenários (1MB Imagem vs. 400KB Texto vs. 300KB Imagem):** Explicar por que o cenário de texto (processamento PHP + leitura MySQL) e os cenários de imagem (I/O e banda do Apache/Nginx) impactam de formas diferentes o tempo de resposta e o RPS.
   - **Análise da Escalabilidade (1 vs. 2 vs. 3 instâncias do WordPress):** Mostrar nos gráficos como o balanceamento do Nginx reduziu o tempo de resposta ou aumentou o RPS.
   - **Discussão sobre o Gerador de Carga no Mesmo Host (exigência do `requisitos.txt`):** Explicar como o fato do contêiner do Locust rodar na mesma máquina disputa CPU e memória com os contêineres da aplicação, podendo limitar o ganho ao escalar para 3 instâncias.

---

## 📊 Resumo da Divisão Atualizada

| Integrante | Responsabilidade Principal | Entregável |
| :--- | :--- | :--- |
| **Pessoa 1** | Subir repo inicial + Calibrar e testar na **Máquina 1** | Repo no GitHub + `results/maquina_1/resumo.csv` + Specs Máquina 1 |
| **Pessoa 2** | Calibrar e testar na **Máquina 2** (hardware diferente) | `results/maquina_2/resumo.csv` + Specs Máquina 2 |
| **Pessoa 3** | Gerar os gráficos + Redigir análise comparativa e relatório | Gráficos PNG (`results/*/graficos/`) + Relatório/Análise final |
