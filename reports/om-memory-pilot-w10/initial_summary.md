# pi-observational-memory vs baseline: initial full-run summary

- pairs: 113
- baseline mean_partial: 0.774167
- OM mean_partial: 0.856332
- baseline solves: 2/113
- OM solves: 10/113
- partial improved/worse/tie: 69/33/11

## buckets

- hard: n=38 baseline=0.401454 OM=0.709870 delta=+0.308417 solves 0->1
- medium: n=37 baseline=0.934380 OM=0.912542 delta=-0.021838 solves 0->4
- easy: n=38 baseline=0.990884 OM=0.948064 delta=-0.042819 solves 2->5

## top wins

- mashumaro-flattened-dataclass-fields (hard): 0.000->1.000 Δ=+1.000 tokens Δ=+7,792,399
- fastapi-implicit-head-options (hard): 0.000->0.997 Δ=+0.997 tokens Δ=+20,581,688
- kombu-single-active-consumer-priority (hard): 0.000->0.993 Δ=+0.993 tokens Δ=+10,508,933
- anko-default-function-arguments (hard): 0.000->0.992 Δ=+0.992 tokens Δ=+4,958,124
- kgateway-consistent-hash-policy (hard): 0.000->0.991 Δ=+0.991 tokens Δ=+7,598,262
- sqlite-utils-safe-import-checkpoints (hard): 0.000->0.971 Δ=+0.971 tokens Δ=+3,325,338
- ts-pattern-match-each (hard): 0.066->0.989 Δ=+0.923 tokens Δ=-894,160
- oxvg-structural-selector-preservation (hard): 0.000->0.912 Δ=+0.912 tokens Δ=+11,449,771
- go-critic-doc-link-checker (hard): 0.000->0.895 Δ=+0.895 tokens Δ=+2,269,028
- helm-array-merge-strategies (hard): 0.000->0.763 Δ=+0.763 tokens Δ=+5,434,670
- yaegi-go-embed-directives (hard): 0.000->0.719 Δ=+0.719 tokens Δ=+17,607,097
- pwntools-tube-multiplexing (hard): 0.351->0.919 Δ=+0.568 tokens Δ=+1,020,966
- tengo-destructuring-bindings (hard): 0.000->0.462 Δ=+0.462 tokens Δ=+4,309,889
- opa-template-string-reconstruction (hard): 0.444->0.889 Δ=+0.444 tokens Δ=+10,202,136
- pebble-durability-wait-apis (hard): 0.573->0.932 Δ=+0.359 tokens Δ=-4,121,581

## top losses

- adaptix-name-mapping-aliases (easy): 0.999->0.000 Δ=-0.999 tokens Δ=-19,855,300
- cattrs-partial-structuring-recovery (medium): 0.947->0.132 Δ=-0.816 tokens Δ=-2,461,302
- opa-rego-rule-profiling (hard): 0.581->0.000 Δ=-0.581 tokens Δ=-3,264,593
- etree-xml-diff-patch (hard): 0.791->0.254 Δ=-0.537 tokens Δ=+1,932,206
- igel-persist-feature-schema (hard): 0.577->0.077 Δ=-0.500 tokens Δ=+5,859,599
- task-task-graph-export (medium): 0.838->0.541 Δ=-0.297 tokens Δ=+3,211,156
- dasel-html-document-format (easy): 0.992->0.698 Δ=-0.294 tokens Δ=+133,749
- abs-stepped-slices (hard): 0.667->0.417 Δ=-0.250 tokens Δ=-5,525,069
- go-git-worktree-merge-conflicts (hard): 0.737->0.526 Δ=-0.211 tokens Δ=+1,896,650
- kcp-go-multiplexed-kcp-streams (hard): 0.524->0.333 Δ=-0.190 tokens Δ=+1,389,870
- onedump-dump-encryption-pipeline (medium): 0.977->0.807 Δ=-0.170 tokens Δ=+1,330,224
- optique-conditional-option-dependencies (easy): 0.983->0.833 Δ=-0.150 tokens Δ=+4,469,588
- ink-grid-box-layout (hard): 0.824->0.689 Δ=-0.135 tokens Δ=+1,813,329
- bandit-interprocedural-taint-checks (easy): 0.997->0.886 Δ=-0.111 tokens Δ=+726,809
- happy-dom-deterministic-intersectionobserver (medium): 0.957->0.870 Δ=-0.087 tokens Δ=+570,555
