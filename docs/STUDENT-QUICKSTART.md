# Student Quick Start Guide

You want to prepare for the TU Wien Raumplanung entrance exam. You have Claude Cowork (the Claude desktop app on Windows/Mac). You are not a developer. This guide gets you your own personal copy of the study dashboard that you can customise, extend, and publish.

## What You Will End Up With

| What | Description |
|------|-------------|
| Your own copy of the website | Running locally on your laptop, editable by you + Claude |
| Your own Supabase account | Cloud database storing your quiz scores across devices |
| Your own published website | Live on the internet (e.g., Netlify) so you can access it from phone/tablet |
| Full control | Add quizzes, change content, add new features — it's yours |

## Overview (7 Steps)

| Step | What you do | What Claude Cowork does | Time |
|------|-------------|------------------------|------|
| **1** | Open Claude Cowork, paste the setup prompt | Downloads the template repo to your laptop | 2 min |
| **2** | Confirm the folder location | Creates a local copy of all files | 1 min |
| **3** | Open `site/index.html` in your browser | Verifies everything works locally | 1 min |
| **4** | Create a free Supabase account (Claude walks you through) | Sets up the database table, updates the config | 10 min |
| **5** | Create a free Netlify account (Claude walks you through) | Deploys your site to a public URL | 10 min |
| **6** | Study, take quizzes, track progress | Your scores sync to Supabase | Ongoing |
| **7** | Ask Claude to customise (add questions, change theme, etc.) | Edits the files, you refresh the browser | Ongoing |

## Step 1: Download the Template

Open [Claude Cowork](https://claude.ai/code) and paste this entire prompt:

---

```
I want to create my own personal study dashboard for the TU Wien
Raumplanung entrance exam (Reihungstest, 10 July 2026).

There is a template at https://github.com/JohnGavin/urban_planning

Please:
1. Download/clone that repository to a folder on my computer
   (e.g., C:\Users\me\Documents\raumplanung or ~/Documents/raumplanung)
2. Read the CLAUDE.md file in the repo — it tells you how the project works
3. Open site/index.html in my browser so I can see it
4. Tell me what the next setup steps are (Supabase + publishing)

I am not a developer. Please explain everything simply.
Do NOT use technical jargon. Handle all technical steps for me.
```

---

Claude will download the files and open the dashboard in your browser.

## Step 2: Set Up Your Own Cloud Database (Supabase)

This stores your quiz scores so they sync across devices. Ask Claude:

```
Help me set up my own Supabase account for quiz score storage.
Follow the steps in docs/SUPABASE-GUIDE.md.
Walk me through each step — I don't have a Supabase account yet.
```

Claude will:
1. Tell you to go to https://supabase.com and create a free account
2. Guide you through creating a project
3. Tell you to run the SQL from `docs/supabase-setup.sql` in the Supabase SQL editor
4. Update `site/js/supabase-sync.js` with YOUR project URL and key (replacing the template ones)

After this, your quiz scores are stored in YOUR database, not the template's.

## Step 3: Publish Your Site Online

You want to access your dashboard from your phone or another computer. The simplest option for non-developers is **Netlify** (free, no terminal needed).

Ask Claude:

```
I want to publish my raumplanung site online so I can access it
from my phone. I don't have a Netlify account. Help me set it up.
I want the simplest possible approach — drag and drop if possible.
```

Claude will explain:
1. Go to https://app.netlify.com/signup — sign up with email (free)
2. After login, drag your `site/` folder onto the Netlify page
3. Netlify gives you a URL like `https://your-name-raumplanung.netlify.app`
4. Done — your site is live

**Alternative if you prefer GitHub Pages:** Claude can help you create a GitHub account and push the repo there, but Netlify drag-and-drop is simpler if you don't want to learn Git.

## Step 4: Study and Take Quizzes

Open your site (locally or via Netlify URL) and follow the study path on the home page.

## Step 5: Customise and Extend

Here are things you can ask Claude Cowork to do:

| What you want | What to say to Claude |
|---------------|----------------------|
| **Add quiz questions** | "Add 10 new hard questions about megatrends to site/data/questions.json" |
| **Change the theme** | "Change the accent colour to green in site/css/style.css" |
| **Add study notes** | "Create a new page site/knowledge/my-notes.html with my personal study notes about Klimawandel" |
| **Add a new quiz topic** | "Create a new quiz page for Raumtypen questions" |
| **Fix something broken** | "The quiz on this page isn't loading — please check site/js/quiz-engine.js" |
| **Translate content** | "Translate the OEREK 2030 page to English" |
| **Update after changes** | "Re-upload my site/ folder to Netlify" (or just drag-drop again) |

## Step 6: Transfer Progress Between Devices

Your Supabase database stores quiz scores for your student ID. To use the same scores on another device:

1. Open the site on the new device
2. Open browser console (F12 → Console)
3. Type: `localStorage.setItem('raumplanung_student_id', 'YOUR_ID_HERE')`
4. Refresh the page

To find your student ID: on the old device, open console and type: `localStorage.getItem('raumplanung_student_id')`

Or ask Claude: "Help me transfer my quiz progress to my phone"

## You Do NOT Need

- A GitHub account (unless you want GitHub Pages instead of Netlify)
- Programming knowledge
- Node.js, Python, R, or any other tools
- A terminal or command line
- To understand HTML, CSS, or JavaScript

Claude Cowork handles all technical steps for you.

## If Something Goes Wrong

| Problem | What to tell Claude |
|---------|---------------------|
| "I can't open the site" | "site/index.html isn't working in my browser — help me fix it" |
| "My scores disappeared" | "My Supabase data seems empty — help me check the database" |
| "I want to start fresh" | "Delete my local copy and re-download from the GitHub template" |
| "Netlify won't update" | "Help me re-deploy my site/ folder to Netlify" |
| "I broke something" | "Something is broken after my last change — help me undo it" |

## Exam Key Facts

| Detail | Value |
|--------|-------|
| Date | **10 July 2026** |
| Duration | 2 hours |
| Format | Paper, multiple choice (German only) |
| Scoring | A: Subject Knowledge (40%) + B: Text Comprehension (20%) + C: Cognitive Abilities (40%) |
| Places | 200 per year |
| Registration | [TISS Portal](https://tiss.tuwien.ac.at/aufnahme/aufnahmeverfahren) — deadline 4 May 2026 |
