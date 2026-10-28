#!/usr/bin/env python3
"""
scripts/run_all_benchmarks.py

Orquestra os testes de carga do Trabalho 3 usando o Locust de verdade (contêiner
grubykarol/locust na mesma rede Docker da aplicação, via scripts/run_test.sh).
Durante cada execução, o `docker stats` é amostrado em paralelo para medir a
disputa de recursos entre o Locust e WordPress/Nginx/MySQL (requisitos.txt).

Subcomandos:
  calibrar   Varre cargas crescentes com 1 instância para descobrir U_min, U_med e U_max
             (U_max: maior carga com erro <= 10%; U_min/U_med: 0% de erro).
  matriz     Executa cenários x instâncias x cargas e gera resumo.csv e disputa_recursos.csv.
  exaustao   Varre cargas crescentes com 1, 2 e 3 instâncias e gera exaustao.csv.
  graficos   Gera os gráficos PNG a partir dos CSVs existentes.

Exemplos:
  python3 scripts/run_all_benchmarks.py calibrar --maquina maquina_1 --usuarios 100 200 400 800
  python3 scripts/run_all_benchmarks.py matriz   --maquina maquina_1 --usuarios 150 300 600
  python3 scripts/run_all_benchmarks.py exaustao --maquina maquina_1 --usuarios 300 600 900 1200
  python3 scripts/run_all_benchmarks.py graficos --maquina maquina_1 --maquina-label "Máquina 1" \\
      --comparar-com maquina_2 --comparar-label "Máquina 2"
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import threading
import time
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from consolidate_csv import parse_locust_stats_csv  # noqa: E402

RESULTS_DIR = os.path.join(ROOT_DIR, "results")
APP_CONTAINERS = {"mysql", "wordpress1", "wordpress2", "wordpress3", "nginx"}
LIMITE_ERRO_PCT = 10.0

MEM_UNITS_MB = {
    "B": 1 / (1024 * 1024),
    "KiB": 1 / 1024,
    "kB": 1 / 1000,
    "MiB": 1.0,
    "MB": 1.0,
    "GiB": 1024.0,
    "GB": 1000.0,
}


# =============================================================================
# Coleta de docker stats em paralelo
# =============================================================================
def parse_mem_mb(mem_usage: str) -> float:
    """Converte '123.4MiB / 30GiB' para MB (usa apenas a parte usada)."""
    used = mem_usage.split("/")[0].strip()
    m = re.match(r"([\d.]+)\s*([A-Za-z]+)", used)
    if not m:
        return 0.0
    return float(m.group(1)) * MEM_UNITS_MB.get(m.group(2), 1.0)


def friendly_service_name(name: str) -> str:
    if name.startswith("wordpress"):
        return f"WordPress ({name})"
    if name == "nginx":
        return "Nginx (Load Balancer)"
    if name == "mysql":
        return "MySQL (Banco)"
    return "Locust (Gerador de Carga)"


class DockerStatsSampler:
    """Amostra `docker stats` em segundo plano enquanto um teste do Locust roda."""

    def __init__(self):
        self.samples = []  # (timestamp, container, cpu_pct, mem_mb)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()

    def _loop(self):
        while not self._stop.is_set():
            proc = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"],
                capture_output=True,
                text=True,
            )
            now = time.time()
            for line in proc.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                name = parts[0].strip()
                # Só contêineres da aplicação e o contêiner do Locust criado pelo `docker compose run`
                if name not in APP_CONTAINERS and "locust" not in name:
                    continue
                try:
                    cpu = float(parts[1].replace("%", "").strip())
                except ValueError:
                    continue
                self.samples.append((now, name, cpu, parse_mem_mb(parts[2])))

    def averages(self):
        """Média de CPU% e memória por contêiner, ignorando amostras sem carga (Locust ausente)."""
        locust_ts = {ts for ts, name, _, _ in self.samples if "locust" in name}
        acc = defaultdict(lambda: [0.0, 0.0, 0])
        for ts, name, cpu, mem in self.samples:
            if ts not in locust_ts:
                continue
            key = "locust" if "locust" in name else name
            acc[key][0] += cpu
            acc[key][1] += mem
            acc[key][2] += 1
        return {k: (cpu / n, mem / n, n) for k, (cpu, mem, n) in acc.items()}


# =============================================================================
# Execução de um teste do Locust
# =============================================================================
def run_locust(maquina: str, cenario: int, inst: int, users: int, spawn_rate: int, duracao: str,
               reset_stats: bool, log_path: str):
    """Roda um teste via run_test.sh e devolve (métricas, médias de docker stats)."""
    env = dict(os.environ)
    if reset_stats:
        env["LOCUST_EXTRA_OPTS"] = "--reset-stats"

    with open(log_path, "a", encoding="utf-8") as log, DockerStatsSampler() as sampler:
        log.write(f"\n### cenario={cenario} inst={inst} users={users}\n")
        log.flush()
        proc = subprocess.run(
            ["./scripts/run_test.sh", maquina, str(cenario), str(inst), str(users), str(spawn_rate), duracao],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
        )

    stats_csv = os.path.join(RESULTS_DIR, maquina, f"cenario{cenario}_inst{inst}_users{users}_stats.csv")
    if proc.returncode != 0 or not os.path.exists(stats_csv):
        raise RuntimeError(f"Teste falhou (veja {log_path}): cenario={cenario} inst={inst} users={users}")

    return parse_locust_stats_csv(stats_csv), sampler.averages()


def print_result(prefix: str, metrics):
    avg_ms, rps, err_pct = metrics
    print(f"{prefix} -> Latência: {avg_ms:.1f}ms | RPS: {rps:.1f} | Erros: {err_pct:.2f}%", flush=True)


def write_csv(path: str, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[OK] {path} ({len(rows)} linhas)")


def stats_rows(cenario, inst, users, averages):
    return [
        [cenario, inst, users, friendly_service_name(name), round(cpu, 2), round(mem, 2), n]
        for name, (cpu, mem, n) in sorted(averages.items())
    ]


# =============================================================================
# Subcomandos
# =============================================================================
def cmd_calibrar(args):
    out_dir = os.path.join(RESULTS_DIR, args.maquina, "calibracao")
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "execucao.log")
    maquina = f"{args.maquina}/calibracao"

    print(f">>> Calibrando {args.maquina} (cenário {args.cenario}, 1 instância)")
    rows = []
    for users in sorted(args.usuarios):
        metrics = run_locust(maquina, args.cenario, 1, users, args.spawn_rate, args.duracao, args.reset_stats, log_path)[0]
        print_result(f"  [Usuários: {users:>5}]", metrics)
        rows.append([args.cenario, 1, users, *[round(v, 2) for v in metrics]])
        if metrics[2] > LIMITE_ERRO_PCT and args.parar_ao_exceder:
            print(f"  Erro acima de {LIMITE_ERRO_PCT:.0f}%; interrompendo a varredura.")
            break

    write_csv(os.path.join(RESULTS_DIR, args.maquina, "calibracao.csv"),
              ["cenario", "instancias", "usuarios", "tempo_resposta_ms", "rps", "taxa_erro_pct"], rows)

    sem_erro = [r[2] for r in rows if r[5] == 0.0]
    ate_limite = [r[2] for r in rows if r[5] <= LIMITE_ERRO_PCT]
    print("\nSugestão (confirme rodando a matriz):")
    print(f"  U_max (erro <= {LIMITE_ERRO_PCT:.0f}%): {max(ate_limite) if ate_limite else 'nenhuma carga dentro do limite'}")
    print(f"  Cargas com 0% de erro (candidatas a U_min/U_med): {sem_erro or 'nenhuma'}")
    print("  O ideal é U_max com erro próximo de 10%; refine a varredura entre os pontos vizinhos se necessário.")


def cmd_matriz(args):
    out_dir = os.path.join(RESULTS_DIR, args.maquina)
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "execucao.log")
    usuarios = sorted(args.usuarios)

    rows, amostras = [], []
    for cenario in args.cenarios:
        print(f"\n--- Cenário {cenario} ---")
        for inst in args.instancias:
            for users in usuarios:
                metrics, averages = run_locust(args.maquina, cenario, inst, users, args.spawn_rate,
                                               args.duracao, args.reset_stats, log_path)
                print_result(f"  [Instâncias: {inst}] [Usuários: {users:>5}]", metrics)
                rows.append([cenario, inst, users, *[round(v, 2) for v in metrics]])
                amostras.extend(stats_rows(cenario, inst, users, averages))

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    write_csv(os.path.join(out_dir, "resumo.csv"),
              ["cenario", "instancias", "usuarios", "tempo_resposta_ms", "rps", "taxa_erro_pct"], rows)
    write_csv(os.path.join(out_dir, "disputa_recursos_por_teste.csv"),
              ["cenario", "instancias", "usuarios", "service", "cpu_percent", "mem_mb", "amostras"], amostras)

    # Disputa de recursos consolidada: média sobre os testes de carga máxima com o maior nº de instâncias
    max_users, max_inst = usuarios[-1], max(args.instancias)
    acc = defaultdict(lambda: [0.0, 0.0, 0])
    for _, inst, users, service, cpu, mem, _ in amostras:
        if inst == max_inst and users == max_users:
            acc[service][0] += cpu
            acc[service][1] += mem
            acc[service][2] += 1
    disputa = [[s, round(c / n, 2), round(m / n, 2)] for s, (c, m, n) in sorted(acc.items())]
    if disputa:
        write_csv(os.path.join(out_dir, "disputa_recursos.csv"), ["service", "cpu_percent", "mem_mb"], disputa)
        print(f"     (média dos testes com {max_inst} instâncias e {max_users} usuários)")
    else:
        print("[AVISO] Nenhuma amostra de docker stats com o Locust ativo; disputa_recursos.csv não gerado.")

    erros = [r for r in rows if r[5] > LIMITE_ERRO_PCT]
    if erros:
        print(f"\n[AVISO] {len(erros)} teste(s) acima de {LIMITE_ERRO_PCT:.0f}% de erro (revise a calibragem):")
        for r in erros:
            print(f"  cenario={r[0]} inst={r[1]} users={r[2]} erro={r[5]}%")


def cmd_exaustao(args):
    out_dir = os.path.join(RESULTS_DIR, args.maquina, "exaustao")
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "execucao.log")
    maquina = f"{args.maquina}/exaustao"

    rows = []
    for inst in args.instancias:
        print(f"\n--- Estresse com {inst} instância(s), cenário {args.cenario} ---")
        for users in sorted(args.usuarios):
            metrics = run_locust(maquina, args.cenario, inst, users, args.spawn_rate, args.duracao,
                                 args.reset_stats, log_path)[0]
            print_result(f"  [Usuários: {users:>5}]", metrics)
            rows.append([inst, users, *[round(v, 2) for v in metrics]])

    write_csv(os.path.join(RESULTS_DIR, args.maquina, "exaustao.csv"),
              ["instancias", "usuarios", "tempo_resposta_ms", "rps", "taxa_erro_pct"], rows)


def cmd_graficos(args):
    base = os.path.join(RESULTS_DIR, args.maquina)
    cmd = [
        sys.executable, "scripts/plot_results.py", os.path.join(base, "resumo.csv"),
        "--output-dir", os.path.join(base, "graficos"),
        "--maquina-label", args.maquina_label or args.maquina,
    ]
    for flag, filename in (("--exhaustion-csv", "exaustao.csv"), ("--contention-csv", "disputa_recursos.csv")):
        path = os.path.join(base, filename)
        if os.path.exists(path):
            cmd += [flag, path]
    if args.comparar_com:
        cmd += [
            "--compare-csv", os.path.join(RESULTS_DIR, args.comparar_com, "resumo.csv"),
            "--compare-label", args.comparar_label or args.comparar_com,
        ]
    subprocess.run(cmd, check=True)


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Testes de carga do Trabalho 3 com Locust.")
    sub = parser.add_subparsers(dest="comando", required=True)

    def add_locust_args(p, default_duracao):
        p.add_argument("--maquina", required=True, help="Pasta de resultados (ex: maquina_1)")
        p.add_argument("--usuarios", type=int, nargs="+", required=True, help="Cargas de usuários simultâneos")
        p.add_argument("--spawn-rate", type=int, default=50, help="Usuários iniciados por segundo (padrão: 50)")
        p.add_argument("--duracao", default=default_duracao, help=f"Duração de cada teste (padrão: {default_duracao})")
        p.add_argument("--sem-reset-stats", dest="reset_stats", action="store_false",
                       help="Não zerar as estatísticas após a rampa de spawn (por padrão a rampa é descartada)")

    p = sub.add_parser("calibrar", help="Descobre os limites de carga com 1 instância")
    add_locust_args(p, "60s")
    p.add_argument("--cenario", type=int, default=1, choices=[1, 2, 3])
    p.add_argument("--parar-ao-exceder", action="store_true", help="Para quando o erro passar de 10%%")
    p.set_defaults(func=cmd_calibrar)

    p = sub.add_parser("matriz", help="Executa cenários x instâncias x cargas")
    add_locust_args(p, "60s")
    p.add_argument("--cenarios", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3])
    p.add_argument("--instancias", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3])
    p.set_defaults(func=cmd_matriz)

    p = sub.add_parser("exaustao", help="Curva de exaustão com 1, 2 e 3 instâncias")
    add_locust_args(p, "60s")
    p.add_argument("--cenario", type=int, default=1, choices=[1, 2, 3])
    p.add_argument("--instancias", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3])
    p.set_defaults(func=cmd_exaustao)

    p = sub.add_parser("graficos", help="Gera os gráficos a partir dos CSVs")
    p.add_argument("--maquina", required=True)
    p.add_argument("--maquina-label", default=None, help="Rótulo nos títulos (ex: 'Máquina 1 (Ryzen 5 9600X)')")
    p.add_argument("--comparar-com", default=None, help="Outra pasta de máquina para o gráfico comparativo")
    p.add_argument("--comparar-label", default=None)
    p.set_defaults(func=cmd_graficos)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
