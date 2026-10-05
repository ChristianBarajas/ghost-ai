<div align="center">

<img src="assets/ghost-logo.png" alt="GHOST Logo" width="600">

# GHOST

### Self-Programming Personal Software

**Observe. Learn. Automate.**

GHOST is an experimental AI agent built around one idea:

> **What if software could learn how you work instead of requiring every workflow to be programmed manually?**

GHOST can observe or receive demonstrations of tasks, identify the underlying intent and reusable behavior, convert that behavior into structured skills, select those skills from natural-language requests, execute them with deterministic tools, verify whether they succeeded, and remember what happened.

The long-term goal is simple:

### **Software that learns how you work.**

</div>

---

## 👻 The Idea

Most automation works like this:

```text
DEVELOPER DEFINES WORKFLOW
        ↓
DEVELOPER WRITES AUTOMATION
        ↓
SOFTWARE REPEATS IT
```

GHOST explores a different model:

```text
YOU PERFORM OR DEMONSTRATE A TASK
                ↓
          GHOST OBSERVES
                ↓
       STRUCTURES THE ACTIONS
                ↓
        AI IDENTIFIES INTENT
                ↓
     REUSABLE PATTERN IS FOUND
                ↓
        GHOST PROPOSES A SKILL
                ↓
           USER APPROVES
                ↓
          SKILL IS STORED
                ↓
      GHOST CAN USE IT LATER
```

The goal is not:

> **"Repeat exactly what I clicked."**

The goal is:

> **"Understand what I was trying to accomplish and learn a reusable way to do it again."**

That distinction is the core of GHOST.

---

# ⚡ What GHOST Can Do Right Now

GHOST has evolved beyond recorded browser replay.

The current prototype can:

- understand natural-language requests
- choose between available skills using an LLM
- extract required variables from the user's request
- detect when required information is missing
- pause execution instead of inventing missing information
- ask the user for what it needs
- resume the same selected workflow afterward
- execute browser-based semantic workflows
- research informational questions
- evaluate and open external sources
- extract webpage content
- summarize research using AI
- inspect local software projects
- detect project technology stacks
- generate safe project verification plans
- run build, lint, and compile checks
- verify whether workflows actually succeeded
- remember previous executions
- learn reusable workflow candidates from multiple demonstrations
- identify values that should become variables
- generate semantic workflow steps
- validate AI-generated skills before saving them
- require approval before persisting learned capabilities
- automatically discover newly learned skills
- route future natural-language requests to those learned skills
- execute newly learned browser workflows without adding a custom router rule for every skill

The current agent loop looks like this:

```text
NATURAL-LANGUAGE REQUEST
          ↓
     UNDERSTAND INTENT
          ↓
       SELECT SKILL
          ↓
      EXTRACT INPUTS
          ↓
   ARE INPUTS MISSING?
       ↙         ↘
     YES          NO
      ↓            ↓
   ASK USER      EXECUTE
      ↓            ↓
   RESUME        VERIFY
       ↘          ↙
          MEMORY
```

---

# 🧠 Natural-Language Agent Routing

GHOST maintains a library of reusable skills.

The user does not have to manually choose which internal workflow should handle a task.

For example:

```text
Check if ~/Desktop/ghost is healthy
```

GHOST can determine:

```text
skill:
verify_project

variables:
project_path = ~/Desktop/ghost

confidence:
1.0
```

Another request:

```text
What is reinforcement learning?
```

can route to:

```text
skill:
research_topic

variables:
query = What is reinforcement learning?
```

The routing layer returns structured information including:

```text
selected skill
confidence
extracted variables
missing variables
reason for selection
```

The LLM is the reasoning layer.

It does not directly control every low-level operation.

A useful way to think about GHOST is:

```text
LLM = BRAIN

GHOST EXECUTORS = HANDS
```

The model decides **what capability fits the task**.

The deterministic runtime controls **how that capability is executed**.

---

# 💬 Multi-Turn Agent Execution

GHOST does not invent missing information simply to force a workflow to run.

Suppose the user says:

```text
Check if my project is healthy
```

GHOST can correctly determine:

```text
skill = verify_project
```

but also detect:

```text
missing = project_path
```

Instead of guessing a project path, GHOST pauses.

The interface asks:

```text
Which project should I verify?
```

The user can respond:

```text
~/Desktop/ghost
```

GHOST then continues the already-selected workflow.

