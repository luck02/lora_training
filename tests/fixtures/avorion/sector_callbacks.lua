-- Sector initialization
function Sector.onInitialize()
    print("Sector initialized")
    Sector():addScriptOnce("data/scripts/sector/sector_events.lua", "sector_events.lua")
end

-- Sector cleanup
function Sector.onDestroy()
    print("Sector destroyed")
    -- Cleanup resources
end

-- Sector event handler
function Sector.onEvent(eventType, eventData)
    if eventType == "player_enter" then
        -- Handle player entering sector
        handlePlayerEnter(eventData.player)
    elseif eventType == "enemy_spawn" then
        -- Handle enemy spawning
        spawnEnemy(eventData.enemyType)
    end
end