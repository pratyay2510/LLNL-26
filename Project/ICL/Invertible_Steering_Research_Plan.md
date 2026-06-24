# Steer, Then Invert
### Auditable & On-Manifold Control of In-Context Reasoning via Invertible Latent Steering

**Author:** Pratyay Dutta (pdutt005@ucr.edu) — UC Riverside / Lawrence Livermore National Laboratory
**Advisor:** Prof. Bir Bhanu
**Date:** 2026-06-19
**Status:** Research plan — ready to implement. This document is the single source of truth for the sprint.

---

## 0. TL;DR (read this first)

We control a model's **reasoning by manipulating its latent state**, not by editing the prompt or reading the
output — and crucially we make that control **interpretable, verifiable, and on-manifold** by closing a loop
that no prior work has closed:

```
   prompt  ──forward (ICL ≈ latent gradient step)──▶  latent state h
        ▲                                                   │
        │                                          steer:  z = h + λ·v   (v = +positives − γ·negatives)
   SIPIT (exact inverse)                                    │
        │                                                   ▼
   recovered prompt  ◀──────── INVERT the *steered* state z ──────  z
```

Three named ingredients, one new mechanism:

| Ingredient | From | What it gives us | What it lacks alone |
|---|---|---|---|
| **In-Context Vectors (ICV)** | Liu et al., ICML 2024 | ICL = shifting latent states; a steering vector | Opaque; no idea what prompt it = ; may go off-manifold |
| **SIPIT / Injectivity** | Nikolaou et al., ICLR 2026 | prompt↔latent is an exact bijection; an algorithm to invert it | Only ever inverts *natural* states |
| **QVM / FRE / BI** | Yin, **Bhanu**, Chang, Dong, TPAMI 2005 | the missing **γ repulsion** (push from negatives) + per-axis FRE weighting | classical IR, never connected to LLM latents |

**The new mechanism = Steer → Invert → Verify (SIV).** We steer the latent reasoning state with a
contrastive (positive-minus-negative) vector, then **invert the steered state with SIPIT** to (a) read back, in
plain English, *what prompt that engineered reasoning direction corresponds to*, and (b) measure how far the
steering pushed the model **off the manifold of real prompts** — a quantity we turn into a *training
regularizer* for safe, reliable control.

This is the first work to invert a *manipulated* hidden state, and the first to make latent steering
**auditable**. It is achievable in a 4-week sprint because all three building blocks have public code.

---

## 1. Motivation & the precise gap

The user's thesis: *control reasoning via latent-space manipulation rather than relying on the final output.*
The literature already says ICL **is** latent manipulation:

- **ICL ≈ latent feature shifting.** A self-attention layer with demonstrations computes
  `Attn = α·h(query) + (1−α)·h(demos)` — i.e., demonstrations *shift* the query's latent state (ICV §2; this
  is exactly the residual+attention update in the QVM bridge below).
- **ICL ≈ an implicit gradient step.** von Oswald et al. (2023) and Dai et al. (2023) show attention performs
  an implicit gradient-descent / meta-optimization update on the query representation. So the "shift" is a
  *gradient*, and a steering vector is a *hand-designed gradient step*.
- **The shift is uncontrolled and opaque.** ICV's own framing: the direction/magnitude of the shift are
  "automatically controlled by the self-attention mechanism … not transparent and difficult to control."

So three concrete problems remain open, and each maps to one ingredient:

1. **No repulsion (the missing γ-term).** Classical relevance feedback moves the query *toward* positives **and
   away from** negatives: `q_new = α·q_old + β·mean(D⁺) − γ·mean(D⁻)`. ICL attention is a convex combination
   over context — it has the `β·mean(D⁺)` attraction term but **no `−γ·mean(D⁻)` repulsion**. Negative /
   hard-negative / flawed-reasoning demonstrations cannot push the latent state away from a wrong attractor.
   *(This is the gap already identified in the existing QVM-FRE-BI plan — we keep it and operationalize it.)*

2. **Steering is unaccountable.** When you add a steering vector you have **no idea what prompt it corresponds
   to**, whether it encodes the task you think it does, or whether it smuggles in spurious content. For a
   safety-critical lab (LLNL) this is a real problem: latent edits are unauditable.

