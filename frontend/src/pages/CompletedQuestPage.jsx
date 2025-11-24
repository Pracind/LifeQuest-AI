import { useEffect, useState } from "react";
import { getCompletedGoals } from "../api";
import { useNavigate } from "react-router-dom";


function formatCompletedAt(value) {
  if (!value) return "Unknown date";

  const d = new Date(value);

  if (Number.isNaN(d.getTime())) {
    return "Unknown date";
  }

  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}


export default function CompletedGoalsPage() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        const data = await getCompletedGoals();
        setGoals(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Completed Quests</h1>

      {goals.length === 0 && (
        <p className="text-sm text-slate-500">No completed quests yet.</p>
      )}

      {goals.map((g) => (
        <div
          key={g.id}
          onClick={() => navigate(`/goals/${g.id}`)}   
          className="p-4 rounded-md border border-slate-700 cursor-pointer hover:bg-slate-900/80 transition-colors"
        >
          <div className="font-semibold">{g.title}</div>
          <div className="text-xs text-slate-400">
            Completed: {formatCompletedAt(g.completed_at)}
          </div>
        </div>
      ))}
    </div>
  );
}
