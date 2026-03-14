# Conference Talk Design: Pack Smart, Schedule Fair

**Date:** 2026-03-13
**Format:** 10-minute class presentation, conference-style (OSDI/NSDI/ATC)
**Audience:** CS244C classmates + instructors; do NOT assume familiarity with Gavel or FGD
**Structure:** Classic systems talk (Problem -> Gap -> Idea -> Eval -> Insight)
**Central takeaway:** "Fragmentation depends on node topology diversity, not GPU type heterogeneity."

## Design Decisions

- **10 slides, 1 per minute** -- less is better
- **Embedded screen recording** (15-20s) of viz tool as default; live tab ready as backup
- **Honest limitations slide** with arrival order sensitivity caveat
- **Slide 6->7 transition is the climax:** FGD works on mixed nodes -> zero benefit on uniform nodes

## Timing Budget

| # | Slide | Time | Purpose |
|---|-------|------|---------|
| 1 | Problem: GPU fragmentation wastes capacity | 1:00 | Hook + motivation |
| 2 | Two systems, one gap (Gavel + FGD) | 1:00 | Background + gap |
| 3 | Our approach: two-stage architecture | 1:00 | Key idea + design |
| 4 | Evaluation setup (2 clusters, 900 experiments) | 1:00 | Methodology |
| 5 | Replication validates both baselines | 1:00 | Credibility |
| 6 | FGD cuts fragmentation 30-40% on mixed nodes | 1:00 | Main result |
| 7 | But zero benefit on uniform nodes (the twist) | 1:00 | Central insight |
| 8 | Utilization impact: 280 GPUs recovered, 17% throughput | 1:00 | Practical impact |
| 9 | Limitations + viz tool demo clip | 1:00 | Honest caveat + demo |
| 10 | Takeaway | 1:00 | One sentence |

## Slide-by-Slide Design

### Slide 1: Problem -- GPU Fragmentation Wastes Capacity

**Visual:** Simple diagram showing a cluster with partial GPU allocations. Fragments highlighted in red. One stat callout: "21-42% of free GPU capacity is unusable due to fragmentation."

**Talking points:**
- GPU clusters for ML training are expensive. Utilization averages 25-50%.
- GPU sharing helps -- multiple tasks on one GPU -- but creates fragments: leftover capacity too small for any waiting job.
- Alibaba production data: up to 42% of free GPUs are fragmented and unusable.
- This is the equivalent of leaving hundreds of GPUs powered on doing nothing.

**Transition:** "Two recent systems tackle parts of this problem..."

---

### Slide 2: Two Systems, One Gap

**Visual:** Split slide. Left: Gavel diagram (Fig 2 -- LP allocation across GPU types). Right: FGD diagram (Fig 3 -- gradient descent on nodes). Gap highlighted in the middle: "Gavel ignores where jobs land. FGD ignores which GPU type to use."

**Talking points:**
- Gavel (OSDI 2020): solves an LP to allocate jobs across GPU types based on per-model throughput. Reduces JCT by 20-70%. But treats placement as random.
- FGD (ATC 2023): places each job on the node that minimizes fragmentation growth. Reduces wasted GPUs by 49%. But uses simple FIFO ordering.
- These operate at different levels: Gavel picks *which GPU type*, FGD picks *which node*. Natural question: what if we combine them?

**Transition:** "Our approach layers them..."

---

### Slide 3: Two-Stage Architecture

**Visual:** Fig 1 (architecture diagram) -- the two-stage pipeline. Stage 1: Gavel LP -> type allocation. Stage 2: FGD -> node selection. Telemetry feedback loop.

**Talking points:**
- Stage 1: Gavel's LP computes time-fraction allocations per GPU type (which type, how much).
- Stage 2: Within the allocated type, FGD selects the specific node that minimizes fragmentation gradient (where to place).
- Clean separation -- allocation and placement are orthogonal concerns that compose independently.
- Also explored GavelFGD+: feeding placement availability back into the LP as a POA signal.

**Transition:** "To test this, we needed two very different clusters..."

---

### Slide 4: Evaluation Setup

**Visual:** Table comparing the two clusters side by side (Table I from paper). Alibaba Split: 6,212 GPUs, 12 types, uniform 8-GPU nodes. Cluster H: 5,592 GPUs, 1 type, mixed 1/2/4/8-GPU nodes. Callout: "900 total experiments, 4 placement strategies, 2 policies, 3 seeds."

**Talking points:**
- Two Alibaba cluster topologies chosen to isolate one variable: node size diversity.
- Alibaba Split: heterogeneous GPU *types* but uniform node sizes (all 8-GPU).
- Cluster H: homogeneous GPU type but mixed node sizes (1, 2, 4, 8 GPUs per node).
- This is the controlled experiment. Same traces, same simulator, same placement strategies. Only node topology differs.
- 4 placement strategies: Random, Strided (Gavel default), BestFit, FGD.

**Transition:** "First, we validated our implementations..."

---

### Slide 5: Replication Validates Both Baselines

**Visual:** Two panels. Left: Gavel replication (our curves vs. digitized paper, 3 configs). Right: FGD replication (4 metrics, 6 policies). Small relative error subplots visible.

**Talking points:**
- Before combining, we replicated each system independently.
- Gavel: 504 experiments on Philly trace. Close match at sub-saturation loads; divergence only near saturation knee.
- FGD: Alibaba Cluster H, 6 placement policies. At 80% demand, Random fragments 85% of free GPUs vs. FGD's 42%.
- This gives us confidence the integration is comparing real implementations, not artifacts.

