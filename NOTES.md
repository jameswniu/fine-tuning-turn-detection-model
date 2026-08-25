# Scratch notes (not a deliverable)

## aj / rvats roadmap pulls from the voice-ai guide (voiceaiandvoiceagents.com), 2026-08-24

James's read holds: rvats already covers most of what the guide teaches (turn config, interruption handling, latency SLOs, evals, the telephony lane). What the guide has that rvats does not own yet, worth roadmap lines in the rvats repo once the take-home ships:

- The guide's biggest latency lever is speculative response generation, starting LLM inference the moment an endpoint looks likely and cancelling if the caller resumes. It maps directly onto the rvats deferral apparatus, shrinking the gap the holding lines exist to cover.
- Owning the turn detector, which is this project. Shadow first, then live behind a pluggable orchestration lane (Pipecat or LiveKit agents, keeping ElevenLabs TTS and ASR as components). Upgrades five-hard-problems row 1 from "Partly".
- Budgeting latency per layer, so ASR partial cadence, the endpoint decision, LLM time to first token, and TTS first byte each get measured against their own slice of the answer-latency SLO instead of only end to end.
- Caching context on the talking layer to cut time to first token on every turn.
- Moving the conversation to a state machine, where each state carries its own small system instruction, its own tool subset, and explicit exits to other states, instead of one 24k-char prompt file. aj does not have this today (confirmed 2026-08-24, the prompt is one file). Same motivation as the per-department line already in the rvats README, a rulebook small enough that the suite can actually cover it.

Keep here until the take-home ships, then move into the rvats README roadmap section.

## Monitoring section design (for the approach doc), 2026-08-24

James's framing, kept. Monitoring means doing traces and observing trash and failures so we can craft our evals and guardrails. It is the intake pipe for the junk the reliance layer is made of, not dashboards to stare at. The pipeline runs trace, observe, route. Every decision gets traced, failures get observed, and each confirmed failure lands either as a new eval case in the offline replay corpus or, for absolute-rule classes, as a new tier 1 guardrail.

Each per-turn trace carries the turn id, the conversation context, the prefix probability trajectory rather than just the final score, the decision, the threshold in force, model latency, and what the caller did next.

What makes this problem special is that turn detection grades itself in production, seconds later, for free, because "what happened next" is the label. A SPEAK decision followed by the caller talking over the agent within about half a second was a false speak. A WAIT decision followed by dead air stretching until the agent finally responds was a false wait. Production traffic is therefore a self-labeling stream, and the two proxy rates are the online eval with no annotation cost. A small weekly human-audited slice (the labeling booth pointed at sampled production turns, biased toward low-confidence decisions and every barge-in) keeps the auto-labels honest and feeds retraining. This answers their "are we limited by the datasets previously built" bullet directly. The limit dissolves the day traces start converting into cases.
