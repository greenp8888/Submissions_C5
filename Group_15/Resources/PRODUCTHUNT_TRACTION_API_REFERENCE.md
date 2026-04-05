# Product Hunt Traction Signals — API Reference (Third-Party Perspective)

## Purpose

This document maps Product Hunt as a traction signal source for the LangGraph agent. Product Hunt is a concentrated snapshot of what early adopters and "smart money" believe is gaining momentum. The API is GraphQL-based with generous rate limits for read-only scanning.

Source: [producthunt/producthunt-api schema.graphql](https://github.com/producthunt/producthunt-api/blob/master/schema.graphql) (canonical)

## Core Assumption

**We are external analysts scanning public Product Hunt launches for software traction signals.** Read-only access via Developer Token or OAuth2 client credentials. No user-level actions needed.

---

## Authentication

### Path A: Developer Token (Simplest — Recommended for Hackathon)

1. Go to `https://api.producthunt.com/v2/oauth/applications`
2. Create an application
3. Generate a **Developer Token** on the application page
4. Token never expires, tied to your account

### Path B: OAuth2 Client Credentials (Programmatic, Read-Only)

```
POST https://api.producthunt.com/v2/oauth/token
Content-Type: application/json
```

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "grant_type": "client_credentials"
}
```

Response contains `access_token`. Use identically to Developer Token.

### Using the Token

**Endpoint:** `POST https://api.producthunt.com/v2/api/graphql`

