# Rate limiter

A rate limiter built using FastAPI, Redis, and Lua, supporting both fixed window and sliding window strategies with atomic enforcement.

---

## How It Works

When a user hits an API endpoint, the redis client sends a SHA key ( preloaded during application startup ) that accesses the cached lua script to keep it in O(1) ; thereby not having to load the script every time a user makes a request.

The script is then run atomically to prevent race conditions and to enable multiple concurrent workers that are trying to hit the endpoint at the same time.

The fixed and sliding window approaches have been implemented, although the latter is vastly more precise since it enforces rate limits over a rolling time-window rather than using fixed buckets.

<br><br>
Rate limit set = 10<br>
Window = 60 seconds.

## Endpoints

- These can be run on postman to hit the endpoint

### Fixed Window

```
GET /fixed_limit/{user_id}

```

### Sliding Window

```
GET /sliding_limit/{user_id}

```

## Running the Project

clone the repo and docker build :

```bash
git clone <repo-url>
cd rate-limiter
docker-compose up -d
```

API available at:

```
http://localhost:8001
```
