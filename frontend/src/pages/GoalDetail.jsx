// src/pages/GoalDetailPage.jsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StepCard from "../components/StepCard";
import { getGoal } from "../api";

export default function GoalDetailPage() {
  const { id } = useParams();
  const [goal, setGoal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
      console.log("Loaded goal detail:", data); // 👈 see exactly what backend sends
      setGoal(data);
    } catch (err) {
      console.error("Failed to load goal", err);
      setError(err.message || "Failed to load goal");
      setGoal(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadGoal();
  }, [id]);

  if (loading) return <div>Loading goal...</div>;
  if (error) return <div className="text-red-300 text-sm">{error}</div>;
  if (!goal) return <div>Goal not found</div>;

  // --- Progress calculation ---
  const steps = Array.isArray(goal.steps) ? goal.steps : [];

  const completedCount = steps.filter((s) => {
    if (typeof s.is_completed === "boolean") return s.is_completed;
    if (typeof s.completed === "boolean") return s.completed;
    if (typeof s.status === "string") return s.status === "completed";
    return false;
  }).length;

  const totalSteps = steps.length;
  const progress =
    totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{goal.title}</h1>
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

      {/* Steps */}
      <div className="space-y-4">
        {steps.length > 0 ? (
          steps.map((step) => (
            <StepCard
              key={step.id}
              step={step}
              goalId={goal.id}
              onStepUpdated={(patch) =>
                handleStepLocallyUpdated(step.id, patch)
              }
            />
          ))
        ) : (
          <p className="text-sm text-slate-500">No steps yet</p>
        )}
      </div>
    </div>
  );
}