It does not need to send the entire task through the router again.

```text
UNDERSTAND
    ↓
SELECT SKILL
    ↓
MISSING INPUT
    ↓
PAUSE
    ↓
ASK USER
    ↓
RECEIVE INPUT
    ↓
RESUME SAME SKILL
    ↓
EXECUTE
    ↓
VERIFY
    ↓
REMEMBER
```

This is the beginning of persistent multi-turn agent behavior rather than treating every prompt as an unrelated request.

---

# 🧬 Learning Skills From Demonstrations

One of the most important parts of GHOST is the ability to move beyond manually-authored workflows.

GHOST can receive multiple demonstrations and ask its AI reasoning layer:

> **What reusable behavior is shared by these examples?**

For example:

### Demonstration 1

```text
navigate → https://example.com
extract  → useful_content
```

### Demonstration 2

```text
navigate → https://www.python.org
extract  → useful_content
```

The URLs are different.

The underlying task is the same.

GHOST analyzes the demonstrations and recognizes that the changing value should become a variable:

```text
url
```

It can then generate a candidate skill:

```text
Skill:
read_website_content

Variable:
url

Steps:

navigate → {{url}}
extract  → useful_content
```

Instead of memorizing:

```text
open example.com
```

GHOST learns:

```text
open whatever URL the user provides
```

That is the core idea behind reusable workflow learning.

---

# 🛡 Learned Skills Require Approval

GHOST does not allow an LLM to silently generate and immediately trust executable workflows.

Learning and approval are separate steps.

```text
DEMONSTRATIONS
      ↓
AI GENERALIZATION
      ↓
VARIABLE DISCOVERY
      ↓
SEMANTIC WORKFLOW
      ↓
VALIDATION
      ↓
SKILL CANDIDATE
      ↓
USER APPROVAL
      ↓
PERSISTED SKILL
```

The AI proposes.

The GHOST runtime validates.

The user approves.

Only then does the skill become part of the active skill library.

Existing skills are also protected from silent replacement.

A newly generated workflow cannot automatically overwrite an existing capability unless replacement is explicitly allowed.

---

# 👻 GHOST Learned a New Skill — Then Used It

The current prototype has already completed the entire learning loop.

GHOST was given multiple demonstrations involving opening different websites and reading their content.

From those demonstrations, it generated:

```text
read_website_content
```

with:

```text
Variable:
url
```

and the semantic workflow:

```text
navigate → {{url}}
extract  → useful_content
```

The skill was reviewed and approved.

It was then saved into the GHOST skill library.

Later, the user submitted a completely new natural-language request:

```text
Open https://example.com and read the useful content
```

GHOST automatically:

```text
understood the request
        ↓
searched its skill library
        ↓
selected read_website_content
        ↓
extracted https://example.com
        ↓
executed the learned workflow
        ↓
opened the webpage
        ↓
extracted its content
        ↓
verified success
        ↓
saved the execution to memory
```

The router selected the learned skill with:

```text
100% confidence
```

Most importantly:

> **No special routing rule was added for `read_website_content`.**

The skill became part of the same dynamic capability library used by the rest of GHOST.

This demonstrates one of the project's central goals:

### **A capability can be learned, persisted, discovered, selected, and executed later from a new natural-language request.**

---

# 🧩 Semantic Skills

Literal browser recordings are fragile.

A raw automation might contain:

```text
scroll 965 pixels

click DOM element #438

wait

scroll 320 pixels

click exact link

open page
```

That sequence depends heavily on the exact state of the website.

GHOST attempts to represent the meaning instead:

```text
input   → search_input
submit  → search_input
select  → relevant_result
open    → external_source
extract → useful_content
```

Or:

```text
navigate → {{url}}
extract  → useful_content
```

The skill describes:

```text
WHAT should happen
```

while the executor determines:

```text
HOW to make it happen
```

This separation allows workflows to become reusable capabilities rather than recordings of one exact interaction.

---

# 🔎 Research Agent

GHOST includes a semantic research workflow.

A request such as:

```text
What is reinforcement learning?
```

can automatically route to:

```text
research_topic
```

GHOST then performs an actual workflow:

```text
search the web
      ↓
inspect results
      ↓
choose a relevant result
      ↓
open an external source
      ↓
evaluate source usefulness
      ↓
extract relevant content
      ↓
use AI to understand the content
      ↓
generate a concise answer
      ↓
verify completion
      ↓
remember the run
```

