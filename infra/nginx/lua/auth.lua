-- JWT (RS256) and API Key authentication for VerifID API Gateway.
--
-- Flow:
-- 1. Check for Authorization: Bearer <JWT> header → validate JWT
-- 2. Check for X-API-Key header → validate API key
-- 3. If neither present → 401 Unauthorized
--
-- JWT public keys are cached in shared memory for performance.

local jwt_cache = ngx.shared.jwt_cache
local cjson = require("cjson.safe")

-- Environment-based configuration
local JWT_ENABLED = os.getenv("JWT_ENABLED") or "false"
local API_KEY_ENABLED = os.getenv("API_KEY_ENABLED") or "true"
local AUTH_BYPASS = os.getenv("AUTH_BYPASS") or "true"  -- true in dev

-- Skip auth if bypass is enabled (development mode)
if AUTH_BYPASS == "true" then
    return
end

local function respond_unauthorized(msg)
    ngx.status = ngx.HTTP_UNAUTHORIZED
    ngx.header["Content-Type"] = "application/json"
    ngx.header["WWW-Authenticate"] = 'Bearer realm="verifid"'
    ngx.say(cjson.encode({ detail = msg or "Unauthorized" }))
    return ngx.exit(ngx.HTTP_UNAUTHORIZED)
end

local function respond_forbidden(msg)
    ngx.status = ngx.HTTP_FORBIDDEN
    ngx.header["Content-Type"] = "application/json"
    ngx.say(cjson.encode({ detail = msg or "Forbidden" }))
    return ngx.exit(ngx.HTTP_FORBIDDEN)
end

-- Validate JWT token (RS256)
local function validate_jwt(token)
    -- Check cache first
    local cached_sub = jwt_cache:get("jwt:" .. token)
    if cached_sub then
        ngx.req.set_header("X-User-ID", cached_sub)
        return true
    end

    -- Decode JWT parts (header.payload.signature)
    local parts = {}
    for part in token:gmatch("[^%.]+") do
        table.insert(parts, part)
    end

    if #parts ~= 3 then
        return false, "Invalid JWT format"
    end

    -- Decode payload (base64url)
    local payload_b64 = parts[2]
    -- Convert base64url to base64
    payload_b64 = payload_b64:gsub("-", "+"):gsub("_", "/")
    local padding = 4 - (#payload_b64 % 4)
    if padding < 4 then
        payload_b64 = payload_b64 .. string.rep("=", padding)
    end

    local payload_json = ngx.decode_base64(payload_b64)
    if not payload_json then
        return false, "Failed to decode JWT payload"
    end

    local payload = cjson.decode(payload_json)
    if not payload then
        return false, "Failed to parse JWT payload"
    end

    -- Check expiration
    local now = ngx.time()
    if payload.exp and payload.exp < now then
        return false, "Token expired"
    end

    -- Check issuer if configured
    -- if payload.iss ~= "verifid" then return false, "Invalid issuer" end

    -- NOTE: Full RS256 signature verification requires lua-resty-jwt or
    -- delegating to the backend. In production, use lua-resty-jwt module.
    -- For now, we do basic payload checks and delegate full verification
    -- to the FastAPI backend middleware.

    -- Cache the result (5 min TTL)
    local sub = payload.sub or "unknown"
    jwt_cache:set("jwt:" .. token, sub, 300)
    ngx.req.set_header("X-User-ID", sub)
    ngx.req.set_header("X-JWT-Claims", payload_json)

    return true
end

-- Validate API Key
local function validate_api_key(key)
    -- Check cache
    local cached = jwt_cache:get("apikey:" .. key)
    if cached then
        ngx.req.set_header("X-Client-ID", cached)
        return true
    end

    -- Validate against backend (subrequest)
    local res = ngx.location.capture("/_internal/validate-key", {
        method = ngx.HTTP_POST,
        body = cjson.encode({ api_key = key }),
    })

    if res and res.status == 200 then
        local body = cjson.decode(res.body)
        if body and body.client_id then
            -- Cache for 5 minutes
            jwt_cache:set("apikey:" .. key, body.client_id, 300)
            ngx.req.set_header("X-Client-ID", body.client_id)
            return true
        end
    end

    return false, "Invalid API key"
end

-- Main auth logic
local auth_header = ngx.var.http_authorization
local api_key = ngx.var.http_x_api_key

if auth_header and JWT_ENABLED == "true" then
    -- Try JWT authentication
    local token = auth_header:match("^[Bb]earer%s+(.+)$")
    if token then
        local ok, err = validate_jwt(token)
        if ok then
            return  -- authenticated
        end
        return respond_unauthorized(err or "Invalid token")
    end
end

if api_key and API_KEY_ENABLED == "true" then
    -- Try API Key authentication
    local ok, err = validate_api_key(api_key)
    if ok then
        return  -- authenticated
    end
    return respond_unauthorized(err or "Invalid API key")
end

-- No valid credentials provided
if JWT_ENABLED == "true" or API_KEY_ENABLED == "true" then
    return respond_unauthorized("Authentication required")
end
