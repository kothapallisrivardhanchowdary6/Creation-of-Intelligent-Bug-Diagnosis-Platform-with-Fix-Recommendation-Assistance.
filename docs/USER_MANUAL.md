# User Manual

## DefectMind AI — Step-by-Step Guide

**Live Application:** https://defectmind-frontend.onrender.com/

---

## Getting Started

Open the application at https://defectmind-frontend.onrender.com/ in any modern browser (Chrome, Firefox, Edge, Safari). No account or login is required.

> **First visit tip:** The backend on Render.com may take 30–60 seconds to wake up from inactivity. If the Dashboard shows no data or API calls hang, wait a moment and refresh the page.

---

## Navigation

The left sidebar contains eight navigation items:

| Icon | Page | Purpose |
|---|---|---|
| 📊 Dashboard | Dashboard | Overview and quick actions |
| 📄 Submit Bug | Bug Submission | Report a new bug |
| 🐛 Bug List | Bug List | View and manage all submitted bugs |
| ⚙️ Analysis | Bug Analysis | View AI analysis results |
| 📈 Analytics | Analytics | Defect pattern visualisations |
| 🔍 Knowledge Base | Knowledge Base | Semantic search |
| 📚 KB Growth | Knowledge Base Growth | Add resolved bugs to the KB |
| 🧪 E2E Testing | E2E Testing | Run automated tests |

On mobile, tap the ☰ menu icon to open the sidebar.

---

## 1. Dashboard

The Dashboard is the home page. It shows:

- **Stats cards:** Total Bugs, Analyzed, Pending, Critical
- **AI Agent Pipeline diagram:** The five-stage pipeline with brief descriptions
- **Recent Submissions:** The last five submitted bugs with quick-action buttons

**Quick actions:**
- Click **Submit New Bug** to go to the submission form
- Click **Search Knowledge Base** to go to the search page
- Click **Analyze** next to any submitted (pending) bug to start analysis
- Click **View Results** next to any analyzed bug to see the full analysis

---

## 2. Submitting a Bug

Navigate to **Submit Bug** in the sidebar.

### Required fields

| Field | Description | Minimum |
|---|---|---|
| **Title** | A short, specific title describing the bug | 5 characters |
| **Description** | What happens, steps to reproduce, expected vs. actual behaviour | 10 characters |

### Optional fields (strongly recommended)

| Field | Description | Tip |
|---|---|---|
| **Stack Trace** | Paste the full stack trace here | Java, Python, and Node.js are parsed automatically |
| **Error Logs** | Paste relevant log lines | Lines with ERROR/FATAL will be highlighted |
| **Environment** | Runtime environment details | e.g., "Java 17, Spring Boot 3.1, Production" |

### File attachments

Click the attachment area or drag files onto it. Supported formats: `.txt`, `.log`, `.md`, `.json`, `.csv`. The file content will be read locally and included in the submission.

### Submitting

Click **Submit Bug Report**. On success:
- A notification appears with the generated Bug ID (e.g., `BUG-A3F12B9C04E8`)
- The page navigates to the Bug List
- The new bug appears with status **submitted**

---

## 3. Running AI Analysis

From the Bug List, find a bug with status **submitted** and click **Analyze**.

The system runs the five-agent pipeline:
1. **Triage** — classifies severity, priority, component, category
2. **Log Analysis** — parses stack traces and extracts exceptions
3. **Root Cause** — searches the knowledge base and generates hypotheses
4. **Duplicate Detection** — checks for similar existing bugs
5. **Remediation** — suggests actionable fixes

Analysis typically completes in under one second in mock mode. With a real LLM, expect 5–30 seconds depending on the model.

When complete:
- Bug status changes to **analyzed**
- The page navigates automatically to the Analysis view
- A notification confirms completion

---

## 4. Reading Analysis Results

The Analysis page shows five expandable cards, one per agent.

### 4.1 Triage Card

Shows the bug's classification:

| Field | Description |
|---|---|
| Severity | `critical` / `high` / `medium` / `low` — colour-coded |
| Priority | `P0` / `P1` / `P2` / `P3` |
| Category | Type of defect (e.g., Null Reference, Concurrency) |
| Component | Affected system component |
| Confidence | 0–100% — how confident the agent is |
| Reasoning | Text explanation of the classification |

### 4.2 Log Analysis Card

Shows parsed exception details:

| Section | Description |
|---|---|
| Failure Point | File, line, and method where the exception occurred |
| Code Path | Dot-notation path to the failure |
| Exceptions | List of exception types, messages, and locations |
| Error Patterns | High-level patterns detected (e.g., "Null reference/pointer") |
| Confidence | Parser confidence score |
| Summary | Human-readable summary |

### 4.3 Root Cause Card

