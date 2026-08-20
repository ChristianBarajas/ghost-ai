<div align="center">

<img src="assets/ghost-logo.png" alt="GHOST Logo" width="600">

# GHOST

### Self-Programming Personal Software

**Observe. Learn. Automate.**

GHOST is an experimental AI agent that learns browser workflows by observing how a user interacts with software, comparing multiple demonstrations, identifying the user's intent, and converting repeated behavior into reusable skills.

</div>

---

## 👻 The Idea

Most automation requires a developer to manually define every step.

GHOST explores a different approach:

> **What if software could learn a workflow simply by watching you perform it?**

```text
YOU PERFORM A TASK
        ↓
GHOST OBSERVES
        ↓
STRUCTURES THE ACTIONS
        ↓
STORES THE DEMONSTRATION
        ↓
YOU DEMONSTRATE AGAIN
        ↓
AI COMPARES THE WORKFLOWS
        ↓
GHOST IDENTIFIES THE INTENT
        ↓
GENERATES A REUSABLE SKILL
        ↓
EXECUTES IT ON NEW INPUTS
        ↓
VERIFIES COMPLETION
```

The project is moving beyond:

> **"Repeat exactly what I did."**

toward:

> **"Understand what I was trying to accomplish and learn how to do it again."**

---

## ⚡ Current Prototype — GHOST v0.1

GHOST currently supports browser workflow observation, persistent memory, replay, AI-powered workflow generalization, reusable skill generation, and autonomous execution of learned research workflows.

### Observation & Memory

- ✅ Records browser navigation
- ✅ Records clicks and text input
- ✅ Records scrolling behavior
- ✅ Watches newly opened browser tabs
- ✅ Converts interactions into structured actions
- ✅ Filters duplicate and noisy browser events
- ✅ Stores demonstrations locally with SQLite
- ✅ Retrieves and inspects previous workflows

### Workflow Execution

- ✅ Replays recorded browser workflows with Playwright
- ✅ Resolves semantic browser targets such as `search_input`
- ✅ Supports provider-based execution
- ✅ Detects dynamically rendered search results
- ✅ Opens and evaluates external sources
- ✅ Retries when a source is unusable
- ✅ Extracts useful webpage content
- ✅ Verifies successful workflow completion

### AI Learning

- ✅ Compares multiple demonstrations
- ✅ Uses an OpenAI LLM to infer user intent
- ✅ Identifies variable inputs across demonstrations
- ✅ Distinguishes required behavior from optional/noisy actions
- ✅ Generates reusable semantic workflow steps
- ✅ Converts demonstrations into stored GHOST skills
- ✅ Uses AI to analyze and summarize extracted research
- ✅ Falls back to local processing when AI summarization is unavailable

### Future Work

- 🚧 Natural-language skill selection
- 🚧 Permission and approval system
- 🚧 Multi-step workflows beyond research
- 🚧 Cross-application workflow learning
- 🚧 Terminal, file system, and desktop automation

---

## 🧠 Learning From Demonstration

One of GHOST's main goals is to separate a user's **intent** from the exact mouse and keyboard actions used to accomplish it.

For example, GHOST observed two different demonstrations.

### Demonstration 1

```text
Search Bing
→ Enter "what is deep learning"
→ Inspect search results
→ Open an explanatory article
```

### Demonstration 2

```text
Search Bing
→ Enter "what is computer vision"
→ Inspect search results
→ Open an explanatory article
```

The raw demonstrations contain differences:

```text
navigation
clicks
scroll distances
query text
selected result
external source
```

Instead of simply memorizing those actions, GHOST sends the demonstrations through its AI generalization layer.

The model inferred:

```text
Intent:
Find information about a user-provided topic by
searching the web and consulting relevant sources.

Skill:
research_topic

Variable:
query

Semantic workflow:

input  → search_input → {{query}}
submit → search_input
select → relevant_result
open   → external_source
extract → useful_content
```

