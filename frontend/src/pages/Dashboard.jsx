import { useNavigate } from "react-router-dom";

export default function DashboardPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  function handleCreateGoal() {
    navigate("/goals/new");
  }

  function handleViewGoals() {
    navigate("/goals");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="max-w-xl w-full px-4">
        <h1 className="text-3xl font-bold mb-2">LifeQuest Dashboard</h1>
        <p className="text-slate-400 mb-4">
          This will soon show your active goals, XP and quest progress.
        </p>

        <div className="flex gap-2 mb-4">
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

        <p className="text-xs text-slate-500 break-all">
          Current token (localStorage): {token ? token : "No token found"}
        </p>
      </div>
    </div>
  );
}
