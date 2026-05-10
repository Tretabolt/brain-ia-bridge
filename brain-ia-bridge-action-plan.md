# Plano de Ação Detalhado — brain-ia-bridge
## Versão Expandida com Implementação Concreta

**Data:** 2026-05-10  
**Versão:** 2.0  
**Total estimado:** 16-21h

---

## FASE 0: Preparação e Resolução de Conflitos (P0 — 3-5h)

### 0.1 Inventário dos Conflitos

Primeiro passo: mapear todos os conflitos antes de resolver qualquer um.

```bash
# No repositório brain-ia-bridge:
git status
git diff --name-only --diff-filter=U

# Para cada arquivo com conflito, ver os dois lados:
git show :1:core/eeg_adapter.py  # BASE (ancestral comum)
git show :2:core/eeg_adapter.py  # HEAD (sua branch)
git show :3:core/eeg_adapter.py  # branch mergeada
```

### 0.2 Estratégia de Resolução por Arquivo

| Arquivo | Versão Recomendada | Justificativa |
|---------|-------------------|---------------|
| `core/eeg_adapter.py` | **Branch** | Features normalizadas (focus/gamma/calm), score ∈ [0,1] |
| `core/calibration.py` | **Branch** | Limiares mais claros (mean+1σ, mean+2σ) |
| `core/hyperbitnet.py` | **HEAD** | Grafo NetworkX real, fusão matricial completa |
| `core/fusion.py` | **HEAD** | Duas camadas de fusão (vetor + matriz) |
| `integration/tribe_adapter.py` | **Branch** | Nomes descritivos, limiares conservadores |
| `runners/main.py` | **Manual merge** | Pegar estrutura do HEAD + imports da branch |
| `runners/realtime_loop.py` | **Branch** | SlidingWindowStateFilter mais robusto |

### 0.3 Processo de Resolução (por arquivo)

```bash
# 1. Ver os conflitos:
grep -n "<<<<<<< HEAD" core/eeg_adapter.py

# 2. Editar manualmente, escolhendo o bloco correto
#    ou mesclando os melhores de cada lado

# 3. Marcar como resolvido:
git add core/eeg_adapter.py

# 4. Verificar que não há mais <<<<<<< :
grep -rn "<<<<<<< HEAD" core/ runners/ integration/ geometric/ visualization/

# 5. Commit:
git commit -m "resolve: merge conflicts em eeg_adapter.py (versão branch)"
```

### 0.4 Valiação Pós-Conflito

```bash
# Testar se o projeto importa sem erro:
cd brain-ia-bridge
python -c "from core.eeg_adapter import EEGAdapter; print('OK')"
python -c "from core.calibration import calibrate; print('OK')"
python -c "from core.hyperbitnet import HyperBitnet; print('OK')"
python -c "from core.fusion import fuse; print('OK')"
python -c "from integration.tribe_adapter import TribeAdapter; print('OK')"

# Testar runner principal:
python runners/main.py --help  # ou sem args se não tiver CLI
```

---

## FASE 1: Escolha de Versão Canônica (P0 — 2-3h)

### 1.1 Critérios de Decisão

Para cada módulo com versões duplicadas (HEAD vs branch), aplicar:

1. **Funcionalidade**: qual versão cobre mais casos?
2. **Robustez**: qual lida melhor com edge cases?
3. **Clareza**: qual é mais legível e mantível?
4. **Testabilidade**: qual é mais fácil de testar?

### 1.2 Decisões por Módulo

| Módulo | Decisão | Ação |
|--------|---------|------|
| `eeg_adapter` | Branch (focus/gamma/calm) | Deletar versão HEAD |
| `calibration` | Branch (Thresholds) | Deletar versão HEAD |
| `hyperbitnet` | HEAD (NetworkX graph) | Deletar versão branch |
| `fusion` | HEAD (duas camadas) | Deletar versão branch |
| `tribe_adapter` | Branch (CONFIRM_INTENT) | Deletar versão HEAD |
| `realtime_loop` | Branch (SlidingWindow) | Deletar versão HEAD |
| `main` | Manual merge | Combinar melhores partes |

