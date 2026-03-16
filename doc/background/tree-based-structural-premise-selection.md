# Tree-Based and Structural Methods for Premise Selection in Formal Math

Deep research on training-free, structure-aware retrieval methods for formal mathematics, with implementation-level detail.

---

## 1. Wang et al. "Tree-Based Premise Selection for Lean4" (NeurIPS 2025)

**Authors**: Zichen Wang, Anjie Dong, Zaiwen Wen
**Venue**: NeurIPS 2025 (Poster)
**Code**: https://github.com/imathwy/tbps (Python 58%, TypeScript 33%, Lean 4%)
**OpenReview**: https://openreview.net/forum?id=omyNP89YW6

### 1.1 Core Idea

A training-free, structure-first premise selection framework that represents Lean4 theorems as expression trees, applies Common Subexpression Elimination (CSE) to normalize them, then uses a multi-stage pipeline: Weisfeiler-Lehman (WL) kernel for coarse screening followed by Tree Edit Distance (TED) + multiple similarity metrics for fine ranking.

### 1.2 Dataset

- **Source**: Lean4 Mathlib4 v4.18.0-rc1
- **Initial extraction**: 339,746 theorems
- **After filtering**: 217,555 valid mathematical theorems
- The paper includes node-count and depth distribution histograms (Figure 4 in paper)

### 1.3 Common Subexpression Elimination (CSE) on Lean Expressions

**Implementation** (`tbps-be/search_app/cse.py`):

The CSE algorithm operates in three phases:

**Phase 1: De Bruijn Normalization**
- Converts de Bruijn indices (BVar) to binder names from the enclosing Lam/ForallE/LetE
- Maintains a `binder_stack` during recursive traversal
- Purpose: ensure structurally identical subexpressions under different binders hash the same way

**Phase 2: Subexpression Hashing and Counting**
- Recursively traverses the expression tree
- `hash_expr()` creates unique string identifiers by type-prefixed recursive hashing:
  - Atomic nodes: `"BVar-3"`, `"Const-Nat.add-[]"`, `"Sort-0"`
  - Composite: `"App-{hash(fn)}-{hash(arg)}"`, `"Lam-{name}-{hash(type)}-{hash(body)}"`
- `count_dict: defaultdict(int)` maps each hash to its occurrence count

**Phase 3: Variable Replacement**
- `replace_with_vars()` traverses the tree
- When `count_dict[expr_hash] > 1` (subexpression appears more than once):
  - Const nodes are preserved unchanged (they are already named references)
  - All other repeated subexpressions are replaced with `FVar(new_variable_name)`
  - `var_map` caches the mapping from hash to generated variable name
  - `existing_vars` ensures uniqueness of generated names

**Two entry points**:
- `cse()`: full pipeline with de Bruijn conversion
- `cse_without_deBruijn()`: skips conversion for pre-normalized expressions

**Effect on tree size**: CSE converts an expression tree into a DAG-like structure where shared subexpressions are represented once. In formal math, common patterns include:
- Repeated type annotations (e.g., `Nat` appearing many times)
- Shared hypothesis types in dependent function types
- Common subgoal structures in complex propositions

### 1.4 Expression Tree Representation

**Implementation** (`tbps-be/search_app/myexpr.py`):

Lean4 expressions are represented as Python dataclasses mirroring `Lean.Expr`:

| Node Type | Fields | Leaf/Interior |
|-----------|--------|---------------|
| `BVar` | de Bruijn index (int) | Leaf |
| `FVar` | free variable ID (string) | Leaf |
| `MVar` | metavariable ID (string) | Leaf |
| `Sort` | universe level | Leaf |
| `Const` | declaration name, universe params | Leaf |
| `Lit` | literal value | Leaf |
| `App` | function expr, argument expr | Interior (2 children) |
| `Lam` | binder name, binder type, body | Interior (2-3 children) |
| `ForallE` | binder name, binder type, body | Interior (2-3 children) |
| `LetE` | binder name, type, value, body | Interior (3-4 children) |
| `MData` | metadata, inner expr | Interior (1 child) |
| `Proj` | struct name, index, struct expr | Interior (1 child) |