**This card explicitly separates evidence from inference:**

| Section | Description |
|---|---|
| Probable Cause | The primary identified root cause |
| Confidence | Overall confidence in the analysis |
| Hypotheses | Ranked list of alternative explanations with supporting evidence and causal chains |
| Retrieved Evidence | **Historical bugs retrieved from the knowledge base** — each shows Bug ID, document text, similarity %, component, and resolution |
| Agent Reasoning | **What the agent inferred** — labelled separately so you know what is not from evidence |
| Evidence Summary | One-sentence summary of what the KB retrieval found |

> **Important:** `insufficient_evidence` status means the agent did not have enough signals to produce a confident root cause. This is correct behaviour for vague bug reports — the system will not hallucinate a confident answer.

### 4.4 Duplicate Detection Card

| Section | Description |
|---|---|
| Classification | `Likely Duplicate` / `Related Issue` / `New Unique Bug` / `Insufficient Evidence` |
| Top Similarity | Cosine similarity % of the closest match |
| Duplicate Probability | Weighted probability across top-3 matches |
| Matched Bugs | List of similar historical bugs with individual similarity scores and classifications |
| Thresholds Used | The configured thresholds (0.82 for duplicate, 0.55 for related) |

### 4.5 Remediation Card

| Section | Description |
|---|---|
| Suggested Fix | The primary fix recommendation |
| Fix Source | `Historical Evidence` / `Best Practice` / `Agent Reasoning` — labelled for transparency |
| Confidence | How confident the agent is in the fix |
| Implementation Steps | Numbered steps with optional code hints. Steps tagged **Inferred** are speculative |
| Debugging Steps | How to reproduce and investigate the issue |
| Validation Steps | How to verify the fix works |
| Regression Tests | What tests to run after the fix |
| Historical Resolutions | Fixes from similar bugs retrieved from the KB |
| Best Practices | General engineering guidance |
| Estimated Effort | e.g., "2–4 hours" |
| Risk Level | `low` / `medium` / `high` |

---

## 5. Bug List

The Bug List shows all submitted bugs as cards. Each card displays:
- Bug ID (monospace)
- Status badge (submitted / analyzing / analyzed / error)
- Severity and priority badges (if analyzed)
- Title and description excerpt
- Submission timestamp
- Component (if analyzed)

**Actions per bug:**
- **Analyze** — Runs the AI pipeline (only for `submitted` bugs)
- **Results** — Opens the Analysis view (only for `analyzed` bugs)
- **Delete** (trash icon) — Permanently removes the bug

Use the **Refresh** button to reload the list from the server.

---

## 6. Analytics Dashboard

Navigate to **Analytics** for defect pattern visualisations.

### Overview Stats

At the top, four stat cards show: Total Bugs, Critical/High counts, Duplicate count, and Knowledge Base size.

### Charts

| Chart | Description |
|---|---|
| Severity Distribution (pie) | How bugs are distributed across critical/high/medium/low |
| Priority Distribution (pie) | P0/P1/P2/P3 breakdown |
| Bugs per Component (stacked bar) | Which components have the most bugs, by severity |
| Top Exception Types (horizontal bar) | Most common exception classes |
| Most Common Root Causes (bar list) | Top identified root causes |
| Defect Trends (line chart) | Bug volume over time — day/week/month granularity |
| Duplicate Classification (pie) | Likely duplicate vs. related vs. unique |
| KB Clusters (radar/bar) | Knowledge base defects grouped by component |
| Similar Bug Clusters | Your submitted bugs matched against the KB |
| Common Error Patterns | Recurring error pattern tags |
| Root Cause Confidence | Confidence distribution bands |

### Filters

Use the filter bar to restrict all charts to a subset of bugs:

| Filter | How to use |
|---|---|
| Severity | Select from the dropdown |
| Priority | Select from the dropdown |
| Component | Type a component name |
| Exception Type | Type an exception class name |
| Date Range | Pick from/to dates |
| Duplicates Only | Check the checkbox |

Click **Clear filters** to reset.

The charts update immediately when a filter is applied.

> **Note:** Analytics only show data from bugs submitted and analyzed in the current session. The backend uses an in-memory store — data is reset when the server restarts.

---

## 7. Knowledge Base Search

Navigate to **Knowledge Base** to search the historical defect database.

### KB Status Panel

Shows the current state of the ChromaDB collection:
- Total indexed documents
- Projects covered
- Embedding model and dimensions
- Index status

### Semantic Search

1. Type a natural language query in the search box
2. Click **Search** or press Enter
3. Results appear as cards ranked by similarity

Each result shows:
- Bug ID and source project
- Full document text
- Similarity score (0–100%) with a colour-coded bar
- Component and severity metadata