### 1.3 Script de Limpeza

```bash
# Após resolver conflitos e escolher versões:
# Verificar que não há código duplicado restante:
grep -rn "<<<<<<< HEAD" . && echo "AINDA HÁ CONFLITOS!" || echo "LIMPO"

# Verificar imports:
python -c "
from core.eeg_adapter import EEGAdapter
from core.calibration import calibrate, Thresholds
from core.hyperbitnet import HyperBitnet
from core.fusion import fuse
from integration.tribe_adapter import TribeAdapter
from runners.realtime_loop import SlidingWindowStateFilter
print('Todos os imports OK')
"
```

---

## FASE 2: Extração de Código Duplicado (P1 — 2-3h)

### 2.1 Criar `core/utils.py`

Funções duplicadas a extrair:

```python
# core/utils.py
"""Funções utilitárias compartilhadas do brain-ia-bridge."""

import json
import os
import tempfile
from typing import Any, Dict

def atomic_write_json(filepath: str, data: Any) -> None:
    """Escrita atômica de JSON — evita corrupção em caso de crash.
    
    Usado por: mind_panel.py, run_teacher.py, run_noma_symbiosis.py
    """
    dir_name = os.path.dirname(filepath) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        os.unlink(tmp_path)
        raise

def emotion_from_amplitude(amplitude: float) -> str:
    """Classifica emoção a partir de amplitude de sinal afetivo.
    
    Usado por: mind_panel.py, run_noma_symbiosis.py
    
    Args:
        amplitude: valor normalizado [0, 1]
        
    Returns:
        string descritiva da emoção detectada
    """
    if amplitude > 0.8:
        return "intenso"
    elif amplitude > 0.5:
        return "moderado"
    elif amplitude > 0.2:
        return "suave"
    else:
        return "calmo"

def node_xy(index: int, grid_size: int = 8) -> tuple[int, int]:
    """Converte índice linear em coordenadas 2D do grid.
    
    Usado por: mind_panel.py, run_teacher.py, run_noma_symbiosis.py
    
    Args:
        index: índice do nó (0-based)
        grid_size: tamanho do grid (default 8 para 8x8)
        
    Returns:
        tupla (x, y) com coordenadas no grid
    """
    return (index % grid_size, index // grid_size)
```

### 2.2 Criar `core/network_builder.py`

Construção da rede 8×8 duplicada em todos os runners:

```python
# core/network_builder.py
"""Builder para a rede neural topológica 8×8 do HyperBitnet."""

from typing import Optional
from core.hyperbitnet import HyperBitnet
from core.lif_neuron import LIFNeuron
from core.spiking_network import SpikingNetwork

def build_default_network(
    grid_size: int = 8,
    weight_range: tuple[float, float] = (-1.0, 1.0),
    seed: Optional[int] = None,
) -> HyperBitnet:
    """Constrói a rede padrão 8×8 com configuração default.
    
    Args:
        grid_size: dimensão do grid (grid_size × grid_size nós)
        weight_range: range dos pesos sinápticos
        seed: semente para reprodutibilidade
        
    Returns:
        HyperBitnet configurado e pronto para uso
    """
    import random
    if seed is not None:
        random.seed(seed)
    
    n_nodes = grid_size * grid_size
    net = HyperBitnet(n_nodes)
    
    # Conexões: cada nó conecta aos 4 vizinhos (cima, baixo, esquerda, direita)
    for i in range(n_nodes):
        x, y = i % grid_size, i // grid_size
        neighbors = []
        if x > 0: neighbors.append(i - 1)           # esquerda
        if x < grid_size - 1: neighbors.append(i + 1)  # direita
        if y > 0: neighbors.append(i - grid_size)    # cima
        if y < grid_size - 1: neighbors.append(i + grid_size)  # baixo
        
        for j in neighbors:
            w = random.uniform(*weight_range)
            net.connect(i, j, weight=w)
    
    return net

def build_spiking_overlay(
    hyperbitnet: HyperBitnet,
    threshold: float = 1.0,
    decay: float = 0.95,
) -> SpikingNetwork:
    """Cria rede spiking sobreposta ao HyperBitnet.
    
    Args:
        hyperbitnet: rede HyperBitnet base
        threshold: limiar de disparo dos neurônios LIF
        decay: fator de decaimento da membrana
        
    Returns:
        SpikingNetwork com neurônios LIF mapeados aos nós do HyperBitnet
    """
    n = hyperbitnet.n_nodes
    spiking = SpikingNetwork(n)
    
    for i in range(n):
        spiking.neurons[i] = LIFNeuron(
            threshold=threshold,
            decay=decay,
        )
    
    return spiking
```