Applications are binary (curried): `f x y` = `App(App(f, x), y)`.

### 1.5 Weisfeiler-Lehman Kernel for Coarse Screening

**Implementation** (`tbps-be/search_app/WL_embedding/wl_kernel.py` and `WL/wl_kernel.py`):

**Step 1: Initial Labeling**
```
label(node) = f"{simplified_prefix(node.label)}_d{depth}"
```
Where `simplified_prefix` maps BVar/FVar/MVar/Sort/Const to their base type string to reduce label cardinality.

**Step 2: Iterative Relabeling (h iterations)**
For each iteration:
1. Collect sorted children labels for each node
2. Concatenate: `new_label = f"{current_label}({','.join(sorted(children_labels))})" `
3. Compress via MD5 hash: `hashlib.md5(new_label.encode()).hexdigest()`
4. Store the hash as the new node label

**Step 3: Multi-resolution Histogram**
- At each iteration i, count label occurrences across all nodes
- Combine into single dictionary: keys = `"{iteration}_{md5_hash}"`, values = counts
- This is the WL encoding of the tree

**Step 4: Kernel Computation**
- Cosine similarity between two WL encoding vectors:
  `kernel(T1, T2) = dot(h1, h2) / (||h1|| * ||h2||)`
- Only common keys contribute to the dot product

**Offline preprocessing**: WL encodings are computed for all 217K theorems and stored in PostgreSQL as JSONB columns (`simp_wl_encode_{k}` for various k values). Tested k = 1, 3, 5, 10, 20, 40, 80 iterations.

**Used for screening**: The pipeline uses h=3 iterations for the coarse screening stage, retrieving top-1500 candidates ranked by WL cosine similarity.

**Clustering**: MiniBatch K-Means with optional PCA (1200 components) clusters theorems by WL vectors. IDF-like weighting: `weight(feature) = log(total_count / feature_count)` for features appearing >5 times.

### 1.6 Tree Edit Distance for Fine Ranking

**Implementation** (`tbps-be/search_app/compute/zss_compute.py`):

Uses the Python `zss` library (Zhang-Shasha algorithm).

**Cost model (primary variant `zss_edit_distance_TreeNode`)**:
- **Insert cost**: 0.2 for variable/constant nodes (BVar, FVar, MVar, Sort, Const); 1.0 otherwise
- **Delete cost**: 0.2 for variable/constant nodes; 1.0 otherwise
- **Rename cost**: 0.0 if nodes match or are both variable/constant type; 0.4 otherwise

This asymmetric cost model reflects the intuition that leaf nodes (variables, constants) are less structurally significant than interior nodes (App, Lam, ForallE), which carry structural information.

**Normalization**:
```
ted_similarity = 1 - (edit_distance / max(|T1|, |T2|))
```

**Critical threshold**: TED is **only computed when target expression has <= 50 nodes**. For larger expressions, it is skipped entirely due to the O(n^2 * m^2) cost of Zhang-Shasha on the Python `zss` library.

### 1.7 Additional Similarity Metrics

**Collapse-Match Similarity** (`can_t1_collapse_match_t2_soft()`):
- Measures whether the target tree structure can "collapse onto" a candidate theorem's tree through node merging operations
- Scores 1.0 per matching level plus recursive child scores
- Normalized: `raw_score / total_nodes_in_T2`
- Range: [0, 1] where 1 = perfect structural conformance

**Const Declaration Name Similarity** (`const_decl_name_similarity()`):
- Extracts all constant declaration names from both trees
- Filters out names containing "inst" (typeclass instances)
- Computes Jaccard similarity: `|intersection| / |union|`
- Returns 1.0 when both sets empty

### 1.8 Multi-Stage Pipeline

