# GitHub Traction Signals — API Reference (Third-Party Perspective)

## Purpose

This document maps traction signals from the research document ("Identifying Software Traction Sources") to concrete GitHub API endpoints available to **any third party scanning public repositories they do not own.** This serves as the spec for an MCP server that scans ANY public GitHub repo for real adoption signals.

## Core Assumption

**We are external analysts, not repo owners.** We have zero special access. All endpoints must work with a standard read-only PAT against public repos.

---

## What's Available vs. What's Not

| Available (Third-Party) | NOT Available (Owner-Only) |
|---|---|
| Forks (count, who, when, activity) | Clone data (volume, unique cloners) |
| Commit velocity (52-week history) | Page views / unique visitors |
| Contributor diversity | Referring sites / top paths |
| Issue labels + reaction counts | |
| PR merge frequency + cycle time | |
| Comment volume + participants | |
| Dependency count (via scraping) | |
| Releases + tags | |
| License type | |

**The 3 owner-only metrics (clones, views, referrers) are excluded from this spec entirely.** They cannot be used for competitor/market analysis.

---

## Rate Limits

| Auth Method | Limit |
|---|---|
| No auth | 60 req/hr |
| **PAT (read-only)** | **5,000 req/hr** |
| GraphQL (PAT) | 5,000 points/hr |
| Search API | 30 req/min |

**Recommended:** Fine-grained PAT with `public_repo` read-only scope.

---

## 1. Forks — Builder Intent Signal

**Why it matters:** A fork = someone taking the idea and building on it. Fork velocity over time is a leading indicator of adoption.

### REST — Fork Count (from repo object)

```
GET /repos/{owner}/{repo}
```

Response field: `forks_count`

### REST — Fork List (who forked + when)

```
GET /repos/{owner}/{repo}/forks
```

| Parameter | Type | Description |
|---|---|---|
| `sort` | string | `newest`, `oldest`, `stargazers`, `watchers` |
| `per_page` | int | Max 100 |
| `page` | int | Pagination |

Response per fork:
- `created_at` — fork timestamp
- `owner.login` — who forked
- `stargazers_count` — stars on the fork (active fork signal)
- `open_issues_count` — activity on the fork
- `pushed_at` — last push (is the fork alive?)

### GraphQL — Forks with Activity Check

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    forkCount
    forks(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        createdAt
        owner { login }
        stargazerCount
        pushedAt
        defaultBranchRef {
          target {
            ... on Commit {
              committedDate
            }
          }
        }
      }
    }
  }
}
```

**Traction formula:** `active_forks (pushed_at > fork created_at + 7 days) / total_forks`

---

## 2. Dependency Graph — "Used By" Count

**No official API exists for inbound dependents.** GitHub shows "Used by X repositories" on the web UI but does not expose it via REST or GraphQL. The GraphQL `dependencyGraphManifests` field only returns **outbound** dependencies (what a repo uses), never inbound (who uses it). This is a confirmed permanent gap in the API.

### Primary Method — Web Scrape via `github-dependents-info`

The `/network/dependents` page is **server-rendered HTML** — no Playwright or headless browser needed. Simple `requests` + `BeautifulSoup` works. A ready-made package handles all parsing and pagination.

```bash
pip install github-dependents-info
```

**Programmatic usage (for MCP tool integration):**

```python
import os
import asyncio
from github_dependents_info import GithubDependentsInfo

async def get_repo_dependents(repo: str, max_pages: int = 5) -> dict:
    client = GithubDependentsInfo(
        repo=repo,
        sort="stars",
        max_scraped_pages=max_pages,
        github_token=os.getenv("GITHUB_TOKEN")
    )
    return await client.collect_dependents_info()
