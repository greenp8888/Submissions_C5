# Reddit Traction Signals — API Reference (Third-Party Perspective)

## Purpose

This document maps Reddit as a traction signal source for the LangGraph agent. All endpoints are accessible as a third party with a free OAuth2 "script" app. Covers: official Reddit API, CloudSearch advanced syntax, PullPush (Pushshift successor) for historical/bulk access, and AsyncPRAW as the Python integration layer.

## Core Assumption

**We are external analysts scanning public subreddits for software product signals.** Read-only access. No moderation or write operations needed.

---

## Authentication — OAuth2 Script App Flow

Source: [reddit-archive/reddit/wiki/OAuth2](https://github.com/reddit-archive/reddit/wiki/OAuth2)

### Setup

1. Go to `https://www.reddit.com/prefs/apps` → "create another app" → type **script**
2. You get: `client_id` (14-char string below app name) + `client_secret`

### Token Request

```
POST https://www.reddit.com/api/v1/access_token
```

| Header | Value |
|---|---|
| `Authorization` | `Basic base64(client_id:client_secret)` |
| `User-Agent` | `<platform>:<app_id>:<version> (by /u/<username>)` |
| `Content-Type` | `application/x-www-form-urlencoded` |

| Body Parameter | Value |
|---|---|
| `grant_type` | `password` |
| `username` | Your Reddit username |
| `password` | Your Reddit password |

**Response:**
```json
{
  "access_token": "eyJ...abc",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "*"
}
```

Token expires in 1 hour. No refresh token in script flow — re-authenticate.

### Using the Token

**Base URL:** `https://oauth.reddit.com` (NOT www.reddit.com)

**Required headers on every request:**
```
Authorization: bearer <access_token>
User-Agent: <platform>:<app_id>:<version> (by /u/<username>)
```

**Critical:** Default user-agents (`python-requests`, `urllib`, etc.) get severe rate-limiting. Spoofing browsers = permanent ban.

### Available Scopes

For read-only traction scanning, you need: `read`, `history`

Full list: `identity`, `edit`, `flair`, `history`, `modconfig`, `modflair`, `modlog`, `modposts`, `modwiki`, `mysubreddits`, `privatemessages`, `read`, `report`, `save`, `submit`, `subscribe`, `vote`, `wikiedit`, `wikiread`

---

## Rate Limits

Source: [reddit-archive/reddit/wiki/API](https://github.com/reddit-archive/reddit/wiki/API)

| Client Type | Limit |
|---|---|
| **OAuth2 authenticated** | **60 requests/minute** |
| Unauthenticated | 10 requests/minute |

### Response Headers (check on every response)

| Header | Type | Meaning |
|---|---|---|
| `X-Ratelimit-Used` | integer | Requests consumed in current window |
| `X-Ratelimit-Remaining` | float | Requests remaining |
| `X-Ratelimit-Reset` | integer | Seconds until window resets |

**Exceeding:** Returns `429 Too Many Requests`. Repeated violations trigger 10–60 minute blocks.

---

## 1. Search Endpoints

### Global Search

```
GET https://oauth.reddit.com/search
```

### Subreddit-Scoped Search

```
GET https://oauth.reddit.com/r/{subreddit}/search
```

### Multi-Subreddit Search (combine with +)

```
GET https://oauth.reddit.com/r/SaaS+devtools+LocalLLaMA/search
```

### Parameters

| Parameter | Type | Values | Default | Notes |
|---|---|---|---|---|
| `q` | string | Search query (required) | — | Supports Lucene and CloudSearch syntax |
| `sort` | string | `relevance`, `hot`, `new`, `top`, `comments` | `relevance` | |
| `t` | string | `hour`, `day`, `week`, `month`, `year`, `all` | `all` | Time filter (meaningful with `sort=top` or `sort=new`) |
| `limit` | integer | 1–100 | 25 | Results per page |
| `after` | string | Fullname (e.g., `t3_abc123`) | — | Cursor for next page |
| `before` | string | Fullname | — | Cursor for previous page |
| `count` | integer | 0+ | 0 | Hints for pagination numbering |
| `restrict_sr` | boolean | `true`/`false` | `false` | **Must be `true`** to restrict to subreddit in URL path |
| `type` | string | `link`, `sr`, `user` | — | Filter result types (omit for all) |
| `syntax` | string | `lucene`, `cloudsearch`, `plain` | `lucene` | Query syntax mode |
| `include_over_18` | boolean | `true`/`false` | — | Include NSFW results |
| `raw_json` | integer | `1` | — | Prevents HTML entity encoding in response |

### Hard Limit

**Results capped at ~1,000 per query** regardless of pagination. Design queries to stay under this via narrower time windows or subreddit scoping.

---

## 2. Query Syntax

### Default Lucene Syntax (`syntax=lucene`)

| Operator | Example | Behavior |
|---|---|---|
| Space / `AND` | `crm software` | Both terms required |
| `OR` | `crm OR erp` | Either term |
| `NOT` / `-` | `crm -salesforce` | Exclude term |
| Quotes | `"pain points"` | Exact phrase |
| Wildcard | `integrat*` | Prefix match |
| `title:` | `title:alternatives` | Search title only |
| `selftext:` | `selftext:frustrating` | Search post body only |
| `author:` | `author:username` | Posts by specific user |
| `flair:` | `flair:discussion` | Filter by post flair |
| `subreddit:` | `subreddit:saas` | Target subreddit (in global search) |

### CloudSearch Syntax (`syntax=cloudsearch`)

Source: [paperlined.org CloudSearch reference](https://paperlined.org/apps/reddit/technical/cloudsearch_reference.html)

Add `&syntax=cloudsearch` to enable. Uses prefix-notation boolean operators and unlocks numeric/date range filters.

**Boolean operators:**
```
(and title:'alternatives' selftext:'too expensive')
(or (and title:crm) (and title:salesforce))
(not author:'spammer_name')
```

**All searchable fields:**

| Field | Type | Notes |
|---|---|---|
| `text:` | string | Searches title + author + subreddit + selftext |
| `title:` | string | Post title |
| `selftext:` | string | Body of self-posts |
| `author:` | string | Username |
| `subreddit:` | string | Subreddit name |
| `site:` | string | Domain of linked URL |
| `url:` | string | Specific URL path |
| `flair:` | string | Post flair text |
| `flair_text:` | string | Post flair text (alias) |
| `flair_css_class:` | string | CSS class of flair |
| `timestamp:` | unix range | Post creation time |
| `num_comments:` | integer range | Comment count |
| `ups:` | integer range | Upvote count |
| `downs:` | integer range | Downvote count |
| `top:` | integer range | Total score |
| `nsfw:` / `over18:` | 0 or 1 | Content rating |
| `self:` / `is_self:` | 0 or 1 | 1 = text post, 0 = link post |
| `sr_id:` | string | Base36-decoded subreddit ID |
| `fullname:` | string | Thread fullname (t3_xxx) |

**Range syntax:**
- `num_comments:40..500` — closed range
- `ups:100..` — open minimum (100+)
- `timestamp:1700000000..1710000000` — date range via Unix timestamps

**Examples:**
```
(and subreddit:'SaaS' title:'alternatives' num_comments:10..)
(and selftext:'switched from' timestamp:1700000000..)
(or title:'voice coding' title:'speech to code')
```

---

## 3. Listing Endpoints (Hot, New, Top, Rising)

These return posts from a subreddit sorted by algorithm, without a search query.

### Endpoints

```
GET https://oauth.reddit.com/r/{subreddit}/hot
GET https://oauth.reddit.com/r/{subreddit}/new
GET https://oauth.reddit.com/r/{subreddit}/top
GET https://oauth.reddit.com/r/{subreddit}/rising
GET https://oauth.reddit.com/r/{subreddit}/controversial
```

### Parameters

| Parameter | Type | Values | Default | Notes |
|---|---|---|---|---|
| `t` | string | `hour`, `day`, `week`, `month`, `year`, `all` | `day` | Time filter (only for `/top` and `/controversial`) |
| `limit` | integer | 1–100 | 25 | |
| `after` | string | Fullname | — | Next page cursor |
| `before` | string | Fullname | — | Previous page cursor |
| `count` | integer | 0+ | 0 | |
| `raw_json` | integer | `1` | — | Prevents HTML encoding |

**Cap:** Listing endpoints max out at ~1,000 most recent posts per subreddit.

---

## 4. Post Object Fields

Every post in a search or listing response is wrapped in `{"kind": "t3", "data": {...}}`.

### Key Fields for Traction Scanning

| Field | Type | Traction Use |
|---|---|---|
| `id` | string | ID36 without prefix (e.g., `abc123`) |
| `name` | string | Fullname with prefix (e.g., `t3_abc123`) — used for pagination |
| `title` | string | Post headline — primary text for keyword matching |
| `selftext` | string | Body of self-post; empty for link posts; `[removed]` if deleted |
| `score` | integer | Net upvotes (ups - downs) |
| `ups` | integer | Raw upvote count |
| `downs` | integer | Raw downvotes (often 0 due to vote fuzzing) |
| `upvote_ratio` | float | e.g., `0.95` — ratio of upvotes to total votes |
| `num_comments` | integer | Total comment count including nested |
| `created_utc` | float | Unix timestamp (UTC) |
| `subreddit` | string | Subreddit name without prefix |
| `subreddit_name_prefixed` | string | e.g., `r/SaaS` |
| `author` | string | Username; `[deleted]` if account removed |
| `author_fullname` | string | Account fullname (e.g., `t2_abc`) |
| `link_flair_text` | string/null | Flair label |
| `url` | string | External URL (link posts) or permalink (self-posts) |
| `permalink` | string | Relative path (e.g., `/r/saas/comments/abc123/title/`) |
| `is_self` | boolean | `true` for text posts |
| `over_18` | boolean | NSFW flag |
| `stickied` | boolean | Pinned by mods |
| `locked` | boolean | Comments locked |
| `total_awards_received` | integer | Award count |

### Signal Interpretation

| Field Combination | Signal |
|---|---|
| High `score` + high `num_comments` | Viral, broad interest |
| Low `score` + high `num_comments` | Controversial — active debate (check `upvote_ratio`) |
| `upvote_ratio >= 0.85` | Strong consensus |
| `upvote_ratio 0.50–0.69` | Polarizing — potential switching-intent signal |
| `is_self = true` + long `selftext` | Detailed pain point or experience report |
| `link_flair_text` = "Show & Tell" or "Launch" | Product announcement |

---

## 5. Comment Tree Endpoint

### Fetch Comments for a Post

```
GET https://oauth.reddit.com/r/{subreddit}/comments/{post_id}
```

or without subreddit:
```
GET https://oauth.reddit.com/comments/{post_id}
```

### Parameters

| Parameter | Type | Values | Default | Notes |
|---|---|---|---|---|
| `sort` | string | `confidence`, `top`, `new`, `controversial`, `old`, `random`, `qa`, `live` | user pref | |
| `limit` | integer | 1–500 | ~200 | Max top-level comments |
| `depth` | integer | 1–10 | 10 | Nesting levels to retrieve |
| `comment` | string | ID36 | — | Use specific comment as root |
| `context` | integer | 0–8 | — | Parent levels to include (for permalink) |
| `raw_json` | integer | `1` | — | |

### Response Structure

Returns a **two-element JSON array**:

```json
[
  {"kind": "Listing", "data": {"children": [{"kind": "t3", "data": {...post...}}]}},
  {"kind": "Listing", "data": {"children": [
    {"kind": "t1", "data": {...comment with replies...}},
    {"kind": "more", "data": {"count": 142, "children": ["id1","id2"], "depth": 0}}
  ]}}
]
```

### Comment Object Fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | ID36 |
| `name` | string | Fullname (e.g., `t1_abc123`) |
| `body` | string | Comment text (markdown) |
| `body_html` | string | Rendered HTML |
| `author` | string | Username |
| `score` | integer | Net upvotes |
| `created_utc` | float | Unix timestamp |
| `depth` | integer | 0 = top-level |
| `parent_id` | string | Fullname of parent (post = `t3_`, comment = `t1_`) |
| `replies` | object/"" | Nested Listing of child comments; empty string if leaf |

### Expanding "More Comments"

When `{"kind": "more"}` appears in the tree:

```
POST https://oauth.reddit.com/api/morechildren
Content-Type: application/x-www-form-urlencoded
```

| Parameter | Type | Notes |
|---|---|---|
| `link_id` | string | Fullname of the post (e.g., `t3_abc123`) |
| `children` | string | Comma-delimited ID36 list from the `more` object |
| `sort` | string | Same options as comments endpoint |
| `depth` | integer | Levels to retrieve |
| `limit_children` | boolean | `true` = only return requested IDs without their children |

Response is a **flat array** — `replies` is always empty. Reconstruct tree using `parent_id`.

**Constraint:** Only one concurrent `/api/morechildren` request per client.

---

## 6. Subreddit Discovery

### Search Subreddits

```
GET https://oauth.reddit.com/subreddits/search
```

| Parameter | Type | Notes |
|---|---|---|
| `q` | string | Search query (required) — searches `display_name` and `public_description` |
| `sort` | string | `relevance` or `activity` |
| `limit` | integer | 1–100, default 25 |
| `after` | string | Pagination cursor |
| `include_over_18` | boolean | Include NSFW subreddits |

### Subreddit Autocomplete

```
GET https://oauth.reddit.com/api/subreddit_autocomplete
```

Fuzzy matching typeahead for subreddit names.

### Subreddit Info

```
GET https://oauth.reddit.com/r/{subreddit}/about
```

Returns: `subscribers`, `display_name`, `public_description`, `description` (full sidebar), `created_utc`, `subreddit_type` (`public`/`private`/`restricted`), `over18`, `quarantine`.

### Subreddit Object Fields (key fields)

| Field | Type | Notes |
|---|---|---|
| `display_name` | string | e.g., `saas` |
| `subscribers` | integer | Member count |
| `active_user_count` | integer | Currently online (when available) |
| `public_description` | string | Short description |
| `description` | string | Full sidebar (markdown) |
| `created_utc` | float | Unix timestamp |
| `subreddit_type` | string | `public`, `private`, `restricted` |

---

## 7. Target Subreddits for Software Traction Scanning

### Tier 1: High Signal — Technical Buyers Present

| Subreddit | ~Members | Why It Matters |
|---|---|---|
| r/devops | 300k | Infrastructure practitioners, tool evaluators, budget owners |
| r/LocalLLaMA | 671k | AI builders, self-hosters — extremely tool-aware |
| r/selfhosted | 148k | OSS vs. SaaS decision-makers, privacy-first |
| r/SaaS | 386k | Founders discussing tools, pricing, switching |
| r/IndieHackers | 200k | Bootstrapped builders sharing revenue + tools |
| r/devtools | 50k | Niche but pure signal — active tool evaluation |
| r/programming | 7M | Large; AI content banned April 2025 but technical core remains |
| r/webdev | 1.1M | Tool discussion common; has "show off" threads |

### Tier 2: Moderate Signal — Practitioner Communities

| Subreddit | ~Members | Why It Matters |
|---|---|---|
| r/MachineLearning | 3M | ML practitioner tooling frustrations |
| r/datascience | 700k | Data tooling complaints |
| r/Python | 1.7M | Python library/framework discussions |
| r/nocode | 100k | Automation tool switching (Zapier -> Make -> custom) |
| r/ProductManagement | 130k | PMs discussing tools they can't get devs to build |

### Tier 3: Niche but High-Value for Specific Categories

| Subreddit | ~Members | Why It Matters |
|---|---|---|
| r/sysadmin | 800k | Enterprise tooling, vendor fatigue |
| r/aws | 300k | Cloud tooling alternatives, cost frustration |
| r/kubernetes | 200k | Orchestration tool switching intent |
| r/ChatGPT | 3M | Consumer-heavy but captures enterprise use frustrations |

### Note on r/programming AI Ban

April 2025: r/programming banned LLM content. AI tool discussions scattered to r/LocalLLaMA, r/devtools, r/MachineLearning. For AI-adjacent product scanning, this actually increases signal density in niche subs.

---

## 8. Traction Signal Query Patterns

Ready-to-use query strings for the LangGraph agent's Reddit tools.

### Switching Intent (Highest Signal)

```python
switching_queries = [
    '"alternatives to {product}"',
    '"switched from {product}"',
    '"moved from {product}"',
    '"replaced {product} with"',
    '"left {product} because"',
    '"{product} vs"',
]
```

### Pain Points

```python
pain_queries = [
    '"frustrated with {product}"',
    '"{product} doesn\'t support"',
    '"wish {product} could"',
    '"{product} limitation"',
    '"anyone else struggling with {product}"',
]
```

### Internal Tool Signals (Very High Value — Validated Demand)

```python
internal_tool_queries = [
    '"built an internal tool" OR "we built a tool"',
    '"hacked together" OR "homegrown solution"',
    '"ended up building our own"',
    '"tired of waiting, just built"',
]
```

### Willingness to Pay

```python
budget_queries = [
    '"would pay for" {category}',
    '"shut up and take my money" {category}',
    '"I would subscribe if" {category}',
    '"killer feature would be" {category}',
]
```

### Market Validation

```python
validation_queries = [
    '"does anyone use" {product}',
    '"is {product} worth it"',
    '"what do you use for {workflow}"',
    '"looking for a tool that" {capability}',
    '"best tool for {workflow}"',
]
```

---

## 9. Comment-Level Signal Patterns

Regex patterns for extracting traction signals from comment bodies.

### Tier 1 — Production Use / Budget Signals (Highest Value)

```python
tier1_patterns = [
    r"we (use|run|deploy) this in prod",
    r"running (this )?at scale",
    r"we switched (from|away from)",
    r"replaced .+ with",
    r"would pay \$[\d,]+",
    r"take my money",
    r"been looking for (exactly )?this",
    r"we built something similar internally",
]
```

### Tier 2 — Validated Interest

```python
tier2_patterns = [
    r"\+1",
    r"same (here|problem|issue|boat|situation)",
    r"we (also|have this|face this)",
    r"this is a (real|common) problem",
    r"I've been wanting (this|something like this)",
    r"how (many|large) is your (team|org)",  # scale question = buyer signal
]
```

### Tier 3 — Competitive Intelligence

```python
competitor_patterns = [
    r"we (left|dropped|stopped using) [A-Z][a-z]+",
    r"(better|worse) than [A-Z][a-z]+",
    r"[A-Z][a-z]+ doesn't (handle|support|have)",
    r"[A-Z][a-z]+ (pricing|price) is (too high|insane|ridiculous)",
]
```

---

## 10. PullPush API — Historical/Bulk Access

Source: [pullpush.io](https://pullpush.io)

PullPush is the operational Pushshift successor. Use it when Reddit's native search is insufficient (>1,000 results, comment-level search, precise date ranges).

### Submission Search

```
GET https://api.pullpush.io/reddit/search/submission/
```

| Parameter | Type | Values | Notes |
|---|---|---|---|
| `q` | string | Search query | Full-text search |
| `title` | string | Title-only search | More precise than `q` |
| `selftext` | string | Body-only search | |
| `subreddit` | string | Subreddit name | |
| `author` | string | Username | |
| `after` | epoch/string | Unix timestamp or relative (`30d`, `4h`) | Start of time range |
| `before` | epoch/string | Unix timestamp or relative | End of time range |
| `score` | string | `>100`, `<25` | Comparison syntax |
| `num_comments` | string | `>10` | Comparison syntax |
| `size` | integer | Max 100 | Results per request |
| `sort` | string | `asc`, `desc` | Sort direction |
| `sort_type` | string | `score`, `num_comments`, `created_utc` | Sort field |
| `over_18` | boolean | `true`/`false` | NSFW filter |
| `is_video` | boolean | `true`/`false` | |
| `locked` | boolean | `true`/`false` | |
| `stickied` | boolean | `true`/`false` | |

### Comment Search

```
GET https://api.pullpush.io/reddit/search/comment/
```

Same parameters as submissions, plus:

| Parameter | Type | Notes |
|---|---|---|
| `link_id` | string | Base36 submission ID — get all comments for a specific post |

**This is the key advantage over Reddit's API:** PullPush lets you full-text search comment bodies directly, while Reddit's native API cannot.

### Response Format

```json
{
  "data": [
    {
      "id": "abc123",
      "title": "...",
      "selftext": "...",
      "author": "username",
      "subreddit": "SaaS",
      "score": 42,
      "num_comments": 15,
      "created_utc": 1700000000,
      "permalink": "/r/SaaS/comments/abc123/..."
    }
  ],
  "metadata": {
    "execution_time_milliseconds": 150,
    "total_results": 87
  }
}
```

### Rate Limits

Not officially documented. Practical safe target: ~15 req/min soft limit, 30/min hard limit.

---

## 11. Post-Level Metric Interpretation

### Upvote Thresholds (Subreddit-Relative)

Absolute thresholds are meaningless. Use relative thresholds:

| Subreddit Size | Meaningful Signal | Notes |
|---|---|---|
| < 50k members | 10+ score | Even 5 with 3+ comments is notable |
| 50k–300k | 25+ score | r/devtools, r/selfhosted tier |
| 300k–1M | 50+ score | r/SaaS, r/Python tier |
| 1M+ | 100+ score | r/webdev, r/programming tier |

### Key Ratios

| Metric | Formula | Interpretation |
|---|---|---|
| Comment density | `num_comments / score` | > 0.3 = high engagement relative to reach |
| Engagement ratio | `num_comments / 5 > score` | Comments outpacing upvotes = emotional topic |
| Upvote consensus | `upvote_ratio >= 0.85` | Strong agreement |
| Upvote controversy | `upvote_ratio 0.50–0.69` | Polarizing — potential switching signal |
| Post velocity | `score / hours_since_post` | Speed of engagement |

### Astroturfing Filters

Reject posts where:
- Account age < 30 days
- `comment_karma < 50`
- All comments are shallow one-liners ("Great tool!", "Looks useful")
- Comment timestamps clustered within 15 min of posting
- Title matches product's own tagline exactly

---

## 12. AsyncPRAW — Python Integration for LangGraph

### Why AsyncPRAW (not PRAW)

| | PRAW | AsyncPRAW |
|---|---|---|
| I/O model | Blocking/sync | `async/await` |
| LangGraph compatibility | Needs `asyncio.to_thread()` hack | Native |
| Rate limiting | Auto | Auto |
| Pagination | Auto via generators | Auto via async generators |
| Version | Stable | v7.8.1 (Dec 2024), stable |

### Installation

```bash
pip install asyncpraw
```

### Core Pattern

```python
import asyncpraw
import os

async with asyncpraw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="traction-scanner/0.1 by u/your_username",
) as reddit:
    subreddit = await reddit.subreddit("SaaS")
    async for post in subreddit.search(
        query='"alternatives to cursor"',
        sort="top",
        time_filter="year",
        limit=50,
    ):
        print(post.title, post.score, post.num_comments)
```

### Search

```python
# Global search (all subreddits)
subreddit = await reddit.subreddit("all")
async for post in subreddit.search(query, sort="top", time_filter="month", limit=100):
    ...

# Multi-subreddit search
subreddit = await reddit.subreddit("SaaS+devtools+LocalLLaMA")
async for post in subreddit.search(query, restrict_sr=True, ...):
    ...
```

Pagination is automatic — `async for` fetches next pages transparently.

### Comment Tree

```python
submission = await reddit.submission(id="POST_ID")
await submission.comments.replace_more(limit=5)  # expand "load more" nodes
all_comments = await submission.comments.list()   # flat list

for comment in all_comments:
    print(comment.body, comment.score, comment.depth)
```

`replace_more(limit=5)` = expand 5 "more comments" nodes. `limit=None` = expand all (can make 50+ HTTP requests — avoid in hackathon).

### LangGraph Tool Wrappers

```python
from langchain_core.tools import tool
from typing import Annotated
import json

@tool
async def search_reddit_for_product(
    product_name: Annotated[str, "Product or software to search for"],
    time_filter: Annotated[str, "Time window: 'week', 'month', 'year', 'all'"] = "month",
    limit: Annotated[int, "Max posts to return (max 100)"] = 25,
) -> str:
    """Search Reddit for posts mentioning a specific software product."""
    async with asyncpraw.Reddit(...) as reddit:
        subreddit = await reddit.subreddit("all")
        results = []
        async for post in subreddit.search(
            query=f'"{product_name}"',
            sort="top",
            time_filter=time_filter,
            limit=limit,
        ):
            results.append({
                "title": post.title,
                "subreddit": str(post.subreddit),
                "score": post.score,
                "num_comments": post.num_comments,
                "upvote_ratio": post.upvote_ratio,
                "body_preview": post.selftext[:200],
                "permalink": f"https://reddit.com{post.permalink}",
                "created_utc": post.created_utc,
            })
    return json.dumps(results, indent=2)


@tool
async def search_switching_intent(
    product_name: Annotated[str, "Product to find switching-away signals for"],
) -> str:
    """Find Reddit threads where users discuss alternatives to or switching from a product."""
    queries = [
        f'"alternatives to {product_name}"',
        f'"switched from {product_name}"',
        f'"replaced {product_name} with"',
        f'"{product_name} alternative"',
    ]
    # ... run each query, deduplicate by post ID, sort by score
    ...


@tool
async def get_reddit_comment_thread(
    post_id: Annotated[str, "Reddit post ID (e.g. 'abc123')"],
    min_score: Annotated[int, "Minimum comment score to include"] = 3,
) -> str:
    """Fetch comment tree from a high-signal Reddit post for detailed analysis."""
    async with asyncpraw.Reddit(...) as reddit:
        submission = await reddit.submission(id=post_id)
        await submission.comments.replace_more(limit=5)
        comments = []
        for comment in await submission.comments.list():
            if hasattr(comment, "body") and comment.score >= min_score:
                comments.append({
                    "body": comment.body[:400],
                    "score": comment.score,
                    "depth": comment.depth,
                    "author": str(comment.author) if comment.author else "[deleted]",
                })
    return json.dumps(comments, indent=2)


@tool
async def discover_subreddits(
    topic: Annotated[str, "Topic to find relevant subreddits for"],
    limit: Annotated[int, "Max subreddits to return"] = 15,
) -> str:
    """Find relevant subreddits for a topic, sorted by activity."""
    async with asyncpraw.Reddit(...) as reddit:
        results = []
        async for sr in reddit.subreddits.search(topic, limit=limit):
            results.append({
                "name": sr.display_name,
                "subscribers": sr.subscribers,
                "description": sr.public_description[:200],
                "type": sr.subreddit_type,
            })
    return json.dumps(sorted(results, key=lambda x: x["subscribers"], reverse=True), indent=2)
```

---

## 13. Key Constraints to Design Around

| Constraint | Impact | Workaround |
|---|---|---|
| 1,000 result cap per query | Can't paginate past 1,000 | Split by time windows or subreddits |
| No comment search in Reddit API | Can't search comment text directly | Use PullPush comment endpoint |
| Reddit search quality is poor | Inconsistent stemming, no proximity | Use CloudSearch syntax; supplement with PullPush |
| 60 req/min rate limit | ~1 req/sec max throughput | AsyncPRAW handles automatically; batch queries |
| NSFW blocked for 3rd-party apps | May miss some results | Not relevant for dev tool scanning |
| Deleted posts | ~20-35% of posts removed by mods | PullPush caches pre-deletion content |
| Private subreddits | Not accessible via any API | Use Google `site:reddit.com` for seed discovery |
| Token expires in 1 hour | Must re-authenticate | Re-call token endpoint; AsyncPRAW handles this |

---

## LangGraph Agent Tool Summary

| Tool | Description | API Used |
|---|---|---|
| `search_reddit_for_product` | Find posts mentioning a product | AsyncPRAW search (Reddit API) |
| `search_switching_intent` | Find "alternatives to X" threads | AsyncPRAW search, multiple queries |
| `get_reddit_comment_thread` | Deep-dive into a high-signal thread | AsyncPRAW comments + replace_more |
| `discover_subreddits` | Find relevant subreddits for a topic | AsyncPRAW subreddit search |
| `search_pain_points` | Surface frustration and feature requests | AsyncPRAW search with pain query patterns |
| `search_internal_tools` | Find "we built our own" signals | AsyncPRAW search with internal tool queries |
| `bulk_search_comments` | Full-text comment search | PullPush comment endpoint |
| `calculate_reddit_signal_score` | Score posts using traction formula | Aggregates above signals |

**Auth:** `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` env vars.
**Library:** AsyncPRAW (async-native, auto rate-limiting, auto pagination).
**Fallback:** PullPush for historical data and comment-body search.
