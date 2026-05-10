# brain-ia-bridge — Análise e Compreensão do Projeto

**Data:** 2026-05-10  
**Autor:** Análise automática (pós-resolução de conflitos)  
**Status:** Relatório técnico

---

## 1. O Que É o brain-ia-bridge

O brain-ia-bridge é um **pipeline de BCI (Brain-Computer Interface)** que conecta sinais cerebrais (EEG) a redes neurais spiking com processamento topológico. O objetivo final é permitir **comunicação latente** entre um cérebro humano e um modelo de IA — sem traduzir para texto, preservando a geometria do sinal.

### A Ideia Central

```
Tradução (convencional):
  Cérebro → texto → tokens → processamento → tokens → texto → Cérebro
  (perde geometria a cada conversão)

Comunicação latente (brain-ia-bridge):
  Cérebro → espaço latente ← Modelo de IA
  (preserva a topologia)
```

A premissa é que **mapas se comunicam pela geometria, não pela linguagem**. Um cérebro humano e um modelo de IA são ambos "mapas" — organizam conhecimento em regiões, caminhos e conexões. A diferença é o substrato (biológico vs silício), mas a estrutura é a mesma: **topológica**.

---

## 2. Arquitetura do Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  EEG Input  │────▶│  Calibração  │────▶│  HyperBitnet │────▶│  TRIBE Cmd   │
│  (features) │     │  (thresholds)│     │  (grafo)     │     │  (comando)   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     focus                μ ± σ            estados clássicos     CONFIRM_INTENT
     gamma                adaptive         + quânticos           TRANSITION
     calm                                      ↓                  IDLE
                                         ┌──────────┐
                                         │  Fusão   │
                                         │ clássico │
                                         │ + quânt. │
                                         └──────────┘