**Transition:** "Now the combined system results..."

---

### Slide 6: FGD Cuts Fragmentation 30-40% on Mixed Nodes

**Visual:** Cluster H fragmentation rate vs. arrival rate. Four curves: Strided (highest, ~10%), Random (middle), BestFit and FGD (lowest, ~5%). Annotation arrow showing the 40-50% gap.

**Talking points:**
- On Cluster H (mixed node sizes), FGD and BestFit reduce fragmentation by 40-50% vs. Strided across the full arrival rate sweep.
- Ordering is consistent: FGD ~ BestFit < Random < Strided.
- This holds under both Max-Min Fairness and FIFO -- placement benefit is independent of scheduling policy.
- So far, exactly what we'd expect. FGD works.

**Transition:** "But then we ran the same experiment on uniform nodes..."

---

### Slide 7: Zero Benefit on Uniform Nodes (The Twist)

**Visual:** Side by side. Left: Cluster H panel (curves spread apart). Right: Alibaba Split panel (all four curves converged). Big annotation: "All placement strategies converge." Below: topology diagram (Fig 9) showing why -- uniform nodes mean every placement is equivalent.

**Talking points:**
- Same simulator, same traces, same placement algorithms. Only difference: node topology.
- On uniform 8-GPU nodes, all four strategies produce identical fragmentation. FGD provides zero benefit.
- **Why?** On uniform nodes, any job that fits on one node fits equally well on any other. On mixed nodes, a 3-GPU job can't use scattered 1-GPU fragments -- placement *matters*.
- **Central finding: fragmentation depends on node topology diversity, not GPU type heterogeneity.**

**Transition:** "And this has real capacity implications..."

---

### Slide 8: Practical Impact -- 280 GPUs Recovered

**Visual:** Utilization and effective capacity curves. Strided caps at 89%, FGD reaches 94%. Effective capacity gap: 13 percentage points. Callout: "280 recoverable GPUs. 17% more completed jobs."

**Talking points:**
- On mixed-node Cluster H, the fragmentation gap translates directly to usable capacity.
- Strided leaves 280 GPUs of fragmented, unusable capacity on the table.
- Effective capacity (utilization minus fragmentation): 13 percentage point gap at high load, meaning 17% more jobs completed.
- Per-job completion time is identical across all placements -- placement shapes *cluster capacity*, allocation shapes *per-job throughput*. Orthogonal.

**Transition:** "A few honest caveats, then a tool we built..."

---

### Slide 9: Limitations + Viz Tool Demo

**Visual:** Top half: 3 bullet limitations. Bottom half: embedded 15-20s screen recording of viz tool.

**Talking points:**
- FGD is sensitive to workload ordering -- underperforms simpler baselines in 5 of 7 arrival orders we tested. Wins only when large jobs arrive first.
- All results are trace-driven simulation -- no feedback effects, no real migration costs.
- [Play clip] We built an interactive visualization tool to explore all 843 experiments. Side-by-side comparison, time-series charts, aggregate results with digitized paper overlays. Open source.
- [If time/interest: switch to live tab for quick walkthrough]

**Transition:** "So what should you take away?"

---

### Slide 10: Takeaway

**Visual:** Clean slide, minimal text. One sentence in large font: **"Fragmentation is driven by node topology diversity, not GPU type heterogeneity."** Three bullet implications below. Repo URLs at bottom.

**Talking points:**
- New uniform clusters don't need fragmentation-aware placement.
- Clusters with accumulated mixed hardware benefit substantially from FGD-style placement.
- Allocation and placement are orthogonal -- compose them independently.
- Code is open source: simulator repo + visualization tool.

**End. Open for questions.**

---

## Backup Slides (for Q&A)

1. **Arrival order sensitivity table** (Table II) -- if asked about robustness in depth
2. **GavelFGD+ POA results** (Fig 13) -- if asked about allocation-placement coordination
3. **Wall time analysis** (Fig 14) -- if asked about simulation scalability/cost
4. **Per-utilization breakdowns** (Figs 11, 12) -- if asked for more detailed results
5. **Live viz tool tab** -- if audience wants to see it interactively

## Figures Needed from Paper

| Slide | Figure | Source |
|-------|--------|--------|
| 1 | Fragmentation diagram (new or adapted from Fig 9) | Create simplified version |
| 2 | Fig 2 (Gavel LP) + Fig 3 (FGD gradient) | Paper figures |
| 3 | Fig 1 (architecture) | Paper figure |
| 4 | Table I (cluster comparison) | Paper table |
| 5 | Fig 5 (Gavel replication) + Fig 6 (FGD replication) | Paper figures |
| 6 | Fragmentation vs. arrival rate, Cluster H panel | Paper figure (panel a) |
| 7 | Both panels + Fig 9 (topology) | Paper figures |
| 8 | Utilization + effective capacity | Paper figure |
| 9 | Screen recording of viz tool | Record from live tool |
| 10 | Text only | N/A |

## Presentation Tips

- **Rehearse the slide 6->7 transition** most -- it's the climax
- **Pause after the twist** on slide 7 to let it land
- For the viz demo clip, record at 1.5x speed with clear mouse movements
- Keep a browser tab with the live viz tool open but minimized
- Time yourself: if running long, compress slides 4-5 (setup/replication); if short, expand slide 8 (impact)