3. **Steering can leave the manifold.** Nothing guarantees the steered state `z = h + λv` is a state that *any*
   real prompt could ever produce. Off-manifold states are where models behave unpredictably. There is
   currently **no metric** for "how off-manifold is my intervention?"

**The unexploited fact that solves 2 and 3:** SIPIT proves the map prompt → last-token (and per-layer) hidden
state is **almost-surely injective**, and gives a **linear-time exact inverse**. Therefore:

- Inverting a steered state answers problem #2: *"what prompt does this latent intervention correspond to?"*
- The **inversion residual** (distance from the steered state to the nearest exactly-reconstructable state)
  is a principled answer to problem #3: an **on-manifold-ness metric**, usable as a regularizer.

No published paper inverts a manipulated state, nor uses invertibility to audit/regularize steering. **That is
the contribution.**

---

## 2. Positioning vs. the six source papers (and what we reuse)

| Paper | One-line | How we use it | How we go beyond |
|---|---|---|---|
| **Dong et al., "A Survey on ICL", EMNLP 2024** (`2024.emnlp-main.64.pdf`) | Canonical ICL formulation, demo selection/ordering, implicit-Bayesian view | Framing, formalism, related work scaffold | We add the latent-control + inversion axis the survey lists as open |
| **Liu et al., "In-Context Vectors", ICML 2024** (`In-context-vectors.pdf`) | ICL = latent shift; PCA of `h(y)−h(x)` as a steering vector; task arithmetic | Backbone steering code (`github.com/shengliu66/ICV`); norm-preserving injection (their Eq. 5–6) | (i) explicit γ-repulsion over demo *sets* (not just x→y); (ii) **invert** the steered state; (iii) on-manifold regularizer |
| **Nikolaou et al., "LMs are Injective & Invertible (SIPIT)", ICLR 2026** (`llms-are-invertible.pdf`) | prompt↔latent is a bijection; SIPIT recovers exact prompt from hidden states | SIPIT code (`github.com/giorgosnikolaou/SIPIT`); Thm 3.2 robustness bound | First to invert a **manipulated** state; turn the inversion *residual* into a control metric & loss |
| **Yin, Bhanu, Chang, Dong, "Relevance Feedback via RL", TPAMI 2005** (`Integrating_relevance_feedback...pdf`) | QVM + FRE + BI + long-term RL memory for CBIR | Source of the γ-term, FRE per-axis `1/σ_j` weighting, and the RL-memory idea | Realize all three in transformer latent space; FRE-weighted steering |
| **Peng et al., "LIVE: Learnable In-Context Vector", NeurIPS 2024** (`NeurIPS-2024-live...pdf`) | Make the ICV *learnable* (per-layer, distilled from many demo sets) by matching output distributions | Learnable-steering recipe + per-layer vectors (`github.com/ForJadeForest/LIVE-...`) | Add the on-manifold (invertibility) term to the learnable objective; invert the learned vector |
| **Zhang et al., "Active Example Selection", EMNLP 2022** (`Active-example-selection.pdf`) | RL searches *prompt space* to pick demos; gains shrink on big models | Conceptual **baseline** for "discover good prompts" | We optimize in *latent* space then **invert to a prompt** — exact, not a learned/RL search |

**Net:** our plan is the natural synthesis the existing QVM-FRE-BI direction was reaching for, sharpened into a
single falsifiable mechanism by the brand-new invertibility result.

---

## 3. Theory: the prompt↔latent bijection as a controllable substrate

### 3.1 The QVM ⇄ attention bridge (already in your research log)
Classical Rocchio query-vector movement:
```
q_new = α·q_old + β·(1/|D⁺|) Σ_{x∈D⁺} x − γ·(1/|D⁻|) Σ_{x∈D⁻} x        (QVM)
```
A transformer layer's update of the query token's state:
```
h_q^new = h_q^old + Σ_{i∈C} softmax( (W_q h_q^old)(W_k h_i)^T / √d ) · W_v h_i        (Attention)
```
Identification: residual `h_q^old` ↔ `α·q_old`; attention-weighted sum of context values ↔ `β·mean(D⁺)`
(dynamic, learned weights). **Missing:** the `−γ·mean(D⁻)` repulsion. *We inject it explicitly as a steering
vector* (§4.1).

