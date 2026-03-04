-- Circuit breaker response tracking (log_by_lua_file).
--
-- Records upstream response status codes and updates circuit state.

local shared = ngx.shared.circuit_breaker

local WINDOW_SECONDS = 30
local FAILURE_THRESHOLD = 0.50
local MIN_REQUESTS = 5

local function get_circuit_key()
    return "cb:verifid_api"
end

local key = get_circuit_key()
local status = ngx.var.upstream_status

if not status then
    return
end

local status_code = tonumber(status) or 0
local is_error = status_code >= 500

local now = ngx.time()
local window_key = key .. ":window:" .. tostring(math.floor(now / WINDOW_SECONDS))

-- Increment counters
local total_key = window_key .. ":total"
local error_key = window_key .. ":errors"

local total = shared:incr(total_key, 1, 0)
if total == 1 then
    shared:expire(total_key, WINDOW_SECONDS * 2)
end

if is_error then
    local errors = shared:incr(error_key, 1, 0)
    if errors == 1 then
        shared:expire(error_key, WINDOW_SECONDS * 2)
    end
end

-- Evaluate circuit state
local state = shared:get(key .. ":state") or "closed"

if state == "half_open" then
    if is_error then
        -- Probe failed → reopen circuit
        shared:set(key .. ":state", "open")
        shared:set(key .. ":open_since", now)
        ngx.log(ngx.WARN, "circuit_breaker: probe failed, reopening circuit")
    else
        -- Probe succeeded → close circuit
        shared:set(key .. ":state", "closed")
        ngx.log(ngx.INFO, "circuit_breaker: probe succeeded, closing circuit")
    end
elseif state == "closed" then
    total = shared:get(total_key) or 0
    local errors = shared:get(error_key) or 0

    if total >= MIN_REQUESTS then
        local error_rate = errors / total
        if error_rate >= FAILURE_THRESHOLD then
            shared:set(key .. ":state", "open")
            shared:set(key .. ":open_since", now)
            ngx.log(ngx.ERR, "circuit_breaker: OPENING circuit, error_rate=", error_rate)
        end
    end
end
