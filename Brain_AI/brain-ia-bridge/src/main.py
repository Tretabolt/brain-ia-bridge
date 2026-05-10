<<<<<<< HEAD
"""
brain-ia-bridge — Pipeline principal de demonstração.

Fluxo completo:
  1. Calibração de baseline via stream EEG (mockado).
  2. Inicialização do grafo HyperBitnet com conexões quânticas.
  3. Simulação de propagação de estados sobre o grafo.
  4. Fusão matricial (BitNet × HyperBitnet).
  5. Tradução do resultado em comando TRIBE.
"""

import random

import numpy as np

from core.eeg_adapter import compute_score
from core.calibration import calibrate_thresholds, state_from_score
from core.hyperbitnet import HyperBitnet, bitnet_efficient_matrix
from core.fusion import fusion_vector, full_fusion
from integration.tribe_adapter import to_tribe_command


# ---------------------------------------------------------------------------
# Configuração da rede
# ---------------------------------------------------------------------------
NUM_NODES = 8          # Nós no grafo HyperBitnet
NUM_EDGES = 12         # Conexões quânticas aleatórias
SIM_STEPS = 5          # Passos de propagação na simulação
BASELINE_WINDOWS = 30  # Janelas de calibração EEG


def mock_eeg_stream(n: int = BASELINE_WINDOWS):
    """Gera *n* pacotes EEG mockados com Alpha/Beta aleatórios."""
    for _ in range(n):
        yield {"alpha": random.uniform(0.1, 0.9), "beta": random.uniform(0.1, 0.9)}


def main():
    # ── 1. Calibração de Baseline ─────────────────────────────────
    print(f"[1] Calibrando Thresholds Adaptativos ({BASELINE_WINDOWS} janelas)...")
    baseline = [compute_score(m) for m in mock_eeg_stream()]

    calib = calibrate_thresholds(baseline)
    print(f"    → Low  = {calib.thresholds.low:.4f}")
    print(f"    → High = {calib.thresholds.high:.4f}")
    print(f"    → μ = {calib.baseline_mean:.4f}  σ = {calib.baseline_std:.4f}")

    # ── 2. Construção do HyperBitnet ──────────────────────────────
    print(f"\n[2] Inicializando HyperBitnet ({NUM_NODES} nós, {NUM_EDGES} arestas)...")
    hbn = HyperBitnet(num_nodes=NUM_NODES)
    hbn.connect_quantum_nodes(num_edges=NUM_EDGES)

    print(f"    → Arestas efetivas: {hbn.graph.number_of_edges()}")
    print(f"    → Estados iniciais:  {hbn.get_state_vector()}")
    print(f"    → Q-states iniciais: {np.round(hbn.get_quantum_vector(), 3)}")

    # ── 3. Simulação de Propagação ────────────────────────────────
    print(f"\n[3] Executando simulação quântica ({SIM_STEPS} passos)...")
    hbn.run_quantum_simulation(num_steps=SIM_STEPS)

    print(f"    → Estados pós-sim:  {hbn.get_state_vector()}")
    print(f"    → Q-states pós-sim: {np.round(hbn.get_quantum_vector(), 3)}")

    # ── 4. Injetar sinal EEG no grafo via calibração ──────────────
    print("\n[4] Processando pacote EEG isolado...")
    metrics = {"alpha": 0.85, "beta": 0.20}
    score = compute_score(metrics)
    state = state_from_score(score, calib.thresholds)

    # Fusão leve (vetor) — para uso no loop realtime
    q_vec = hbn.get_quantum_vector().tolist()
    state_vec = hbn.get_state_vector().tolist()
    fused_light = fusion_vector(state_vec, q_vec)

    print(f"    → Score bruto:  {score:.4f}")
    print(f"    → Estado:       {state}")
    print(f"    → Fusão leve:   {[round(v, 4) for v in fused_light]}")

    # ── 5. Fusão Matricial Completa ───────────────────────────────
    print("\n[5] Fusão Matricial BitNet × HyperBitnet...")
    fusion_matrix = full_fusion(hbn)

    nonzero = np.count_nonzero(fusion_matrix)
    energy = float(np.sum(fusion_matrix))
    print(f"    → Dimensão:   {fusion_matrix.shape}")
    print(f"    → Elementos ≠ 0: {nonzero}")
    print(f"    → Energia total:  {energy:.6f}")

    # ── 6. Comando TRIBE ──────────────────────────────────────────
    print("\n[6] Traduzindo para TRIBE...")
    tribe_cmd = to_tribe_command(fused_light)
    print(f"    → Comando: {tribe_cmd}")

    print("\n✓ Pipeline completo.")


if __name__ == "__main__":
    main()
=======
from core.eeg_adapter import compute_score
from core.calibration import calibrate_thresholds, state_from_score
from core.hyperbitnet import HyperBitnet
from core.fusion import fusion_vector
from integration.tribe_adapter import to_tribe_command


def collect_baseline_windows():
    """
    Simulate 30 resting-state windows for calibration.
    In production these would come from the Crown/SDK during a brief
    eyes-closed baseline period.
    """
    return [
        {"focus": 0.30, "gamma": 0.28, "calm": 0.62},
        {"focus": 0.35, "gamma": 0.32, "calm": 0.60},
        {"focus": 0.33, "gamma": 0.30, "calm": 0.58},
        {"focus": 0.29, "gamma": 0.27, "calm": 0.65},
        {"focus": 0.31, "gamma": 0.29, "calm": 0.61},
        {"focus": 0.34, "gamma": 0.31, "calm": 0.59},
        {"focus": 0.32, "gamma": 0.30, "calm": 0.60},
        {"focus": 0.28, "gamma": 0.26, "calm": 0.66},
        {"focus": 0.36, "gamma": 0.33, "calm": 0.57},
        {"focus": 0.30, "gamma": 0.29, "calm": 0.63},
    ] * 3  # 30 windows


def run_once(eeg_features, low, high):
    score = compute_score(eeg_features)
    state = state_from_score(score, low, high)

    net = HyperBitnet(n_nodes=8)
    net.inject_state(state)

    intent = fusion_vector(net.states, net.quantum_states)
    command = to_tribe_command(intent)

    return {
        "score": round(score, 4),
        "state": state,
        "intent_energy": round(sum(intent), 4),
        "command": command["command"],
    }


if __name__ == "__main__":
    # 1) Initial calibration
    baseline = collect_baseline_windows()
    th = calibrate_thresholds(baseline)

    print("=== Calibration ===")
    print(
        {
            "baseline_mean": round(th.baseline_mean, 4),
            "baseline_std": round(th.baseline_std, 4),
            "low": round(th.low, 4),
            "high": round(th.high, 4),
        }
    )

    # 2) Sample real-time inference
    live_samples = [
        {"focus": 0.40, "gamma": 0.35, "calm": 0.50},  # likely transition
        {"focus": 0.82, "gamma": 0.78, "calm": 0.20},  # likely confirmed intent
        {"focus": 0.22, "gamma": 0.18, "calm": 0.70},  # likely disconnection
    ]

    print("\n=== Live Inference ===")
    for i, sample in enumerate(live_samples, start=1):
        out = run_once(sample, th.low, th.high)
        print(f"sample_{i}:", out)
>>>>>>> 531fc65123544157015ba2046c143129823abab2