### 3.2 Injectivity makes this substrate controllable *and* readable
SIPIT's theorem: for standard decoder-only transformers, `s ≠ s′ ⇒ r(s;θ) ≠ r(s′;θ)` almost surely, at init
**and** preserved by training. Two consequences we exploit:

- **Readability.** Every hidden state has a unique prompt; SIPIT recovers it exactly in ≤ `T·|V|` steps
  (≈28 s for a 20-token GPT-2 prompt; <0.22% of vocab explored in practice).
- **A manifold with a margin.** SIPIT Thm 3.2 (robustness): if a state is perturbed by `‖e_t‖ < Δ_{π,t}/2`
  (half the local inter-token gap), the **original** prompt is still recovered exactly. This predicts a
  **phase transition** in our steered-then-inverted experiments (§5, Phase A) — the central empirical result.

### 3.3 Steering = a contrastive in-context gradient step
If ICL is an implicit gradient step (von Oswald/Dai), then a steering vector is a *chosen* gradient step. The
QVM γ-term turns it into a **contrastive** gradient: ascend the positive-class log-likelihood, descend the
negative-class one. This is the link the user asked for between "ICL ≈ gradient update" and "find better
prompts": the optimal contrastive gradient defines a **target latent state**, and SIPIT **inverts that target
into the prompt that would induce it** (§4.4, the inverse-design experiment).

---

## 4. Method

Notation: layer `ℓ`, hidden width `d`, hidden state at layer ℓ, last token: `h_ℓ ∈ R^d`. Positive demo set
`D⁺`, negative/hard-negative set `D⁻`. Steering strength `λ`. We steer at a single layer `ℓ*` and invert from
the same layer (keeps the loop clean; ICV adds at all layers, we restrict for invertibility).

### 4.1 Contrastive In-Context Steering (CIS) — the γ-term, realized
```
v_ℓ  =  β · (1/|D⁺|) Σ_{p∈D⁺} h_ℓ(p)   −   γ · (1/|D⁻|) Σ_{n∈D⁻} h_ℓ(n)        (attraction − repulsion)
z    =  h_ℓ + λ · v_ℓ ,   then renormalize:  z ← z · ‖h_ℓ‖ / ‖z‖   (ICV norm-preservation)
```
- `γ = 0` recovers (a set-based variant of) ICV; `γ > 0` is the **new repulsive term** ICL lacks.
- **FRE-weighted variant (Bhanu).** Weight each axis `j` by `w_j = (1/σ_j)/Σ_k(1/σ_k)` where `σ_j` is the
  per-dimension spread of `D⁺`; i.e., steer harder along axes where positives are tight. This is Mahalanobis /
  inverse-variance steering — directly imports FRE into the latent edit. Ablate `FRE on/off`.
- **Definitions of `D⁻`** (three regimes, increasingly interesting):
  1. *wrong-class* reps (sentiment: negative-class for a positive target) — classic Rocchio;
  2. *flawed-reasoning* exemplars (correct CoT vs. corrupted CoT) — reasoning control;
  3. *spurious-feature* exemplars (same label, different surface form) — debiasing.

### 4.2 Inversion-as-Audit (Steer → Invert → Verify)
Run SIPIT on the **steered** state `z` to obtain `ŝ = SIPIT(z)` — the prompt whose natural layer-ℓ* trajectory
best matches the engineered state. Two SIPIT modes (we use both — important detail, do not conflate):

- **Exact SIPIT** (accept a token only if within ε-ball): may *fail to terminate* off-manifold → failure is
  itself the on-manifold signal.
- **Relaxed / nearest-token SIPIT** (always pick `argmin_v ‖z_t − h_t(prefix⊕v)‖`): always returns *some*
  prompt = the **projection of the steered trajectory onto prompt space**. Always interpretable; use this for
  the audit/readback.

**Outputs of the audit:** (a) human-readable `ŝ`; (b) token-level diff vs. the original prompt; (c) does `ŝ`
contain the *concept* we steered toward? (judge via a classifier / LLM-judge). This is the first time a latent
edit can be *spoken aloud*.

