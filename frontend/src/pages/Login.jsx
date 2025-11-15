import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await login({
        email: form.email,
        password: form.password,
      });

      // Save token in localStorage
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("token_type", data.token_type || "bearer");
      localStorage.setItem("user_email", form.email);

      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-xl">
        <h1 className="text-2xl font-semibold text-slate-50 mb-2">
          Welcome back to LifeQuest
        </h1>
        <p className="text-sm text-slate-400 mb-6">
          Log in to continue your quests and earn more XP.
        </p>

        {error && (
          <div className="mb-4 rounded-md bg-red-500/10 border border-red-500/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm text-slate-200" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-slate-200" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              className="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed px-3 py-2 text-sm font-medium text-white transition-colors"
          >
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="mt-4 text-xs text-slate-400 text-center">
          Don&apos;t have an account yet?{" "}
          <Link
            to="/signup"
            className="text-blue-400 hover:text-blue-300 font-medium"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
