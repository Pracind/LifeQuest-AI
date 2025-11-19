import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StepCard from "../components/StepCard";

export default function GoalDetailPage() {
  const { id } = useParams();
  const [goal, setGoal] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchGoal() {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`http://localhost:8000/goals/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();
      setGoal(data);
      setLoading(false);
    }

    fetchGoal();
  }, [id]);

  if (loading) return <div>Loading goal...</div>;
  if (!goal) return <div>Goal not found</div>;

  const completedCount = 0;
  const totalSteps = Array.isArray(goal.steps) ? goal.steps.length : 0;
  const progress = totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{goal.title}</h1>
      </div>

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

      <div className="space-y-4">
        {Array.isArray(goal.steps) && goal.steps.length > 0 ? (
          goal.steps.map((step) => (
            <StepCard key={step.id} step={step} />
          ))
        ) : (
          <p className="text-sm text-slate-500">No steps yet</p>
        )}
      </div>
    </div>
  );
}