```

**Output structure:**
```json
{
  "packages": [{
    "name": "owner/repo",
    "total_dependents_number": 15200,
    "public_dependents": [{"name": "user/repo", "stars": 42}],
    "private_dependents_number": 3100
  }],
  "all_public_dependent_repos": [{"name": "user/repo", "stars": 42}]
}
```

**HTML selectors used internally (stable for years):**
```python
rows = soup.select("#dependents .Box-row")              # each dependent
repo_name = row.select_one("a.text-bold")               # repo link
next_page = soup.select_one("#dependents .pagination a[rel='next']")  # pagination
```

Pagination: 30 results per page via `?dependents_after=<cursor>` query param.

### Scoping Constraint — Cap Pages for Large Repos

| Repo size | Pages needed | Time | Hackathon viable? |
|---|---|---|---|
| Small (<500 dependents) | 1-17 pages | Seconds | Yes, full scrape |
| Medium (500-5,000) | 17-167 pages | Minutes | Yes, cap at 10 pages |
| Large (10k+, e.g. React, Flask) | 300+ pages | Hours | Cap at 5 pages (~150 dependents) |

**Recommendation:** Default `max_pages=5`. Returns ~150 top dependents sorted by stars — more than enough for traction scoring.

### Rate Limiting for Scraping

| Scenario | Risk |
|---|---|
| With `GITHUB_TOKEN`, small/medium repo | Very low |
| With `GITHUB_TOKEN`, large repo, capped pages | Low |
| Without token, any repo | Medium — 429s likely |
| No delay between pages | High — anti-abuse detection |

**Mitigations:**
- Always pass `GITHUB_TOKEN` (reuses same PAT as REST/GraphQL calls)
- The package adds 1-5s random delay between pages automatically
- Cache results during development — don't re-scrape same repo repeatedly

### Fallback — libraries.io API

For package-level dependents (npm, PyPI, etc.), libraries.io offers a free API:

```
GET https://libraries.io/api/{platform}/{name}/dependents?api_key=YOUR_KEY
```

- Free tier with registration, 60 req/min
- Only covers packages on registries — misses repos that import without declaring in a manifest
- Good complement, not a replacement

### Fallback — Code Search API (rough proxy)

```
GET /search/code?q=require("{package-name}")+in:file
```

`total_count` in response gives approximate usage. Very rate-limited (30 req/min). Useful for packages not on `/network/dependents`.

### Implementation Effort

**~30-60 minutes.** The package handles parsing, pagination, and async fetching. The MCP tool is a thin wrapper. This is the highest-weighted signal (5x) in the traction score and worth including.

**Traction signal:** Dependency count = other developers invested time to build on top of this. The strongest third-party-accessible indicator of real-world adoption.

---

## 3. Issue Labels + Reactions — Unmet Needs Signal

### REST — Issues by Label

```
GET /repos/{owner}/{repo}/issues
```

| Parameter | Type | Description |
|---|---|---|
| `labels` | string | Comma-separated: `enhancement,feature request` |
| `state` | string | `open`, `closed`, `all` |
| `sort` | string | `created`, `updated`, `comments` |
| `direction` | string | `asc`, `desc` |
| `since` | string | ISO 8601 timestamp filter |
| `per_page` | int | Max 100 |
| `page` | int | Pagination |

**Label variants to scan** (case-sensitive — check all):
- `enhancement`
- `feature request`
- `feature-request`
- `Feature Request`
- `help wanted`
- `good first issue`
- `question`
- `discussion`
- `proposal`
- `rfc`

### REST — Reactions on an Issue

```
GET /repos/{owner}/{repo}/issues/{issue_number}/reactions
```

| Parameter | Type | Description |
|---|---|---|
| `content` | string | Filter: `+1`, `-1`, `laugh`, `confused`, `heart`, `hooray`, `rocket`, `eyes` |
| `per_page` | int | Max 100 |

Key signal: `+1` (thumbs up) count on feature requests = validated demand.

### GraphQL — Issues with Reactions (most efficient)

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(
      first: 100,
      labels: ["enhancement"],
      states: OPEN,
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      totalCount
      nodes {
        title
        number
        createdAt
        reactions(content: THUMBS_UP) { totalCount }
        reactions(content: THUMBS_DOWN) { totalCount }
        comments { totalCount }
        labels(first: 10) { nodes { name } }
        participants { totalCount }
      }
    }
  }
}
```

Note: GraphQL doesn't allow two `reactions` fields with different args in one level. Use aliases:

```graphql
thumbsUp: reactions(content: THUMBS_UP) { totalCount }
thumbsDown: reactions(content: THUMBS_DOWN) { totalCount }
```

**Traction formula:** Issues sorted by `thumbs_up DESC` = prioritized list of unmet market needs.

---

## 4. Commit Velocity — Active Maintenance Signal

### REST — Weekly Commit Activity (last 52 weeks)