**Stage 1: Size Filtering**
- Filter candidates by node count ratio relative to query
- Default ratio: 1.2x (i.e., candidate nodes in [target/1.2, target*1.2])
- For large expressions (>=600 nodes): ratio widens to 1.8x

**Stage 2: WL Coarse Screening**
- Compute WL kernel similarity (cosine) between query and all size-filtered candidates
- Use pre-computed WL encodings from database (h=3 iterations)
- Return top-1500 candidates

**Stage 3: Fine Ranking with Metric Fusion**

For expressions with **<= 50 nodes** (full pipeline):
```
score = 0.15 * WL_similarity
      + 0.40 * TED_similarity
      + 0.30 * collapse_match_similarity
      + 0.15 * const_name_jaccard
```

For expressions with **> 50 nodes** (no TED):
```
score = 0.15 * WL_similarity
      + 0.30 * collapse_match_similarity
      + 0.15 * const_name_jaccard
```
(weights sum to 0.60; effectively the remaining 0.40 is dropped)

**Stage 4: Top-K Extraction**
- Sort by combined score descending
- Return top-10 results by default

### 1.9 Performance Numbers

The paper reports results on Mathlib4 (217K theorems) using Top-k Recall, Precision, F1, nDCG, and MRR. The method "significantly outperforms existing premise retrieval tools across various metrics" including BM25 and MePo.

**Specific numbers** (from the paper, Table 7 -- exact values require PDF access):
- The method beats BM25 and MePo across all K values
- Evaluated at K = 1, 4, 8, 16, 32, 64, 128, 256
- The method is training-free and requires no GPU

### 1.10 Computational Cost

**Offline (one-time)**:
- CSE transformation of all 217K theorems
- WL encoding computation at multiple h values (stored in PostgreSQL)
- MiniBatch K-Means clustering

**Online (per query)**:
- CSE on query expression
- WL encoding computation (h=3, linear in tree size)
- Cosine similarity against 217K pre-computed vectors (batched from DB in 90K chunks)
- TED computation on top-1500 candidates (only for queries with <=50 nodes)
- Collapse-match and Jaccard on top candidates

**Bottleneck**: TED computation. Zhang-Shasha is O(n^2 * m^2) worst case. The 50-node cutoff is critical -- beyond this, the system falls back to WL + collapse-match + Jaccard only.

---

## 2. Weisfeiler-Lehman Graph Kernel

**Reference**: Shervashidze et al., "Weisfeiler-Lehman Graph Kernels", JMLR 2011

### 2.1 Algorithm

The WL subtree kernel is based on the 1-dimensional Weisfeiler-Lehman graph isomorphism test:

```
Input: Graph G = (V, E) with node labels l_0(v) for each v in V
Parameters: Number of iterations h

For i = 1 to h:
  For each node v in V:
    1. Collect multiset M_i(v) = {l_{i-1}(u) : u in N(v)}
    2. Sort M_i(v) to get string s_i(v)
    3. Concatenate: combined = l_{i-1}(v) || "," || s_i(v)
    4. Hash/compress: l_i(v) = hash(combined)

Feature vector: phi(G) = (count of each label at each iteration)
Kernel: k_WL(G, G') = <phi(G), phi(G')>
       = sum_{i=0}^{h} sum_{sigma in Sigma_i} c_i(G, sigma) * c_i(G', sigma)
```

### 2.2 Time Complexity

- **Single pair**: O(h * m) where m = number of edges
- **N graphs**: O(N * h * m) for computing all pairwise kernel values
- The key insight: relabeling is O(m) per iteration (visit each edge once), and histogram comparison is O(|Sigma_i|) which is bounded by m

### 2.3 Adaptation for Trees/Expression Comparison

For rooted trees (as in formal math), the algorithm simplifies:
- Edges = parent-child relationships
- Children of each node are its neighbors (excluding parent)
- The sorted children label concatenation naturally captures subtree patterns
- After h iterations, each node's label encodes its depth-h subtree structure

