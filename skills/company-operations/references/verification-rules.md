# Verification rules

The verifier runs the same checks in server mode and in host mode. A task is done only when every check passes.

## Checks for every task

| Check | What it rejects |
| --- | --- |
| schema | A result that is not an object with a summary and a list of claims |
| work | A task with tools that made no working tool call, or a result with no claims and no honest empty result |
| evidence | A claim with no evidence ids, an id no tool call returned, a claim that cites only failed calls, a quote not found in the cited evidence, a quote shorter than three words when the evidence is long, a number the cited evidence does not contain (spelled numbers such as forty count) |
| support | A claim whose content words the cited evidence does not hold. A real quote next to an unrelated sentence fails here. |
| urls | A link that no tool result, the owner's request or a harvested thread contains |
| numbers | A number in the summary that no tool result or the owner's request contains |
| summary | A summary whose longer words appear in no evidence, claim, earlier verified work or the owner's request |
| empty | data.nothing_found without a reason, without a tool call that ran, or when a harvest returned threads |
| auditor model | A claim the second model finds unsupported by its evidence. The objection must name a real claim. A planted false claim checks the auditor model: if it passes that claim, its verdict is marked unreliable and the trust level drops. |

A claim marked assumption=true needs no evidence. It appears in the report as an assumption. Use it rarely. A claim that reports a failure sets about_failure=true and may cite the failed call.

The worker also runs the checks above (without the auditor model) before it hands in a result, and fixes issues without using an attempt.

## Trust level

Each verified task carries a trust level. High means every check and an independent auditor passed. Medium means the checks passed and no auditor ran. Low means the auditor was unreliable or unavailable. The report shows the weakest task as the overall level, or partial while work is open. Set AGENT_REACH_AUDITOR_PROVIDER to audit with a different model provider than the workers.

## Checks by role

| Role | Extra checks |
| --- | --- |
| analyst | The profile was saved in this task. Features and prices appear in the site text or the request. Pain phrases do not name the product. |
| scout | A harvest call ran and at least one succeeded. Every listed thread appears in a harvest result of this task. An empty harvest must be reported as nothing_found. |
| qualifier | Each lead exists, was saved in this task and has a harvested thread behind it. A high potential lead has a verified quote. A second model reads the thread again. A large disagreement blocks the lead. |
| writer | Each draft exists, was saved in this task and passed the linter. Numbers in the draft appear in the profile or the thread. Links appear only when the owner allows them. |
| editor | Every new draft has a verdict. Revise and reject carry a concrete reason. Approve is refused when the stored lint report has errors. The editor ran the linter itself. |
| researcher | A page was fetched in this task. Each fact has a quote. Each listed source was fetched in this task. |
| follow_up | Each reported thread was read in this task. The state is open, closed, new_replies or unreachable. |
| inspector | Not a model. The engine computes it from the database and the posting gates, so it needs no verification. |

## Retries

A task gets three attempts. Each failure returns the list of issues to the specialist. After the third failure the task is escalated and every task that depends on it is blocked. The CEO decides: retry, reassign or skip. A rate limit or a timeout from the model waits and retries without using an attempt. A task that runs longer than 20 minutes without a result goes back to the queue. A directive stops using tools after 150 calls.

## Owner checkpoints

The profile needs the owner's confirmation before any search starts. When the request names no site and no product, the owner is asked for one first. The owner approves every reply before it can post. The CEO records the owner's own words and the channel (dashboard, cli or assistant). An empty answer is refused.
