import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createGoal,
  generateGoalPlan,
  confirmGoalPlan,
  regenerateGoalPlan,
} from "../api";

export default function CreateGoalPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "",
    description: "",
  });
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [error, setError] = useState("");
  const [goalId, setGoalId] = useState(null);
  const [acceptLoading, setAcceptLoading] = useState(false);
  const [regenLoading, setRegenLoading] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setSteps([]);
    setGoalId(null);

    try{
      // 1) Create the goal
      const goal = await createGoal({
        title: form.title,
        description: form.description,
      });

      setGoalId(goal.id);

      // 2) Call /generate for that goal (fills ai_plan, not DB steps)
      const generated = await generateGoalPlan(goal.id);

      // Show generated plan (not yet confirmed)
      setSteps(generated.steps || []);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleGoDashboard() {
    navigate("/dashboard");
  }
  
  async function handleAcceptQuest() {
    if (!goalId) return;
    setError("");
    setAcceptLoading(true);

    try {
      const confirmed = await confirmGoalPlan(goalId);
      // Use confirmed DB steps (now real quest)
      setSteps(confirmed.steps || []);
      // Optionally navigate to detail page to "start playing"
      navigate(`/goals/${goalId}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setAcceptLoading(false);
    }
  }

  async function handleRegenerateQuest() {
    if (!goalId) return;
    setError("");
    setRegenLoading(true);

    try {
      const regenerated = await regenerateGoalPlan(goalId);
      setSteps(regenerated.steps || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setRegenLoading(false);
    }
  }
  

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="max-w-2xl w-full px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">
            Create a new quest 🎯
          </h1>
          <button
            onClick={handleGoDashboard}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Back to dashboard
          </button>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
          {error && (
            <div className="mb-4 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-sm text-slate-200" htmlFor="title">
                Goal title
              </label>
              <input
                id="title"
                name="title"
                type="text"
                className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.title}
                onChange={handleChange}
                required
                placeholder="e.g. Finish 30-day coding challenge"
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm text-slate-200" htmlFor="description">
                Description (optional)
              </label>
              <textarea
                id="description"
                name="description"
                className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
                value={form.description}
                onChange={handleChange}
                placeholder="Add more context so the AI can generate better steps..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2 text-sm font-medium text-white transition-colors"
            >
              {loading ? "Creating & generating..." : "Create goal and generate steps"}
            </button>
          </form>

            {steps.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-slate-200">
                  Generated linear steps
                </h2>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleRegenerateQuest}
                    disabled={regenLoading || loading || !goalId}
                    className="rounded-md border border-slate-600 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 disabled:cursor-not-allowed px-3 py-1.5 text-xs text-slate-100"
                  >
                    {regenLoading ? "Regenerating..." : "Regenerate quest"}
                  </button>
                  <button
                    type="button"
                    onClick={handleAcceptQuest}
                    disabled={acceptLoading || !goalId}
                    className="rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed px-3 py-1.5 text-xs font-medium text-white"
                  >
                    {acceptLoading ? "Accepting..." : "Accept quest & start"}
                  </button>
                </div>
              </div>

              <ol className="space-y-2 text-sm">
                {steps.map((step) => (
                  <li
                    key={step.position}
                    className="flex flex-col gap-3 rounded-md bg-slate-800/80 border border-slate-700 px-3 py-2"
                  >
                    <div className="flex gap-3">
                      <span className="mt-1 text-xs text-slate-400">
                        #{step.position}
                      </span>
                      <div>
                        <div className="font-medium">
                          {step.title}
                        </div>
                        {step.description && (
                          <div className="text-xs text-slate-400 mt-1">
                            {step.description}
                          </div>
                        )}
                        <div className="mt-1 text-[10px] text-slate-500 uppercase">
                          {step.difficulty} ·{" "}
                          {step.est_time_minutes
                            ? `${step.est_time_minutes} min`
                            : "No estimate"}
                        </div>
                      </div>
                    </div>

                    {step.substeps && step.substeps.length > 0 && (
                      <ol className="ml-8 list-decimal text-xs text-slate-300 space-y-1">
                        {step.substeps.map((substep, i) => (
                          <li key={i} className="pl-1">
                            {substep}
                          </li>
                        ))}
                      </ol>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
