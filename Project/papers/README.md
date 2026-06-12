# LLNL Internship Reading List
**Research Plan: Advancing Relational Reasoning in Vision-Language Models via Anchored Representations and Concept Bottlenecks**

Papers are numbered in order of reading priority, as outlined in the internship research plan.

---

## 🔴 Priority 1 — Mentor's Foundational Work (Read First)

These papers form the direct theoretical backbone of the internship. Understanding them deeply is mandatory before Week 1 ends.

| # | File | Paper | Venue | Why It Matters |
|---|------|-------|-------|----------------|
| 1 | `01_Anchoring_for_Training_Vision_Models_NeurIPS2024.pdf` | **On the Use of Anchoring for Training Vision Models** | NeurIPS 2024 | Core method: introduces the masking regularizer λ to prevent shortcut learning in reference-residual pairs. The primary anchoring protocol you will extend to VLMs. |
| 2 | `02_DeltaUQ_Stochastic_Data_Centering_NeurIPS2022.pdf` | **Single Model Uncertainty Estimation via Stochastic Data Centering (Δ-UQ)** | NeurIPS 2022 | Original anchoring/Δ-UQ framework. Explains the coordinate transformation theory, NTK analysis, and why anchored predictions yield calibrated epistemic uncertainty. |
| 3 | `03_CB-SAE_Concept_Bottleneck_Sparse_Autoencoders_CVPR2026.pdf` | **Interpretable & Steerable Concept Bottleneck Sparse Autoencoders (CB-SAE)** | CVPR 2026 | Mentor's accepted paper. Details the I·S scoring metric and CLIP-Dissect alignment. Direct predecessor to the RCB-SAE trajectory. |
| 4 | `04_DECIDER_Foundation_Model_Priors_ECCV2024.pdf` | **DECIDER: Leveraging Foundation Model Priors for Improved Model Failure Detection** | ECCV 2024 | Prior Induced Model (PIM) + cross-entropy disagreement-based failure flagging. Foundation for the R-DECIDER trajectory. |

---

## 🟠 Priority 2 — Core External Papers (Read by Week 2)

Critical external state-of-the-art work that defines the problem space and proposes competing solutions.

| # | File | Paper | Venue | Why It Matters |
|---|------|-------|-------|----------------|
| 5 | `05_Test-Time_Matching_Compositional_Reasoning_ICLR2026.pdf` | **Test-Time Matching: Unlocking Compositional Reasoning in Multimodal Models** | ICLR 2026 | Supervision-free iterative bootstrapping; introduces GroupMatch metric. Key inspiration for Trajectory 3 (Transductive Test-Time Anchoring). |
| 6 | `06_Compositional_Grounding_Gap_REGROUND.pdf` | **The Compositional Grounding Gap: Why VLMs Fail at Relational Reasoning** | OpenReview 2025 | Mathematically proves that pooled visual features destroy relational geometry (accuracy degrades as O(1/n!)). Introduces REGROUND test-time intervention. Establishes the theoretical boundary of the problem. |
| 7 | `07_CREPE_Learnable_Prompting_CLIP_Visual_Relationships_ICASSP2024.pdf` | **CREPE: Learnable Prompting With CLIP Improves Visual Relationship Prediction** | ICASSP 2024 | LLNL paper. Union bounding box + contrastive training for predicate extraction. Blueprint for spatial localization anchoring in RCB-SAE. |
| 8 | `08_SATORI-R1_Spatial_Grounding_Verifiable_Rewards.pdf` | **SATORI-R1: Incentivizing Multimodal Reasoning with Spatial Grounding and Verifiable Rewards** | arXiv 2025 | Decomposes VQA into verifiable stages with explicit reward signals for spatial anchoring. Motivates RL-based spatial grounding approach. |

---

## 🟡 Priority 3 — Benchmarks & Supporting Papers (Read by Week 3)

These provide the evaluation datasets and additional context for the broader field.

| # | File | Paper | Venue | Why It Matters |
|---|------|-------|-------|----------------|
| 9 | `09_ConMe_Compositional_Reasoning_Evaluation_NeurIPS2024.pdf` | **ConMe: Rethinking Evaluation of Compositional Reasoning for Modern VLMs** | NeurIPS 2024 | Adversarial compositional benchmark; VLM-generated hard negatives cause 33% performance drops in SOTA models. Key evaluation benchmark for all three trajectories. |
| 10 | `10_SpatialVLM_Spatial_Reasoning_CVPR2024.pdf` | **SpatialVLM: Endowing Vision-Language Models with Spatial Reasoning Capabilities** | CVPR 2024 | Baseline for spatial reasoning in VLMs. Understand what existing spatial training achieves before proposing improvements. |
| 11 | `11_Fine-Grained_Evaluation_VLMs_Autonomous_Driving_ICCV2025.pdf` | **Fine-Grained Evaluation of Large VLMs in Autonomous Driving** | ICCV 2025 | Motivates the high-stakes deployment context (LLNL's mission-critical AI). Shows where VLMs currently fail in real-world spatial tasks. |

---

## Key Concepts to Track While Reading

- **Anchoring / Δ-UQ**: input centering via random reference anchors → calibrated epistemic uncertainty
- **Masking regularizer (λ)**: prevents shortcut learning in anchor-residual pairs
- **CB-SAE scoring (I·S)**: Interpretability × Steerability metric for neuron pruning
- **Compositional grounding gap**: pooled features → factorial accuracy degradation O(1/n!)
- **REGROUND**: parse-guided spatial attention at test time, no parameter updates
- **GroupMatch**: strict group-level matching metric (better than pairwise accuracy)
- **Winoground / SugarCrepe / VSR / ConMe / ARO**: adversarial benchmarks for relational reasoning

---

## GitHub Repositories to Clone

```
github.com/LLNL/anchoring     ← Paper 1
github.com/LLNL/DeltaUQ       ← Paper 2
github.com/Trustworthy-ML-Lab/CB-SAE  ← Paper 3
github.com/LLNL/DECIDER        ← Paper 4
github.com/LLNL/CREPE          ← Paper 7
```
