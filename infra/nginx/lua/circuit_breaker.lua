-- Circuit breaker for upstream services.
--
-- States:
--   CLOSED   → requests pass through normally
--   OPEN     → requests rejected with 503 (upstream known to be down)
--   HALF_OPEN → one probe request allowed to test recovery
--
-- Configuration:
--   failure_threshold: 50% error rate in 30s window → open circuit
--   recovery_timeout: 15s in OPEN before transitioning to HALF_OPEN

local cjson = require("cjson.safe")
local shared = ngx.shared.circuit_breaker

-- Configuration
local WINDOW_SECONDS = 30
local FAILURE_THRESHOLD = 0.50  -- 50% failure rate
local RECOVERY_TIMEOUT = 15     -- seconds before half-open
local MIN_REQUESTS = 5          -- minimum requests before evaluating

local function get_circuit_key()
    return "cb:verifid_api"
end

local function respond_service_unavailable()
    ngx.status = 503
    ngx.header["Content-Type"] = "application/json"
    ngx.header["Retry-After"] = tostring(RECOVERY_TIMEOUT)
    ngx.say(cjson.encode({
        detail = "Service temporarily unavailable (circuit breaker open)",
        retry_after = RECOVERY_TIMEOUT,
    }))
    return ngx.exit(503)
end

-- Get current circuit state
local key = get_circuit_key()
local state = shared:get(key .. ":state") or "closed"
local open_since = shared:get(key .. ":open_since") or 0

if state == "open" then
    local now = ngx.time()
    if now - open_since >= RECOVERY_TIMEOUT then
        -- Transition to half-open: allow one probe request
        shared:set(key .. ":state", "half_open")
        ngx.log(ngx.WARN, "circuit_breaker: transitioning to HALF_OPEN")
    else
        return respond_service_unavailable()
    end
end

-- For closed and half-open states, let the request through.
-- The log_by_lua phase will record the result.
-- (Response tracking is handled in a separate log phase script)
