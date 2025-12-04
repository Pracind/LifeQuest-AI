# LifeQuest AI

LifeQuest AI is a gamified self-improvement app that transforms big goals into achievable “quests.” Instead of overwhelming to-do lists, you get a structured, game-like progression system that keeps you motivated, consistent, and focused.

Powered by Groq AI, LifeQuest breaks down your long-term goals into small, meaningful steps — each with XP rewards, difficulty levels, and optional reflections that help reinforce your learning.

---

## 🌟 What LifeQuest AI Does

LifeQuest AI helps you:

- Turn any long-term goal into a sequence of manageable quests  
- Track your progress with XP, levels, and daily activity charts  
- Reflect as you complete steps to build habits and internalize learning  
- Stay motivated through game mechanics instead of stress or overwhelm  

It’s not just another productivity app.  
It’s a **personal progress RPG** where *you* are the main character, leveling up in real life.

---

## 🚀 How It Works (User Experience)

### 1. Sign up & Log in
Users create an account and enter the app through JWT-authenticated sessions.

### 2. App Layout
Once logged in, a sidebar displays:

- Profile picture & display name  
- Settings shortcut  
- Level & XP progress bar  
- Navigation: Dashboard, New Goal, Goals, Completed Goals  

### 3. Dashboard
Your home base includes:

- XP earned each day (last 7 days)  
- Current level + progress to next level  
- Total XP accumulated  
- Number of active quests  
- Number of completed quests  
- The next actionable step from your ongoing quests  

### 4. Creating a New Goal
On the **New Goal** page you can:

- Enter a goal title  
- Add optional description/context  
- Generate a step-by-step roadmap using Groq AI  
- Regenerate steps until you're satisfied  
- Accept the quest and make it an active goal  

### 5. Working on a Goal
Each goal page shows:

- All generated steps with difficulty & estimated duration  
- Ability to **start** or **complete** a step  
- AI-generated reflection prompts for certain tasks  
- XP rewards for completions and reflections  
- A progress bar and a timeline documenting each completed step  

Active goals appear in the **Goals** page.

### 6. Completed Goals
After finishing a goal:

- Groq AI generates a **personalized summary** based on your actions and reflections  
- The summary acts as a motivational recap  
- Completed goals appear under **Completed Goals**  

### 7. Settings
Users can:

- Change their display name  
- Update profile picture (using an image URL)  
- Change password  

---

## 🧠 AI (Groq) Integration

Groq powers:

- Step-by-step goal breakdowns  
- Difficulty & XP assignments  
- Reflection prompts  
- Completed goal summaries  

The app combines structured logic (XP, leveling, charts) with AI-generated content to keep everything dynamic yet grounded.

---

## ⚙️ Technical Overview

### Frontend
- **React / Vite**
- **React Router** for routing  
- **TailwindCSS** for styling  

### Backend  
- **FastAPI**

### AI
- Groq API is used to generate:
  - Step sequences  
  - Reflective prompts  
  - Completed goal summaries  

---

## 🏆 Features

- ✔ AI-generated goal breakdowns  
- ✔ XP + leveling system  
- ✔ Daily XP activity chart  
- ✔ Timeline-based progress history  
- ✔ Reflections with XP boosts  
- ✔ Real-time XP updates  
- ✔ Completed goal summaries  
- ✔ Full user profile settings  
- ✔ Responsive design  

---