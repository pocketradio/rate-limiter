---@diagnostic disable: undefined-global


local current_count = redis.call('GET', KEYS[1])
-- keys[1 ] is the user key. currentcount gets value of the key from the redis DB.

local limit = tonumber(ARGV[1])

if current_count and tonumber(current_count) >=limit then
    return 0
end

current_count = redis.call('INCR', KEYS[1]) -- on first call this adds the key to redis with value 1. subseq calls -> incr value by 1

if current_count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
    -- initializes the time counter for this specific key ( argv[2] is window seconds in main.py)
end

return current_count