### 4.3 The invertibility-gap = on-manifold regularizer (the new loss)
Define the **inversion residual** (per-position SIPIT match error of the steered state):
```
ρ(z)  =  Σ_t  min_{v∈V}  ‖ z_t − h_t( ŝ_{<t} ⊕ v ) ‖₂          (cheap: one batched vocab forward per position)
```
`ρ(z)≈0` ⇒ a real prompt reproduces `z` ⇒ the steering is **on-manifold and auditable**. Large `ρ` ⇒ the edit
is a fiction no prompt could create. We add it to any steering objective:
```
L  =  L_task(z)            // e.g., −log p(correct | z), or KL(out(z) ‖ out(full-shot ICL))  (LIVE-style)
    + μ · ρ(z)             // NEW: keep control on the reachable manifold
    + η · ‖z − h_ℓ‖²       // proximity / minimal-edit
```
Use it three ways: (i) as a **diagnostic** plotted vs. λ; (ii) as a **stopping rule** for how hard to steer;
(iii) as a **regularizer** when *learning* a steering vector (LIVE-style finetune of `v`, model frozen).

### 4.4 Inverse design: optimize in latent space, invert to a prompt
The user's "use SIPIT to see what prompts produce a given direction," fully realized:
1. Pick a **reasoning target**: maximize a contrastive margin `m(z) = log p(y⁺|z) − log p(y⁻|z)` (or a
   direction toward a probe-defined "correct-reasoning" axis).
2. Optimize the latent target `z* = h + λv` by gradient ascent on `m(z) − μ·ρ(z)` (on-manifold constrained).
3. `s* = SIPIT(z*)` → the **discovered prompt / demonstrations** that would induce that reasoning.
4. **Compare `s*` to Active-Example-Selection (RL) and retrieval baselines.** Selling point: SIPIT is *exact*,
   training-free, and operates in continuous latent space, whereas prior prompt discovery (AutoPrompt, Hard
   Prompts, RL selection) searches discrete prompt space and is approximate.

---

## 5. Experimental plan (de-risked, 4-week sprint + buffer)

Order is by **risk**: the first result is essentially guaranteed to work and is already a paper; later phases
are upside.

### Phase 0 — Infra & faithful reproduction (Days 1–4)
- Stand up activation hooks + single-layer intervention (reuse your Phase-1 codebase + ICV repo).
- Reproduce **one** ICV number (e.g., ParaDetox detox toxicity drop on Falcon-7B or Llama-7B) — sanity that
  steering works in our harness.
- Reproduce **one** SIPIT number (100% exact recovery on GPT-2-Small, 20-token prompts, ~28 s) — sanity that
  inversion works in our harness.
- **Gate:** both reproduced within tolerance before proceeding.

### Phase A — Steer→Invert phase transition (Days 5–11) — *the safe core result*
For models `{GPT-2 Small, GPT-2 Large, Pythia-1.4B}` (+ one scaling point: `Llama-3.1-8B`), tasks
`{SST-2, AGNews, formality/sentiment transfer (ICV tasks)}`:
- Steer with CIS at layer `ℓ*` over a sweep `λ ∈ {0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0}`.
- Run **exact** and **relaxed** SIPIT on each steered state; record:
  - `recover_original` (exact SIPIT returns the source prompt) — expected for small λ (Thm 3.2);
  - `recover_different` (returns a *different* valid prompt) — the interesting middle band;
  - `off_manifold` (exact SIPIT fails / `ρ` large) — expected for large λ;
  - the **residual `ρ(λ)` curve** and the **token-edit distance** of `ŝ` vs. source.
- **Deliverable:** the phase-transition figure (`ρ` and recovery-regime vs. λ, per layer/model). This *will*
  produce a clean, novel result regardless of downstream task gains.
- **Hypotheses:** H-A1 there is a critical `λ_c ≈ Δ/2` below which steering is token-invisible (predicted by
  Thm 3.2); H-A2 `λ_c` grows with depth (SIPIT shows inter-state gaps grow with depth); H-A3 deeper layers
  give a wider "recover_different" band (richer, more semantic edits).

