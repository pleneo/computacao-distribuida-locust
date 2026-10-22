#!/usr/bin/env python3
"""
scripts/plot_results.py

Gera todos os gráficos do Trabalho 3:
1. Gráficos Oficiais do PDF (Páginas 4 e 5):
   - Tempo de Resposta Médio (s) vs Número de Usuários (agrupado por 1, 2, 3 instâncias)
   - Requisições por Segundo (RPS) vs Número de Instâncias (agrupado por cargas de usuários)
2. Gráficos Avançados (Requisitos Extras e Requisitos do Professor):
   - Curva de Exaustão e Saturação (1 vs 2 vs 3 instâncias sob estresse extremo)
   - Disputa de Recursos no mesmo host (CPU/RAM do Locust vs WordPress/Nginx/MySQL - Requisito 3)
   - Comparativo de Calibragem entre as Máquinas (Máquina 1 Forte vs Máquina 2 Fraca)
"""

import argparse
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np


def load_summary_csv(csv_path: str):
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
    colors_inst = ["#9ecae1", "#fdae6b", "#a1d99b"]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    for idx, inst in enumerate(instancias_list):
        valores_y = [scenario_data.get((inst, u), {}).get("resp_s", 0.0) for u in usuarios_list]
        offset = (idx - (len(instancias_list) - 1) / 2) * width
        label = f"{inst} instância" if inst == 1 else f"{inst} instâncias"
        color = colors_inst[idx % len(colors_inst)]
        bars = ax.bar(x + offset, valores_y, width, label=label, color=color, edgecolor="#2b2b2b", linewidth=0.8)
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.2f}s",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Número de usuários simultâneos", fontsize=11, fontweight="bold")
    ax.set_ylabel("Tempo médio de resposta (s)", fontsize=11, fontweight="bold")
    ax.set_title(f"{title_prefix} — Tempo de Resposta ({maquina_label})", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{u} usuários" for u in usuarios_list], fontsize=10)
    ax.legend(frameon=True, facecolor="#f8f9fa", edgecolor="#cccccc")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_resp = os.path.join(output_dir, f"cenario_{cenario}_tempo_resposta.png")
    fig.savefig(out_resp, dpi=160)
    plt.close(fig)
    print(f"[OK] Gráfico gerado: {out_resp}")

    # =========================================================================
    # Gráfico 2 (Página 5 do PDF):
    # Eixo X: Número de instâncias | Eixo Y: Requisições por segundo (RPS)
    # Séries (barras): Cargas de usuários (Baixa, Média, Máxima)
    # =========================================================================
    x_inst = np.arange(len(instancias_list))
    colors_users = ["#bcbddc", "#fa9fb5", "#c7e9c0"]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    for idx, u in enumerate(usuarios_list):
        valores_rps = [scenario_data.get((inst, u), {}).get("rps", 0.0) for inst in instancias_list]
        offset = (idx - (len(usuarios_list) - 1) / 2) * width
        label = f"{u} usuários"
        color = colors_users[idx % len(colors_users)]
        bars = ax.bar(x_inst + offset, valores_rps, width, label=label, color=color, edgecolor="#2b2b2b", linewidth=0.8)
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.1f}",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Número de instâncias WordPress", fontsize=11, fontweight="bold")
    ax.set_ylabel("Requisições por segundo (RPS)", fontsize=11, fontweight="bold")
    ax.set_title(f"{title_prefix} — Requisições por Segundo ({maquina_label})", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x_inst)
    ax.set_xticklabels([f"{i} Instância" if i == 1 else f"{i} Instâncias" for i in instancias_list], fontsize=10)
    ax.legend(frameon=True, facecolor="#f8f9fa", edgecolor="#cccccc")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_rps = os.path.join(output_dir, f"cenario_{cenario}_rps.png")
    fig.savefig(out_rps, dpi=160)
    plt.close(fig)
    print(f"[OK] Gráfico gerado: {out_rps}")


