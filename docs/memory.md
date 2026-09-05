# Memory Architecture

## 1. Purpose

The memory subsystem is what turns the QA agent from a one-time executor into a continuously improving system.

It must store:
- what worked
- what failed
- how failures were healed
- which locators are stable
- what pages and flows look like
- what visual baselines are approved
- what policies users prefer

---

# 2. Memory Principles

## 2.1 Verified Writes Only
Memory should be written only from:
- successful runs
- approved healing candidates
- validated visual baselines
- explicit user feedback

Do not blindly persist AI guesses.

## 2.2 Versioned Knowledge
Every memory entry should be versioned so it can be:
- audited
- rolled back
- compared over time

## 2.3 Scoped Knowledge
Memory must be scoped by:
- project
- environment
- page/route
- component intent
- viewport/theme where relevant

## 2.4 Explainable Memory
Every memory entry should answer:
- what is stored?
- why was it stored?
- when was it verified?
- how often has it succeeded?
- where was it used?

## 2.5 Decay and Supersession
Old knowledge should not permanently dominate.
Memory entries should support:
- confidence decay
- supersession by newer verified knowledge
- archival

---

# 3. Memory Types

## 3.1 Locator Memory
Stores the most reliable way to identify UI elements.

### Example
```json
{
  "memory_type": "locator",
  "project_id": "proj_123",
  "page_hint": "/login",
  "intent": "submit_login_button",
  "primary_selector": "[data-testid='login-submit']",
  "fallback_selectors": [
    "button:has-text('Sign in')",
    "xpath=//button[@type='submit']"
  ],
  "confidence": 0.94,
  "success_count": 18,
  "failure_count": 1,
  "last_verified_at": "2026-01-01T10:20:00Z",
  "provenance": {
    "run_id": "run_456",
    "healing_candidate_id": "hc_789"
  }
}