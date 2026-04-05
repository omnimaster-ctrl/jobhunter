# /apply — Apply to selected jobs

Start the application flow for selected jobs. For each job: tailor resume, send PDF for review, wait for approval, then submit.

## Usage
`/apply <job_ids>`

Examples:
- `/apply 1,3,5`
- `/apply 1`

## Process

For each selected job:

1. **Load job data** from the database

2. **Create application record** in database (status: 'draft')

3. **Tailor resume** — Spawn Resume Tailor sub-agent with:
   - Job analysis (from database match_analysis)
   - Base resume template
   - Candidate profile

4. **Compile PDF** — Use `resume.compiler.ResumeCompiler` to:
   - Fill template with tailored content
   - Compile to PDF with pdflatex
   - If compilation fails, use fallback (base resume)
   - Update application status to 'ready'

5. **Send PDF for review** — Send the compiled PDF to the user via Telegram with:
   ```
   📄 Resume tailored for: [Job Title] at [Company]
   Match Score: [X/100]

   Key changes:
   - [summary of what was tailored]

   Reply: ✅ approve | ❌ reject | ✏️ edit [instructions]
   ```

6. **Wait for approval**:
   - ✅ approve → Update status to 'approved', proceed to submit
   - ❌ reject → Update status to 'skipped', move to next job
   - ✏️ edit → Re-run Resume Tailor with edit instructions, loop back to step 5

7. **Submit application** — Spawn Application Executor sub-agent
   - Upload approved PDF
   - Fill Easy Apply form
   - Take screenshot proof
   - Update status to 'submitted' or 'failed'

8. **Wait between applications** — Random delay of 5-15 minutes (rate limiting)

9. **Report results** after all jobs processed:
   ```
   📊 Application Summary:
   ✅ Submitted: 3
   ❌ Rejected by you: 1
   ⚠️ Failed (manual needed): 1
   ```