GHOST then stores this as a reusable skill.

---

## 🧪 Unseen Workflow Test

After learning `research_topic` from the previous demonstrations, GHOST was given a new query that was not part of the demonstrations:

```bash
python3 main.py run-skill research_topic \
  --query "what is artificial general intelligence"
```

GHOST autonomously:

```text
Selected a search provider
        ↓
Opened the search engine
        ↓
Entered the unseen query
        ↓
Detected search results
        ↓
Selected a relevant result
        ↓
Opened an external source
        ↓
Evaluated source quality
        ↓
Extracted useful content
        ↓
Used an LLM to summarize the research
        ↓
Verified successful completion
```

Example successful execution:

```text
👻 FOUND 10 POSSIBLE RESULTS

👻 TRYING RESULT #1
👻 RESULT → Artificial general intelligence - Wikipedia

✅ SOURCE ACCEPTED
👻 QUALITY → source looks useful (relevance=1.00)

🧠 GHOST AI → analyzing research
✅ AI summary generated.

Summary engine: ai

✅ External research source detected.
✅ Research summary generated.

✅ GHOST verified successful completion.
```

This demonstrates that GHOST can execute a learned workflow using an input that was never part of the original demonstrations.

---

## 🏗 Architecture

GHOST is separated into multiple layers so that observation, reasoning, execution, and verification are not handled by one monolithic system.

```text
┌─────────────────────────────┐
│           USER              │
│    Demonstrates a task      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│         OBSERVER            │
│     Python + Playwright     │
│                             │
│ Captures browser behavior   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│          MEMORY             │
│           SQLite            │
│                             │
│ Stores demonstrations       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      AI GENERALIZER         │
│         OpenAI LLM          │
│                             │
│ Infers intent, variables,   │
│ and reusable behavior       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│           SKILL             │
│                             │
│ Semantic representation     │
│ of learned behavior         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       PROVIDER LAYER        │
│                             │
│ Maps abstract behavior to   │
│ execution environments      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│          RUNNER             │
│     Python + Playwright     │
│                             │
│ Executes learned behavior   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│     QUALITY / RETRY         │
│                             │
│ Rejects unusable results    │
│ and retries alternatives    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       AI PROCESSING         │
│                             │
│ Understands extracted       │
│ information                 │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       VERIFICATION          │
│                             │
│ Confirms the workflow       │
│ actually succeeded          │
└─────────────────────────────┘
```

---

## 🤖 AI Integration

GHOST does not train its own large language model.

Instead, it integrates an OpenAI LLM as a reasoning layer inside the larger agent architecture.

The LLM is currently used for two primary tasks:

### Workflow Generalization

Given multiple recorded demonstrations, the model identifies:

- the user's likely intent
- values that should become variables
- behavior shared across demonstrations
- optional actions that can be ignored
- semantic steps required to reproduce the task

The model returns structured workflow data that GHOST can convert into an executable skill.

### Research Understanding

After GHOST autonomously opens and extracts content from a useful source, the LLM converts the raw webpage content into a concise answer and meaningful key terms.

If AI processing is unavailable, GHOST can fall back to a local summarization pipeline.

---

## 🧩 Why Semantic Skills?

Recorded browser automation is fragile.

A literal workflow might contain:

```text
scroll 965px
click exact HTML element
navigate
scroll 430px
click another exact element
```

GHOST instead attempts to represent the underlying behavior:

```text
input → search_input
submit → search_input
select → relevant_result
open → external_source
extract → useful_content
```

This allows the execution system to determine **how** to perform an action while the learned skill describes **what** needs to happen.

---

## 🛠 Tech Stack

- **Python** — core application and agent logic
- **Playwright** — browser observation and automation
- **SQLite** — persistent workflow and demonstration memory
- **OpenAI API / LLMs** — workflow reasoning and research understanding
- **Pydantic** — structured workflow and skill models
- **JSON** — persistent semantic skill representation
- **Git / GitHub** — source control and development workflow