This is different from simply sending:

```text
"What is reinforcement learning?"
```

directly to an LLM.

GHOST gathers source material through its execution system first and uses AI as a reasoning layer over that information.

During testing, GHOST successfully routed the reinforcement-learning request to `research_topic`, selected an IBM source, generated a concise answer, verified the result, and saved the execution.

---

# 💻 Software Project Verification

GHOST is not limited to browser automation.

It also has a separate execution engine for developer-oriented workflows.

The `verify_project` skill can inspect a local software repository.

Example:

```text
Check if ~/Desktop/ghost is healthy
```

GHOST can:

```text
inspect repository
      ↓
discover project structure
      ↓
detect technology stack
      ↓
build verification plan
      ↓
run safe checks
      ↓
inspect results
      ↓
verify project health
      ↓
remember execution
```

When GHOST verifies its own repository, it detects technologies including:

```text
Python
Node
Vite
```

and generates checks such as:

```text
python -m compileall -q .

npm run build

npm run lint
```

A successful verification run produced:

```text
3 CHECKS
3 PASSED
0 FAILED
```

The project verifier can also inspect Git status so the result reflects the actual state of the repository at execution time.

This demonstrates GHOST's multi-executor architecture:

```text
REQUEST
   ↓
ROUTER
   ↓
SKILL
   ↓
EXECUTOR DISPATCHER
   ├── Browser Executor
   └── Project Executor
```

The GHOST architecture is therefore not tied to only one kind of software interaction.

---

# 🧠 Persistent Memory

GHOST stores execution history.

A task record can contain:

```text
request
selected skill
provider
status
success
verification state
result
error
creation time
completion time
```

This means GHOST can remember:

```text
what was attempted
what capability handled it
whether it succeeded
what result was produced
when it happened
```

Successful runs are preserved.

Failed runs are preserved too.

The control center exposes this history through **Recent Runs**.

Today, memory provides execution history.

Long-term, that history can become part of how GHOST learns which behaviors are useful, reliable, repeated, or worth improving.

---

# 🌐 The GHOST Control Center

GHOST includes a web interface for interacting with the agent.

The control center exposes the internal agent flow instead of hiding everything behind a single response.

The user can:

### Submit Natural-Language Tasks

```text
What is reinforcement learning?
```

```text
Check if ~/Desktop/ghost is healthy
```

```text
Open https://example.com and read the useful content
```

### Inspect AI Routing

The interface displays:

```text
selected skill
confidence
routing explanation
extracted inputs
```

### Supply Missing Information

If a required value is unavailable, GHOST can ask for it and continue the same task afterward.

### Inspect Execution Results

Research workflows display researched information and sources.

Project workflows display verification checks and results.

### Browse Capabilities

The control center displays every discovered GHOST skill.

### Inspect Skill Definitions

Each skill exposes:

```text
description
variables
semantic steps
```

### Inspect Memory

Recent executions can be reopened and inspected.

The goal is to make agent execution visible and understandable rather than completely opaque.

---

# 🧠 Current Skill Library

GHOST's current skill library contains capabilities including:

## `research_topic`

Search the web for an informational topic, select an external source, extract useful information, generate an AI-assisted answer, and verify completion.

## `web_search`

Perform a semantic web search using a user-provided query.

## `verify_project`

Inspect a local software project, detect its stack, build a safe verification plan, execute checks, and determine project health.

## `read_website_content`

A skill generated by GHOST from demonstrations.

It accepts:

```text
url
```

and executes:

```text
navigate → {{url}}
extract  → useful_content
```

## `research_topic_via_web_search`

An earlier experimental research workflow retained in the current skill library while the skill system continues to evolve.

---

# 🔄 Two Connected GHOST Loops

GHOST currently contains two major loops.

## Agent Execution

```text
USER REQUEST
      ↓
AI ROUTER
      ↓
SKILL LIBRARY
      ↓
VARIABLE EXTRACTION
      ↓
MISSING INPUT HANDLING
      ↓
EXECUTOR
      ↓
VERIFICATION
      ↓
MEMORY
```

## Skill Learning

```text
DEMONSTRATIONS
      ↓
AI GENERALIZER
      ↓
INTENT DISCOVERY
      ↓
VARIABLE DISCOVERY
      ↓
SEMANTIC STEPS
      ↓
VALIDATION
      ↓
USER APPROVAL
      ↓
SKILL LIBRARY
```

