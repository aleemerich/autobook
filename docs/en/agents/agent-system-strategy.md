# Agent System Strategy

This is the current architectural decision for agents.

## Decision

The `agent_system/` package remains a modern adapter over the legacy `agents.py`
module.

This avoids a large and risky migration of agent classes right now, preserves
compatibility with existing calls and still lets new code depend on more
explicit contracts (`AgentSpec`, registry and modern factory).

## Current Contract

- New code should import `AgentFactory`, `create_agent` and role metadata from
  `agent_system/` whenever possible.
- `agents.py` remains the concrete implementation backend for agents.
- Dynamic custom agent registration is still supported, but access must go
  through public legacy methods such as `register_agent`,
  `has_registered_agent` and `unregister_agent`.
- No new code should read or modify `_agents_registry` directly.

## Optional Future Migration

A full migration from `agents.py` to `agent_system/` should only happen if it
clearly improves maintenance. If it happens, it should be broken into small
phases:

1. move one agent class at a time;
2. keep `agents.py` as compatibility layer;
3. preserve external prompts in `prompts/{LANG}/agents/`;
4. keep legacy factory compatibility tests until the end of the transition.

## Structured Feedback

Critic agents should prefer JSON output using the `CriticReport` contract, with
`critic_role` and `findings`. Each finding should contain:

- `source`
- `instruction`
- `quote`
- `severity`

The parser in `pipelines/book_generation_steps/critique.py` continues to accept
markdown as fallback for smaller models or malformed responses.
