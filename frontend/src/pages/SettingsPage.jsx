// src/pages/SettingsPage.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SettingsPage() {
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

  // load current profile
  useEffect(() => {
    async function loadMe() {
      try {
        const res = await fetch("http://localhost:8000/me", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        if (!res.ok) throw new Error("Failed to load profile");
        const data = await res.json();
        setDisplayName(data.display_name || "");
        setAvatarUrl(data.avatar_url || "");
      } catch (err) {
        console.error(err);
        setError(err.message || "Failed to load profile");
      }
    }
    loadMe();
  }, []);

  async function handleSaveProfile(e) {
    e.preventDefault();
    setProfileSaving(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({
          display_name: displayName || null,
          avatar_url: avatarUrl || null,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.detail || "Failed to update profile");
      }

      // ✅ update sidebar immediately
      window.dispatchEvent(
        new CustomEvent("profile-updated", { detail: data })
      );
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  }

 async function handleChangePassword(e) {
  e.preventDefault();
  setError("");

  if (!newPassword || !confirmPassword) {
    setError("Please enter and confirm your new password.");
    return;
  }

  if (newPassword !== confirmPassword) {
    setError("New password and confirmation do not match.");
    return;
  }

  setPasswordSaving(true);

  try {
    const res = await fetch("http://localhost:8000/change-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
      body: JSON.stringify({
        // no current_password any more
        new_password: newPassword,
      }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Failed to update password");
    }

    // clear form
    setNewPassword("");
    setConfirmPassword("");
  } catch (err) {
    console.error(err);
    setError(err.message || "Failed to update password");
  } finally {
    setPasswordSaving(false);
  }
}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Settings</h1>
        <button
          onClick={() => navigate("/dashboard")}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          ← Back to dashboard
        </button>
      </div>

      {error && (
        <div className="rounded-md border border-red-500/60 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Profile card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 space-y-4">
        <h2 className="text-sm font-semibold mb-2">Profile</h2>

        <form onSubmit={handleSaveProfile} className="space-y-3">
          <div className="flex items-center gap-3">
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt="avatar"
                className="h-12 w-12 rounded-full object-cover"
              />
            ) : (
              <div className="h-12 w-12 rounded-full bg-slate-800 flex items-center justify-center text-xl text-slate-400">
                ?
              </div>
            )}
            <p className="text-xs text-slate-400">
              Paste a public image URL for your avatar, or leave it blank to
              use your initial.
            </p>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-slate-300">Display name</label>
            <input
              type="text"
              className="w-full rounded-md bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
              placeholder="How should LifeQuest refer to you?"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs text-slate-300">Avatar URL</label>
            <input
              type="url"
              className="w-full rounded-md bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
              placeholder="https://example.com/your-photo.png"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={profileSaving}
            className="inline-flex items-center rounded-md bg-blue-600 hover:bg-blue-500 px-4 py-1.5 text-xs font-medium text-white disabled:opacity-60"
          >
            {profileSaving ? "Saving..." : "Save profile"}
          </button>
        </form>
      </div>

      {/* Change password card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 space-y-4" autoComplete="off">
        <h2 className="text-sm font-semibold mb-2">Change password</h2>

        <form onSubmit={handleChangePassword} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-slate-300">New password</label>
              <input
                type="password"
                autoComplete="new-password"
                className="w-full rounded-md bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-300">
                Confirm new password
              </label>
              <input
                type="password"
                autoComplete="new-password"
                className="w-full rounded-md bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={passwordSaving}
            className="inline-flex items-center rounded-md bg-emerald-600 hover:bg-emerald-500 px-4 py-1.5 text-xs font-medium text-white disabled:opacity-60"
          >
            {passwordSaving ? "Updating..." : "Update password"}
          </button>
        </form>
      </div>
    </div>
  );
}