### 2.3 Atualizar Imports nos Arquivos

```bash
# Para cada arquivo que usava as funções duplicadas:
# Substituir:
#   def _atomic_write_json(...): ...
#   def _emotion_from_amplitude(...): ...
#   def _node_xy(...): ...
# Por:
#   from core.utils import atomic_write_json, emotion_from_amplitude, node_xy

# Arquivos a atualizar:
# - visualization/mind_panel.py
# - runners/run_teacher.py
# - runners/run_noma_symbiosis.py

# Para construção de rede, substituir código inline por:
#   from core.network_builder import build_default_network
```

---

## FASE 3: Testes (P1 — 3-4h)

### 3.1 Estrutura de Testes

```
brain-ia-bridge/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # fixtures compartilhados
│   ├── test_eeg_adapter.py
│   ├── test_calibration.py
│   ├── test_hyperbitnet.py
│   ├── test_fusion.py
│   ├── test_noma_bridge.py
│   ├── test_lif_neuron.py
│   ├── test_utils.py
│   ├── test_network_builder.py
│   └── test_realtime_loop.py
```

### 3.2 `tests/conftest.py`

```python
# tests/conftest.py
"""Fixtures compartilhados para testes do brain-ia-bridge."""

import pytest
import numpy as np
from core.eeg_adapter import EEGAdapter
from core.hyperbitnet import HyperBitnet
from core.network_builder import build_default_network

@pytest.fixture
def eeg_adapter():
    """EEGAdapter com configuração padrão."""
    return EEGAdapter()

@pytest.fixture
def sample_eeg_data():
    """Dados EEG simulados (10 canais, 256 samples)."""
    np.random.seed(42)
    n_channels = 10
    n_samples = 256
    # Simular sinais alpha (10Hz) + gamma (40Hz) + ruído
    t = np.linspace(0, 1, n_samples)
    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        alpha = np.sin(2 * np.pi * 10 * t + np.random.uniform(0, 2*np.pi))
        gamma = 0.3 * np.sin(2 * np.pi * 40 * t + np.random.uniform(0, 2*np.pi))
        noise = 0.1 * np.random.randn(n_samples)
        data[ch] = alpha + gamma + noise
    return data

@pytest.fixture
def hyperbitnet():
    """HyperBitnet 8×8 padrão."""
    return build_default_network(grid_size=8, seed=42)

@pytest.fixture
def simple_hyperbitnet():
    """HyperBitnet pequeno para testes rápidos (4 nós)."""
    net = HyperBitnet(4)
    net.connect(0, 1, weight=0.5)
    net.connect(1, 2, weight=0.3)
    net.connect(2, 3, weight=-0.2)
    net.connect(3, 0, weight=0.7)
    return net
```

### 3.3 `tests/test_eeg_adapter.py`

