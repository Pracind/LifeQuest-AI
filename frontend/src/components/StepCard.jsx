import { useState, useEffect } from "react";
import { startStep, completeStep, reflectOnStep } from "../api";

const STATUS_IDLE = "idle";
const STATUS_IN_PROGRESS = "in_progress";
const STATUS_COMPLETED = "completed";

export default function StepCard({ step, goalId, onStepUpdated }) {
  const [status, setStatus] = useState(() => {
    if (step.is_completed) return STATUS_COMPLETED;
    if (step.is_started) return STATUS_IN_PROGRESS;
    return STATUS_IDLE;
  });

  useEffect(() => {
    if (step.is_completed) setStatus(STATUS_COMPLETED);
    else if (step.is_started) setStatus(STATUS_IN_PROGRESS);
    else setStatus(STATUS_IDLE);
  }, [step.is_started, step.is_completed]);

  const [hasReflection, setHasReflection] = useState(step.has_reflection);
  const [reflecting, setReflecting] = useState(false);
  const [reflectionText, setReflectionText] = useState(
    step.reflection_text || ""
  );

  useEffect(() => {
    setReflectionText(step.reflection_text || "");
  }, [step.reflection_text]);

  // --- Handlers with optimistic UI + patch back to parent ---------

  async function handleStart() {
    // optimistic UI: assume it works
    setStatus(STATUS_IN_PROGRESS);
    onStepUpdated?.({ is_started: true });

    try {
      await startStep(goalId, step.id);
      // backend is in sync now; nothing else needed
    } catch (err) {
      console.error("Failed to start step", err);
      // rollback if request fails
      setStatus(STATUS_IDLE);
      onStepUpdated?.({ is_started: false });
    }
  }

  async function handleComplete() {
    const prevStatus = status;

    // optimistic UI
    setStatus(STATUS_COMPLETED);
    onStepUpdated?.({ is_started: true, is_completed: true });

    try {
      await completeStep(goalId, step.id);

      // 👇 tell the rest of the app that XP has changed
      window.dispatchEvent(new Event("xp-updated"));
    } catch (err) {
      console.error("Failed to complete step", err);
      // rollback
      setStatus(prevStatus);
      onStepUpdated?.({ is_completed: false });
    }
  }

  async function handleSaveReflection() {
    if (!reflectionText.trim()) return;

    // optimistic UI
    setHasReflection(true);
    setReflecting(false);
    onStepUpdated?.({
      has_reflection: true,
      reflection_text: reflectionText,
    });

    try {
      await reflectOnStep(goalId, step.id, reflectionText);

      // 👇 XP also changes when you add first reflection
      window.dispatchEvent(new Event("xp-updated"));
    } catch (err) {
      console.error("Failed to save reflection", err);
      // rollback
      setHasReflection(false);
      onStepUpdated?.({ has_reflection: false });
    }
  }

  function handleOpenReflection() {
    setReflectionText(step.reflection_text || "");
    setReflecting(true);
  }

  // --- Button rendering -------------------------------------------

  function renderPrimaryButton() {
    if (status === STATUS_IDLE) {
      return (
        <button
          onClick={handleStart}
          className="text-xs px-3 py-2 border border-slate-700 rounded-md hover:bg-slate-800"
        >
          Start
        </button>
      );
    }

    if (status === STATUS_IN_PROGRESS) {
      return (
        <button
          onClick={handleComplete}
          className="text-xs px-3 py-2 border border-emerald-600 bg-emerald-600/10 rounded-md hover:bg-emerald-600/20"
        >
          Mark Complete
        </button>
      );
    }

    if (status === STATUS_COMPLETED) {
      // If this step doesn't need reflection, just show Done
      if (!step.reflection_required) {
        return (
          <span className="text-xs px-3 py-2 border border-slate-700 rounded-md text-slate-300">
            Done
          </span>
        );
      }

      return (
        <button
          onClick={handleOpenReflection}
          className="text-xs px-3 py-2 border border-blue-600 bg-blue-600/10 rounded-md hover:bg-blue-600/20"
        >
          {hasReflection ? "Edit reflection" : "Reflect"}
        </button>
      );
    }

    return null;
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg">
          {step.position}. {step.title}
        </h2>
        <span className="text-xs px-2 py-1 rounded bg-slate-700 capitalize">
          {step.difficulty}
        </span>
      </div>

      <p className="text-sm text-slate-300 mt-1">{step.description}</p>

      <div className="text-xs text-slate-500 mt-2">
        Estimated time: {step.est_time_minutes} min
      </div>

      {step.substeps && step.substeps.length > 0 && (
        <ol className="ml-5 mt-3 list-decimal text-xs text-slate-300 space-y-1">
          {step.substeps.map((sub, i) => (
            <li key={i}>{sub}</li>
          ))}
        </ol>
      )}

      <div className="mt-4 flex gap-2 items-center">
        {renderPrimaryButton()}

        {hasReflection && (
          <span className="text-[11px] text-emerald-400">
            + XP awarded for reflection
          </span>
        )}
      </div>

      {reflecting && (
        <div className="mt-4 border border-slate-700 rounded-lg p-3 bg-slate-950/80">
          <label className="text-xs text-slate-300 block mb-1">
            {step.reflection_prompt || "Reflection"}
          </label>
          <textarea
            className="w-full text-xs bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-slate-100"
            rows={3}
            value={reflectionText}
            onChange={(e) => setReflectionText(e.target.value)}
            placeholder="Write your reflection here..."
          />
          <div className="mt-2 flex gap-2 justify-end">
            <button
              onClick={() => {
                setReflecting(false);
                // revert to last saved reflection from backend/parent
                setReflectionText(step.reflection_text || "");
              }}
              className="text-[11px] px-2 py-1 rounded border border-slate-700"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveReflection}
              className="text-[11px] px-3 py-1 rounded bg-blue-600 hover:bg-blue-500"
            >
              Save reflection
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