```
GET /repos/{owner}/{repo}/stats/commit_activity
```

No parameters. Returns array of 52 weekly objects:
```json
{
  "days": [0, 3, 26, 20, 39, 1, 0],
  "total": 89,
  "week": 1336280400
}
```

`week` = Unix timestamp for start of week (Sunday). `days` = Sun–Sat commit counts.

### REST — Participation (owner vs all)

```
GET /repos/{owner}/{repo}/stats/participation
```

Returns:
```json
{
  "all": [11, 21, 15, ...],   // 52 weeks, total commits
  "owner": [3, 5, 2, ...]     // 52 weeks, owner-only commits
}
```

**Traction signal:** `all - owner` = community contribution. If community share is growing, the project is gaining organic traction.

### Gotcha: Async Computation

Stats endpoints return `HTTP 202` if data isn't cached. Must retry:

```python
def get_stats_with_retry(url, headers, retries=5, delay=3):
    for _ in range(retries):
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 202:
            time.sleep(delay)
    return None
```

---

## 5. Contributor Diversity — Ecosystem Health Signal

**Note:** Org membership is public, but the collaborator list requires push access. Use org members as the "core team" proxy instead.

### REST — Contributor List

```
GET /repos/{owner}/{repo}/contributors
```

| Parameter | Type | Description |
|---|---|---|
| `anon` | string | `true` to include anonymous contributors |
| `per_page` | int | Max 100 |
| `page` | int | Pagination |

Response per contributor:
- `login` — GitHub username
- `contributions` — total commit count
- `type` — `User` or `Bot`

### REST — Org Members (to identify "core team")

```
GET /orgs/{org}/members
```

Public for public orgs. Compare contributor logins against this list.

### REST — Per-Contributor Weekly Stats

```
GET /repos/{owner}/{repo}/stats/contributors
```

Response:
```json
[
  {
    "author": { "login": "octocat" },
    "total": 135,
    "weeks": [
      { "w": 1367712000, "a": 6898, "d": 77, "c": 10 }
    ]
  }
]
```

`w` = week Unix timestamp, `a` = additions, `d` = deletions, `c` = commits.

**Traction formula:**
```
diversity_ratio = contributors_not_in_org / total_contributors
```
Above 0.4 for projects >6 months old = strong ecosystem signal.

---

## 6. PR Merge Frequency — Velocity Signal

### REST — Merged PRs

```
GET /repos/{owner}/{repo}/pulls
```

| Parameter | Type | Description |
|---|---|---|
| `state` | string | `closed` (then filter for `merged_at != null`) |
| `sort` | string | `created`, `updated`, `popularity`, `long-running` |
| `direction` | string | `asc`, `desc` |
| `per_page` | int | Max 100 |
| `page` | int | Pagination |
| `base` | string | Filter by base branch |

Response fields:
- `merged_at` — null if closed without merge
- `user.login` — PR author
- `merged_by.login` — who merged
- `additions`, `deletions` — change size
- `created_at`, `closed_at` — for cycle time calculation

### GraphQL — Merged PRs (more efficient)

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: MERGED, first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount
      nodes {
        mergedAt
        author { login }
        mergedBy { login }
        additions
        deletions
        createdAt
      }
    }
  }
}
```

**Traction formulas:**
- `merge_rate = merged_PRs_last_30d / unique_PR_authors` — PRs per contributor
- `cycle_time = merged_at - created_at` — time from PR open to merge
- `external_PR_ratio = PRs_by_non_org / total_PRs` — community contribution

---

## 7. Comments on Issues/PRs — Engagement Signal

### REST — Issue Comments (repo-wide)

```
GET /repos/{owner}/{repo}/issues/comments
```

| Parameter | Type | Description |
|---|---|---|
| `sort` | string | `created`, `updated` |
| `direction` | string | `asc`, `desc` |
| `since` | string | ISO 8601 — only comments after this date |
| `per_page` | int | Max 100 |

### REST — PR Review Comments (repo-wide)

```
GET /repos/{owner}/{repo}/pulls/comments
```

Same parameters as issue comments.

### GraphQL — Top Issues by Engagement

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, states: OPEN, orderBy: {field: COMMENTS, direction: DESC}) {
      nodes {
        title
        number
        comments { totalCount }
        participants { totalCount }
        thumbsUp: reactions(content: THUMBS_UP) { totalCount }
        updatedAt
        createdAt
      }
    }
  }
}
```

