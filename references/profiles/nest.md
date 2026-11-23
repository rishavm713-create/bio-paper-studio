# NEST biology profile (for the paper generator)

Built from nest-2017 (15 Q), nest-2024-s1 (20), nest-2024-s2 (20), nest-2025 (20) = 75 questions.
Keys ignored (options shuffled). Figures were not captured, so figure-dependence is inferred from the stems.
nest-2026 was used only in the Backtest section and did not change anything above it.

## Weightage

Each question went to one primary group (judgement calls noted below).

| Group | 2017 | 24-S1 | 24-S2 | 2025 | Total | % of 75 |
|---|---|---|---|---|---|---|
| Cell and biomolecules (enzymes, proteins, organelles, cell cycle, bioenergetics) | 4 | 5 | 4 | 4 | 17 | 22.7 |
| Plant physiology | 0 | 2 | 1 | 3 | 6 | 8.0 |
| Human physiology | 1 | 0 | 1 | 1 | 3 | 4.0 |
| Genetics and evolution (inheritance, molecular genetics, selection, phylogeny) | 3 | 5 | 4 | 6 | 18 | 24.0 |
| Reproduction | 1 | 0 | 0 | 0 | 1 | 1.3 |
| Ecology (interactions, productivity, conservation, behaviour) | 3 | 3 | 3 | 2 | 11 | 14.7 |
| Biotechnology (cloning, PCR, sequencing, vectors) | 1 | 1 | 3 | 2 | 7 | 9.3 |
| Diversity and structural organisation (algae/fungi/animal features, anatomy) | 1 | 2 | 3 | 1 | 7 | 9.3 |
| Health and disease (immunity, pathogens, vaccines) | 1 | 2 | 1 | 1 | 5 | 6.7 |

Classification rules used: Meselson-Stahl, lac operon, central dogma, pedigrees, selection types and phylogeny
trees go to genetics and evolution. Cloning, PCR and plasmid selection go to biotechnology. Endosymbiosis and
algal pigment questions go to diversity. Mitosis/meiosis ploidy, enzymes, rRNA/organelle questions go to cell.
Microbial growth counting went to biotechnology (lab quantitation).

Takeaways:
- Genetics and evolution plus cell/biomolecules is about 47% of the paper. Ecology is a steady 3 of 20.
- Reproduction is almost absent (plant ploidy only once). Human physiology is thin in this sample.
- No topic is zero in every paper except reproduction, so rotate the small groups instead of dropping them.
- Plant physiology trends up (0, 2, 1, 3). Do not treat the 2017 count as typical.
- Suggested 20-Q allocation: cell 4, plant phys 2, human phys 1, genetics/evolution 5, reproduction 0,
  ecology 3, biotech 2, diversity 2, health 1. Allow a swap of one question between neighbouring groups.
- Cross-topic questions are common (a gel/vector question that needs immunology or rRNA knowledge).
  Place them by the concept being examined, not by the context.

## Types

- 2017: 10 single-correct (3 marks, -1) plus 5 multi-correct ("one or more", 4 marks, no negative).
  2024-S1, 2024-S2, 2025: 20 single-correct each, 100% (the 2024 papers state "only one answer correct").
- Pooled: 70 single (93%), 5 multi (7%). For the current format use single-correct only.
  Keep 0-1 multi-correct only if a 2017-style paper is asked for.
- Four options (A-D) throughout. Options are often a permutation of the same items (ordering/matching).

Style mix across the 75 (approximate, a question can carry two tags):
- Figure, graph, table, pedigree or gel dependent: about 40%. Every paper has at least 6 of these.
  A text-only generator must describe the data in a small table or in words.
- Experiment or scenario with a changed condition (new organism, swapped reagent, mutant): about 40%.
- Statement set (i)-(iv) with "correct combination" options: about 20%. 2-4 per paper.
- Short passage or case (real research, Nobel work, a named experiment) leading to one question: about 20%.
- Numerical or logic derivation (ratios, GPP, Km, ploidy, fragment assembly, genotype from a cross): about 20%.
- Direct one-line NCERT recall: about 15%. Mostly the 2017 paper; almost absent after 2024.
- Event or sequence ordering and "which pair is correctly matched": about 8%.

## Difficulty rubric

NEST asks short conceptual questions that rarely need NCERT-only recall. Papers self-rate average difficulty
2.6-2.7 on their own scale; on the 1-5 scale below the mean is about 3.0.

- Level 1: single fact straight from NCERT. One step, no data. Distractors obviously wrong.
- Level 2: one concept applied to a simple, familiar case. Short stem, one inference. Terminology pairs.
- Level 3: one concept in an unfamiliar setting, or two linked facts. Data or statement set needs checking
  line by line, but the route is clear. Typical NEST question.