---

## 🚀 Run GHOST

### Clone the repository

```bash
git clone https://github.com/ChristianBarajas/ghost-ai.git
cd ghost-ai
```

### Create the environment

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### Configure AI

Set your OpenAI API key in your local environment:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

Never commit API keys to the repository.

---

## 👀 Observe a Workflow

```bash
python3 main.py observe "My Workflow"
```

A browser opens.

Perform the task normally, then return to the terminal and press ENTER when finished.

GHOST stores the demonstration in its local workflow memory.

---

## 🧠 Inspect GHOST's Memory

```bash
python3 main.py show 10
```

Example:

```text
[navigate]
[click]
[input]
[navigate]
[scroll]
[click]
[navigate]
```

---

## 🔁 Replay a Workflow

```bash
python3 main.py replay 10
```

GHOST opens a new browser and attempts to reproduce the recorded workflow.

---

## 🧠 Learn From Multiple Demonstrations

```bash
python3 main.py learn-multi 10 11
```

GHOST compares the demonstrations and uses its AI reasoning layer to infer a reusable skill.

Example:

```text
🧠 GHOST AI → analyzing demonstrations

✅ AI workflow pattern detected.

Skill: research_topic
Confidence: 0.98

Variables detected:
- query = "what is deep learning"

Semantic steps:
1. input target=search_input value={{query}}
2. submit target=search_input
3. select target=relevant_result
4. open target=external_source
5. extract target=useful_content
```

The resulting skill is stored under:

```text
data/skills/
```

---

## 👻 Execute a Learned Skill

```bash
python3 main.py run-skill research_topic \
  --query "what is artificial general intelligence"
```

GHOST executes the semantic workflow using the new input rather than replaying the original demonstrations literally.

---

## ⚠️ Current Limitations

GHOST is an experimental prototype.

The current system is strongest with browser-based research and search workflows.

It does **not** yet:

- understand arbitrary software workflows
- autonomously operate desktop applications
- execute unrestricted computer actions
- learn every type of browser task
- select any learned skill from unrestricted natural language
- contain its own trained foundation model

Some browser behavior still depends on provider-specific resolution logic, and website changes can affect automation reliability.

The purpose of v0.1 is to validate the central idea:

> **Can multiple human demonstrations be transformed into reusable AI-assisted software behavior?**

The current prototype demonstrates an initial working version of that concept.

---

## 🗺 Roadmap

### Phase 1 — Observe & Replay ✅

Capture, store, inspect, and reproduce browser workflows.

### Phase 2 — Understand ✅

Compare demonstrations, remove noise, identify variable inputs, and infer user intent.

### Phase 3 — Learn ✅

Use AI reasoning to convert multiple demonstrations into reusable semantic skills.

### Phase 4 — Agent 🚧

Select learned skills from natural-language requests, plan multi-step tasks, request permission for sensitive actions, recover from failures, and verify outcomes.

### Phase 5 — Beyond the Browser

Expand workflow learning into:

- terminal commands
- file system operations
- development tools
- desktop applications
- multi-application workflows

---

## 🎯 Long-Term Vision

The long-term goal of GHOST is not simply browser automation.

It is to explore a model of personal software that adapts to the user.

Instead of requiring every workflow to be explicitly programmed:

```text
USER BEHAVIOR
      ↓
OBSERVATION
      ↓
MEMORY
      ↓
GENERALIZATION
      ↓
LEARNED SKILLS
      ↓
PERMISSION
      ↓
AUTOMATION
```

GHOST aims to move toward software that can learn **how a user works**, build reusable knowledge from those demonstrations, and assist with repetitive workflows while keeping execution visible and permission-controlled.

---

<div align="center">

### 👻 GHOST

**Software that learns how you work.**

Built by Christian Barajas

</div>