The important part is that these loops connect.

```text
LEARNED SKILL
      ↓
SKILL LIBRARY
      ↓
ROUTER DISCOVERS IT
      ↓
FUTURE REQUEST
      ↓
EXECUTION
```

A learned workflow can become a future agent capability.

---

# 🏗 GHOST Architecture

```text
┌──────────────────────────────────┐
│               USER               │
│                                  │
│ Natural-language requests        │
│ Workflow demonstrations          │
└─────────────────┬────────────────┘
                  ↓
┌──────────────────────────────────┐
│          AI REASONING            │
│                                  │
│ Intent understanding             │
│ Skill routing                    │
│ Variable extraction              │
│ Workflow generalization          │
└─────────────────┬────────────────┘
                  ↓
┌──────────────────────────────────┐
│            SKILL LIBRARY         │
│                                  │
│ Reusable semantic capabilities   │
└─────────────────┬────────────────┘
                  ↓
┌──────────────────────────────────┐
│        EXECUTOR DISPATCHER       │
└────────────┬─────────────┬───────┘
             ↓             ↓
       Browser Engine   Project Engine
             ↓             ↓
             └──────┬──────┘
                    ↓
┌──────────────────────────────────┐
│           VERIFICATION           │
│                                  │
│ Did the intended task succeed?   │
└─────────────────┬────────────────┘
                  ↓
┌──────────────────────────────────┐
│              MEMORY              │
│                                  │
│ Store task, result, and outcome  │
└──────────────────────────────────┘
```

The AI does not replace the rest of the system.

Instead:

```text
AI reasoning
+
structured skills
+
deterministic tools
+
verification
+
memory
```

form the complete agent.

---

# 🔄 The Bigger Vision

The long-term GHOST loop is:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
LEARN
   ↓
RECOGNIZE
   ↓
SUGGEST
   ↓
APPROVE
   ↓
ACT
   ↓
VERIFY
   ↓
REMEMBER
```

## Observe

Watch how the user performs meaningful workflows.

## Understand

Determine what the user is actually trying to accomplish.

## Learn

Convert repeated behavior into reusable capabilities.

## Recognize

Determine when a learned capability applies to a new situation.

## Suggest

Eventually offer to perform workflows before the user has to manually repeat them.

## Approve

Require permission when actions are meaningful or consequential.

## Act

Use deterministic tools to carry out the workflow.

## Verify

Check whether the intended outcome actually occurred.

## Remember

Store what happened and use that history to improve future behavior.

---

# ✅ Current Progress

```text
OBSERVE       ✅ Browser demonstration infrastructure

UNDERSTAND    ✅ LLM intent and workflow reasoning

LEARN         ✅ Demonstrations → reusable skill candidates

APPROVE       ✅ Explicit learned-skill approval

RECOGNIZE     ✅ Natural-language skill routing

ASK           ✅ Missing-input detection and follow-up

RESUME        ✅ Continue an already-routed task

ACT           ✅ Browser and project executors

VERIFY        ✅ Workflow verification

REMEMBER      ✅ Persistent task history
```

The next major challenge is connecting these pieces more deeply and making workflow recognition increasingly proactive.

---

# 🚧 What GHOST Is Not Yet

GHOST is still an experimental prototype.

It does **not** yet:

- continuously observe everything happening on the user's computer
- understand every arbitrary desktop application
- safely execute unrestricted operating-system actions
- generalize every possible browser interaction
- automatically trust AI-generated workflows
- autonomously perform consequential actions without approval
- proactively detect every repeated behavior
- fully recover from every website or environment change
- learn arbitrary cross-application workflows
- contain a foundation model trained from scratch

The newest workflow-learning pipeline currently works with structured demonstrations supplied to GHOST.

Browser observation infrastructure exists, but automatically connecting passive observation to continuous skill proposals is still part of the larger vision.

Raw webpage extraction can also contain noise depending on the structure of the source.

GHOST is therefore not a finished autonomous computer-use system.

It is an experiment in:

> **AI-assisted workflow learning, reusable agent capabilities, deterministic execution, verification, and personal software adaptation.**

---

# 🗺 Roadmap

## Phase 1 — Observe & Replay ✅

Capture browser interactions, structure them into actions, store demonstrations, inspect previous workflows, and replay recorded behavior.

## Phase 2 — Understand ✅

Compare demonstrations, remove incidental behavior, infer intent, identify variable inputs, and represent workflows semantically.

## Phase 3 — Learn ✅

Generate reusable skill candidates from demonstrations, validate them, require approval, and persist approved capabilities.

## Phase 4 — Agent Core ✅

Route natural-language requests to skills, extract inputs, execute workflows, verify results, and maintain task history.

## Phase 5 — Conversational Execution ✅ / 🚧

Detect missing information, pause execution, ask follow-up questions, resume existing tasks, and expand toward richer multi-turn planning.

Basic continuation is working.

More general multi-step conversation and planning is still being developed.

## Phase 6 — Recognition & Proactive Assistance 🚧

Move from:

```text
"Run this task."
```

toward:

```text
"You normally perform this workflow now.
Would you like me to do it?"
```

This requires GHOST to learn **when** a workflow is relevant, not only **how** to execute it.

## Phase 7 — Beyond the Browser 🚧

Expand reusable execution toward:

```text
terminal workflows
file-system operations
development tools
desktop applications
multi-application workflows
```

Consequential actions should remain permission-controlled.

---

# 🎯 Long-Term Vision

GHOST is not intended to become another chatbot wrapper.

The goal is not:

```text
USER ASKS QUESTION
        ↓
