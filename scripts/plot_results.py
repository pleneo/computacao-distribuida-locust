#!/usr/bin/env python3
"""
Gera os gráficos exigidos no PDF do Trabalho 3 a partir de um arquivo CSV consolidado
ou dos arquivos gerados pelo Locust em results/<maquina>/.

Estilos de gráficos gerados para cada cenário (páginas 4 e 5 do PDF):
1. Tempo de resposta médio (s) vs. Número de usuários (barras agrupadas por 1, 2 e 3 instâncias)
2. Requisições por segundo (RPS) vs. Número de instâncias (barras agrupadas pelas 3 cargas de usuários)

Uso:
    python3 scripts/plot_results.py results/maquina_1/resumo.csv --output-dir results/maquina_1/graficos
"""

import argparse
import csv
import os
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Erro: instale matplotlib e numpy antes de gerar os gráficos:")
    print("  pip install matplotlib numpy")
    raise SystemExit(1)


def load_summary_csv(csv_path: str):
    """
    Lê o CSV de resumo com as colunas:
    cenario,instancias,usuarios,tempo_resposta_ms,rps,taxa_erro_pct
    """
    data = defaultdict(dict)
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cenario = int(row["cenario"])
            inst = int(row["instancias"])
            users = int(row["usuarios"])
            resp_s = float(row["tempo_resposta_ms"]) / 1000.0
            rps = float(row["rps"])
            err = float(row.get("taxa_erro_pct", 0.0))
            data[cenario][(inst, users)] = {
                "resp_s": resp_s,
                "rps": rps,
                "err": err,
            }
    return data


def plot_scenario_charts(cenario: int, scenario_data: dict, output_dir: str, maquina_label: str):
    instancias_list = sorted({inst for (inst, _) in scenario_data.keys()})
    usuarios_list = sorted({users for (_, users) in scenario_data.keys()})

    cenario_titles = {
        1: "Cenário 1 (Imagem ~1MB)",
        2: "Cenário 2 (Texto ~400KB)",
        3: "Cenário 3 (Imagem ~300KB)",
    }
    title_prefix = cenario_titles.get(cenario, f"Cenário {cenario}")

    # =========================================================================
    # Gráfico 1 (Página 4 do PDF):
    # Eixo X: Número de usuários | Eixo Y: Tempo de resposta (s)
    # Séries (barras): 1 instância, 2 instâncias, 3 instâncias
    # =========================================================================
    x = np.arange(len(usuarios_list))
    width = 0.25
    colors_inst = ["#cbd5e8", "#fdcdac", "#f4cae4"]

    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, inst in enumerate(instancias_list):
        valores_y = [scenario_data.get((inst, u), {}).get("resp_s", 0.0) for u in usuarios_list]
        offset = (idx - (len(instancias_list) - 1) / 2) * width
        label = f"{inst} instância" if inst == 1 else f"{inst} instâncias"
        color = colors_inst[idx % len(colors_inst)]
        ax.bar(x + offset, valores_y, width, label=label, color=color, edgecolor="#333333")

    ax.set_xlabel("Número de usuários", fontsize=11)
    ax.set_ylabel("Tempo de resposta (s)", fontsize=11)
    ax.set_title(f"{title_prefix} - Tempo de Resposta ({maquina_label})", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([str(u) for u in usuarios_list])
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_resp = os.path.join(output_dir, f"cenario_{cenario}_tempo_resposta.png")
    fig.savefig(out_resp, dpi=150)
    plt.close(fig)
    print(f"[OK] Gráfico salvo: {out_resp}")

    # =========================================================================
    # Gráfico 2 (Página 5 do PDF):
    # Eixo X: Número de instâncias | Eixo Y: Requisições por segundo (s)
    # Séries (barras): Cargas de usuários (Baixa, Média, Máxima)
    # =========================================================================
    x_inst = np.arange(len(instancias_list))
    colors_users = ["#ccebc5", "#cbd5e8", "#fff2ae"]

    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, u in enumerate(usuarios_list):
        valores_rps = [scenario_data.get((inst, u), {}).get("rps", 0.0) for inst in instancias_list]
        offset = (idx - (len(usuarios_list) - 1) / 2) * width
        label = f"{u} usuários"
        color = colors_users[idx % len(colors_users)]
        ax.bar(x_inst + offset, valores_rps, width, label=label, color=color, edgecolor="#333333")

    ax.set_xlabel("Número de instâncias", fontsize=11)
    ax.set_ylabel("Requisições por segundo (s)", fontsize=11)
    ax.set_title(f"{title_prefix} - Requisições por Segundo ({maquina_label})", fontsize=12, fontweight="bold")
    ax.set_xticks(x_inst)
    ax.set_xticklabels([str(i) for i in instancias_list])
    ax.legend(frameon=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_rps = os.path.join(output_dir, f"cenario_{cenario}_rps.png")
    fig.savefig(out_rps, dpi=150)
    plt.close(fig)
    print(f"[OK] Gráfico salvo: {out_rps}")


def main():
    parser = argparse.ArgumentParser(description="Plota os gráficos do Trabalho 3 (Locust + WordPress).")
    parser.add_argument("csv_path", help="Caminho para o CSV de resumo (ex: results/maquina_1/resumo.csv)")
    parser.add_argument("--output-dir", default=None, help="Diretório onde salvar os gráficos PNG")
    parser.add_argument("--maquina-label", default="Máquina 1", help="Rótulo da máquina para o título do gráfico")
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.dirname(os.path.abspath(args.csv_path))
    os.makedirs(output_dir, exist_ok=True)

    data = load_summary_csv(args.csv_path)
    for cenario, scenario_data in sorted(data.items()):
        plot_scenario_charts(cenario, scenario_data, output_dir, args.maquina_label)


if __name__ == "__main__":
    main()
