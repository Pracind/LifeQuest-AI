"""
AI utilities for LifeQuest AI.

- Single public entrypoint: generate_plan_for_goal(title, description)
- Supports Groq as the main provider + a mock fallback
- Always returns a list of GeneratedStep objects
"""

from __future__ import annotations

import json
import os
import textwrap
from enum import Enum
from typing import List, Optional

from pydantic import ValidationError

from backend.schemas import GeneratedStep, Difficulty
from backend.logging_config import logger

# Optional Groq import (handle ImportError gracefully)
try:
    from groq import Groq  # type: ignore
except ImportError:
    Groq = None


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

class AIProvider(str, Enum):
    groq = "groq"
    mock = "mock"


def get_provider() -> AIProvider:
    """
    Decide which AI provider to use, based on:
    - LQ_AI_PROVIDER (if set)
    - otherwise: auto-detect based on available keys/imports
    """
    value = os.getenv("LQ_AI_PROVIDER")

    if value:
        try:
            return AIProvider(value)
        except ValueError:
            logger.warning("AI: unknown LQ_AI_PROVIDER=%r, falling back to auto-detect", value)

    # Auto-detect
    if os.getenv("GROQ_API_KEY") and Groq is not None:
        return AIProvider.groq

    # Default to mock if nothing else is available
    return AIProvider.mock


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """
    If the model replies with ```json ... ``` or ``` ... ```, strip the fences
    and return the inner JSON fragment.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (``` or ```json)
        lines = lines[1:]
        # Drop last line if it looks like closing ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _parse_steps_from_json(raw: str) -> List[GeneratedStep]:
    """
    Parse a JSON string of steps into a list[GeneratedStep].

    Validates:
    - JSON is a list
    - Each item is an object
    - Each item matches GeneratedStep schema
    - Positions are normalized to a strict 1..N linear order
    """

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI output was not valid JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of steps")

    steps: List[GeneratedStep] = []
    
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Step {idx} was not an object")
        
        # Provide defaults / safety for missing or weird fields
        # Position: if missing or invalid, use current index
        position = item.get("position")
        if not isinstance(position, int) or position <= 0:
            item["position"] = idx

        # Substeps: ensure it's always present as a list
        if "substeps" not in item or item["substeps"] is None:
            item["substeps"] = []
        elif not isinstance(item["substeps"], list):
            raise ValueError(f"Step {idx} substeps must be a list of strings")

        try:
            step = GeneratedStep.model_validate(item)
        except ValidationError as e:
            raise ValueError(f"Step {idx} did not match schema: {e}") from e

        steps.append(step)
        
    
    steps.sort(key=lambda s: s.position)

    for idx, step in enumerate(steps, start=1):
        step.position = idx

    logger.info("AI: received %d steps after validation", len(steps))

    return steps


def _mock_plan(goal_title: str) -> List[GeneratedStep]:
    base_title = goal_title

    return [
        GeneratedStep(
            title=f"Clarify what '{base_title}' means for you",
            description=f"Write a short paragraph describing what success for '{base_title}' looks like.",
            position=1,
            difficulty=Difficulty.easy,
            est_time_minutes=20,
            reflection_required=True,
            reflection_prompt="After writing your definition of success, what surprised you or felt most important?"
        ),
        GeneratedStep(
            title=f"Research the key requirements for '{base_title}'",
            description="Spend 30–45 minutes searching for skills, constraints, and prerequisites related to this goal.",
            position=2,
            difficulty=Difficulty.medium,
            est_time_minutes=40,
            reflection_required=True,
            reflection_prompt="What did you learn about the gap between where you are now and these requirements?"
        ),
        # ... some steps might not need reflection:
        GeneratedStep(
            title="Do the scheduled action",
            description="Follow through and fully complete the action you scheduled.",
            position=5,
            difficulty=Difficulty.hard,
            est_time_minutes=60,
            reflection_required=True,
            reflection_prompt="What did you notice about your energy, emotions, or resistance while doing this action?"
        ),
        GeneratedStep(
            title="Reflect and choose the next action",
            description="Reflect on how it went and decide on the next concrete action you’ll take.",
            position=6,
            difficulty=Difficulty.easy,
            est_time_minutes=20,
            reflection_required=True,
            reflection_prompt="What worked well, what didn’t, and what will you change in your next action?"
        ),
    ]


# ---------------------------------------------------------------------------
# Groq implementation (main one)
# ---------------------------------------------------------------------------

def _generate_with_groq(goal_title: str, goal_description: Optional[str]) -> List[GeneratedStep]:
    if Groq is None:
        raise RuntimeError("groq package is not installed")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)

    system_prompt = (
        "You are LifeQuest AI, an assistant that turns personal goals into "
        "clear, linear quests. You ALWAYS respond with pure JSON only, "
        "no explanations or extra text.\n"
        "\n"
        "RULES:\n"
        "- Each step must be a concrete, highly specific physical or digital ACTION the user can perform.\n"
        "- Each step must clearly state WHERE and HOW to do it.\n"
        "- The steps MUST be executable in 25–90 minutes.\n"
        "- Avoid vague verbs.\n"
        "- Additionally, you must decide if each step is reflection-worthy:\n"
        "  - reflection_required = true ONLY for steps where the user learns something, faces difficulty, makes a decision, or might change strategy.\n"
        "  - reflection_required = false for trivial or purely mechanical steps (e.g. 'open VS Code', 'create folder', 'install tool').\n"
        "- For reflection-worthy steps, write reflection_prompt as a single, concrete question that helps the user extract value from that action.\n"
        "- For non-reflection-worthy steps, set reflection_required = false and reflection_prompt = null.\n"
        "\n"
        "Output strictly JSON of actionable checkpoints."
    )

    user_prompt = textwrap.dedent(
        f"""
        Turn the following goal into a sequence of as many extremely actionable steps as needed to fully complete the goal.
        This may be anywhere from 10 to 50 steps depending on complexity.
        Do not combine multiple actions into one step. Every step must be a standalone action.

        Goal title: "{goal_title}"
        Goal description: "{goal_description or ""}"

        Each step MUST contain:
        - title
        - description
        - position (integer, strictly sequential)
        - difficulty ("easy" | "medium" | "hard")
        - est_time_minutes
        - substeps: 6–12 atomic micro-actions written as short commands
        - reflection_required: true or false
        - reflection_prompt: a single, specific reflection question if reflection_required is true, otherwise null

        SUBSTEP RULES:s
        - Tell the user exactly what to do, without needing to think
        - Include websites, apps, example search text, folder names, numbers and targets
        - Break actions down into individual clicks / searches / typing
        - Avoid generic verbs like “prepare”, “research”, “look into”, “improve”, “practice”, “review”

        SYSTEM RULES:
        - Each step must be a concrete actionable task the user can perform
        - No vague tasks
        - No planning steps like “break into milestones”
        
        Respond ONLY with a JSON array of steps.
        The response MUST begin with '[' and end with ']'.
        Do NOT include any explanation, commentary, or markdown fences.
        """
    ).strip()


    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    message = response.choices[0].message
    content = getattr(message, "content", None) or message.get("content")  # type: ignore

    raw_json = _strip_code_fences(content)
    return _parse_steps_from_json(raw_json)


# ---------------------------------------------------------------------------
# Goal completion summary
# ---------------------------------------------------------------------------

def _fallback_completion_summary(goal, steps, reflections) -> str:
    """
    Simple non-AI summary we can fall back to if Groq is not available.
    """
    total_steps = len(steps)
    hard_count = sum(1 for s in steps if getattr(s, "difficulty", None) == Difficulty.hard)
    easy_medium = total_steps - hard_count
    reflection_count = len(reflections)

    return (
        f'You finished the quest "{goal.title}". '
        f"You moved this from idea to done over {total_steps} quest step(s), "
        f"including {hard_count} deeper challenge(s) and {easy_medium} lighter ones. "
        f"Along the way you paused to reflect {reflection_count} time(s). "
        "Take a moment to appreciate what you pulled off here before you jump into the next quest."
    )


def generate_completion_summary_for_goal(goal, steps, reflections) -> str:
    """
    Generate a warm, motivational completion summary using Groq if available.
    Falls back to a simple template if AI fails or provider is not Groq.
    """
    provider = get_provider()
    # If not using Groq, just return the fallback
    if provider != AIProvider.groq:
        logger.info("AI summary: provider is %s, using fallback summary", provider.value)
        return _fallback_completion_summary(goal, steps, reflections)

    # Build context for the model
    step_titles = [s.title for s in steps[:12]]

    reflection_snippets = []
    for r in reflections[:10]:
        text = getattr(r, "text", None)
        if text:
            t = text.strip().replace("\n", " ")
            if len(t) > 200:
                t = t[:197] + "..."
            reflection_snippets.append(t)

    system_msg = (
        "You are a motivational reflection coach summarizing a completed goal.\n"
        "Write a warm, natural 3–6 sentence summary.\n"
        "- Do NOT list steps or bullets.\n"
        "- Do NOT enumerate actions one by one.\n"
        "Blend:\n"
        "• celebration of completion\n"
        "• the essence of what was accomplished overall\n"
        "• themes from reflections, without quoting the user verbatim\n"
        "End by gently encouraging momentum into the next quest.\n"
    )

    user_msg = f"""
