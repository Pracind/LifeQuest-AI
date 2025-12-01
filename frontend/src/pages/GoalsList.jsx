import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getGoals, deleteGoal } from "../api";

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function StatusBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide border bg-emerald-500/10 text-emerald-300 border-emerald-500/40">
      Active
    </span>
  );
}

export default function GoalsListPage() {
  const navigate = useNavigate();
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadGoals() {
      setLoading(true);
      setError("");

      try {
        const data = await getGoals();
        if (isMounted) {
           setGoals((data || []).filter(g => !g.completed_at));
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadGoals();
    return () => {
      isMounted = false;
    };
  }, []);

  function handleBack() {
    navigate("/dashboard");
  }

  function handleCreate() {
    navigate("/goals/new");
  }

  function handleOpen(goalId) {
  navigate(`/goals/${goalId}`);
  }

  async function handleDelete(goalId) {
    const ok = window.confirm(
      "Delete this quest and all its progress? This cannot be undone."
    );
    if (!ok) return;

    setMenuOpenId(null);
    setDeletingId(goalId);

    setGoals((prev) => {
      window.__lastGoalsBackup = prev;
      return prev.filter((g) => g.id !== goalId);
    });

    try {
      await deleteGoal(goalId);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
    } catch (err) {
      console.error("Failed to delete goal", err);
      alert("Something went wrong while deleting the quest.");
    
    setGoals(window.__lastGoalsBackup || []);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="w-full max-w-3xl px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Your quests</h1>
            <p className="text-sm text-slate-400">
              All goals you&apos;ve created in LifeQuest.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleBack}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              Back to dashboard
            </button>
            <button
              onClick={handleCreate}
              className="inline-flex items-center rounded-md bg-blue-600 hover:bg-blue-500 px-3 py-1.5 text-xs font-medium text-white transition-colors"
            >
              + New goal
            </button>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl">
          {loading && (
            <p className="text-sm text-slate-400">Loading goals...</p>
          )}

          {error && (
            <div className="mb-4 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          {!loading && !error && goals.length === 0 && (
            <p className="text-sm text-slate-400">
              You don&apos;t have any goals yet. Create one to get started!
            </p>
          )}

          {!loading && !error && goals.length > 0 && (
            <ul className="space-y-3">
              {goals.map((goal) => (
                <li
                  key={goal.id}
                  onClick={() => handleOpen(goal.id)}
                  className="relative rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3 flex flex-col gap-1 cursor-pointer hover:border-blue-500/60 hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-sm font-semibold">{goal.title}</h2>
                        <StatusBadge isConfirmed={goal.is_confirmed} />
                      </div>
                      {goal.description && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          {goal.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="text-right text-[11px] text-slate-500">
                        <div>Created</div>
                        <div>{formatDate(goal.created_at)}</div>
                      </div>

                      {/* 3-dots menu button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuOpenId((prev) => (prev === goal.id ? null : goal.id));
                        }}
                        className="text-slate-400 hover:text-slate-100 px-1"
                      >
                        ⋮
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-1">
                    <div className="text-[11px] text-slate-500 uppercase tracking-wide">
                      {/* placeholder XP until XP system is wired */}
                      XP: 0
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // don't trigger card click twice
                        handleOpen(goal.id);
                      }}
                      className="text-[11px] text-blue-300 hover:text-blue-200"
                    >
                      View details →
                    </button>
                  </div>

                  {menuOpenId === goal.id && (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="absolute right-3 top-10 z-10 w-40 rounded-md bg-slate-900 border border-slate-700 shadow-lg text-xs"
                    >
                      <button
                        disabled={deletingId === goal.id}
                        onClick={() => {
                          if (deletingId === goal.id) return;
                          handleDelete(goal.id);
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-red-500/10 text-red-300 disabled:opacity-60"
                      >
                        {deletingId === goal.id ? "Deleting..." : "Delete quest"}
                      </button>
                    </div>
                  )}                        
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