- Level 4: two or three concepts combined, a modified textbook experiment, or a multi-step calculation or
  figure reading. All options plausible; one needs a reasoned elimination.
- Level 5: novel research-style setup with a hidden constraint, or a derived quantity (kinship coefficient,
  net ion current, selection-design critique). Needs setting up the model yourself.

Observed mix across the 75 (my estimate): L1 5%, L2 25%, L3 40%, L4 22%, L5 8%.
Early 2017 sits lower (more L2); 2024-25 have more L4 in genetics, biotech and ecology.

App level mapping:
- Easy: mostly L1-2 (about 70%), rest L3. Keep stems short, single concept.
- Medium: mostly L3 (about 55%), plus 20% L2 and 20% L4, 5% L1/L5.
- Hard: mostly L4-5 (about 70%: 45% L4, 25% L5), rest L3.
- Mixed: the observed mix above.

## Style and traps

1. Change one thing in a textbook experiment. Examples: replication is declared dispersive instead of
   semi-conservative; a different polymerase replaces the thermostable one; a protein is moved between
   compartments. The memorised answer is a distractor.
2. Statement sets hide one wrong word. A comparison is flipped (which leaf type is thicker, which plant group
   photorespires more) or a qualifier like "neither" or "always" is added. Two statements are true, two almost true.
3. Terminology twins in the options: homologous/analogous, divergent/convergent, orthologous/paralogous,
   commensalism/mutualism/amensalism, directional/disruptive/stabilising selection. Define by the scenario given.
4. Multi-species interaction chains. Several organisms each affect each other (a pest, its predator, a pollinator,
   a weed). The answer depends on which pair is named, not on the overall picture.
5. Control-design questions. Choose which extra experiment proves a claim (complete digestion, a negative
   control). Look for the option that changes only one variable.
6. Quantitative traps with a unit or definition twist: gross productivity is light bottle minus dark bottle;
   a half-maximal substrate value gives Km, so Vmax is derived; ploidy after a stage is not the stage's DNA content.
7. Data shown as a small table or graph (growth, allele frequencies, oxygen curves, biomass under treatments).
   One option is true for a different row or treatment. Read the exact condition named in the option.
8. Real-world research context (a Nobel finding, a newly described archaeon, a field study of wasps or ants) with a
   question that needs only an NCERT principle. Do not be pulled by unfamiliar names.
9. Options are the same items rearranged (ordering of events, which label goes with which sample). Solve
   independently first, then match.
10. Recent papers (2025, 2026-style) lean on bioenergetics logic and quantitative reasoning with a stated
    assumption ("assume complete digestion", "assume random mating"). The generator should always state
    its assumptions and constraints in the stem.

## Backtest 2026

nest-2026: 20 questions, all single-correct. Profile above was not edited after this table.

2026 per-question group: genetics/evolution 4 (independent assortment, Meselson-Stahl variant, Hardy-Weinberg,
haplodiploid relatedness); cell 4 (lysozyme and osmosis, pyruvate dehydrogenase block, surface to volume,
ATP synthase uncoupling); human physiology 3 (carbonic anhydrase, synapse order, giant squid axon current);
ecology 5 (microbial interaction curves, carbon budget, niche, desert ant navigation, food web matrix);
plant physiology 2 (Casparian strip, phloem loading); biotech 1 (MfeI/EcoRI ends); diversity 1 (animal feature
matrix); reproduction 0; health 0.

| Group | Predicted % | Actual 2026 % | Abs error (pp) |
|---|---|---|---|
| Cell and biomolecules | 22.7 | 20.0 | 2.7 |
| Plant physiology | 8.0 | 10.0 | 2.0 |
| Human physiology | 4.0 | 15.0 | 11.0 |
| Genetics and evolution | 24.0 | 20.0 | 4.0 |
| Reproduction | 1.3 | 0.0 | 1.3 |
| Ecology | 14.7 | 25.0 | 10.3 |
| Biotechnology | 9.3 | 5.0 | 4.3 |
| Diversity and structural org. | 9.3 | 5.0 | 4.3 |
| Health and disease | 6.7 | 0.0 | 6.7 |

Mean absolute error: 5.2 percentage points (46.6 / 9).

Reading the result (not applied to the profile):
- Biggest misses were human physiology (+11 pp more) and ecology (+10 pp more) in 2026, with health and disease absent.
- Type and style held: single-correct only, scenario/quantitative heavy, statement sets present (2 of 20).
- Level held: more L4-5 numerical items (kinship, ion current, Hardy-Weinberg), no pure recall question.
- With only 20 questions per paper, a 1-2 question swing is 5-10 pp, so group-level misses of this size are
  within normal paper-to-paper noise.
