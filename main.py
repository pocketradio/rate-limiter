from redis import asyncio as redis
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
import time
import aiofiles

REDIS_HOST: str = os.getenv("REDIS_HOST")
RATE_LIMIT = 10
WINDOW_SECONDS = 60
PORT: str = os.getenv("REDIS_PORT")

redis_client = None
lua_script_contents = None
lua_script_hash = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    pool = redis.ConnectionPool(
        host = REDIS_HOST,
        port = int(PORT),
        db = 0
    )
    global redis_client
    global lua_script_contents
    global lua_script_hash
    
    redis_client = redis.Redis(connection_pool=pool)
    
    async with aiofiles.open('./lua_scripts/fixed_window_rate_limit.lua', mode='r') as f:
        lua_script_contents = await f.read()
        
    lua_script_hash = await redis_client.script_load(lua_script_contents) # redis permanently stores the script on the server and returns a SHA1 hash. 
    # so now we only have to send the hash over the network instead of the entire lua script. ( server side cachingg scripts with EVALSHA )
    yield
    
app = FastAPI(lifespan=lifespan)

def key_generation(id):

    current_time = time.time()
    current_time_window = current_time // WINDOW_SECONDS
    
    return f"rate_limit:{id}:{current_time_window}"


@app.get("/limit/{user_id}")
async def send_hash(user_id : int):
    
    user_key = key_generation(id= user_id)
    result = await redis_client.evalsha(lua_script_hash, 1, user_key, RATE_LIMIT, WINDOW_SECONDS  ) # evalsha docs show arguments to be strictly positional, hence.

    if result == 0:
        raise HTTPException(status_code=429, detail='Rate limit reached. goodbye child')

    return{
        "status" : "request allowed yay",
        "count" : result
    }