from redis import asyncio as redis
import os
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
import time
import aiofiles
from redis.exceptions import NoScriptError, RedisError


REDIS_HOST: str = os.getenv("REDIS_HOST")
RATE_LIMIT = 10
WINDOW_SECONDS = 60
REDIS_PORT: str = os.getenv("REDIS_PORT")


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    pool = redis.ConnectionPool(
        host = REDIS_HOST,
        port = int(REDIS_PORT),
        db = 0
    )
    
    redis_client = redis.Redis(connection_pool=pool)
    
    async with aiofiles.open('./lua_scripts/fixed_window_rate_limit.lua', mode='r') as f:
        lua_script_contents_fixed = await f.read()
            
    lua_script_hash_fixed = await redis_client.script_load(lua_script_contents_fixed) # redis permanently stores the script on the server and returns a SHA1 hash. 
    # so now we only have to send the hash over the network instead of the entire lua script. ( server side cachingg scripts with EVALSHA )        
        
    async with aiofiles.open('./lua_scripts/sliding_window_rate_limit.lua', mode= 'r') as f:
        lua_script_contents_sliding = await f.read()
    
    lua_script_hash_sliding = await redis_client.script_load(lua_script_contents_sliding)
    
    
    app.state.redis = redis_client
    app.state.sliding_window_sha = lua_script_hash_sliding
    app.state.fixed_window_sha = lua_script_hash_fixed
    app.state.script_contents_fixed = lua_script_contents_fixed
    
    
    yield
    
    await redis_client.close()
    
    
app = FastAPI(lifespan=lifespan)

def key_generation(user_id):

    current_time = time.time()
    current_time_window = current_time // WINDOW_SECONDS
    
    return f"rate_limit:{user_id}:{current_time_window}"


@app.get("/fixed_limit/{user_id}")
async def rate_limit_check_fixed_window(user_id : int, request: Request):
    
    redis_client = request.app.state.redis
    sha_fixed = request.app.state.fixed_window_sha
    
    user_key = key_generation(user_id= user_id)
    try:
        result = await redis_client.evalsha(sha_fixed, 1, user_key, RATE_LIMIT, WINDOW_SECONDS  ) # evalsha docs show arguments to be strictly positional, hence.

    except NoScriptError:
        sha = await redis_client.script_load(request.app.state.script_contents_fixed)
        request.app.state.fixed_window_sha = sha
        result = await redis_client.evalsha(sha, 1, user_key, RATE_LIMIT, WINDOW_SECONDS)
    except RedisError:
        raise HTTPException(500, "rate limiter unavailable.")
    
    if result == 0:
        raise HTTPException(status_code=429, detail='Rate limit reached. goodbye child')

    return{
        "status" : "request allowed yay",
        "count" : result
    }