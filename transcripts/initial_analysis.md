https://aistudio.google.com/prompts/1NQgplifU6KLxdk3jjgN3xzBS8fj8t-Co

# Session Instruction Log

## 1. Introduction

This document is a log of every user-provided instruction from the current interactive session, presented in chronological order. It serves as a record of the conversational path taken to generate the project's design and planning documentation.

## 2. Instruction Log

0.  **Instruction:**
    > map out the dependency structure and data flow of this codebase:

1.  **Instruction:**
    > list each function in the codebase. for each, analyze whether it's a pure function or has side effects

2.  **Instruction:**
    > propose an impl order, compoent by component, for translating this codebase into pytorch

3.  **Instruction:**
    > as a case study, trace the effect of mosaicity param(s) end to end, as the autodiff would have to

4.  **Instruction:**
    > do the same for all other model parameters

5.  **Instruction:**
    > think about a testing strategy. how can ground truth be established?

6.  **Instruction:**
    > brainstorm alternate testign approaches, compare to this approach, and then think about which is best. then make a recommendation

7.  **Instruction:**
    > review our conversation up till now. brainstorm which architecture, component, dependency, and plan docs we will need to understand the c codebase, guide / give context for various tasks, and do the actual testing and implementation

8.  **Instruction:**
    > think about what should go into C_Architecture_Overview.md

9.  **Instruction:**
    > think about what dhould go into C_Parameter_Dictionary.md

10. **Instruction:**
    > think about what should go into PyTorch_Architecture_Design.md

11. **Instruction:**
    > draft the document

12. **Instruction:**
    > think about what should go into Testing_Strategy.md

13. **Instruction:**
    > carefully think about what should go into Parameter_Trace_Analysis.md, then outline it

14. **Instruction:**
    > draft Parameter_Trace_Analysis.md

15. **Instruction:**
    > write a unified git patch for the creation of each of these documents in their entirety

16. **Instruction:**
    > does the patch contain all the docs in their entireties?

17. **Instruction:**
    > were there any other docs that you forgot?

18. **Instruction:**
    > proceed
