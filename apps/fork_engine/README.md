# Fork Engine (fork_engine)

The Fork Engine is the simulation and reactive core of the dt-chat Digital Twin framework.

## What it is

This package acts as an event-driven orchestrator. It listens to the touchpoint event stream on Redis (`tp_channel`). When a designated trigger condition (e.g. human operator escalation) occurs, it duplicates the active conversation state, forks the history, and spins up multiple alternative **Digital Twin** simulations in parallel—each running a different configuration of conversational agents and user bots under identical preceding dialogue context.

## For what it can be used for

- Performing automated "what-if" testing and comparison of different chatbot setups (such as varying prompts, alternative models, or multi-tool RAG setups).
- Evaluating how a chatbot handles critical conversational triggers (catalyst points) starting from identical preceding states.
- Running reactive, parallel user swarms on demand to uncover agent pathways and bottlenecks.

---

## Detailed Documentation

For a detailed walkthrough of how the fork conditions work, the engine's internals, and sequence diagrams, see the dedicated documentation page:
👉 **[docs/fork_engine.md](../../docs/fork_engine.md)**

To learn how to run the Fork Engine inside your local simulation pipeline, refer to the:
👉 **[docs/USAGE.md](../../docs/USAGE.md)**
