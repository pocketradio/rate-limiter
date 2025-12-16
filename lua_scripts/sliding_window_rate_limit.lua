---@diagnostic disable: undefined-global



local now = redis.call('TIME')
local seconds = tonumber(now[1])
local microseconds = tonumber(now[2])

-- [number] since lua returns a table with seconds (1) and microsec (2)

local range = seconds - tonumber(ARGV[2])

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', range)

local count = redis.call('ZCARD', KEYS[1])

if count >= tonumber(ARGV[1]) then
    return -1
else
    redis.call('ZADD', KEYS[1], seconds, "time:" .. seconds .. microseconds) -- both sec and msec needed to prevent hard collisions
end

redis.call('EXPIRE', KEYS[1], tonumber(ARGV[2]))

return count + 1