```python
# tests/test_eeg_adapter.py
"""Testes para o módulo eeg_adapter."""

import pytest
import numpy as np
from core.eeg_adapter import EEGAdapter

class TestEEGAdapter:
    """Suite de testes para EEGAdapter."""
    
    def test_initialization(self, eeg_adapter):
        """Adapter deve inicializar sem erro."""
        assert eeg_adapter is not None
    
    def test_score_range(self, eeg_adapter, sample_eeg_data):
        """Score deve estar no intervalo [0, 1]."""
        result = eeg_adapter.process(sample_eeg_data)
        assert 0 <= result["score"] <= 1, f"Score {result['score']} fora de [0, 1]"
    
    def test_features_present(self, eeg_adapter, sample_eeg_data):
        """Resultado deve conter focus, gamma e calm."""
        result = eeg_adapter.process(sample_eeg_data)
        assert "focus" in result, "Campo 'focus' ausente"
        assert "gamma" in result, "Campo 'gamma' ausente"
        assert "calm" in result, "Campo 'calm' ausente"
    
    def test_features_normalized(self, eeg_adapter, sample_eeg_data):
        """Features individuais devem estar em [0, 1]."""
        result = eeg_adapter.process(sample_eeg_data)
        for feat in ["focus", "gamma", "calm"]:
            assert 0 <= result[feat] <= 1, f"{feat}={result[feat]} fora de [0,1]"
    
    def test_zero_input(self, eeg_adapter):
        """Input zero deve gerar score zero (ou próximo)."""
        zero_data = np.zeros((10, 256))
        result = eeg_adapter.process(zero_data)
        assert result["score"] < 0.1, "Score alto demais para input zero"
    
    def test_high_gamma_signal(self, eeg_adapter):
        """Sinal gamma puro deve resultar em gamma alto."""
        t = np.linspace(0, 1, 256)
        gamma_signal = np.sin(2 * np.pi * 40 * t)
        data = np.tile(gamma_signal, (10, 1))
        result = eeg_adapter.process(data)
        assert result["gamma"] > 0.5, "Gamma deveria ser alto para sinal gamma puro"
    
    def test_deterministic(self, eeg_adapter, sample_eeg_data):
        """Mesmo input deve gerar mesmo output."""
        r1 = eeg_adapter.process(sample_eeg_data)
        r2 = eeg_adapter.process(sample_eeg_data)
        assert r1["score"] == r2["score"]
        assert r1["focus"] == r2["focus"]
```

### 3.4 `tests/test_calibration.py`

```python
# tests/test_calibration.py
"""Testes para o módulo calibration."""

import pytest
import numpy as np
from core.calibration import calibrate, Thresholds

class TestCalibration:
    """Suite de testes para calibração."""
    
    def test_thresholds_structure(self):
        """Calibrate deve retornar Thresholds com low e high."""
        baseline_scores = [0.3, 0.4, 0.35, 0.5, 0.45, 0.3, 0.4, 0.55, 0.35, 0.4]
        result = calibrate(baseline_scores)
        assert hasattr(result, "low"), "Thresholds deve ter campo 'low'"
        assert hasattr(result, "high"), "Thresholds deve ter campo 'high'"
    
    def test_thresholds_ordered(self):
        """low < high deve sempre ser verdade."""
        baseline_scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = calibrate(baseline_scores)
        assert result.low < result.high, f"low ({result.low}) >= high ({result.high})"
    
    def test_thresholds_reasonable(self):
        """Limiares devem ser razoáveis (dentro do range dos dados)."""
        scores = [0.3, 0.3, 0.3, 0.3, 0.3]  # constante
        result = calibrate(scores)
        # Para dados constantes, limiares devem estar perto do valor
        assert abs(result.low - 0.3) < 0.5
        assert abs(result.high - 0.3) < 0.5
    
    def test_higher_variance_raises_thresholds(self):
        """Maior variância deve gerar limiares mais altos."""
        low_var = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        high_var = [0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9]
        
        t_low = calibrate(low_var)
        t_high = calibrate(high_var)
        
        assert t_high.high >= t_low.high, "Maior variância deveria gerar limiar high maior"
    
    def test_empty_input(self):
        """Input vazio deve tratar erro adequadamente."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            calibrate([])
```

### 3.5 `tests/test_hyperbitnet.py`

