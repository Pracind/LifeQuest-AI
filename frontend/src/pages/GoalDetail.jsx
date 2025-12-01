// src/pages/GoalDetailPage.jsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import StepCard from "../components/StepCard";
import { getGoal, deleteGoal, finishGoal } from "../api";

function isStepCompleted(step) {
  if (!step) return false;
  if (typeof step.is_completed === "boolean") return step.is_completed;
  if (typeof step.completed === "boolean") return step.completed;
  if (typeof step.status === "string") return step.status === "completed";
  return false;
}

export default function GoalDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [goal, setGoal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  function handleStepLocallyUpdated(stepId, patch) {
    setGoal((prev) => {
      if (!prev) return prev;

      const updatedSteps = (prev.steps || []).map((s) =>
        s.id === stepId ? { ...s, ...patch } : s
      );

      return {
        ...prev,
        steps: updatedSteps,
      };
    });
  }

  async function loadGoal() {
    setLoading(true);
    setError("");

    try {
      const data = await getGoal(id);
      console.log("Loaded goal detail:", data);
      setGoal(data);
    } catch (err) {
      console.error("Failed to load goal", err);
      setError(err.message || "Failed to load goal");
      setGoal(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteGoal() {
    if (!goal || deleting) return;

    const ok = window.confirm(
      "Are you sure you want to delete this quest? This cannot be undone."
    );
    if (!ok) return;

    setDeleting(true);
    navigate("/dashboard");

    try {
      await deleteGoal(goal.id);
    } catch (err) {
      console.error("Failed to delete goal", err);
      alert("Something went wrong while deleting the quest.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleFinishGoal() {
    try {
      const res = await finishGoal(goal.id);
      alert(`Quest completed! Bonus XP earned: ${res.bonus_xp}`);
      navigate("/goals/completed");
    } catch (err) {
      console.error("Failed to finish quest", err);
      alert(err.message || "Could not finish quest");
    }
  }

  useEffect(() => {
    loadGoal();
  }, [id]);

  if (loading) return <div>Loading goal...</div>;
  if (error) return <div className="text-red-300 text-sm">{error}</div>;
  if (!goal) return <div>Goal not found</div>;

  const steps = Array.isArray(goal.steps) ? goal.steps : [];

  const completedCount = steps.filter(isStepCompleted).length;
  const totalSteps = steps.length;
  const progress =
    totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

  const timelineItems = steps
    .filter((s) => s.completed_at)
    .slice()
    .sort(
      (a, b) =>
        new Date(a.completed_at).getTime() - new Date(b.completed_at).getTime()
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{goal.title}</h1>
        <button
          onClick={handleDeleteGoal}
          disabled={deleting}
          className="text-xs px-3 py-1.5 rounded-md border border-red-500/60 text-red-300 hover:bg-red-500/10 disabled:opacity-60"
        >
          {deleting ? "Deleting..." : "Delete quest"}
        </button>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Completion summary – only for finished quests */}
      {goal.completed_at && goal.completion_summary && (
        <div className="mt-4 bg-slate-900/70 border border-emerald-500/50 rounded-xl p-4">
          <div className="text-sm font-semibold text-emerald-300 mb-1">
            Well done! 🎉
          </div>
          <p className="text-sm text-slate-100 whitespace-pre-line">
            {goal.completion_summary}
          </p>
        </div>
      )}

      {/* Timeline – only show for completed steps */}
      {timelineItems.length > 0 && (
        <div className="mt-4">
          <h2 className="text-sm font-semibold mb-2 text-slate-200">
            Quest timeline
          </h2>
          <ol className="relative border-l border-slate-700 ml-2">
            {timelineItems.map((step) => (
              <li key={step.id} className="mb-4 ml-4">
                <div className="absolute -left-[7px] mt-1 h-3 w-3 rounded-full bg-blue-500" />
                <div className="text-[11px] text-slate-400">
                  {new Date(step.completed_at).toLocaleString()}
                </div>
                <div className="text-sm text-slate-50 font-medium">
                  {step.position}. {step.title}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-4">
        {steps.length > 0 ? (
          steps.map((step, index) => {
            const prevCompleted =
              index === 0
                ? true
                : steps.slice(0, index).every((s) => isStepCompleted(s));

            return (
              <StepCard
                key={step.id}
                step={step}
                goalId={goal.id}
                canStart={prevCompleted}
                onStepUpdated={(patch) =>
                  handleStepLocallyUpdated(step.id, patch)
                }
              />
            );
          })
        ) : (
          <p className="text-sm text-slate-500">No steps yet</p>
        )}
      </div>

      {/* Finish quest button at the bottom */}
      {progress === 100 && !goal.completed_at && (
        <div className="pt-2">
          <button
            onClick={handleFinishGoal}
            className="text-xs px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500"
          >
            Finish Quest 🎉
          </button>
        </div>
      )}
    </div>
  );
}
