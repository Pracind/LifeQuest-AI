import { Routes, Route, Navigate } from "react-router-dom";
import SignupPage from "./pages/Signup";
import LoginPage from "./pages/Login";
import DashboardPage from "./pages/Dashboard";
import CreateGoalPage from "./pages/CreateGoal";
import GoalsListPage from "./pages/GoalsList";
import AppLayout from "./components/AppLayout";
import GoalDetailPage from "./pages/GoalDetail";
import CompletedQuestsPage from "./pages/CompletedQuestPage";

function RequireAuth({ children }) {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
    <Route path="/" element={<Navigate to="/login" replace />} />
    <Route path="/signup" element={<SignupPage />} />
    <Route path="/login" element={<LoginPage />} />
    
    <Route
      path="/dashboard"
      element={
        <RequireAuth>
          <AppLayout>
            <DashboardPage />
          </AppLayout>
        </RequireAuth>
      }
    />


    <Route
      path="/goals/new"
      element={
        <RequireAuth>
          <AppLayout>
            <CreateGoalPage />
          </AppLayout>
        </RequireAuth>
      }
    />


    <Route
      path="/goals"
      element={
        <RequireAuth>
          <AppLayout>
            <GoalsListPage />
          </AppLayout>
        </RequireAuth>
      }
    />

    <Route
      path="/goals/completed"
      element={
        <AppLayout>
          <CompletedQuestsPage />
        </AppLayout>
      }
    />


    <Route
      path="/goals/:id"
      element={
        <RequireAuth>
          <AppLayout>
            <GoalDetailPage />
          </AppLayout>
        </RequireAuth>
      }
    />

    <Route path="*" element={<Navigate to="/login" replace />} />
  </Routes>
  );
}
