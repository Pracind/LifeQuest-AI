export default function DashboardPage() {
  const token = localStorage.getItem("access_token");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
      <div className="max-w-xl w-full px-4">
        <h1 className="text-3xl font-bold mb-2">LifeQuest Dashboard</h1>
        <p className="text-slate-400 mb-4">
          This is just a placeholder. Soon this will show your goals, XP and quests.
        </p>
        <p className="text-xs text-slate-500 break-all">
          Current token (localStorage): {token ? token : "No token found"}
        </p>
      </div>
    </div>
  );
}