**For coarse screening/hashing**:
- Compute the WL feature vector (label histogram) for each tree
- This is a fixed-dimensional sparse vector
- Use cosine similarity or histogram intersection for fast comparison
- Can be indexed/clustered for sublinear retrieval

### 2.4 Properties Relevant to Formal Math

- **Completeness**: WL distinguishes trees up to subtree isomorphism at depth h
- **Incrementality**: Adding one more iteration captures one more level of neighborhood
- **Label alphabet growth**: Without hashing, labels grow exponentially; MD5 compression is essential
- **Depth sensitivity**: For trees of depth d, h >= d iterations capture the full tree structure

---

## 3. Tree Edit Distance (TED)

### 3.1 Zhang-Shasha Algorithm (1989)

**Problem**: Given ordered labeled trees T1, T2, find the minimum cost sequence of edit operations (insert, delete, rename) to transform T1 into T2.

**Algorithm**:
- Dynamic programming over "relevant subproblems"
- Decomposes trees into "keyroots" based on leftmost leaf descendants
- For each pair of keyroots, computes a forest distance table

**Complexity**:
- Time: O(|T1| * |T2| * min(depth(T1), leaves(T1)) * min(depth(T2), leaves(T2)))
- Space: O(|T1| * |T2|)
- Worst case: O(n^2 * m^2) for trees of size n, m
- In practice for balanced trees: closer to O(n^2 * m * log(m))

**Python implementation**: `zss` library on PyPI. Supports custom cost functions for insert, delete, and update operations. Optional numpy acceleration.

### 3.2 APTED Algorithm (Pawlik & Augsten)

**Improvement over Zhang-Shasha**:
- Uses optimal decomposition strategy (not limited to left/right/heavy paths)
- Considers all root-leaf paths for decomposition
- Computes optimal strategy in O(n^2) time

**Complexity**:
- Time: O(n^3) worst case; O(n * m^2 * (1 + log(n/m))) for m <= n
- Space: O(n * m)
- This is worst-case optimal for the class of decomposition-strategy algorithms

**Implementation**: Java reference at https://github.com/DatabaseGroup/apted
- API: `new APTED(costModel).computeEditDistance(t1, t2)`
- Cost model interface: `insert(node)`, `delete(node)`, `rename(node1, node2)`
- Default: unit cost (1 for all operations)

### 3.3 Practical Considerations for Formal Math

**Typical expression tree sizes** (Lean4 Mathlib):
- Most theorem statements: 10-200 nodes after CSE
- Complex theorems: 200-1000+ nodes
- The tbps code uses a 50-node cutoff for enabling TED (beyond this, TED becomes too slow per query in the Python zss implementation)

**Cost model design choices** (from tbps):
- Leaf nodes (variables, constants) are cheap to insert/delete (cost 0.2) because they carry less structural information
- Interior nodes (App, Lam, ForallE) are expensive (cost 1.0) because they define structure
- Rename between matching types is free (0.0); cross-type rename costs 0.4

---

## 4. Common Subexpression Elimination in Formal Math

### 4.1 Why CSE Matters

In dependent type theory (Lean4/Coq), expression trees contain enormous redundancy:

1. **Repeated type annotations**: In `forall (x : Nat) (y : Nat) (z : Nat), ...`, the `Nat` type appears 3 times
2. **Elaborated implicit arguments**: Lean/Coq elaboration inserts type annotations everywhere, often repeating the same complex types
3. **Typeclass instance arguments**: `[inst : Add Nat]` inserts complex dictionary expressions
4. **Shared subgoal structures**: In `A /\ B -> A /\ B`, the `A /\ B` subtree is duplicated

### 4.2 CSE on Lean Expressions (tbps algorithm)

The algorithm:
1. Normalize de Bruijn indices to binder names (so structurally identical subexpressions under different binders hash identically)
2. Hash every subexpression recursively
3. Count occurrences; any subexpression appearing >1 times is replaced by a fresh free variable