```

### 2.1 EEG Adapter (`core/eeg_adapter.py`)

Recebe features do headset EEG e calcula um score de ativação normalizado [0, 1]:

```python
score = focus × 0.5 + gamma × 0.3 + (1 - calm) × 0.2
```

- **focus** (peso 0.5): sinal primário de intenção
- **gamma** (peso 0.3): engajamento cognitivo (banda 40Hz)
- **calm** (peso 0.2): inverso — menos calma = mais ativação

### 2.2 Calibração (`core/calibration.py`)

Coleta uma baseline em repouso e calcula limiares adaptativos:

```
low  = μ + 1σ   → fronteira de transição
high = μ + 2σ   → fronteira de confirmação
```

Estados discretos resultantes:

| Estado | Significado |
|--------|-------------|
| `-1`   | Desconexão / idle |
| `0`    | Ambiguo / transição |
| `1`    | Intenção confirmada |

### 2.3 HyperBitnet (`core/hyperbitnet.py`)

Rede neural-topológica com estados clássicos e quânticos simulados:

- **Estados clássicos** (`states`): valores [0, 1] biased pela intenção + ruído
- **Estados quânticos** (`quantum_states`): projeção cosseno que modela superposição

```python
angle = π × (1 - classical)
quantum = (1 + cos(angle)) / 2
```

Ativação alta → ângulo próximo de 0 → quantum próximo de 1 (coerência máxima).  
Ativação baixa → ângulo próximo de π → quantum próximo de 0 (coerência mínima).

### 2.4 Fusão (`core/fusion.py`)

Combina estados clássicos e quânticos em um vetor de intenção:

```python
intent[i] = (classical[i] + quantum[i]) / 2
```

Mantém valores em [0, 1] — pronto para o adapter TRIBE.

### 2.5 TRIBE Adapter (`integration/tribe_adapter.py`)

Traduz o vetor de intenção contínuo em comando simbólico:

| Energia média | Comando |
|---------------|---------|
| ≥ 0.65 | `CONFIRM_INTENT` |
| ≥ 0.40 | `TRANSITION` |
| < 0.40 | `IDLE` |

### 2.6 Filtro Temporal (`realtime_loop.py`)

`SlidingWindowStateFilter` — janela deslizante de 8 estados com limiar de 5 votos:

- Evita falsos positivos em spikes isolados
- Exige consenso (5/8 votos iguais) para mudar estado
- Transição suave entre estados

---

## 3. Estrutura de Arquivos

```
brain-ia-bridge/
├── brain-ia-bridge-core-vision.md      # Visão fundacional (Santaló, Goodfire, Interlat)
├── brain-ia-bridge-action-plan.md      # Plano de ação 5 fases (16-21h)
├── Brain_AI/brain-ia-bridge/
│   ├── README.md                       # Documentação principal
│   ├── CLAUDE.md                       # Specs da UI (PyGame)
│   ├── docs/architecture.md            # Arquitetura técnica
│   ├── requirements.txt                # Dependências
│   ├── setup_native.py                 # Build do módulo C++
│   ├── noma_memory.bin                 # Memória serializada (NOMA)
│   ├── src/
│   │   ├── core/                       # Módulos centrais
│   │   │   ├── eeg_adapter.py          # Score EEG
│   │   │   ├── calibration.py          # Thresholds adaptativos
│   │   │   ├── hyperbitnet.py          # Grafo topológico
│   │   │   ├── fusion.py               # Fusão clássico/quântico
│   │   │   ├── lif_neuron.py           # Neurônio LIF (stub)
│   │   │   ├── synapse_stdp.py         # STDP (stub)
│   │   │   ├── spiking_network.py      # Rede spiking
│   │   │   ├── subliminal_learning.py  # AI Teacher (gamma 40Hz)
│   │   │   ├── noma_bridge.py          # Parser NOMA
│   │   │   ├── sensory_encoder.py      # Encoder sensorial
│   │   │   ├── canonical_hasher.py     # Hash canônico
│   │   │   ├── _native_core.cpp        # Módulo C++ nativo
│   │   │   ├── _native_fallback.py     # Fallback Python
│   │   │   └── _native_loader.py       # Loader do módulo nativo
│   │   ├── integration/
│   │   │   ├── tribe_adapter.py        # Comandos TRIBE
│   │   │   └── neurosity_adapter.py    # Adapter Neurosity SDK
│   │   ├── governance/
│   │   │   └── pentacosagram.py        # Hash chain de estados
│   │   ├── runners/
│   │   │   ├── main.py                 # Pipeline demo
│   │   │   ├── realtime_loop.py        # Loop realtime
│   │   │   ├── run_teacher.py          # AI Teacher loop
│   │   │   ├── run_noma_symbiosis.py   # Simbiose NOMA
│   │   │   └── run_realtime_neurosity.py
│   │   ├── mind_panel.py               # Dashboard web (Canvas 8×8)
│   │   ├── mind_panel.html             # Frontend do dashboard
│   │   └── brain_orchestrator.py       # Orquestrador central
│   └── tests/                          # Suite de testes (11 arquivos)
│       ├── test_canonical_hasher.py
│       ├── test_lif_neuron.py
│       ├── test_network_dynamics.py
│       ├── test_noma_bridge.py
│       ├── test_pentacosagram.py
│       ├── test_persistence.py
│       ├── test_sensory_encoder.py
│       ├── test_spiking_network.py
│       ├── test_subliminal_learning.py
│       └── test_synapse_stdp.py
```

---

## 4. Os Três Pilares Teóricos

### 4.1 Santaló — Invariantes Tensoriais

Luis A. Santaló (1970) formalizou que operações vetoriais/tensoriais têm **caráter intrínseco e invariante** — não dependem do sistema de coordenadas. Aplicado ao BCI:

- Features EEG atuais (focus, gamma, calm) são "coordenadas" — dependem do hardware
- Precisamos de **invariantes tensoriais** que capturem a essência do sinal
- Independente do headset, calibração, montagem — a geometria se preserva

### 4.2 Goodfire — Regiões Semânticas

A pesquisa da Goodfire AI mostra que a estrutura interna de modelos de IA se comporta como uma **rede de conceitos conectados**, não como camadas de neurônios:

- Pequenos subconjuntos de componentes funcionais explicam grande parte do comportamento
- Podemos mapear, navegar e esculpir essas regiões
- Decomposição de parâmetros revela subcomponentes funcionais

### 4.3 Interlat — Comunicação Latente

O paper "Enabling Agents to Communicate Entirely in Latent Space" (2025) demonstrou que:

- Modelos podem trocar informação diretamente nos seus hidden states
- Vetores latentes são mais ricos que tokens discretos
- Interlat supera chain-of-thought fine-tuned em certas tarefas

---

## 5. Módulos Avançados (Não-Convencionais)

### 5.1 NOMA Bridge (`noma_bridge.py`)

Parser para blocos `[NOMA_NEURAL]` — um protocolo de comunicação neural:

```
[NOMA_NEURAL]
frequencia_dominante: 10.5
amplitude_afetiva: 0.73
ressonancia_progenitor: 7.83
[/NOMA_NEURAL]
```

### 5.2 Subliminal Learning (`subliminal_learning.py`)

"AI Teacher" — usa gamma 40Hz (frequência associada a consciência e binding perceptual) como sinal de ensino para a rede spiking. Conceito de **aprendizado subliminal**: a rede aprende padrões sem supervisão explícita.

### 5.3 Pentacosagram (`governance/pentacosagram.py`)

Hash chain criptográfica de estados — governance/audit trail. Cada estado da rede é hasheado e encadeado, criando um registro imutável da evolução do sistema.

### 5.4 Mind Panel (`mind_panel.py` + `.html`)

Dashboard web com Canvas 8×8 que mostra:
- Estado dos neurônios (brilho proporcional à ativação)
- Força das sinapses
- Nível de intenção
- Coerência quântica

### 5.5 Módulo Nativo C++ (`_native_core.cpp`)

Implementação C++ de alta performance do motor de simulação. Fallback Python disponível (`_native_fallback.py`) para portabilidade.

---

## 6. Estado Atual do Projeto

### ✅ O que existe e funciona:
- Pipeline completo: EEG → Score → Calibração → HyperBitnet → Fusão → TRIBE
- Loop realtime com filtro temporal (SlidingWindow)
- Módulo C++ compilado (.so)
- 11 arquivos de testes
- Dashboard Mind Panel (web)
- Documentação completa

### ⚠️ O que precisa de atenção:
- **Merge conflicts** recém-resolvidos (Fase 0 do action plan concluída)
- `lif_neuron.py` e `synapse_stdp.py` são stubs (7 linhas cada)
- Adapter Neurosity é mock — precisa do SDK real
- `noma_memory.bin` — arquivo binário no repo (deveria ser .gitignore?)

### 📋 Próximos passos (do action plan):
- **F1**: Escolher versão canônica por módulo ✅ (feito junto com resolução de conflitos)
- **F2**: Extrair código duplicado → `utils.py` + `network_builder.py`
- **F3**: Expandir suite de testes
- **F4**: Documentação + rename "quântico" → "quantum-inspired"
- **F5**: CI/CD com GitHub Actions

---

## 7. Dependências

```
numpy>=1.24.0
networkx>=3.0
matplotlib>=3.7.0
scipy>=1.10.0
```

**Nota**: A versão resolvida (Branch) do HyperBitnet **não usa NetworkX nem scipy** — usa apenas `math` e `random` do stdlib. As dependências no `requirements.txt` são para os módulos avançados (spiking_network, subliminal_learning, etc).

---

## 8. Observações Técnicas

1. **Dualidade de implementações**: O projeto teve duas versões paralelas (HEAD com NetworkX/scipy vs Branch com stdlib). A resolução escolheu a Branch (mais leve), mas a versão HEAD com grafo NetworkX ainda existe no código dos módulos avançados.

2. **"Quântico" é metáfora**: O HyperBitnet usa inspiração de superposição (projeção cosseno, softmax) mas **não realiza computação quântica real**. O action plan recomenda renomear para "quantum-inspired" para evitar confusão.

3. **Pipeline é determinístico**: Para mesmos inputs, o pipeline produz sempre os mesmos outputs (desde que a seed seja fixa). O ruído é controlado.

4. **Escalabilidade**: O HyperBitnet atual usa 8 nós. O `network_builder` proposto no action plan permitiria grids maiores (16×16, 32×32) com topologia configurável.

5. **Gap BCI real**: O pipeline atual funciona com dados simulados. A integração real com headset EEG (Neurosity Crown) requer o SDK e adaptação do `neurosity_adapter.py`.

---

*"O cálculo vetorial e tensorial são útiles porque não introduzem elementos estranhos, pois, ainda que se apoiem em sistemas de coordenadas, seus elementos e operações têm caráter intrínseco e invariante."*  
— Luis A. Santaló, 1961

---

*Relatório gerado em 2026-05-10.*