### Phase B — Contrastive steering for reasoning control (Days 12–20)
- Turn on the **γ-term** and the three `D⁻` regimes (§4.1). Tasks: classification (wrong-class repulsion),
  style/safety transfer (ICV's tasks, for direct comparison), and a reasoning task with correct-vs-flawed CoT
  demos (e.g., GSM8K-style or a 2–3 hop reasoning set; keep it small/controlled).
- **Measure in latent space, not just output:** cosine movement toward correct-class centroid and away from
  wrong-class centroid; margin `m(z)`; calibration (ECE). Then output accuracy/F1 as confirmation.
- **Audit:** for the best γ-steering, invert and report the recovered prompts — show the repulsion is real and
  legible.
- **Hypotheses:** H-B1 γ>0 beats γ=0 (=ICV) most on **ambiguous examples near the decision boundary**;
  H-B2 an optimal task-dependent `γ*` exists; H-B3 FRE-weighting helps when class spreads are anisotropic.

### Phase C — On-manifold regularizer & inverse design (Days 21–27) — *upside*
- Learn a steering vector (LIVE-style, model frozen) with and without the `μ·ρ` term; show the regularized
  vector is (i) more auditable (lower `ρ`, cleaner inverted prompts) at equal task performance, and (ii) more
  robust across demo samples / seeds.
- Inverse design (§4.4) on 1–2 tasks: optimize `z*`, invert to `s*`, compare to RL/retrieval example
  selection. Even a **proof-of-concept** ("inverting the optimal latent target yields competitive
  demonstrations") is a strong figure.

### Buffer & write-up (Days 28–30)
- Ablations, error bars (≥5 seeds), figures, draft.

---

## 6. Models, datasets, metrics, baselines

- **Models (open-weight, activation access):** GPT-2 {Small 124M, Large 774M} and Pythia-1.4B for fast
  iteration + interpretability; **Llama-3.1-8B** and/or **Mistral-7B-v0.1** as the scale point (both are in
  SIPIT's tested set, so inversion is known to work). Falcon-7B / Llama-7B only if reproducing ICV numbers.
- **Tasks:** SST-2, MR, AGNews, TREC, DBPedia (classification); ParaDetox, Yelp/GYAFC formality &
  sentiment transfer (ICV's own tasks → direct comparability); a small controlled multi-step reasoning set for
  the CoT-repulsion experiment.
- **Latent metrics (the point of the paper):** cosine/L2 movement toward/away from class centroids; contrastive
  margin `m(z)`; **inversion residual `ρ`**; recovery regime; token-edit distance of inverted prompt;
  min-pairwise-L2 (SIPIT's collision metric) as a demo-diversity measure.
- **Output metrics (confirmation):** accuracy, macro-F1, ECE; for transfer tasks: style accuracy, ROUGE-1,
  BERTScore, toxicity (match ICV's protocol).
- **Baselines:** zero-shot; standard ICL; **ICV (γ=0)**; LIVE (learnable); LoRA fine-tune; AutoPrompt / Hard
  Prompts Made Easy and **Active Example Selection (RL)** for the inverse-design comparison.

---

## 7. Claims the paper will make (and the experiment that backs each)

1. **C1 (mechanism).** Latent steering can be inverted: a manipulated hidden state maps to a recoverable
   prompt. *(Phase A.)* — *new capability.*
2. **C2 (metric).** The inversion residual `ρ` is a faithful, model-internal measure of how off-manifold an
   intervention is, and exhibits a phase transition at `λ_c ≈ Δ/2` predicted by SIPIT's robustness bound.
   *(Phase A.)*
3. **C3 (control).** The contrastive γ-term — absent from ICL attention — improves controllable reasoning,
   especially near decision boundaries, and the gains are visible **in latent space**, not only in output.
   *(Phase B.)*
4. **C4 (safety/audit).** Regularizing with `ρ` yields steering that is equally effective but **auditable**
   (clean inverted prompts, robust across seeds) — a control knob a safety-critical lab can actually inspect.
   *(Phase C.)*
5. **C5 (inverse design).** Optimizing in latent space and inverting with SIPIT discovers prompts/demos
   competitively with RL/retrieval — exactly, training-free. *(Phase C, proof-of-concept acceptable.)*

Top-tier hook: **the first auditable, on-manifold method for controlling LLM reasoning in latent space**,
built on the just-proven invertibility of transformers. Even C1+C2 alone (Phase A) is a clean, novel,
self-contained paper; C3–C5 are the depth that pushes it to a main-conference bar.

---

## 8. Risks & mitigations (think critically — these are the things that can kill it)

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Exact SIPIT won't terminate on steered states** | If steering is off-manifold, no ε-match exists | Use **relaxed/nearest-token SIPIT** for the audit (always returns a prompt); reserve exact SIPIT for measuring the on-manifold regime. The *failure* of exact SIPIT is a feature (it defines `off_manifold`). |
| **Multi-layer steering breaks per-layer inversion** | ICV adds at all layers; SIPIT inverts from one layer | Restrict steering to layer `ℓ*` and invert at `ℓ*`. Report the layer sweep. |
| **Constant-across-positions steering biases recovery** | `v` added to every token may systematically distort | Two variants: steer last-token-only vs. all-positions; report both. Last-token steering is the cleanest for inversion. |
| **SIPIT cost** | ~28 s/prompt (GPT-2) × big sweeps | Budget: ≤ a few thousand inversions on GPT-2/Pythia; subsample for Llama-8B. Cache prefix forwards. Use gradient-guided SIPIT policy (their default) not brute force. |
| **γ-term gains may be small on large models** | Active-Example-Selection showed effects shrink with scale | Lead with the *mechanism/audit* (C1–C2, C4) which is scale-robust; treat accuracy gains (C3) as secondary; emphasize boundary/ambiguous-example regime where γ helps most. |
| **Reasoning control is hard to measure** | "Reasoning" is fuzzy | Use controlled, label-clean tasks first (classification margins, CoT correct-vs-flawed); avoid open-ended generation for the core claims. |
| **`ρ` not differentiable through argmin** | Limits use as a training loss | Use soft-min / temperature-relaxed residual for gradients; or use `ρ` as a guidance/stopping signal + finite-difference on `λ`. |
| **Reviewer: "isn't this just ICV + a known inverter?"** | Novelty challenge | The novelty is **inverting a manipulated state** and the **on-manifold metric/loss** — neither exists. ICV is opaque; prior inverters are approximate and only invert natural states. State this explicitly. |

**A negative result is still publishable:** if steering is *almost always* token-invisible to exact SIPIT
(large `λ_c`), that itself is a striking statement about how much latent slack transformers have before the
prompt-space identity changes — a interpretability result.

---

## 9. Environment, repos, and exact setup

**Python:** use `C:\Users\bhanu\AppData\Local\Microsoft\WindowsApps\python3.exe` (3.11.9; has `fitz`,
`python-pptx`). For experiments prefer a Linux box / LLNL cluster with a GPU (A100 ideal; SIPIT used a single
A100). PyTorch ≥2.8, transformers ≥4.50 (SIPIT's tested stack).

**Clone / reuse:**
- ICV (steering backbone): `https://github.com/shengliu66/ICV`
- SIPIT (inversion): `https://github.com/giorgosnikolaou/SIPIT`
- LIVE (learnable steering): `https://github.com/ForJadeForest/LIVE-Learnable-In-Context-Vector`

**Minimal first experiment (do this Day 1–4):**
1. Load GPT-2 Small; register a forward hook to read & overwrite layer-`ℓ*` hidden states.
2. Build `v` from 5 positive + 5 negative SST-2 examples (CIS, §4.1).
3. Steer the last-token state of 50 held-out queries across the `λ` sweep.
4. Run relaxed SIPIT from layer `ℓ*` on each steered state; log recovered prompt, `ρ`, recovery regime.
5. Plot `ρ(λ)` and the recovery-regime fractions. **This single plot is the seed of the paper.**

---

## 10. Paper outline & venue/timeline (be realistic)

**Outline.** 1 Intro (the loop figure) · 2 Background (ICL=latent shift; injectivity; QVM γ-term) · 3 Method
(CIS, SIV audit, `ρ` regularizer, inverse design) · 4 The phase transition (Phase A) · 5 Controllable
reasoning (Phase B) · 6 On-manifold control & inverse design (Phase C) · 7 Related work · 8 Limitations
(single-layer, cost, scale) · 9 Broader impact (privacy/audit — SIPIT's own angle).

**Timeline.** Today is 2026-06-19.
- **Weeks 1–4 (by ~2026-07-18):** Phases 0–C → an arXiv-ready draft + all core figures.
- **Realistic top-tier targets:** ICLR 2027 (abstract ~late Sept 2026) is the cleanest fit; AAAI-27 / ARR
  (EMNLP/ACL) cycles as alternatives. Submit a **workshop version + arXiv now** to plant the flag (the
  invertibility paper is *very* recent — speed matters). One month is enough for a complete draft and the
  flag-planting preprint; it is **not** realistic to have a *camera-ready accepted* top-tier paper in 30 days —
  set the mentor's expectation accordingly: *month 1 = submission-grade manuscript.*

---

## 11. Open questions to confirm with mentor (don't block on these — defaults chosen)

1. **Compute:** single GPU vs. LLNL cluster? (Default plan assumes 1×A100-class; scales down to GPT-2/Pythia on
   smaller cards.)
2. **Scale point:** Llama-3.1-8B vs. Mistral-7B for the "it works at scale" claim? (Both SIPIT-validated.)
3. **Reasoning task:** which controlled multi-step set? (Default: small curated CoT correct-vs-flawed set.)
4. **Venue ambition:** plant-the-flag workshop+arXiv now, or hold for ICLR-27 main? (Default: both — preprint
   now, polish for ICLR-27.)
5. **Bhanu framing:** how central should QVM/FRE be vs. the invertibility mechanism? (Default: QVM supplies the
   γ-term & FRE weighting — keeps the advisor's contribution load-bearing — while invertibility is the headline
   novelty.)

---

## 12. References

1. Q. Dong et al. **A Survey on In-Context Learning.** EMNLP 2024. (`2024.emnlp-main.64.pdf`)
2. S. Liu, H. Ye, L. Xing, J. Zou. **In-Context Vectors: Making In-Context Learning More Effective and
   Controllable Through Latent Space Steering.** ICML 2024. (`In-context-vectors.pdf`)
3. G. Nikolaou, T. Mencattini, D. Crisostomi, A. Santilli, Y. Panagakis, E. Rodolà. **Language Models are
   Injective and Hence Invertible (SIPIT).** ICLR 2026. (`llms-are-invertible.pdf`)
4. P.-Y. Yin, B. Bhanu, K.-C. Chang, A. Dong. **Integrating Relevance Feedback Techniques for Image Retrieval
   Using Reinforcement Learning.** IEEE TPAMI 2005. (`Integrating_relevance_feedback...pdf`)
5. Y. Peng et al. **LIVE: Learnable In-Context Vector for Visual Question Answering.** NeurIPS 2024.
   (`NeurIPS-2024-live...pdf`)
6. Y. Zhang, S. Feng, C. Tan. **Active Example Selection for In-Context Learning.** EMNLP 2022.
   (`Active-example-selection.pdf`)
7. J. von Oswald et al. **Transformers Learn In-Context by Gradient Descent.** ICML 2023.
8. D. Dai et al. **Why Can GPT Learn In-Context? LMs Secretly Perform Gradient Descent as Meta-Optimizers.**
   ACL Findings 2023.
9. R. Hendel, M. Geva, A. Globerson. **In-Context Learning Creates Task Vectors.** EMNLP Findings 2023.
10. E. Todd et al. **Function Vectors in Large Language Models.** ICLR 2024.
11. T. Brown et al. **Language Models are Few-Shot Learners.** NeurIPS 2020.
12. S. Min et al. **Rethinking the Role of Demonstrations.** EMNLP 2022.
13. Y. Wen et al. **Hard Prompts Made Easy.** NeurIPS 2023.   ·   T. Shin et al. **AutoPrompt.** EMNLP 2020.
14. J. Morris et al. **Language Model Inversion.** 2023 (approximate, black-box — contrast to SIPIT's exact).

---

*Appendix — direct answers to the original brief:*
- *"Use SIPIT to see what prompts produce a given latent direction"* → §4.2 (audit) + §4.4 (inverse design).
- *"Perturb the latent vector, then SIPIT-recover the prompt"* → Phase A core loop (§5).
- *"Finetune with a new loss"* → on-manifold `ρ` regularizer + contrastive steering loss (§4.3, Phase C).
- *"Exploit ICL ≈ gradient update to find better prompts"* → CIS = contrastive in-context gradient; inverse
  design inverts the optimal gradient step into a prompt (§3.3, §4.4).
- *"Move toward positives, away from negatives"* → the γ-term, the spine of the whole method (§4.1).
