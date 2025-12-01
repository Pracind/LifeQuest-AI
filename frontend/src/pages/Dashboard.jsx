import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getXpSummary,
  getGoals,
  getCompletedGoals,
  getXpLogs,
} from "../api";

function isStepCompleted(step) {
  if (!step) return false;
  if (typeof step.is_completed === "boolean") return step.is_completed;
  if (typeof step.completed === "boolean") return step.completed;
  if (typeof step.status === "string") return step.status === "completed";
  return false;
}

function getLast7Days() {
  const days = [];
  const today = new Date();

  for (let i = 6; i >= 0; i--) {
    const d = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() - i
    );
    const key = d.toISOString().slice(0, 10); // YYYY-MM-DD
    const label = d.toLocaleDateString(undefined, {
      weekday: "short",
    });
    days.push({ key, label });
  }

  return days;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  const [xpSummary, setXpSummary] = useState(null);
  const [activeGoals, setActiveGoals] = useState([]);
  const [completedGoals, setCompletedGoals] = useState([]);
  const [xpLogs, setXpLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  function handleCreateGoal() {
    navigate("/goals/new");
  }

  function handleViewGoals() {
    navigate("/goals");
  }

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setLoading(true);
      try {
        const [summary, active, completed, logs] = await Promise.all([
          getXpSummary(),
          getGoals(),
          getCompletedGoals(),
          getXpLogs(),
        ]);

        if (!isMounted) return;

        setXpSummary(summary);
        setActiveGoals(active || []);
        setCompletedGoals(completed || []);
        setXpLogs(logs || []);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    load();

    // react to XP updates from StepCard
    function handleXpUpdated() {
      getXpSummary().then(setXpSummary).catch(console.error);
      getXpLogs().then(setXpLogs).catch(console.error);
    }
    window.addEventListener("xp-updated", handleXpUpdated);

    return () => {
      isMounted = false;
      window.removeEventListener("xp-updated", handleXpUpdated);
    };
  }, []);

  // XP last 7 days
  const last7 = getLast7Days();

  const xpByDay = last7.map((day) => {
    const totalForDay = xpLogs
      .filter((log) => {
        const created = log.created_at || log.createdAt;
        if (!created) return false;
        const dayKey = String(created).slice(0, 10); // YYYY-MM-DD
        return dayKey === day.key;
      })
      .reduce((sum, log) => sum + (log.amount || 0), 0);

    return { ...day, xp: totalForDay };
  });

  const maxXpInWindow =
    xpByDay.reduce((max, d) => (d.xp > max ? d.xp : max), 0) || 1;

  // Upcoming: next step per active goal
  const upcomingSteps = activeGoals
    .map((goal) => {
      const steps = Array.isArray(goal.steps) ? goal.steps.slice() : [];
      if (!steps.length) return null;

      steps.sort((a, b) => (a.position || 0) - (b.position || 0));

      const next = steps.find((s) => !isStepCompleted(s));
      if (!next) return null;

      return {
        goalId: goal.id,
        goalTitle: goal.title,
        stepId: next.id,
        stepTitle: next.title,
        stepPosition: next.position,
        estTime: next.est_time_minutes,
      };
    })
    .filter(Boolean);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex justify-center">
      <div className="w-full max-w-5xl px-4 py-8 space-y-6">
        {/* Header + buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold mb-1">LifeQuest Dashboard</h1>
            <p className="text-slate-400 text-sm">
              See your XP, quests and what’s coming up next.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreateGoal}
              className="inline-flex items-center rounded-md bg-blue-600 hover:bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-colors"
            >
              + Create new goal
            </button>
            <button
              onClick={handleViewGoals}
              className="inline-flex items-center rounded-md bg-slate-800 hover:bg-slate-700 px-4 py-2 text-sm font-medium text-slate-100 transition-colors border border-slate-700"
            >
              View my goals
            </button>
          </div>
        </div>

        {loading && (
          <div className="text-sm text-slate-400">Loading dashboard...</div>
        )}

        {!loading && (
          <>
            {/* Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Level card */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="text-xs text-slate-400 mb-1">Level</div>
                <div className="text-2xl font-bold">
                  {xpSummary?.level ?? "—"}
                </div>
                {xpSummary && (
                  <div className="mt-2">
                    <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                      <span>Progress to next</span>
                      <span>
                        {Math.round(
                          (xpSummary.progress_to_next || 0) * 100
                        )}
                        %
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500"
                        style={{
                          width: `${
                            Math.round(
                              (xpSummary.progress_to_next || 0) * 100
                            ) || 0
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Total XP */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="text-xs text-slate-400 mb-1">Total XP</div>
                <div className="text-2xl font-bold">
                  {xpSummary?.total_xp ?? "—"}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Every completed step and reflection adds up.
                </div>
              </div>

              {/* Active quests */}
              <div className="rounded-xl border border-slate-800/70 bg-slate-900/70 p-3">
                <div className="text-xs text-slate-400 mb-1">
                  Active quests
                </div>
                <div className="text-2xl font-bold">
                  {activeGoals.length}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Quests currently in progress.
                </div>
              </div>

              {/* Completed quests */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="text-xs text-slate-400 mb-1">
                  Completed quests
                </div>
                <div className="text-2xl font-bold">
                  {completedGoals.length}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Finished stories you can look back on.
                </div>
              </div>
            </div>

            {/* XP chart + upcoming quests */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* XP last 7 days */}
              <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h2 className="text-sm font-semibold">
                      XP in the last 7 days
                    </h2>
                    <p className="text-[11px] text-slate-500">
                      Bars show how much XP you earned each day.
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex gap-4">
                  {xpByDay.map((day) => {
                    const value = day.xp || 0;
                    const hasXp = value > 0;

                    // 0–100% height, with a minimum of 10% for non-zero days
                    const rawPercent = (value / maxXpInWindow) * 100;
                    const barHeight = hasXp ? Math.max(rawPercent, 25) : 0;

                    return (
                      <div
                        key={day.key}
                        className="flex-1 flex flex-col items-center"
                      >
                        {/* Bar track */}
                        <div className="w-8 sm:w-10 h-32 bg-slate-800/80 rounded-xl overflow-hidden flex items-end">
                          {/* Filled part */}
                          <div
                            className={`w-full flex items-end justify-center transition-all duration-300 ${
                              hasXp ? "bg-blue-500" : "bg-slate-700/60"
                            }`}
                            style={{ height: `${barHeight}%` }}
                          >
                            {hasXp && (
                              <span className="mb-1 text-[10px] font-semibold text-slate-50">
                                {value}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Day label */}
                        <div className="mt-2 text-[11px] text-slate-400">
                          {day.label}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Upcoming quests */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                <h2 className="text-sm font-semibold mb-2">
                  Upcoming quests
                </h2>
                <p className="text-[11px] text-slate-500 mb-3">
                  The next concrete steps waiting for you.
                </p>

                {upcomingSteps.length === 0 && (
                  <div className="text-sm text-slate-500">
                    No upcoming steps. Start a new quest or continue an
                    existing one.
                  </div>
                )}

                <ul className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {upcomingSteps.map((item) => (
                    <li
                      key={item.stepId}
                      onClick={() => navigate(`/goals/${item.goalId}`)}
                      className="cursor-pointer rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 transition hover:bg-slate-800 hover:border-blue-500"
                    >
                      <div className="text-[11px] text-slate-400 font-medium">
                        {item.goalTitle}
                      </div>
                      <div className="text-sm text-slate-50 font-semibold">
                        Step {item.stepPosition}. {item.stepTitle}
                      </div>
                      {item.estTime && (
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          ~{item.estTime} min
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}

        {/* Token debug (kept from your original) */}
        <p className="text-xs text-slate-500 break-all mt-4">
          Current token (localStorage): {token ? token : "No token found"}
        </p>
      </div>
    </div>
  );
}