Goal title: {goal.title}
Goal description: {goal.description or ""}

Step titles (context only, NOT for output):
{step_titles}

Reflection themes (NOT quotes, just rough ideas):
{reflection_snippets}
"""

    try:
        if Groq is None:
            raise RuntimeError("groq package is not installed")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.85,
            max_tokens=400,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )

        message = response.choices[0].message
        content = getattr(message, "content", None) or getattr(message, "text", None)
        if not content:
            raise RuntimeError("Groq response had no content")

        summary = content.strip()
        logger.info("AI summary: generated completion summary for goal %s", goal.id)
        return summary

    except Exception as exc:
        logger.exception(
            "AI summary: failed to generate with Groq for goal %s: %r. Using fallback.",
            getattr(goal, "id", "unknown"),
            exc,
        )
        return _fallback_completion_summary(goal, steps, reflections)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def generate_plan_for_goal(goal_title: str, goal_description: Optional[str]) -> List[GeneratedStep]:
    """
    Main function used by FastAPI routes.

    - Chooses provider (Groq / mock)
    - On any error → logs and falls back to mock plan
    """
    provider = get_provider()
    logger.info("AI: using provider=%s for goal=%r", provider.value, goal_title)

    try:
        if provider == AIProvider.groq:
            return _generate_with_groq(goal_title, goal_description)

        # Explicit mock provider
        logger.info("AI: using MOCK provider")
        return _mock_plan(goal_title)

    except Exception as exc:
        logger.exception(
            "AI: provider %s failed with error %r. Falling back to mock plan.",
            provider.value,
            exc,
        )
        return _mock_plan(goal_title)
    


    


# Quick manual test (optional)
if __name__ == "__main__":
    steps = generate_plan_for_goal(
        "Land a job in Latvia",
        "Indian citizen, no EU visa yet, 2 years of experience, wants to relocate safely with a job in hand."
    )
    for s in steps:
        print(s.position, s.title, f"({s.difficulty}, {s.est_time_minutes} min)")






