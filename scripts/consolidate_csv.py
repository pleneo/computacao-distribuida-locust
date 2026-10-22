#!/usr/bin/env python3
"""
Consolida automaticamente os arquivos *_requests.csv gerados pelo Locust
em uma pasta (ex: results/maquina_1/) para o formato resumo.csv esperado
pelo plot_results.py.

Uso:
    python3 scripts/consolidate_csv.py results/maquina_1
"""

import csv
import glob
import os
import re
import sys

PATTERN = re.compile(r"cenario(\d+)_inst(\d+)_users(\d+)_requests\.csv$")


def parse_locust_requests_csv(filepath: str):
    """Extrai tempo médio de resposta (ms), RPS e taxa de erro (%) da linha Total do Locust."""
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        if not reader:
            return None
        total_row = reader[-1]
        num_req = float(total_row.get("# requests", total_row.get("Request Count", 0)) or 0)
        num_fail = float(total_row.get("# fails", total_row.get("Failure Count", 0)) or 0)
        avg_ms = float(total_row.get("Average (ms)", total_row.get("Average response time", 0)) or 0)
        rps = float(total_row.get("Requests/s", 0) or 0)
        err_pct = (num_fail / num_req * 100.0) if num_req > 0 else 0.0
        return avg_ms, rps, err_pct


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "results/maquina_1"
    files = sorted(glob.glob(os.path.join(target_dir, "cenario*_inst*_users*_requests.csv")))

    if not files:
        print(f"Nenhum arquivo *_requests.csv encontrado em {target_dir}")
        raise SystemExit(1)

    rows = []
    for path in files:
        m = PATTERN.search(os.path.basename(path))
        if not m:
            continue
        cenario, inst, users = int(m.group(1)), int(m.group(2)), int(m.group(3))
        metrics = parse_locust_requests_csv(path)
        if metrics:
            avg_ms, rps, err_pct = metrics
            rows.append((cenario, inst, users, round(avg_ms, 2), round(rps, 2), round(err_pct, 2)))

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out_csv = os.path.join(target_dir, "resumo.csv")
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cenario", "instancias", "usuarios", "tempo_resposta_ms", "rps", "taxa_erro_pct"])
        writer.writerows(rows)

    print(f"[OK] Arquivo consolidado gerado em: {out_csv} ({len(rows)} linhas)")


if __name__ == "__main__":
    main()