LLM WRITES RESPONSE
```

The goal is software that builds reusable operational knowledge from how its user works.

```text
USER BEHAVIOR
      ↓
OBSERVATION
      ↓
STRUCTURED MEMORY
      ↓
UNDERSTANDING
      ↓
GENERALIZATION
      ↓
LEARNED SKILLS
      ↓
CONTEXTUAL RECOGNITION
      ↓
SUGGESTION
      ↓
PERMISSION
      ↓
EXECUTION
      ↓
VERIFICATION
      ↓
NEW MEMORY
```

Over time, GHOST should increasingly understand:

```text
what the user does

why they do it

which actions are meaningful

which behavior is accidental noise

what information changes between runs

which workflows repeat

when a learned workflow is useful

which tools should execute it

what requires permission

whether execution actually succeeded
```

The final vision is personal software that gradually learns how its user works and turns repeated behavior into reusable capabilities.

---

# 🛠 Under the Hood

The technology exists to support the idea rather than define it.

GHOST currently uses:

- **OpenAI LLMs** — intent reasoning, skill routing, workflow generalization, research understanding
- **Python** — agent runtime, validation, execution, verification
- **FastAPI** — agent API
- **React + TypeScript** — GHOST control center
- **Playwright** — browser interaction and execution
- **SQLite** — persistent task and workflow memory
- **Pydantic** — validated structured agent data
- **JSON skills** — reusable semantic workflow definitions

The interesting part is how they work together:

```text
LLM reasoning
+
semantic skills
+
deterministic execution
+
verification
+
memory
```

---

# 🚀 Run GHOST

## Clone the repository

```bash
git clone https://github.com/ChristianBarajas/ghost-ai.git
cd ghost-ai
```

## Create the Python environment

```bash
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

playwright install chromium
```

## Configure OpenAI

Create a local `.env` file containing:

```text
OPENAI_API_KEY=your_key_here
```

Never commit API keys.

Load it before starting the backend:

```bash
set -a
source .env
set +a
```

## Start the GHOST API

```bash
uvicorn ghost.api.app:app --reload --port 8000
```

## Start the Control Center

In another Terminal:

```bash
cd frontend

npm install

npm run dev
```

Open the local Vite URL printed in the terminal.

---

# 🧪 Example Requests

### Research

```text
What is reinforcement learning?
```

### Project Verification

```text
Check if ~/Desktop/ghost is healthy
```

### Missing Information

```text
Check if my project is healthy
```

GHOST can respond:

```text
Which project should I verify?
```

### Learned Capability

```text
Open https://example.com and read the useful content
```

---

# 👻 Why GHOST?

Software usually expects people to learn how the software works.

GHOST explores the reverse:

> ### **Software that learns the user.**

Instead of every repeated behavior remaining another manual chore—or another automation that a developer has to explicitly engineer—GHOST explores whether repeated human workflows can gradually become reusable software capabilities.

That is the experiment.

---

<div align="center">

<img src="assets/ghost-logo.png" alt="GHOST Logo" width="350">

### GHOST

**Software that learns how you work.**

Built by Christian Barajas

</div>