def plot_exhaustion_curve(csv_path: str, output_dir: str):
    """Gera gráfico da curva de saturação / exaustão extrema da máquina."""
    if not os.path.exists(csv_path):
        return

    data = defaultdict(dict)
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inst = int(row["instancias"])
            users = int(row["usuarios"])
            data[inst][users] = {
                "resp_s": float(row["tempo_resposta_ms"]) / 1000.0,
                "rps": float(row["rps"]),
                "err_pct": float(row["taxa_erro_pct"]),
            }

    users_list = sorted(list(next(iter(data.values())).keys()))
    colors = {1: "#e41a1c", 2: "#377eb8", 3: "#4daf4a"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Tempo de Resposta sob Estresse
    for inst, u_dict in sorted(data.items()):
        y_resp = [u_dict[u]["resp_s"] for u in users_list]
        ax1.plot(users_list, y_resp, marker="o", linewidth=2.2, label=f"{inst} instância(s)", color=colors[inst])
    ax1.set_xlabel("Usuários Concorrentes (Estresse)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Tempo de Resposta Médio (s)", fontsize=11, fontweight="bold")
    ax1.set_title("Curva de Latência sob Exaustão", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    # Subplot 2: Taxa de Erro (%) sob Estresse
    for inst, u_dict in sorted(data.items()):
        y_err = [u_dict[u]["err_pct"] for u in users_list]
        ax2.plot(users_list, y_err, marker="s", linewidth=2.2, label=f"{inst} instância(s)", color=colors[inst])
    ax2.axhline(10.0, color="#d95f02", linestyle=":", linewidth=1.5, label="Limite do Prof (10% erro)")
    ax2.set_xlabel("Usuários Concorrentes (Estresse)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Taxa de Erro (%)", fontsize=11, fontweight="bold")
    ax2.set_title("Evolução da Taxa de Erro / Saturação", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    fig.suptitle("Curva de Exaustão e Limite de Colapso (Máquina 1 — Ryzen 5 9600X)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    out_path = os.path.join(output_dir, "curva_exaustao_saturacao.png")
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"[OK] Gráfico de exaustão salvo: {out_path}")


def plot_resource_contention(csv_path: str, output_dir: str):
    """Gera gráfico de pizza e barras mostrando a disputa de CPU/RAM (Locust vs Aplicação)."""
    if not os.path.exists(csv_path):
        return

    services, cpu_vals, mem_vals = [], [], []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            services.append(row["service"])
            cpu_vals.append(float(row["cpu_percent"]))
            mem_vals.append(float(row["mem_mb"]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = ["#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#666666", "#1f78b4"]

    # Pizza de CPU
    ax1.pie(cpu_vals, labels=services, autopct="%1.1f%%", startangle=140, colors=colors[:len(services)],
            wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax1.set_title("Distribuição de Uso de CPU (% Total Utilizado)", fontsize=11, fontweight="bold")

    # Barras de Memória
    bars = ax2.barh(services, mem_vals, color=colors[:len(services)], edgecolor="#333333")
    for bar in bars:
        ax2.annotate(f"{bar.get_width():.1f} MB",
                     xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                     xytext=(5, 0), textcoords="offset points",
                     va="center", fontsize=9)
    ax2.set_xlabel("Memória Utilizada (MB)", fontsize=11, fontweight="bold")
    ax2.set_title("Consumo de Memória RAM por Contêiner", fontsize=11, fontweight="bold")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(axis="x", linestyle="--", alpha=0.4)

    fig.suptitle("Disputa de Recursos no Mesmo Host — Locust vs. WordPress/Nginx/MySQL (Requisito 3)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    out_path = os.path.join(output_dir, "disputa_recursos_cpu_ram.png")
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"[OK] Gráfico de disputa de recursos salvo: {out_path}")


def plot_machine_comparison(csv_m1: str, csv_m2: str, output_dir: str):
    """Compara o tempo de resposta e capacidade das Máquinas 1 e 2."""
    if not (os.path.exists(csv_m1) and os.path.exists(csv_m2)):
        return

    data_m1 = load_summary_csv(csv_m1)
    data_m2 = load_summary_csv(csv_m2)

    # Compara cenário 1 com 3 instâncias
    users_m1 = sorted({u for (_, u) in data_m1[1].keys()})
    users_m2 = sorted({u for (_, u) in data_m2[1].keys()})

    fig, ax = plt.subplots(figsize=(9, 5))
    x_labels = ["Carga Baixa (0% erro)", "Carga Média (0% erro)", "Carga Máxima (≤10% erro)"]
    x = np.arange(len(x_labels))
    width = 0.35

    rps_m1 = [data_m1[1][(3, u)]["rps"] for u in users_m1]
    rps_m2 = [data_m2[1][(3, u)]["rps"] for u in users_m2]

    b1 = ax.bar(x - width/2, rps_m1, width, label=f"Máquina 1 (Forte - Ryzen 5 9600X)\n[Cargas: {users_m1[0]}, {users_m1[1]}, {users_m1[2]} users]", color="#1f77b4", edgecolor="#333333")
    b2 = ax.bar(x + width/2, rps_m2, width, label=f"Máquina 2 (Fraca / Restrita)\n[Cargas: {users_m2[0]}, {users_m2[1]}, {users_m2[2]} users]", color="#ff7f0e", edgecolor="#333333")

    for b in b1:
        ax.annotate(f"{b.get_height():.1f} RPS", xy=(b.get_x() + b.get_width()/2, b.get_height()), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5)
    for b in b2:
        ax.annotate(f"{b.get_height():.1f} RPS", xy=(b.get_x() + b.get_width()/2, b.get_height()), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5)

    ax.set_ylabel("Vazão (Requisições por Segundo - RPS)", fontsize=11, fontweight="bold")
    ax.set_title("Comparativo de Desempenho e Calibragem: Máquina Forte vs. Fraca (Cenário 1, 3 Instâncias)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=10)
    ax.legend(frameon=True, facecolor="#f8f9fa", edgecolor="#cccccc")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out_path = os.path.join(output_dir, "comparativo_maquinas_calibragem.png")
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"[OK] Gráfico comparativo de máquinas salvo: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Plota os gráficos do Trabalho 3 (Locust + WordPress).")
    parser.add_argument("csv_path", help="Caminho para o CSV de resumo (ex: results/maquina_1/resumo.csv)")
    parser.add_argument("--output-dir", default=None, help="Diretório onde salvar os gráficos PNG")
    parser.add_argument("--maquina-label", default="Máquina 1", help="Rótulo da máquina para o título do gráfico")
    parser.add_argument("--exhaustion-csv", default=None, help="Caminho para exaustao.csv")
    parser.add_argument("--contention-csv", default=None, help="Caminho para disputa_recursos.csv")
    parser.add_argument("--compare-csv", default=None, help="Segundo CSV de máquina para comparação direta")
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.dirname(os.path.abspath(args.csv_path))
    os.makedirs(output_dir, exist_ok=True)

    data = load_summary_csv(args.csv_path)
    for cenario, scenario_data in sorted(data.items()):
        plot_scenario_charts(cenario, scenario_data, output_dir, args.maquina_label)

    if args.exhaustion_csv:
        plot_exhaustion_curve(args.exhaustion_csv, output_dir)

    if args.contention_csv:
        plot_resource_contention(args.contention_csv, output_dir)

    if args.compare_csv:
        plot_machine_comparison(args.csv_path, args.compare_csv, output_dir)


if __name__ == "__main__":
    main()