**Example queries:**
- `NullPointerException connection retry`
- `memory leak tab rendering`
- `deadlock thread pool concurrency`
- `buffer overflow HTTP header`

---

## 8. Knowledge Base Growth

Navigate to **KB Growth** to add a confirmed-resolved bug to the knowledge base, making it available for future RAG retrieval.

### When to use this

Use this page when:
- A bug has been fully resolved and the fix is validated
- You want future similar bugs to benefit from this resolution
- You want to improve duplicate detection and root cause analysis for similar issues

### Required fields

| Field | Required? | Description |
|---|---|---|
| Title | Yes (min 5) | Bug title |
| Description | Yes (min 10) | What the bug was |
| Root Cause | Yes (min 5) | What caused it |
| Resolution | Yes (min 10) | How it was fixed |
| Resolution Confirmed | Yes (must be ✅) | Confirms the fix has been validated |

### Recommended fields

Component, Severity, Category significantly improve future retrieval quality.

### Workflow

1. Fill in the required fields
2. (Optional) Click **Validate First** to check for errors and see a duplicate check preview before committing
3. Click **Add to Knowledge Base**

The workflow indicator shows progress through six steps:
1. **Fill Details** — form ready
2. **Validate** — field validation
3. **Dup Check** — similarity check against existing KB
4. **Generate Embedding** — 384-dim vector created
5. **Index to KB** — stored in ChromaDB
6. **Verify Retrieval** — confirms new entry is retrievable

On success, a green banner shows the assigned document ID (e.g., `KB-A3B4C5D6E7F8`).

### Advanced fields

Click **Show advanced fields** to access:
- Original Bug ID
- Exception Type
- Error Message
- Source / Project
- Confirmed Fix
- Stack Trace

### Viewing recent additions

Click the **Recent Entries** tab to see bugs added this session.

The right sidebar shows live KB status including the count of user-added entries.

---

## 9. E2E Test Runner

Navigate to **E2E Testing** to run automated validation tests against the live backend.

### Test Scenarios

The **Test Scenarios** tab shows all 11 test cases before running:
- 5 distinct bugs (NPE, DB connection, API 500, Memory Leak, JWT Auth)
- 1 known duplicate scenario
- 1 related-but-non-duplicate scenario
- 1 insufficient evidence scenario
- 3 error-handling scenarios

### Running Tests

Click **Run All Tests**. A progress bar shows which test is currently executing. Tests run sequentially to avoid overwhelming the backend.

When complete, the view switches to **Results**.

### Reading Results

Each test card shows:
- Test ID (BUG-001, ERR-001, etc.)
- Overall status: **PASS** / **FAIL** / **WARN**
- Processing time
- Pipeline stage badges (each agent stage: PASS / FAIL / WARN / SKIP)

Click the **▼** chevron to expand a test and see:
- **Errors** — things that failed
- **Warnings** — potential issues or mismatches from expected values
- **Assertions** — specific expected vs. actual comparisons
- **Agent Results** — per-agent status and details

### Suite Summary

After running, the top section shows:
- Total / Passed / Failed / Warnings counts
- Pass rate bar
- Performance metrics (avg, min, max, P95 analysis time)
- RAG evaluation (total retrievals, successful, avg similarity)
- Duplicate detection F1 metrics (precision, recall, F1 score)

### JSON Export

Scroll to the bottom of the Results view to see the raw JSON test report, which you can copy for reporting purposes.

---

## Tips and Common Questions

**Q: The analysis takes a very long time — is it stuck?**
A: In production mode with a real LLM, analysis can take 5–30 seconds. The loading spinner in the top bar indicates the request is in progress. If it takes more than 60 seconds, the request may have timed out — try again.

**Q: My bug shows "Insufficient Evidence" for root cause — why?**
A: This is intentional. When the bug description is vague (no stack trace, short description), the system caps confidence below the threshold and returns "Insufficient Evidence" rather than generating a confident but unsupported answer. Add a stack trace and/or error logs and re-analyze.

**Q: Analytics are empty — why?**
A: Analytics only show data from bugs submitted and analyzed in the current server session. Submit and analyze a few bugs, then refresh the analytics page.

**Q: The knowledge base shows 0 documents**
A: The KB needs to be seeded. Call `POST /api/knowledge-base/ingest` via the API or run `python scripts/seed_data.py` from the backend directory.

**Q: Can I edit a submitted bug?**
A: Not currently. Delete the bug and resubmit with corrected information.

**Q: What does "Fix Source: Agent Reasoning" mean?**
A: It means the suggested fix was generated by the AI agent's inference rather than retrieved directly from a historical resolution. It is potentially less reliable than "Historical Evidence" and more likely to include speculative steps (tagged "Inferred").
