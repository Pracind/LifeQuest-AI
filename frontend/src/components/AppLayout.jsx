import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getUserProgress } from "../api";

function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const email = localStorage.getItem("user_email") || "adventurer@lifequest.ai";

  const initials = email[0]?.toUpperCase() || "L";

  const navItems = [
    { label: "Dashboard", to: "/dashboard" },
    { label: "Goals", to: "/goals" },
    { label: "New Goal", to: "/goals/new" },
  ];

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_email");
    navigate("/login");
  }

    const [progress, setProgress] = useState({
    total_xp: 0,
    level: 1,
    current_level_xp: 0,
    next_level_xp: 100,
  });
  const [loadingProgress, setLoadingProgress] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchProgress() {
      try {
        const data = await getUserProgress();
        if (!cancelled) {
          setProgress(data);
        }
      } catch (err) {
        console.error("Failed to load user progress", err);
      } finally {
        if (!cancelled) {
          setLoadingProgress(false);
        }
      }
    }

    fetchProgress();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/90 flex flex-col">
        <div className="px-5 pt-5 pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-xl bg-blue-500 flex items-center justify-center text-sm font-bold">
              LQ
            </div>
            <div>
              <div className="text-sm font-semibold">LifeQuest AI</div>
              <div className="text-[11px] text-slate-400">
                Turn goals into quests
              </div>
            </div>
          </div>
        </div>

        <div className="px-5 py-4 border-b border-slate-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-sm font-bold">
              {initials}
            </div>
            <div className="flex-1">
              <div className="text-xs text-slate-400">Logged in as</div>
              <div className="text-sm font-medium truncate">{email}</div>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-2 text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-slate-400">Level</span>
              <span className="font-semibold text-slate-50">
                {progress.level}
              </span>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-slate-400">
                XP
                {loadingProgress && (
                  <span className="ml-1 text-[10px] text-slate-500">
                    (loading…)
                  </span>
                )}
              </span>
              <span className="font-semibold text-slate-50">
                {progress.current_level_xp} / {progress.next_level_xp}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    (progress.current_level_xp / progress.next_level_xp) * 100 || 0
                  )}%`,
                }}
              />
            </div>
          </div>

        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                classNames(
                  "flex items-center gap-2 rounded-md px-3 py-2 transition-colors",
                  isActive
                    ? "bg-blue-600/80 text-white"
                    : "text-slate-200 hover:bg-slate-800"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="w-full text-xs rounded-md border border-slate-700 bg-slate-900/80 hover:bg-slate-800 px-3 py-2 text-slate-200 transition-colors"
          >
            Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-h-screen overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-6">{children}</div>
      </main>
    </div>
  );
}
