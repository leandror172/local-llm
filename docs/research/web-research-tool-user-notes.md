# User Notes: Web Research Tool Architecture Thinking

*Captured 2026-03-16, session 44. Raw thinking from the user about use cases, agent architecture, and testing.*

---

## Use Cases That Shape the Tool

### Use Case 1: Direct Research (simplest)
Before starting the local LLM project, I used Claude Desktop research mode to gather data about where to start. This would probably be the first and simplest example of usage — and likely, already augmented with things like iteration, and human in the loop for conversation during process, among others.

### Use Case 2: Available to Claude Code
This very research is an example, as is asking Claude Code to process the 20 links and see what is useful for this repo, what integrates, makes it better, etc.

### Use Case 3: Persistent Memory / Post-Research Conversation
If we get to persistent memory, you can then use it to actually have a conversation (entry point may not be the same that initiates the research) after research. Note this is a layer that can be added later.

---

## Agent Architecture Thinking

*Note: this is not how it has to be followed, just what I thought of how to execute stuff reliably with limited resources.*

A user (human or not) asks for a research to be initiated.

- While writing the above, I just thought: depending on the prompt, a model can engineer a richer prompt for the next steps
- In any case, this initial context is already a good candidate to be saved, as unlike Claude Code, context isn't automatically stored as conversation flow (unless any of the tools do that; still, anything happening outside them, would not be saved, so, this should be taken into consideration).

**Agent A** (this just identifies instance and context; doesn't have to necessarily be an agent, a specific model; this applies to the rest of the prompt whenever agent is mentioned) manages the research, in the sense of concluding what tools it needs to accomplish the objective. As an example, deep research is fired, does its thing, while Agent A saves its state — again, because no Claude Code; as an example, if this is done by Claude Code managing this agent (be it by starting Claude Code pointing to a local model, or configuring it in a way that frontier Claude Code [you] can start this agent with a local model, and storing context as file, so that VRAM can be freed for the next model), this changes how this requirement behaves.

- The thing is, having that Agent call the tool might mean it needs to use more context in order to know not just about the tool, but how to specifically call it. We haven't retested that after adding new models, including a few that also use RAM to have more context, and models more suited to tool calling. Our benchmarks demonstrated tool calling is hard for local models.
- Here, Agent A could focus on knowing the tools available, what it can do with them, and when to use them; but they only inform that need; another agent, **Agent Tool** knows not just the tools, but how to call them, and route data between different tools.
- Having Agent Tool for this might help minimize the impact of deciding on a language and sticking to it, allowing us to use what's more suited to the specific need of what we have to build. This also allows us to integrate tools that work on different languages, tools that can be smaller and more focused. And, it also opens up the possibility of having tools as plugins, swapping out even with tools that have similar uses.
  - Agent Tool itself can have layers/levels, as a different Agent can be more focused on how to integrate tools, while another would be more focused on deciding a "pipeline" of what to call.
  - Part of the pipeline decision would be what can and can't be parallelized, deciding the pipeline on the fly (and based on historical usage data).
- All of these points must make sense in terms of the context swapping still making it beneficial in terms of having more context available and focused for each task; over-engineering by the sake of it should not happen, if there are no gains.
- Latency between model swaps is a concern, but on certain levels: e.g., in the case of Agent Tool being a team, changing models likely makes no sense, it's the same domain. But Agent A could benefit from using a more suited model for its domain. Really, saying this is **"domain driven design thought as agent/model modeling"** just occurred to me, and makes sense.

Deep research stores the results.
- If we plan to integrate data, this might be the time to have something get queued up: new data is available, is there existing knowledge that integrates? Processing this would then create relations with whatever technique (e.g.: the mentioned graph stuff, but not limited to that).

**Agent(s) Tool** proceed with the pipeline calls, until everything is done.

**Agent B** reviews if deep research answer is enough, or if there is some point exploring/other tools not included in the pipeline should be used. This is just a first pass, and the role of Agent B is just checking if Agent A should go ahead and use the results, or more should be explored; a "more" decision should iteratively get lower, to avoid loops; this likely is worth being configurable.

Agent B gives the go to have the results available for Agent A.
- Summarization likely plays a role here, but with pointers to results, and the results to sources.

Agent A can iterate on checking if the result is enough.

In order to not pollute its own context, **Agent A2** can serve as proxy, with Agent A asking it to sift through results (and Agent B's notes?) and answer queries.
- If the previously connected knowledge processing is in place, this is the moment that those found connections can be informed.

Agent A decides if more research/other tool calls are needed to fulfill the initial request, iterating until criteria are met.
- Note that at this point, if we have knowledge linking, Agent A can then ask questions about the existing knowledge to a different Agent.
- I'm not sure if it's ideal to have a different agent check with Agent A if the initial query was fulfilled, by questioning/analysing its results.

Results are stored and returned.

---

## Testing Thoughts

This is a very "longshot" thinking; development should likely take an iterative/MVP approach.

Testing will be tough; smaller pieces can have the equivalent of (or literal) unit tests, but as the integrative scope grows, testing is less and less deterministic; having everything well tested in low levels eases up the rate of "distrust" of non-deterministic test results from higher levels. Still, for a higher level of testing, we could have something for which we expect certain results (even if it is some content we produce for the sake of it, or something we trust to get the same data from) — even if *analysing* these results are also a non-deterministic problem.

Non-determinism is a problem we have been facing a few times in this project, including testing, and the answer tends to point to:
- Extract what can be considered or transformed to be deterministic, from what really is non-deterministic
- Accept non-determinism and work around it, including but not limited to non-deterministic extraction of information
- Ignore testing non-determinism that is not important/is backed up by lower layers/other tests

We haven't added frontier judgment to the benchmark scripts, but that could play a role in evaluation, *as an option/extra layer*, for a few high level tests.