**Headers (every request):**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
Accept: application/json
```

**Body:** `{"query": "...", "variables": {...}}`

---

## Rate Limits

| Endpoint | Quota | Window |
|---|---|---|
| `/v2/api/graphql` | **6,250 complexity points** | 15 minutes |
| All other `/v2/*` | 450 requests | 15 minutes |

A basic posts query (~15 scalar fields) costs ~10-20 complexity points, giving ~300-600 queries per 15-minute window.

### Response Headers

| Header | Meaning |
|---|---|
| `X-Rate-Limit-Limit` | Total complexity budget for the period |
| `X-Rate-Limit-Remaining` | Remaining complexity |
| `X-Rate-Limit-Reset` | Seconds until window resets |

On breach: HTTP `429 Too Many Requests`. Wait `X-Rate-Limit-Reset` seconds.

---

## Pagination — Relay-Style Cursors

All list queries use Relay connection pattern:

```graphql
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!            # Total matching records
}

type PostEdge {
  cursor: String!
  node: Post!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  endCursor: String           # Pass as `after` for next page
  startCursor: String         # Pass as `before` for previous page
}
```

**Pattern:**
- First page: `posts(first: 20, order: VOTES)`
- Next page: `posts(first: 20, order: VOTES, after: "THE_END_CURSOR")`
- Stop when `pageInfo.hasNextPage == false`

---

## 1. Posts Query — The Core Traction Scanner Endpoint

```graphql
posts(
  first: Int                    # Items from front (max per page)
  last: Int                     # Items from back
  after: String                 # Forward pagination cursor
  before: String                # Backward pagination cursor
  order: PostsOrder = RANKING   # Sort order (default: RANKING)
  featured: Boolean             # Filter: featured posts only
  postedAfter: DateTime         # Filter: posts created after this timestamp
  postedBefore: DateTime        # Filter: posts created before this timestamp
  topic: String                 # Filter: by topic SLUG (e.g., "developer-tools")
  twitterUrl: String            # Filter: by associated Twitter URL
): PostConnection!
```

### PostsOrder Enum

| Value | Behavior |
|---|---|
| `RANKING` | PH ranking algorithm (default) — considers votes, recency, engagement |
| `VOTES` | Descending by vote count |
| `NEWEST` | Descending by creation date |
| `FEATURED_AT` | Descending by date featured on homepage |

### Topic Slugs (Key Ones for Traction Scanning)

| Slug | Category |
|---|---|
| `developer-tools` | Dev tools, IDEs, APIs |
| `artificial-intelligence` | AI/ML products |
| `productivity` | Workflow, time management |
| `saas` | SaaS products |
| `open-source` | OSS projects |
| `no-code` | No-code/low-code tools |
| `api` | API products |
| `automation` | Workflow automation |
| `tech` | General technology |
| `design-tools` | Design software |

**Important:** Pass the slug, not the display name. `"developer-tools"` not `"Developer Tools"`.

---

## 2. Post Object — Complete Fields

```graphql
type Post implements TopicableInterface & VotableInterface {
  # Identity
  id: ID!
  name: String!
  slug: String!
  tagline: String!
  description: String             # May be null
  url: String!                    # Product Hunt URL (/posts/tool-name)
  website: String!                # The product's own website URL

  # Traction Metrics
  votesCount: Int!
  commentsCount: Int!
  reviewsRating: Float!           # Aggregate star rating (0.0–5.0)

  # Timestamps
  createdAt: DateTime!
  featuredAt: DateTime            # Null if not featured

  # Media
  thumbnail: Media
  media: [Media!]!

  # Viewer State (only meaningful with user OAuth token)
  isVoted: Boolean!               # Always false with client credentials
  isCollected: Boolean!           # Always false with client credentials

  # Relations
  user: User!                     # Who submitted the post
  userId: ID!
  makers: [User!]!                # Array of maker User objects (NOT a connection)

  # Connections (paginated)
  topics(first: Int, last: Int, after: String, before: String): TopicConnection!
  comments(first: Int, last: Int, after: String, before: String, order: CommentsOrder = NEWEST): CommentConnection!
  collections(first: Int, last: Int, after: String, before: String): CollectionConnection!
  votes(first: Int, last: Int, after: String, before: String, createdAfter: DateTime, createdBefore: DateTime): VoteConnection!
}
```

### Media Type

```graphql
type Media {
  type: String!                   # "image" or "video"
  url(height: Int, width: Int): String!   # Parameterized URL
  videoUrl: String                # Present when type = "video"
}
```

### Signal Interpretation for Post Fields

| Field / Combination | Traction Signal |
|---|---|
| `votesCount > 500` | Strong launch — top 5% of daily launches |
| `votesCount > 1000` | Exceptional — top 1% |
| `commentsCount > 50` | Deep engagement beyond passive upvoting |
| `commentsCount / votesCount > 0.1` | High comment density = genuine interest, not just vote brigade |
| `reviewsRating >= 4.5` | Strong post-launch satisfaction |
| `featuredAt != null` | PH editorial selected it — algorithmic quality signal |
| `makers` array with serial founders | Repeat makers with prior successful launches = execution signal |
| Comments asking "can it do X?" | Expansion signal — product has nailed core job, users pushing to adjacent |

---

## 3. Comment Object — Complete Fields

```graphql
type Comment implements VotableInterface {
  id: ID!
  body: String!
  createdAt: DateTime!
  url: String!
  votesCount: Int!
  isVoted: Boolean!

  parentId: ID                    # Null if top-level
  parent: Comment                 # Parent comment object if nested

  user: User!
  userId: ID!

  replies(
    first: Int, last: Int, after: String, before: String,
    order: CommentsOrder = NEWEST
  ): CommentConnection!

  votes(
    first: Int, last: Int, after: String, before: String,
    createdAfter: DateTime, createdBefore: DateTime
  ): VoteConnection!
}

enum CommentsOrder {
  NEWEST
  VOTES_COUNT
}
```

### Comment-Level Traction Signals

| Pattern in `body` | Signal Type |
|---|---|
| "Can it do X?" / "Does it support Y?" | **Expansion signal** — core job validated, users want more |
| "We've been looking for exactly this" | **Validated demand** |
| "How does this compare to [competitor]?" | **Competitive positioning** — market is aware and comparing |
| "Just signed up" / "Already using it" | **Conversion signal** |
| "Would be great if it could..." | **Feature gap** — unmet adjacent need |
| Maker replying with feature roadmap | **Active development signal** |
| Comments from "top hunters" / verified makers | **Quality engagement** |

---

## 4. User Object — Complete Fields

```graphql
type User {
  id: ID!
  name: String!
  username: String!
  headline: String                # Bio/tagline
  url: String!                    # PH profile URL
  profileImage(size: Int): String
  coverImage(height: Int, width: Int): String
  twitterUsername: String
  websiteUrl: String
  createdAt: DateTime!

  # Viewer state
  isFollowing: Boolean!
  isMaker: Boolean!
  isViewer: Boolean!

  # Connections (paginated)
  followers(first: Int, last: Int, after: String, before: String): UserConnection!
  following(first: Int, last: Int, after: String, before: String): UserConnection!
  madePosts(first: Int, last: Int, after: String, before: String): PostConnection!
  submittedPosts(first: Int, last: Int, after: String, before: String): PostConnection!
  votedPosts(first: Int, last: Int, after: String, before: String): PostConnection!
  followedCollections(first: Int, last: Int, after: String, before: String): CollectionConnection!
}
```

**Note:** `followersCount` is NOT a direct scalar. Use `followers { totalCount }`.

### Hunter/Maker Quality Signals

| Pattern | Signal |
|---|---|
| `madePosts { totalCount } > 3` | Serial maker — execution track record |
| Prior `madePosts` with high `votesCount` | Proven ability to launch successfully |
| `twitterUsername` present with large following | Distribution advantage |
| `headline` mentions company/role | Professional builder, not hobbyist |

---

## 5. Topic Object — Complete Fields

```graphql
type Topic {
  id: ID!
  name: String!
  slug: String!
  description: String!
  url: String!
  followersCount: Int!
  postsCount: Int!
  createdAt: DateTime!
  isFollowing: Boolean!
  image(height: Int, width: Int): String
}
```

### Topics Query

```graphql
topics(
  first: Int, last: Int, after: String, before: String,
  order: TopicsOrder = NEWEST
  followedByUserId: ID
): TopicConnection!

enum TopicsOrder {
  FOLLOWERS_COUNT
  NEWEST
}
```

---

## 6. Collection Object — Complete Fields

```graphql
type Collection implements TopicableInterface {
  id: ID!
  name: String!
  tagline: String!
  description: String
  url: String!
  coverImage(height: Int, width: Int): String
  followersCount: Int!
  isFollowing: Boolean!
  createdAt: DateTime!
  featuredAt: DateTime

  user: User!
  userId: ID!

  posts(first: Int, last: Int, after: String, before: String): PostConnection!
  topics(first: Int, last: Int, after: String, before: String): TopicConnection!
}

enum CollectionsOrder {
  FEATURED_AT
  FOLLOWERS_COUNT       # default
  NEWEST
}
```

---

## 7. Single Post Lookup

```graphql
post(
  id: ID
  slug: String
): Post
```

Use `slug` to look up a specific product by its PH URL slug. There is **no `url` filter** on the `posts` list query — use this for direct lookups.

---

## 8. Traction Scanner Queries

### Query A: Scan Featured Posts by Topic and Date Range

```graphql
query TractionScan($topic: String!, $after: String, $postedAfter: DateTime, $postedBefore: DateTime) {
  posts(
    first: 20
    order: VOTES
    featured: true
    topic: $topic
    postedAfter: $postedAfter
    postedBefore: $postedBefore
    after: $after
  ) {
    totalCount
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id name slug tagline description
        website url
        votesCount commentsCount reviewsRating
        createdAt featuredAt
        thumbnail { type url(width: 320, height: 180) }
        makers { id name username headline twitterUsername websiteUrl }
        topics(first: 5) { edges { node { name slug } } }
      }
    }
  }
}
```

Variables:
```json
{
  "topic": "developer-tools",
  "postedAfter": "2025-10-01T00:00:00Z",
  "postedBefore": "2026-04-01T00:00:00Z"
}
```

### Query B: Deep-Dive into a Product with Comments

```graphql
query ProductDeepDive($slug: String!) {
  post(slug: $slug) {
    id name tagline description website
    votesCount commentsCount reviewsRating
    createdAt featuredAt
    media { type url(width: 800, height: 450) videoUrl }
    makers {
      id name username headline twitterUsername
      madePosts(first: 5) {
        totalCount
        edges { node { id name votesCount } }
      }
    }
    topics(first: 10) {
      edges { node { id name slug postsCount followersCount } }
    }
    comments(first: 30, order: VOTES_COUNT) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id body createdAt votesCount
          user { id name username headline }
          replies(first: 5) {
            totalCount
            edges { node { id body createdAt user { name username } } }
          }
        }
      }
    }
  }
}
```

### Query C: Topic Discovery (Find Relevant Categories)

```graphql
query DiscoverTopics {
  topics(first: 50, order: FOLLOWERS_COUNT) {
    edges {
      node {
        name slug postsCount followersCount description
      }
    }
  }
}
```

### Query D: Maker Track Record (Serial Founder Analysis)

```graphql
query MakerTrackRecord($username: String!) {
  user(username: $username) {
    name username headline twitterUsername websiteUrl
    followers { totalCount }
    madePosts(first: 20) {
      totalCount
      edges {
        node {
          name slug tagline votesCount commentsCount
          reviewsRating createdAt featuredAt website
          topics(first: 3) { edges { node { name slug } } }
        }
      }
    }
  }
}
```

---

## 9. Python Integration for LangGraph

### Dependencies

```bash
pip install httpx langchain-core langgraph
```

### Client Module

```python
# producthunt_client.py
import httpx
import os
import time

ENDPOINT = "https://api.producthunt.com/v2/api/graphql"

def get_headers():
    return {
        "Authorization": f"Bearer {os.environ['PRODUCTHUNT_TOKEN']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

async def ph_query(query: str, variables: dict = None) -> dict:
    """Execute a Product Hunt GraphQL query with rate limit handling."""
    async with httpx.AsyncClient() as client:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await client.post(ENDPOINT, json=payload, headers=get_headers())

        # Rate limit handling
        remaining = int(response.headers.get("X-Rate-Limit-Remaining", 9999))
        reset_seconds = int(response.headers.get("X-Rate-Limit-Reset", 0))

        if response.status_code == 429:
            time.sleep(reset_seconds + 1)
            return await ph_query(query, variables)  # retry

        if remaining < 200:
            time.sleep(reset_seconds + 1)

        data = response.json()
        if "errors" in data:
            raise Exception(f"PH API Error: {data['errors']}")
        return data["data"]
```

### LangGraph Tool Wrappers

```python
from langchain_core.tools import tool
from typing import Annotated
import json

@tool
async def search_producthunt_launches(
    topic: Annotated[str, "Topic slug (e.g., 'developer-tools', 'artificial-intelligence')"],
    posted_after: Annotated[str, "ISO 8601 date (e.g., '2025-01-01T00:00:00Z')"] = None,
    posted_before: Annotated[str, "ISO 8601 date"] = None,
    order: Annotated[str, "VOTES, RANKING, NEWEST, or FEATURED_AT"] = "VOTES",
    limit: Annotated[int, "Max results (max 20 per page)"] = 20,
) -> str:
    """Search Product Hunt for featured launches in a topic category.
    Returns products with vote counts, comment counts, ratings, and maker info."""
    query = """
    query($topic: String!, $order: PostsOrder!, $first: Int!, $postedAfter: DateTime, $postedBefore: DateTime) {
      posts(first: $first, order: $order, featured: true, topic: $topic,
            postedAfter: $postedAfter, postedBefore: $postedBefore) {
        totalCount
        edges {
          node {
            name slug tagline website
            votesCount commentsCount reviewsRating
            createdAt featuredAt
            makers { name username headline }
            topics(first: 3) { edges { node { name slug } } }
          }
        }
      }
    }
    """
    variables = {"topic": topic, "order": order, "first": limit}
    if posted_after:
        variables["postedAfter"] = posted_after
    if posted_before:
        variables["postedBefore"] = posted_before

    data = await ph_query(query, variables)
    posts = data["posts"]
    results = {
        "total_count": posts["totalCount"],
        "products": [
            {
                "name": e["node"]["name"],
                "tagline": e["node"]["tagline"],
                "website": e["node"]["website"],
                "votes": e["node"]["votesCount"],
                "comments": e["node"]["commentsCount"],
                "rating": e["node"]["reviewsRating"],
                "created": e["node"]["createdAt"],
                "featured": e["node"]["featuredAt"],
                "makers": [m["name"] for m in e["node"]["makers"]],
                "topics": [t["node"]["name"] for t in e["node"]["topics"]["edges"]],
            }
            for e in posts["edges"]
        ],
    }
    return json.dumps(results, indent=2)


@tool
async def get_producthunt_product_detail(
    slug: Annotated[str, "Product Hunt slug (from URL, e.g., 'cursor-2')"],
) -> str:
    """Get detailed info about a Product Hunt product including comments.
    Use this to deep-dive into a specific launch after finding it via search."""
    query = """
    query($slug: String!) {
      post(slug: $slug) {
        name tagline description website
        votesCount commentsCount reviewsRating
        createdAt featuredAt
        makers { name username headline twitterUsername
          madePosts(first: 5) { totalCount edges { node { name votesCount } } }
        }
        comments(first: 20, order: VOTES_COUNT) {
          totalCount
          edges {
            node {
              body createdAt votesCount
              user { name username headline }
              replies(first: 3) { edges { node { body user { name } } } }
            }
          }
        }
        topics(first: 10) { edges { node { name slug postsCount followersCount } } }
      }
    }
    """
    data = await ph_query(query, {"slug": slug})
    post = data["post"]

    result = {
        "name": post["name"],
        "tagline": post["tagline"],
        "description": post["description"],
        "website": post["website"],
        "votes": post["votesCount"],
        "comments_count": post["commentsCount"],
        "rating": post["reviewsRating"],
        "created": post["createdAt"],
        "featured": post["featuredAt"],
        "makers": [
            {
                "name": m["name"],
                "username": m["username"],
                "headline": m["headline"],
                "twitter": m["twitterUsername"],
                "total_products": m["madePosts"]["totalCount"],
                "top_products": [
                    {"name": p["node"]["name"], "votes": p["node"]["votesCount"]}
                    for p in m["madePosts"]["edges"]
                ],
            }
            for m in post["makers"]
        ],
        "topics": [
            {"name": t["node"]["name"], "slug": t["node"]["slug"],
             "posts": t["node"]["postsCount"], "followers": t["node"]["followersCount"]}
            for t in post["topics"]["edges"]
        ],
        "top_comments": [
            {
                "body": c["node"]["body"][:400],
                "votes": c["node"]["votesCount"],
                "author": c["node"]["user"]["name"],
                "author_headline": c["node"]["user"]["headline"],
                "replies_count": len(c["node"]["replies"]["edges"]),
            }
            for c in post["comments"]["edges"]
        ],
    }
    return json.dumps(result, indent=2)


@tool
async def discover_producthunt_topics(
    limit: Annotated[int, "Max topics to return"] = 30,
) -> str:
    """List Product Hunt topics sorted by follower count.
    Use this to discover which categories to scan for traction signals."""
    query = """
    query($first: Int!) {
      topics(first: $first, order: FOLLOWERS_COUNT) {
        edges { node { name slug postsCount followersCount description } }
      }
    }
    """
    data = await ph_query(query, {"first": limit})
    topics = [
        {
            "name": e["node"]["name"],
            "slug": e["node"]["slug"],
            "posts": e["node"]["postsCount"],
            "followers": e["node"]["followersCount"],
            "description": e["node"]["description"][:150],
        }
        for e in data["topics"]["edges"]
    ]
    return json.dumps(topics, indent=2)
```

---

## 10. Key Gotchas

| Gotcha | Impact | Workaround |
|---|---|---|
| `reviewsCount` does not exist | Can't count reviews separately | Use `reviewsRating` as quality proxy |
| `productLinks` not in schema | No app store links | Scrape from website URL if needed |
| `makers` is an array, not a connection | No pagination on makers | Fine — products rarely have >10 makers |
| `topic` filter takes slug not name | `"developer-tools"` not `"Developer Tools"` | Use `discover_producthunt_topics` tool first |
| No `url` filter on `posts` query | Can't search by product website | Use `post(slug: ...)` for direct lookup |
| `isVoted`/`isCollected` always false | Useless with client credentials | Ignore these fields |
| No full-text search on posts | Can't search by keyword in name/tagline | Filter by topic + date range, then keyword-filter client-side |
| Default `posts` returns today only | Misses historical data | Always pass `postedAfter`/`postedBefore` |
| `User.followersCount` not a scalar | Need connection query for count | Use `followers { totalCount }` |

---

## 11. Traction Scoring for Product Hunt

| Signal | Weight | Source |
|---|---|---|
| `votesCount` (relative to daily average) | 3x | `posts` query |
| `commentsCount / votesCount` ratio | 3x | `posts` query — high ratio = genuine engagement |
| Comments containing expansion signals ("can it do X?") | 4x | `comments` query + keyword scan |
| `reviewsRating >= 4.5` | 2x | `post` query |
| `featuredAt != null` | 2x | `posts` query — editorial selection |
| Maker serial launch history | 2x | `user.madePosts` — repeat success signal |
| Topic `followersCount` | 1x | `topics` query — market size proxy |
| Comment quality (verified makers, detailed feedback) | 2x | `comments` + `user.headline` analysis |

---

## LangGraph Agent Tool Summary

| Tool | Description | Query Used |
|---|---|---|
| `search_producthunt_launches` | Scan featured products by topic + date range | `posts` with filters |
| `get_producthunt_product_detail` | Deep-dive: comments, makers, topics | `post(slug:)` with nested connections |
| `discover_producthunt_topics` | Find relevant topic categories | `topics` sorted by followers |
| `analyze_maker_track_record` | Check if makers are serial founders | `user` with `madePosts` history |

**Auth:** `PRODUCTHUNT_TOKEN` env var (Developer Token).
**Library:** `httpx` (async HTTP client) — no PH-specific SDK needed.
**Rate budget:** ~300-600 queries per 15 minutes — generous for a traction scan.
