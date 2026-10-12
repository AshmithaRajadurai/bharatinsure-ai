# Structured Pruning Research for CPU-Deployed Multilingual LLMs
**BharatInsure AI — Architectural Investigation & Deployment Feasibility**
**Date:** 2026-10-10

---

## 1. Executive Summary & Pruning Taxonomy

Pruning reduces deep learning model parameter counts by removing redundant weights. However, the architectural method of pruning fundamentally dictates whether the model can run efficiently on commodity CPU hardware.

| Pruning Paradigm | Mechanism | Hardware Speedup on CPU? | GGUF / Ollama Compatible? | Factual Recovery Effort |
| :--- | :--- | :--- | :--- | :--- |
| **Unstructured Sparsity** | Zeros out individual weight elements below an importance threshold ($\|W_{ij}\| < \epsilon$). | ❌ **No**. SIMD instructions (AVX2, AVX-512) cannot execute sparse matrices efficiently without sparse-matrix libraries like SciPy or CSR format, which incur heavy pointer overhead. | ❌ **No**. GGUF kernels are dense-block quantized; 0-weights take up identical storage and compute. | High (Irregular gradient updates). |
| **Semi-Structured (2:4 Sparsity)** | Enforces exactly 2 zeros out of every 4 consecutive values. | ❌ **No**. Requires dedicated NVIDIA Ampere/Hopper Sparse Tensor Cores; not supported on consumer Intel/AMD laptop CPUs. | ❌ **No**. | Medium. |
| **Structured Pruning** | **Physically deletes complete structural components:** attention heads, entire MLP intermediate neuron channels, or transformer layers. | ✅ **Yes**. Output matrices are strictly smaller, standard dense matrices. Directly reduces FLOPs and KV-cache size on standard CPU SIMD. | ✅ **Yes**. Directly converts to dense Hugging Face architecture, which converts to native GGUF and Ollama. | **Required** (Requires LoRA fine-tuning on calibration data). |

---

## 2. Weight Compatibility & Runtime Feasibility

### 2.1 The GGUF / Ollama Constraint
Ollama relies on the `llama.cpp` runtime. `llama.cpp` executes optimized matrix multiplication routines (using SIMD vector intrinsics like AVX2, AVX-512, or ARM NEON) that require dense multidimensional weight arrays.

- **Why Structured Pruning Works for Ollama:**
  When structured pruning is applied via frameworks like **LLM-Pruner** or **Wanda**:
  - If a model has hidden dimension $d_{model} = 2048$ and MLP dimension $d_{mlp} = 11008$, structured pruning reduces $d_{mlp}$ to, for example, $7168$, or prunes 8 of 16 attention heads.
  - The resulting weight tensors (e.g., `q_proj.weight`, `gate_proj.weight`) are resized to standard, smaller 2D PyTorch matrices.
  - Because the architecture remains standard Dense Transformer with modified configuration (`config.json`), `llama.cpp`'s `convert_hf_to_gguf.py` can convert the exported checkpoint into FP16 GGUF, and `llama-quantize` can compress it into `Q4_K_M`.

### 2.2 Preserving Quantization Alignment
- Ollama uses block-level quantization (e.g., block size 32 for Q4_K_M).
- **Rule:** The remaining matrix dimensions (e.g., intermediate size and hidden size) after structured channel pruning must remain divisible by 32 or 64. If dimensions do not align with quantization block sizes, GGUF conversion fails with dimension alignment assertion errors.

---

## 3. Calibration Data Requirements

Structured pruning removes entire parameter channels, which can cause significant damage to factual knowledge if the importance estimation is inaccurate.

### 3.1 Sensitivity Estimation
Modern pruning frameworks compute the Taylor expansion or Hessian matrix of the loss with respect to weight activations:
$$I_j = \sum_{k} \left| W_{jk} \frac{\partial \mathcal{L}}{\partial W_{jk}} \right|$$
This requires a representative **calibration dataset** to identify which channels are critical for specific reasoning tasks.

### 3.2 Domain-Specific Calibration for BharatInsure AI
- **Risk of General Calibration:** Using generic web corpora (e.g., C4, Wikitext-2) causes the importance metric to treat general English grammar as essential while deeming numerical regulatory thresholds (e.g., "36 months", "₹2,00,000", "Section 80D") disposable.
- **Mandatory Domain Corpus:** The calibration dataset must consist of:
  - 256 high-density passages from Indian insurance policies (health exclusions, waiting periods, room rent caps, claims).
  - 128 multi-turn multilingual financial conversations in Tamil, Hindi, and English.
  - Balanced representation of exact financial figures and legal conditions.

