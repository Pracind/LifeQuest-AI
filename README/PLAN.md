# Project Milestones – LifeQuest AI 🎮  
*AI-powered life gamification app — turning personal goals into linear quests with XP, reflections, and progress tracking.*

---

## 🗓️ Day 0: Prep (Project Skeleton)
- [.] Create project folder structure (`backend/`, `frontend/`, `docs/`)
- [.] Add `.gitignore`, `LICENSE (MIT)`, and `README.md` with summary & tech stack
- [.] Create `README/PLAN.md` with milestones (this file)
- [.] Add `backend/requirements.txt` and `frontend/package.json`
- [.] Create GitHub repo and push initial commit

---

## 🧱 Days 1–2: Database Models & Setup
**Day 1**
- [.] Create Supabase (Postgres) project (free tier)
- [.] Define and document DB schema (`users`, `goals`, `steps`, `user_steps`, `xp_log`, `reflections`, `evidence`)
- [.] Implement backend/models.py (SQLAlchemy + Pydantic)
- [.] Create `.env.example` for DB + API keys

**Day 2**
- [.] Implement `backend/db.py` to connect to Supabase/Postgres
- [.] Create DB init/migration script (`create_db.py`)
- [.] Add demo seed data (sample user + goal)
- [.] Write unit test to validate DB connection and seed data

---

## 🔐 Days 3–5: Auth & Core API (FastAPI)
**Day 3**
- [.] Implement `POST /signup` (with password hashing)
- [.] Implement `POST /login` (returns JWT)
- [.] Add dependency for `get_current_user`

**Day 4**
- [.] Implement `POST /goals` (create new goal, returns goal_id)
- [.] Implement `GET /goals` (list all user goals)
- [.] Implement `GET /goals/{id}` (returns goal + steps)
- [.] Write auth + goal route tests

**Day 5**
- [.] Implement `POST /goals/{id}/generate` (mock AI for now)
- [.] Implement `POST /goals/{id}/confirm` (user confirms AI-generated plan)
- [.] Add logging + structured error handling

---

## 💻 Days 6–7: Frontend Core (React + Vite + Tailwind)
**Day 6**
- [ ] Scaffold React app with Vite
- [ ] Install Tailwind CSS
- [ ] Build Signup/Login UI and connect to backend auth
- [ ] Store JWT in localStorage

**Day 7**
- [ ] Implement "Create Goal" page → calls `/goals` and `/generate`
- [ ] Create "Goals List" page (show goals, statuses, XP)
- [ ] Set up global layout with sidebar (Profile / XP / Level)

---

## 🤖 Days 8–9: AI Integration (Checkpoint Generation)
**Day 8**
- [ ] Implement AI module (`backend/ai.py`) for provider abstraction (OpenAI / Hugging Face)
- [ ] Add prompt template: *Goal → Linear Steps JSON output*
- [ ] Integrate with real LLM API (use free tier/trial)
- [ ] Cache responses in DB to limit API calls

**Day 9**
- [ ] Implement `/goals/{id}/regenerate` (for alternate plans)
- [ ] Validate AI outputs (JSON schema, linear order)
- [ ] Manual test: goal creation → AI step generation → DB save

---

## 🧭 Days 10–11: Goal Progression & Reflection Flow
**Day 10**
- [ ] Build Goal Detail UI → show linear list of steps, progress bar
- [ ] Create Step Card component (title, desc, difficulty, est_time)
- [ ] Add "Start / Reflect / Quiz / Upload / Complete" placeholders

**Day 11**
- [ ] Implement `POST /goals/{id}/steps/{step_id}/reflect` (short text reflection)
- [ ] Save reflection to DB and award base XP
- [ ] Display XP/Level update in header
- [ ] Write unit test for reflection endpoint

---

## 🧩 Day 12: Micro-Quiz Flow (Knowledge Verification)
- [ ] Implement backend `/steps/{id}/quiz` → generates 2–3 MCQs (via AI)
- [ ] Store quiz + hashed correct answers in DB
- [ ] Create Quiz Modal in React, display questions, verify answers
- [ ] If quiz passed → award full XP; else partial XP + encouragement

---

## 📁 Day 13: Evidence Upload & XP System
- [ ] Configure AWS S3 bucket (free tier)
- [ ] Implement `POST /evidence/sign` for presigned upload URLs
- [ ] Implement EvidenceUploader component in React
- [ ] Upload file to S3 → save metadata to DB
- [ ] Finalize XP formula:
  - Easy = 10 XP  
  - Medium = 20 XP  
  - Hard = 40 XP  
  - Reflection bonus = +5 XP  
  - Quiz bonus = +10%  
- [ ] Implement `/api/user/progress` → returns XP, Level, Badges

---

## 🪞 Day 14: Weekly Reflection & UI Polish
- [ ] Backend: `generate_weekly_summary(user_id)` → AI compiles weekly reflection summary
- [ ] Endpoint: `/user/{id}/weekly-summary`
- [ ] Frontend: Weekly Summary tab → shows past 7 days insights
- [ ] Tailwind polish → clean layout, soft shadows, rounded corners
- [ ] Manual end-to-end test (create → complete → reflect → summary)

---

## 🚀 Day 15: Testing, Docs & Deployment
- [ ] Write `README.md` with setup instructions and feature summary
- [ ] Add GitHub Actions CI (lint + test)
- [ ] Deploy backend to Render / Railway (or AWS free tier)
- [ ] Deploy frontend to Vercel
- [ ] Smoke test live demo (signup → create → generate → complete → reflect)
- [ ] Record 3-min demo video / GIF for GitHub README
- [ ] Announce on LinkedIn with screenshot + short caption

---

## ✅ MVP Deliverables
- [ ] Public deployed version (frontend + backend)
- [ ] Working AI checkpoint generation
- [ ] Reflection + XP + Quiz + Evidence loop
- [ ] Weekly reflection summary
- [ ] GitHub repo with clean commits, CI passing, and README with demo link

---

## 🧠 Optional Future Enhancements
- [ ] Add customizable avatar and streaks UI
- [ ] Add "Achievement Badges" system
- [ ] Implement multi-goal dashboard analytics
- [ ] Migrate AI provider to AWS Bedrock (for full AWS integration)
- [ ] Add user theme customization
- [ ] Add export-to-CSV of reflections and XP logs
- [ ] Implement “Quest Master” personality for motivational chat

---

**Author:** Dev Phadke  
**Goal:** 15-day MVP – LifeQuest AI live, deployed, and demo-ready  
**Tech Stack:** FastAPI · React (Vite + Tailwind) · Supabase · OpenAI/HuggingFace · AWS S3  
**Timeline:** 15 days (aggressive MVP)