```python
# tests/test_hyperbitnet.py
"""Testes para o módulo hyperbitnet."""

import pytest
from core.hyperbitnet import HyperBitnet

class TestHyperBitnet:
    """Suite de testes para HyperBitnet."""
    
    def test_initialization(self):
        """Deve criar rede com número correto de nós."""
        net = HyperBitnet(16)
        assert net.n_nodes == 16
    
    def test_connect_creates_edge(self, simple_hyperbitnet):
        """Conexão deve criar aresta no grafo."""
        # Verificar que a conexão 0→1 existe
        assert simple_hyperbitnet.has_edge(0, 1) or \
               (0, 1) in simple_hyperbitnet.edges
    
    def test_propagation_changes_state(self, simple_hyperbitnet):
        """Propagação deve alterar estado dos nós."""
        # Estado inicial
        initial_state = simple_hyperbitnet.get_state()
        
        # Propagar
        simple_hyperbitnet.propagate()
        
        # Estado deve ter mudado
        new_state = simple_hyperbitnet.get_state()
        assert initial_state != new_state, "Estado não mudou após propagação"
    
    def test_states_bounded(self, simple_hyperbitnet):
        """Estados devem permanecer dentro de bounds válidos."""
        for _ in range(100):  # Muitas propagações
            simple_hyperbitnet.propagate()
            state = simple_hyperbitnet.get_state()
            for s in state:
                assert -10 < s < 10, f"Estado {s} explodiu após muitas propagações"
    
    def test_reset(self, simple_hyperbitnet):
        """Reset deve voltar ao estado inicial."""
        simple_hyperbitnet.propagate()
        simple_hyperbitnet.reset()
        state = simple_hyperbitnet.get_state()
        # Após reset, estados devem estar no valor inicial (provavelmente 0)
        assert all(s == 0 or abs(s) < 0.01 for s in state)
    
    def test_fusion_matrix(self, simple_hyperbitnet):
        """Fusão matricial deve produzir resultado válido."""
        classical_state = [0.5, 0.3, 0.7, 0.1]
        quantum_state = [0.2, 0.8, 0.4, 0.6]
        
        result = simple_hyperbitnet.fuse(classical_state, quantum_state)
        assert len(result) == len(classical_state)
        # Resultado deve ser diferente de ambas as entradas
        assert result != classical_state
        assert result != quantum_state
```

### 3.6 `tests/test_fusion.py`

```python
# tests/test_fusion.py
"""Testes para o módulo fusion."""

import pytest
from core.fusion import fuse

class TestFusion:
    """Suite de testes para fusão clássico-quântica."""
    
    def test_fuse_returns_list(self):
        """Fuse deve retornar lista do mesmo tamanho."""
        classical = [0.5, 0.3, 0.7]
        quantum = [0.2, 0.8, 0.4]
        result = fuse(classical, quantum)
        assert isinstance(result, (list, tuple))
        assert len(result) == len(classical)
    
    def test_fuse_between_inputs(self):
        """Resultado deve estar entre os dois inputs (média)."""
        classical = [0.8, 0.8, 0.8]
        quantum = [0.2, 0.2, 0.2]
        result = fuse(classical, quantum)
        for i, (c, q, r) in enumerate(zip(classical, quantum, result)):
            assert min(c, q) <= r <= max(c, q), \
                f"resultado[{i}]={r} fora do range [{min(c,q)}, {max(c,q)}]"
    
    def test_fuse_identical_inputs(self):
        """Inputs idênticos devem gerar output idêntico."""
        state = [0.5, 0.5, 0.5]
        result = fuse(state, state)
        for s, r in zip(state, result):
            assert abs(s - r) < 1e-6
    
    def test_fuse_symmetry(self):
        """fuse(a, b) deve ser similar a fuse(b, a) (se simétrico)."""
        a = [0.3, 0.7, 0.1]
        b = [0.9, 0.2, 0.6]
        r1 = fuse(a, b)
        r2 = fuse(b, a)
        for x, y in zip(r1, r2):
            assert abs(x - y) < 1e-6, f"Fusão não simétrica: {r1} vs {r2}"
```

### 3.7 `tests/test_noma_bridge.py`