`participants.totalCount` = unique people engaged (stronger than raw comment count).

**Sentiment proxy keywords to scan in comment bodies:**
- Production use: "we use this in production", "deployed", "running in prod"
- Demand: "+1", "we need this", "would love this", "blocking us"
- Frustration: "still waiting", "any update", "is this abandoned"

---

## 8. Repo Overview — Single Query Bootstrap

### GraphQL — All Key Metrics in One Call

```graphql
query RepoTraction($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    description
    createdAt
    pushedAt
    updatedAt
    stargazerCount
    forkCount
    watchers { totalCount }
    
    # License check (permissive = higher fork signal)
    licenseInfo { spdxId name }
    
    # Issue health
    openIssues: issues(states: OPEN) { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
    
    # Feature requests specifically
    featureRequests: issues(states: OPEN, labels: ["enhancement"]) { totalCount }
    
    # PR health
    openPRs: pullRequests(states: OPEN) { totalCount }
    mergedPRs: pullRequests(states: MERGED) { totalCount }
    
    # Commit count
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 1) { totalCount }
        }
      }
    }
    
    # Languages
    primaryLanguage { name }
    languages(first: 5) { nodes { name } }
    
    # Topics/tags
    repositoryTopics(first: 10) { nodes { topic { name } } }
    
    # Releases
    releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes { tagName publishedAt }
    }
  }
}
```

---

## Composite Traction Score — Proposed Formula

All signals below are accessible as a third party scanning any public repo:

| Signal | Weight | Source |
|---|---|---|
| Dependency count (used by) | 5x | Web scrape |
| Contributor diversity ratio | 4x | REST + GraphQL |
| Fork velocity (forks/week trend) | 3x | REST + GraphQL |
| Active fork ratio (forks with post-fork commits) | 3x | GraphQL |
| Issue reaction density (thumbs up / issue) | 3x | GraphQL |
| Commit velocity (commits/week trend) | 2x | REST stats |
| Community commit share (all - owner / all) | 2x | REST participation |
| PR merge rate (external PRs/month) | 2x | GraphQL |
| PR cycle time (open to merge) | 2x | GraphQL |
| Comment engagement (participants/issue) | 2x | GraphQL |
| Issue resolution speed (open to close) | 1x | GraphQL |
| Release cadence (releases/month) | 1x | GraphQL |

**Not available as third party (excluded):**
- Clone-to-star ratio (owner only)
- Page view trend (owner only)
- Referring sites (owner only)

---

## MCP Server Design

All tools operate as a third party with a read-only PAT. No owner access required.

| Tool | Description | API Used |
|---|---|---|
| `get_repo_overview` | Single-call traction snapshot | GraphQL bootstrap query |
| `get_fork_activity` | Fork velocity + active fork ratio | REST forks + GraphQL |
| `get_commit_velocity` | 52-week commit trend | REST stats/commit_activity |
| `get_contributor_diversity` | External vs core contributor ratio | REST stats/contributors + orgs/members |
| `get_issue_signals` | Feature requests ranked by demand | GraphQL issues + reactions |
| `get_pr_health` | Merge rate, cycle time, external PRs | GraphQL pullRequests |
| `get_comment_engagement` | Top issues by participation | GraphQL issues by comments |
| `get_dependency_count` | Inbound dependent repos | Web scrape (github-dependents-info) |
| `calculate_traction_score` | Composite weighted score | Aggregates all above |

**Auth:** Single PAT with read-only public repo scope, passed as `GITHUB_TOKEN` env var.
**Transport:** stdio (for Claude Code) or SSE (for web).
**Language:** Python with FastMCP.

---

## Sample Output

See [SAMPLE_OUTPUT_voice_to_code_workflows.md](SAMPLE_OUTPUT_voice_to_code_workflows.md) for a full example of what this scanner produces when queried with: *"Verbally transform workflows into code."*

The sample demonstrates all output sections:
- Executive summary with sub-market mapping
- Per-repo traction profiles with scored signals
- Community sentiment scan (HN, Reddit, Product Hunt)
- Gap analysis (what exists vs. what's missing)
- Composite traction score matrix
- Strategic verdict with entry angle recommendation
