import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { getXpSummary } from "../api";

function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState({
    email: "",
    display_name: "",
    avatar_url: "",
  });

  async function loadUser() {
    try {
      const res = await fetch("http://localhost:8000/me", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      const data = await res.json();
      setUser(data);
      localStorage.setItem("user_email", data.email);
      localStorage.setItem("user_name", data.display_name || "");
      localStorage.setItem("avatar_url", data.avatar_url || "");
    } catch (err) {
      console.error("Failed to load user info", err);
    }
  }

  useEffect(() => {
    loadUser();
  }, []);

  // 🔔 listen for profile updates from SettingsPage
  useEffect(() => {
    function handleProfileUpdated(e) {
      if (e.detail) {
        setUser(e.detail);
      } else {
        // fallback: re-fetch from backend
        loadUser();
      }
    }
    window.addEventListener("profile-updated", handleProfileUpdated);
    return () =>
      window.removeEventListener("profile-updated", handleProfileUpdated);
  }, []);

  const initials = user.display_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || "L";

  const [xpState, setXpState] = useState({
    loading: true,
    level: 1,
    current_level_xp: 0,
    next_level_xp: 100,
    progress_to_next: 0,
  });

  async function loadXp() {
    try {
      const data = await getXpSummary();

      setXpState({
        loading: false,
        level: data.level,
        current_level_xp: data.current_level_xp,
        next_level_xp: data.next_level_xp,
        progress_to_next: data.progress_to_next,
      });
    } catch (err) {
      console.error("Failed to load XP summary:", err);
      // Stop loading but keep whatever we had
      setXpState((prev) => ({ ...prev, loading: false }));
    }
  }

  useEffect(() => {
    loadXp();
  }, []);

  // listen for "xp-updated" from StepCard and refresh XP
  useEffect(() => {
  // sequence token to ignore stale fetch results
  let seq = 0;
  let mounted = true;

  async function refreshXp() {
    const mySeq = ++seq;
    try {
      const data = await getXpSummary();
      // ignore if a newer refresh started or component unmounted
      if (!mounted || mySeq !== seq) return;

      setXpState({
        loading: false,
        level: data.level,
        current_level_xp: data.current_level_xp,
        next_level_xp: data.next_level_xp,
        progress_to_next: data.progress_to_next,
      });
      console.debug("AppLayout: refreshed XP from server", data);
    } catch (err) {
      console.error("AppLayout: failed to refresh XP", err);
      if (mounted) setXpState((prev) => ({ ...prev, loading: false }));
    }
  }

  function handleXpUpdatedEvent(e) {
    console.debug("AppLayout heard xp-updated event", e);
    // always refresh from server when step card signals xp changed
    refreshXp();
  }

  // catch events on both window and document to be extra robust
  window.addEventListener("xp-updated", handleXpUpdatedEvent);
  document.addEventListener("xp-updated", handleXpUpdatedEvent);

  // also refresh when tab becomes visible (useful for multi-tab)
  function handleVisibility() {
    if (document.visibilityState === "visible") {
      refreshXp();
    }
  }
  document.addEventListener("visibilitychange", handleVisibility);

  return () => {
    mounted = false;
    // increment seq so any in-flight promise is ignored
    seq++;
    window.removeEventListener("xp-updated", handleXpUpdatedEvent);
    document.removeEventListener("xp-updated", handleXpUpdatedEvent);
    document.removeEventListener("visibilitychange", handleVisibility);
  };
}, []);

  

  const navItems = [
    { label: "Dashboard", to: "/dashboard", end: true  },
    { label: "New Goal", to: "/goals/new", end: true  },
    { label: "Goals", to: "/goals", end: true  },
    { label: "Completed quests", to: "/goals/completed", end: true  },
  ];

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_email");
    navigate("/login");
  }

  const levelLabel = xpState.loading ? "..." : xpState.level;
  const xpLabel = xpState.loading
    ? "..."
    : `${xpState.current_level_xp} / ${xpState.next_level_xp}`;
  const xpPercent = xpState.loading
    ? 0
    : Math.round((xpState.progress_to_next || 0) * 100);

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
          <div
            className="flex items-center gap-3 mb-3 cursor-pointer hover:opacity-90"
            onClick={() => navigate("/settings")}
          >
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt="avatar"
                className="h-10 w-10 rounded-full object-cover"
              />
            ) : (
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-sm font-bold">
                {initials}
              </div>
            )}

            <div className="flex-1">
              <div className="text-xs text-slate-400">Logged in as</div>
              <div className="text-sm font-medium truncate">{user.display_name || user.email}</div>
              <div className="text-[10px] text-blue-300 mt-0.5">
                Open settings →
              </div>
            </div>
          </div>

          {/* XP / Level card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-2 text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-slate-400">Level</span>
              <span className="font-semibold text-slate-50">{levelLabel}</span>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-slate-400">XP</span>
              <span className="font-semibold text-slate-50">{xpLabel}</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${xpPercent}%` }}
              />
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
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