**Key design decision**: Constants (`Const`) are never replaced, even if repeated. Rationale: constants carry semantic meaning (they are named references to library definitions) and their repetition is semantically significant.

### 4.3 Sharing Patterns in Coq/Lean

**Coq** uses hash-consing internally (in the kernel's `Constr.t` type):
- Structurally identical subterms share memory
- Enables O(1) equality checking via pointer comparison
- The DAG structure is already implicit in Coq's internal representation

**Lean4** uses a similar hash-consing scheme for `Expr`:
- Expressions are interned with hash codes
- But the serialized/exported form is a tree (duplicating shared subexpressions)

**Implication for tree-based methods**: When working with serialized/exported expressions (as tbps does), CSE is essential to recover the sharing that exists in the kernel's internal representation. Without CSE, expression trees can be 2-10x larger than necessary.

---

## 5. Coq Term Structure (Constr.t)

### 5.1 The kind_of_term Type

Coq's kernel terms (now under the Rocq umbrella) are defined in `kernel/constr.ml`. The user-facing view type (as of Coq 8.10+):

```ocaml
type ('constr, 'types, 'sort, 'univs) kind_of_term =
  | Rel of int                              (* de Bruijn index *)
  | Var of Names.Id.t                       (* named variable *)
  | Meta of metavariable                    (* metavariable *)
  | Evar of 'constr pexistential            (* existential variable *)
  | Sort of 'sort                           (* Prop, Set, Type *)
  | Cast of 'constr * cast_kind * 'types    (* type cast *)
  | Prod of binder_annot * 'types * 'types  (* dependent product / forall *)
  | Lambda of binder_annot * 'types * 'constr  (* lambda abstraction *)
  | LetIn of binder_annot * 'constr * 'types * 'constr  (* let binding *)
  | App of 'constr * 'constr array          (* application: f [|a1;...;an|] *)
  | Const of Names.Constant.t * 'univs      (* constant reference *)
  | Ind of Names.inductive * 'univs         (* inductive type *)
  | Construct of Names.constructor * 'univs (* constructor *)
  | Case of case_info * 'constr * 'constr * 'constr array  (* pattern match *)
  | Fix of ('constr, 'types) pfixpoint      (* fixpoint *)
  | CoFix of ('constr, 'types) pcofixpoint  (* cofixpoint *)
  | Proj of Names.Projection.t * 'constr    (* primitive projection *)
  | Int of Uint63.t                         (* primitive integer, 8.10+ *)
```

Later versions (8.17+) add: `Float of float`, `Array of 'univs * 'constr array * 'constr * 'constr`.

### 5.2 Key Structural Properties

**Application representation**: Unlike Lean4's binary App, Coq uses n-ary application: `App(f, [|a1; a2; ...; an|])`. Invariant: f is not itself an App, and the array has >= 1 element.

**De Bruijn indexing**: `Rel(n)` refers to the n-th enclosing binder (1-indexed). Substitution requires shifting: inserting under a binder increments all free indices.

**Hash-consing**: Coq's kernel hash-conses terms, enabling:
- O(1) structural equality via pointer comparison
- Memory sharing for identical subterms
- Efficient memoization of type-checking results

### 5.3 Applying Tree-Based Methods to Coq Terms

To apply tbps-style methods to Coq:

1. **Export Coq terms to a tree representation**: Use MetaCoq's `Template.Ast` or Coq's OCaml API (`Constr.kind`) to extract the term structure
2. **Handle n-ary App**: Either flatten (treat as node with n+1 children) or curryfy (convert to binary App chain like Lean)
3. **CSE**: Hash each subterm, replace duplicates with references. Coq's hash-consing means the kernel already has sharing information -- but serialized/exported forms lose it
4. **WL encoding**: Treat each `kind_of_term` variant as a node label, children as edges
5. **TED**: Compare using standard algorithms with Coq-specific cost models

**Coq-specific considerations**:
- `Cast` nodes are computationally irrelevant (can be stripped)
- `Meta` and `Evar` represent holes -- important for goal matching
- Universe polymorphism (`'univs` parameter) adds complexity; may want to erase for structural comparison
- `Proj` (primitive projections) vs `Case` (eliminators) represent the same concept differently

---

## 6. MePo (Meng-Paulson) Symbol Overlap

**Reference**: Meng & Paulson, "Lightweight Relevance Filtering for Machine-Generated Resolution Problems", Journal of Applied Logic, 2009

### 6.1 Algorithm

MePo is an iterative relevance filtering algorithm based on symbol overlap:

```
Input: Goal formula G, Library of facts F = {f1, ..., fn}
Parameters: p (relevance threshold, default 0.6),
            c (decay constant, default 2.4)

1. Initialize relevant symbol set: S = symbols(G)
2. Initialize selected facts: R = {}
3. Initialize iteration counter: i = 0

Repeat:
  4. For each unselected fact f in F \ R:
     a. Extract symbols(f)
     b. Compute relevance(f, S) based on symbol overlap with S,
        weighted by inverse frequency:
          w(s) = 1 + 2 / log2(freq(s) + 1)
        where freq(s) = number of facts in F containing symbol s
     c. relevance(f) = (sum of w(s) for s in symbols(f) ∩ S)
                      / (sum of w(s) for s in symbols(f))
  5. Select facts where relevance(f) >= p * decay^i
     (threshold decreases with each iteration)
  6. Add selected facts to R
  7. Add their symbols to S: S = S ∪ (union of symbols(selected))
  8. i = i + 1
Until no new facts selected or iteration limit reached

Return: R (selected facts, ranked by relevance)
```

### 6.2 Key Design Decisions

- **Inverse frequency weighting**: Rare symbols are weighted higher. A symbol appearing in only 2 facts is much more discriminating than one appearing in 500
- **Iterative expansion**: Like BFS on the symbol graph. First iteration selects facts directly sharing symbols with the goal. Second iteration adds facts sharing symbols with those selected facts, etc.
- **Decaying threshold**: Each iteration lowers the bar (multiplied by `1/c^i`), allowing more tangentially relevant facts
- **No training**: Purely syntactic, deterministic, fast

### 6.3 Performance

- **Lean4 Mathlib (from LeanHammer paper)**: MePo achieves R@32 = 42.1% and proof rate 27.5%
- **Lean4 MePo implementation**: Available at `Lean/LibrarySuggestions/MePo` in Lean4 core, with parameters `p=0.6`, `c=2.4`, and `useRarity` flag
- **Comparison**: LeanHammer's neural selector (82M params) achieves R@32 = 72.7%, nearly double MePo
- **Strength**: Works without any training data; instant deployment on new libraries
- **Weakness**: Performs poorly when goal symbols are all common (can't discriminate)

### 6.4 Implementation Notes for Coq

CoqHammer already implements a MePo-like symbol overlap approach. Adapting the Lean4 implementation to Coq would require:
- Extracting symbol names from `Constr.t` terms (constants, inductives, constructors)
- Building a frequency table over the library
- The iterative expansion loop is straightforward

---

## 7. SInE (Sumo Inference Engine) Axiom Selection

**Reference**: Hoder & Voronkov, "Sine Qua Non for Large Theory Reasoning", CADE 2011

### 7.1 Algorithm

SInE uses a trigger-based selection heuristic:

```
Input: Conjecture C, Axiom set A
Parameters: tolerance t, generality threshold g, depth d

1. Define trigger relation:
   For each axiom a, find its "least general" symbol:
     trigger(a) = argmin_{s in symbols(a)} occ(s)
   where occ(s) = number of axioms containing symbol s

2. Initialize: Selected = {}, Symbols = symbols(C)

3. For depth iterations 0..d:
   For each axiom a not yet selected:
     If trigger(a) is in Symbols:
       Select a
       Add symbols(a) to Symbols

4. Also select axioms whose trigger symbol has
   occ(trigger(a)) <= g (generality threshold)
```

### 7.2 Key Properties

- **Won CASC large theory division** in 2008 and influenced subsequent winners
- **Very fast**: O(|A| * d) with simple hash lookups
- **Trigger relation**: The key insight is that rare symbols are strong indicators of relevance
- **Depth parameter**: Controls transitivity. d=0 selects only directly triggered axioms; d=1 adds one more hop
- **Tolerance**: Controls how many trigger symbols per axiom (variant: allow multiple triggers if within tolerance factor of the rarest)

---

## 8. Other Structural/Training-Free Retrieval Methods

### 8.1 BM25 on Serialized Expressions

- Treat pretty-printed or serialized expressions as text documents
- Apply standard BM25 (Okapi) term-frequency/inverse-document-frequency ranking
- Tokens = identifiers, operators, keywords in the formal language
- Simple baseline; typically outperformed by structure-aware methods but serves as a useful reference point

### 8.2 k-NN with Proof-Level Locality (Graph2Tac)

- For each proof state, find the k nearest previous proof states in the same proof or nearby proofs
- Use the premises that worked for those states
- Exploits the strong locality prior: nearby proof states often need similar lemmas
- Graph2Tac (ICLR 2024) showed this is highly complementary to GNN-based approaches in Coq

### 8.3 Type-Based Filtering

- Filter candidates by type compatibility: if the goal has type `A -> B`, prefer lemmas whose conclusion unifies with `A -> B`
- Can be implemented via Coq's `Search` with type patterns
- Very precise but low recall (many relevant lemmas have non-obvious type relationships)

### 8.4 Random Forest on Symbol Features

- Piotrowski et al. (2023): Extract symbol features from goals, train random forest classifier
- Features: presence/absence of each symbol, symbol frequency ratios
- Performance on Lean Mathlib: R@32 = 22.3% (significantly below MePo's 42.1%)
- Suggests that simple ML on symbol features underperforms well-tuned heuristics

### 8.5 Kernel Methods on Proof Terms

- Alama et al., "Premise Selection for Mathematics by Corpus Analysis and Kernel Methods" (JAR 2013)
- Used string kernels and tree kernels on MPTP/Mizar problems
- Achieved competitive results with naive Bayes and k-NN baselines
- Tree kernels capture structural similarity without requiring embeddings

---

## 9. Complexity Comparison Summary

| Method | Time (per query) | Space | Training | GPU |
|--------|-----------------|-------|----------|-----|
| MePo | O(|Library| * |symbols|) | O(|Library|) | None | No |
| SInE | O(|Library| * depth) | O(|Library|) | None | No |
| BM25 | O(|Library|) with index | O(|Library|) | None | No |
| WL screening | O(|Library| * h * m) | O(|Library| * features) | None | No |
| TED (Zhang-Shasha) | O(n^2 * m^2) per pair | O(n * m) | None | No |
| TED (APTED) | O(n^3) per pair | O(n * m) | None | No |
| ReProver (neural) | O(|Library|) with FAISS | O(model + index) | Yes (GPU) | Yes |
| LeanHammer neural | O(|Library|) with index | O(model + index) | Yes (GPU) | Yes |

### Key Bottleneck Analysis

For tbps-style pipeline on ~200K theorems:
- **WL coarse screening**: Fast. Cosine similarity of sparse vectors, ~O(200K * avg_features). Can be accelerated with inverted index or approximate nearest neighbor
- **TED fine ranking**: Expensive. Even on 1500 candidates with 50-node trees: 1500 * O(50^2 * 50^2) = 1500 * O(6.25M) = ~10B operations. In Python (zss library), this is the bottleneck
- **Practical latency**: The paper targets interactive use. WL screening is sub-second; TED on small trees adds seconds; the 50-node cutoff prevents worst cases

---

## 10. Summary of Findings

1. **CSE has a significant effect on tree-based methods for CIC terms.** Without CSE, duplicated subterms inflate tree sizes and distort similarity metrics. Coq's internal hash-consing provides sharing at runtime, but exported/serialized terms lose it. CSE on `Constr.t` is straightforward to implement: hash each subterm, replace duplicates.

2. **WL kernel exhibits strong properties for coarse screening.** It runs in O(hm) per tree, is parallelizable, and requires no training. Precomputed WL vectors over an entire library enable cosine-similarity-based retrieval at scale.

3. **TED provides high discriminative power but has high computational cost.** It is feasible only for small expressions (<50 nodes) or for reranking a small candidate set. APTED (O(n^3)) has lower complexity than Zhang-Shasha (O(n^2*m^2)) for larger trees. Native implementations in OCaml or Rust have shown 10-100x speedups over Python.

4. **MePo performs well as a baseline**, achieving 42.1% R@32 on Lean Mathlib with zero training and no deployment overhead.

5. **Multi-metric fusion** (WL + TED + collapse-match + Jaccard) outperforms any single metric in the tbps evaluation. The weights are tunable per domain.

6. **The 50-node threshold in tbps reflects a Python-specific limitation.** The zss library's performance degrades sharply beyond this point. An APTED implementation in a compiled language could raise this to 200-500 nodes, which would cover the majority of Mathlib theorems.

7. **Coq and Lean term structures differ in several respects** relevant to tree-based methods: Coq uses n-ary App (vs. Lean's binary application), includes Cast nodes, carries universe annotations, and has a Proj vs Case duality that affects structural comparison.

---

## Sources

- [Tree-Based Premise Selection for Lean4 (OpenReview)](https://openreview.net/forum?id=omyNP89YW6)
- [Tree-Based Premise Selection for Lean4 (NeurIPS poster)](https://neurips.cc/virtual/2025/poster/116011)
- [tbps GitHub Repository](https://github.com/imathwy/tbps)
- [Premise Selection for a Lean Hammer (arXiv)](https://arxiv.org/html/2506.07477v1)
- [Weisfeiler-Lehman Graph Kernels (JMLR 2011)](https://www.jmlr.org/papers/volume12/shervashidze11a/shervashidze11a.pdf)
- [GraKeL WL Framework Documentation](https://ysig.github.io/GraKeL/0.1a8/kernels/weisfeiler_lehman.html)
- [Zhang-Shasha Python Library (zss)](https://github.com/timtadh/zhang-shasha)
- [APTED Java Implementation](https://github.com/DatabaseGroup/apted)
- [APTED: Optimal Decomposition for Tree Edit Distance](https://dl.acm.org/doi/10.1145/1644015.1644017)
- [Coq Constr API Documentation](https://rocq-prover.org/doc/v8.10/api/coq/Constr/index.html)
- [Coq Constr.t (master)](https://coq.github.io/doc/master/api/coq-core/Constr/index.html)
- [Ramblings on the Coq Kernel](https://ionathan.ch/2019/06/12/ramblings-on-the-coq-kernel.html)
- [Implementing Hash-Consed Structures in Coq](https://arxiv.org/pdf/1311.2959)
- [Lean4 Expressions (Metaprogramming Book)](https://leanprover-community.github.io/lean4-metaprogramming-book/main/03_expressions.html)
- [Lean4 MePo API](https://lean-lang.org/doc/api/Lean/LibrarySuggestions/MePo.html)
- [Meng & Paulson, Lightweight Relevance Filtering](https://www.cl.cam.ac.uk/~lp15/papers/Automation/filtering.pdf)
- [SInE: Sine Qua Non for Large Theory Reasoning](https://link.springer.com/chapter/10.1007/978-3-642-22438-6_23)
- [Proofengineering coq-ast Plugin](https://github.com/proofengineering/coq-ast)
- [Overview and Evaluation of Premise Selection Algorithms](http://grid01.ciirc.cvut.cz/~mptp/premisealgos.pdf)