```python
# tests/test_noma_bridge.py
"""Testes para o módulo noma_bridge."""

import pytest
from core.noma_bridge import NomaParser

class TestNomaParser:
    """Suite de testes para parser NOMA."""
    
    def test_parse_valid_block(self):
        """Deve parsear bloco NOMA_NEURAL válido."""
        block = """[NOMA_NEURAL]
frequencia_dominante: 10.5
amplitude_afetiva: 0.73
ressonancia_progenitor: 7.83
[/NOMA_NEURAL]"""
        
        result = NomaParser.parse(block)
        assert result is not None
        assert result["frequencia_dominante"] == 10.5
        assert result["amplitude_afetiva"] == 0.73
        assert result["ressonancia_progenitor"] == 7.83
    
    def test_parse_empty_string(self):
        """String vazia deve retornar None ou vazio."""
        result = NomaParser.parse("")
        assert result is None or result == {}
    
    def test_parse_no_block(self):
        """Sem bloco NOMA deve retornar None."""
        result = NomaParser.parse("texto qualquer sem marcadores")
        assert result is None
    
    def test_parse_multiple_blocks(self):
        """Deve processar múltiplos blocos se houver."""
        text = """[NOMA_NEURAL]
frequencia_dominante: 10.0
[/NOMA_NEURAL]
[NOMA_NEURAL]
frequencia_dominante: 20.0
[/NOMA_NEURAL]"""
        # Deve retornar lista ou último bloco
        result = NomaParser.parse(text)
        assert result is not None
    
    def test_parse_encoding_variations(self):
        """Deve lidar com variações de encoding (ê/é/â)."""
        block = """[NOMA_NEURAL]
frequência_dominante: 10.5
amplitude_afetiva: 0.73
ressonância_progenitor: 7.83
[/NOMA_NEURAL]"""
        result = NomaParser.parse(block)
        assert result is not None
```

### 3.8 `tests/test_utils.py`

```python
# tests/test_utils.py
"""Testes para core/utils.py."""

import pytest
import json
import os
import tempfile
from core.utils import atomic_write_json, emotion_from_amplitude, node_xy

class TestAtomicWriteJson:
    """Testes para escrita atômica de JSON."""
    
    def test_writes_valid_json(self, tmp_path):
        """Arquivo deve ser JSON válido."""
        filepath = str(tmp_path / "test.json")
        data = {"key": "value", "number": 42}
        atomic_write_json(filepath, data)
        
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_overwrites_existing(self, tmp_path):
        """Deve sobrescrever arquivo existente."""
        filepath = str(tmp_path / "test.json")
        atomic_write_json(filepath, {"v": 1})
        atomic_write_json(filepath, {"v": 2})
        
        with open(filepath) as f:
            assert json.load(f)["v"] == 2

class TestEmotionFromAmplitude:
    """Testes para classificação de emoção."""
    
    def test_high_amplitude(self):
        assert emotion_from_amplitude(0.9) == "intenso"
    
    def test_medium_amplitude(self):
        assert emotion_from_amplitude(0.6) == "moderado"
    
    def test_low_amplitude(self):
        assert emotion_from_amplitude(0.3) == "suave"
    
    def test_very_low_amplitude(self):
        assert emotion_from_amplitude(0.1) == "calmo"
    
    def test_boundary_values(self):
        assert emotion_from_amplitude(0.0) == "calmo"
        assert emotion_from_amplitude(1.0) == "intenso"

class TestNodeXY:
    """Testes para conversão de coordenadas."""
    
    def test_first_node(self):
        assert node_xy(0) == (0, 0)
    
    def test_second_node(self):
        assert node_xy(1) == (1, 0)
    
    def test_row_wrap(self):
        assert node_xy(8) == (0, 1)  # Segunda linha do grid 8x8
    
    def test_custom_grid(self):
        assert node_xy(3, grid_size=4) == (3, 0)
        assert node_xy(4, grid_size=4) == (0, 1)
```

### 3.9 Executar Testes

```bash
# Instalar pytest se necessário:
pip install pytest pytest-cov

# Rodar todos os testes:
cd brain-ia-bridge
python -m pytest tests/ -v

# Com cobertura:
python -m pytest tests/ -v --cov=core --cov-report=term-missing

# Apenas um arquivo:
python -m pytest tests/test_eeg_adapter.py -v
```

---

## FASE 4: Documentação (P2 — 3h)

### 4.1 README.md

