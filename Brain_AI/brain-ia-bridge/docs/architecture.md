# Arquitetura técnica (MVP → v0.2)

## Pipeline

1. **EEG Input** (`core/eeg_adapter.py`)
   - Recebe stream de métricas (bandas Alpha/Beta).
   - Calcula score de engajamento: `α / (β + ε)`.

2. **Calibration Engine** (`core/calibration.py`)
   - Coleta dados de baseline em blocos temporais.
   - Gera *Adaptive Thresholds* via análise estatística (μ ± σ).
   - Classifica estados: `-1` (baixo), `0` (neutro), `1` (alto).

3. **HyperBitnet** (`core/hyperbitnet.py`)
   - Grafo ponderado `networkx` com **N** nós e arestas quânticas.
   - Cada nó possui estado clássico (0|1) e estado quântico contínuo ∈ [0,1).
   - Propagação via:
     - Limiar de ativação ternário usando constante **1.58** (BitNet).
     - Atualização quântica via `scipy.special.softmax` sobre vizinhos.
   - `bitnet_efficient_matrix(size)` gera kernel de pesos `1.58^(i*N+j)`.
   - `hyperbitnet_matrix_fusion()` funde topologia do grafo com a matriz BitNet.

4. **Fusion Engine** (`core/fusion.py`)
   - `fusion_vector()` — fusão leve (vetor) para loop realtime.
   - `full_fusion()` — fusão matricial completa BitNet × HyperBitnet.

5. **TRIBE Adapter** (`integration/tribe_adapter.py`)
   - Traduz vetor de intenção em comando simbólico (`accelerate`, `brake`, `idle`).

## Entrypoints

| Script              | Propósito                                  |
|---------------------|--------------------------------------------|
| `src/main.py`       | Pipeline completo (calibração → TRIBE)     |
| `src/realtime_loop.py` | Loop realtime com buffer deslizante     |

## Dependências

- `numpy` — operações matriciais
- `networkx` — topologia do grafo HyperBitnet
- `scipy` — softmax para propagação de estados quânticos