---

## 4. Post-Pruning Fine-Tuning & Parameter Recovery

Structured pruning typically causes an initial drop of 15% to 35% in factual accuracy and domain reasoning immediately after pruning. Parameter recovery through fine-tuning is required before any deployment.

```
+---------------------+     +--------------------+     +---------------------+
| Pre-trained 3B      | --> | Structured Pruning | --> | Severe Factual Drop |
| Baseline (100% Acc) |     | (Delete 30% Heads) |     | (~65% Acc, High PPL)|
+---------------------+     +--------------------+     +---------------------+
                                                                  |
                                                                  v
+---------------------+     +--------------------+     +---------------------+
| Deployed Pruned     | <-- | Merge LoRA Weights | <-- | QLoRA Fine-Tuning   |
| GGUF (88-92% Acc)   |     | Into Dense Model   |     | on Insurance Corpus |
+---------------------+     +--------------------+     +---------------------+
```

### 4.1 Fine-Tuning Strategy: LoRA / QLoRA
- **Target Modules:** Apply LoRA adapters to all remaining linear layers: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- **Hyperparameters:**
  - Rank $r = 32$, Alpha $\alpha = 64$
  - Learning Rate: $2 \times 10^{-4}$ with Cosine Annealing schedule
  - Warmup Steps: 100
  - Epochs: 3 to 5 epochs over the BharatInsure domain training set
- **Output:** LoRA weights are merged back into the base pruned weights (`model.merge_and_unload()`) to produce a standalone dense PyTorch checkpoint.

---

## 5. End-to-End CPU Deployment Pipeline

1. **Step 1: Pruning in PyTorch**
   ```bash
   python -m llm_pruner.prune \
       --base_model Qwen/Qwen2.5-3B-Instruct \
       --pruning_ratio 0.25 \
       --block_wise \
       --calibration_dataset bharat_insurance_calibration.jsonl \
       --output_dir ./models/qwen2.5-2.3b-pruned
   ```
2. **Step 2: Domain Recovery Fine-Tuning**
   ```bash
   python fine_tune_lora.py \
       --model_path ./models/qwen2.5-2.3b-pruned \
       --data_path ./data/insurance_qa_train.jsonl \
       --output_dir ./models/qwen2.5-2.3b-recovered
   ```
3. **Step 3: GGUF Conversion**
   ```bash
   python llama.cpp/convert_hf_to_gguf.py ./models/qwen2.5-2.3b-recovered \
       --outfile ./models/qwen2.5-2.3b-pruned.fp16.gguf
   ```
4. **Step 4: 4-bit Quantization**
   ```bash
   llama.cpp/build/bin/llama-quantize \
       ./models/qwen2.5-2.3b-pruned.fp16.gguf \
       ./models/qwen2.5-2.3b-pruned.Q4_K_M.gguf Q4_K_M
   ```
5. **Step 5: Ollama Modelfile Creation**
   ```dockerfile
   FROM ./models/qwen2.5-2.3b-pruned.Q4_K_M.gguf
   PARAMETER temperature 0.2
   PARAMETER num_ctx 1536
   ```
   ```bash
   ollama create qwen2.5-pruned:2.3b -f Modelfile
   ```

---

## 6. Engineering Recommendation & Why In-Place Production Pruning Was Avoided

1. **Production Safety:** Never prune production models in-place. Destructive pruning without multi-GPU calibration and recovery fine-tuning introduces hallucinations, broken JSON outputs, and loss of Indian multilingual tokens.
2. **Pre-Trained Architectures vs. Custom Pruned Models:**
   - Pre-trained models like `Qwen2.5-0.5B` have undergone trillions of tokens of pre-training and alignment on optimized architectures.
   - A custom pruned 3B model (e.g., pruned to ~2B) requires significant GPU compute hours for proper LoRA recovery.
   - For resource-constrained local CPU laptops with 16 GB RAM, testing pre-quantized GGUF models (`Qwen2.5-3B` vs `Qwen2.5-0.5B`) provides a verified, reproducible baseline without risk of degrading domain knowledge.