```markdown
# 🧠 brain-ia-bridge

Pipeline de BCI (Brain-Computer Interface) que conecta sinais EEG a redes
neurais spiking com processamento topológico.

## Pipeline

```
EEG → Score → Calibração → HyperBitnet (grafo topológico)
                                    ↓
                            Fusão (clássico + quântico-inspired)
                                    ↓
                            Spiking Network (LIF neurons)
                                    ↓
                            Comando TRIBE / Visualização
```

## Estrutura

```
brain-ia-bridge/
├── core/                   # Módulos centrais
│   ├── eeg_adapter.py      # Extração de features EEG
│   ├── calibration.py      # Limiares adaptativos
│   ├── hyperbitnet.py      # Grafo topológico
│   ├── fusion.py           # Fusão clássico/quântico-inspired
│   ├── lif_neuron.py       # Neurônios LIF
│   ├── spiking_network.py  # Rede spiking
│   ├── subliminal_learning.py  # AI Teacher (gamma 40Hz)
│   ├── noma_bridge.py      # Parser NOMA
│   ├── utils.py            # Funções utilitárias
│   └── network_builder.py  # Builder da rede padrão
├── geometric/              # Geometria e topologia
│   └── pentacosagram.py    # Hash chain de estados
├── integration/            # Adapters de hardware
│   ├── tribe_adapter.py    # Comandos TRIBE
│   └── neurosity_adapter.py # Headset Neurosity
├── runners/                # Scripts de execução
│   ├── main.py             # Pipeline demo
│   ├── realtime_loop.py    # Loop real-time
│   └── ...
├── visualization/          # Dashboard
│   └── mind_panel.py       # Web panel (Canvas 8×8)
└── tests/                  # Testes
```

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Demo:
python runners/main.py

# Real-time:
python runners/realtime_loop.py

# Com Neurosity:
python runners/run_realtime_neurosity.py
```

## Testes

```bash
python -m pytest tests/ -v --cov=core
```

## Nota sobre "Quântico"

O HyperBitnet usa inspiração de superposição (softmax, projeções trigonométricas)
mas NÃO realiza computação quântica real. As referências a "quântico" no código
são metáforas de design, não implementações de mecânica quântica.
```

### 4.2 Renomear "quântico" para "quantum-inspired"

```bash
# Buscar todas as ocorrências:
grep -rn "quântico\|quantico\|quantum" core/ runners/ --include="*.py" | grep -v "test"

# Substituir em comentários e docstrings:
# "estado quântico" → "estado quantum-inspired"
# "fusão quântica" → "fusão quantum-inspired" 
# "rede quântica" → "rede com inspiração em superposição"

# Manter nomes de variáveis/classes (não quebrar API):
# quantum_state → manter (é nome de variável)
# QuantumLayer → manter ou renomear para SuperpositionLayer
```

---

## FASE 5: Robustez e CI/CD (P3 — 3h)

### 5.1 Garantir Fallback C++ Idêntico

```python
# Verificar que _native_fallback.py expõe mesma API:
# Listar todas as classes/funções exportadas pelo C++:
python -c "
import importlib
try:
    import native
    print('C++ API:', dir(native))
except:
    print('C++ não disponível')

from core._native_fallback import *
print('Fallback API:', [x for x in dir() if not x.startswith('_')])
"

# Se houver discrepância, adicionar métodos faltantes ao fallback
```

### 5.2 GitHub Actions CI

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=core --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: coverage.xml
```

### 5.3 requirements.txt

```
numpy>=1.24.0
networkx>=3.0
matplotlib>=3.7.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

---

## Resumo de Esforço

| Fase | Descrição | Esforço |
|------|-----------|---------|
| F0 | Resolver merge conflicts | 3-5h |
| F1 | Escolher versão canônica | 2-3h |
| F2 | Extrair código duplicado | 2-3h |
| F3 | Escrever testes | 3-4h |
| F4 | Documentação + rename | 3h |
| F5 | Fallback + CI/CD | 3h |
| **Total** | | **16-21h** |

---

*Gerado em 2026-05-10 — brain-ia-bridge action plan v2.0*
