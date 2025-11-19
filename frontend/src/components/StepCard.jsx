// src/components/StepCard.jsx
import { useState } from "react";

// Simple heuristic: decide if this step deserves a reflection
function isReflectionWorthy(step) {
  // Very short, purely mechanical actions → skip
  const title = (step.title || "").toLowerCase();

  const trivialPrefixes = [
    "open chrome",
    "open google",
    "open vscode",
    "open visual studio code",
    "install ",
    "create a new folder",
  ];

  if (trivialPrefixes.some((p) => title.startsWith(p))) {
    return false;
  }

  // If it has a decent duration or is medium/hard, it's worth reflecting on
  const minutes = step.est_time_minutes || 0;
  if (minutes >= 20) return true;
  if (["medium", "hard"].includes((step.difficulty || "").toLowerCase())) {
    return true;
  }

  // Fallback: not required
  return false;
}

export default function StepCard({ step }) {
  // local UI state only for now
  const [status, setStatus] = useState("not_started"); // "not_started" | "in_progress" | "completed"
  const [showReflection, setShowReflection] = useState(false);

  const reflectionWorthy = isReflectionWorthy(step);

  function handleStart() {
    setStatus("in_progress");
  }

  function handleComplete() {
    setStatus("completed");
    if (reflectionWorthy) {
      setShowReflection(true);
    }
  }

  function handleOpenReflection() {
    if (reflectionWorthy) {
      setShowReflection(true);
    }
  }

  function handleCloseReflection() {
    setShowReflection(false);
  }

  // Button visibility logic
  const showStartButton = status === "not_started";
  const showCompleteButton = status === "in_progress";
  const showReflectButton = status === "completed" && reflectionWorthy;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 relative">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg">
          {step.position}. {step.title}
        </h2>
        <span className="text-xs px-2 py-1 rounded bg-slate-700">
          {step.difficulty}
        </span>
      </div>

      <p className="text-sm text-slate-300 mt-1">
        {step.description}
      </p>

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

      {/* Action buttons depending on status */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {showStartButton && (
          <button
            type="button"
            onClick={handleStart}
            className="text-xs px-3 py-1.5 rounded-md border border-blue-500/70 text-blue-100 bg-blue-500/10 hover:bg-blue-500/20 transition-colors"
          >
            Start
          </button>
        )}

        {showCompleteButton && (
          <button
            type="button"
            onClick={handleComplete}
            className="text-xs px-3 py-1.5 rounded-md border border-emerald-500/70 text-emerald-100 bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors"
          >
            Complete
          </button>
        )}

        {showReflectButton && (
          <button
            type="button"
            onClick={handleOpenReflection}
            className="text-xs px-3 py-1.5 rounded-md border border-amber-500/70 text-amber-100 bg-amber-500/10 hover:bg-amber-500/20 transition-colors"
          >
            Reflect
          </button>
        )}

        <span className="ml-auto text-[10px] text-slate-500">
          status: {status}
        </span>
      </div>

      {/* Reflection modal (UI-only for now, AI later) */}
      {showReflection && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 shadow-2xl">
            <h3 className="text-sm font-semibold text-slate-100 mb-2">
              Quick reflection on this step
            </h3>
            <p className="text-xs text-slate-300 mb-3">
              {/* For now this is a static prompt; later we’ll fetch it from the AI. */}
              Thinking about: <span className="font-medium">{step.title}</span>
            </p>
            <p className="text-xs text-slate-300 mb-4">
              What felt most challenging or surprising about doing this step?
              What would you do differently next time?
            </p>

            <textarea
              className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3 min-h-[80px]"
              placeholder="Type your reflection here (optional for now)..."
            />

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={handleCloseReflection}
                className="text-xs px-3 py-1.5 rounded-md border border-slate-600 text-slate-200 hover:bg-slate-800"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleCloseReflection}
                className="text-xs px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white rounded-md"
              >
                Save (placeholder)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
