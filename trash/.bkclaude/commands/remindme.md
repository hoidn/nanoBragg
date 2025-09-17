- add a spec generation step to the initiative workflow, something like <this>
- close the loop with linting and unit tests
- zen mcp
- try alternate planning structures, such as: 
  - https://github.com/acoliver/vibetools/blob/main/executor/plans/PLAN.md
  - https://github.com/acoliver/vibetools/tree/main/executor/scripts
  - https://github.com/acoliver/llxprt-code/tree/main/project-plans/prompt-config/plan
- experiment with more manual styles where I stub out comments directly or with todos 

<this>
"One fantastic tip I discovered (sorry I've forgotten who wrote it but probably a fellow HNer):

If you're using an AI for the "architecture" / spec phase, play a few of the models off each other.

I will start with a conversation in Cursor (with appropriate context) and ask Gemini 2.5 Pro to ask clarifying questions and then propose a solution, and once I've got something, switch the model to O3 (or your other preferred thinking model of choice - GPT-5 now?). Add the line "please review the previous conversation and critique the design, ask clarifying questions, and proposal alternatives if you think this is the wrong direction."

Do that a few times back and forth and with your own brain input, you should have a pretty robust conversation log and outline of a good solution.

Export that whole conversation into an .md doc, and use THAT in context with Claude Code to actually dive in and start writing code.

You'll still need to review everything and there will still be errors and bad decisions, but overall this has worked surprisingly well and efficiently for me so far.""
</this>
