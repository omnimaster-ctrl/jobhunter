---
name: resume-tailoring
description: Use when tailoring a resume for a specific job — handles LaTeX template modification, compilation, and PDF delivery
---

# Resume Tailoring Skill

## Overview
Tailor the candidate's LaTeX resume for a specific job by modifying replacement zones, compiling to PDF, and delivering for review.

## When to Use
- After user selects jobs to apply to
- When user requests a tailored resume for a specific posting
- During the /apply flow

## Process

1. **Load job analysis** — Get match analysis, requirements, and talking points from database
2. **Load profile** — Read `config/profile.yaml` for candidate details
3. **Spawn Resume Tailor** — Sub-agent generates content for 4 zones:
   - `%%SUMMARY%%` — Rewritten profile summary
   - `%%SKILLS_ORDER%%` — Reordered skills
   - `%%EXPERIENCE_HIGHLIGHTS%%` — Reordered/reworded experience
   - `%%RELEVANT_PROJECTS%%` — Optional projects section
4. **Compile PDF** — Use `resume.compiler.ResumeCompiler.fill_template()` then `.compile()`
5. **Fallback** — If compilation fails, use `.compile_with_fallback()` and notify user
6. **Store** — Save tex source and PDF path in `resumes` table
7. **Deliver** — Send PDF to user via Telegram for review
8. **Approval loop** — Handle approve/reject/edit responses

## Verification
- [ ] PDF compiles successfully (non-zero file size)
- [ ] No %%ZONE%% markers remain in the compiled tex
- [ ] Resume content is truthful (no fabricated experience)
- [ ] PDF sent to user before any submission
- [ ] User explicitly approved before proceeding
