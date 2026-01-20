-- Player interaction and callback handling in Avorion
function onPlayerJoin(player)
    print("Player joined: " .. player:getTitle())
    
    -- Set up initial ship
    local ship = player:getShip()
    if ship then
        ship:setHull(100)
        ship:setShield(50)
    end
    
    -- Send welcome message
    player:sendChatMessage("Welcome to the server!")
end

function onPlayerCommand(player, command, args)
    if command == "spawn" then
        local entityType = args[1] or "Ship"
        local position = player:getPosition()
        
        local entity = player:getSector():createEntity(entityType)
        entity:setPosition(position)
        entity:setTitle(player:getTitle() .. "'s " .. entityType)
        
        return entity
    elseif command == "info" then
        local ship = player:getShip()
        if ship then
            local info = {
                hull = ship:getHull(),
                shield = ship:getShield(),
                position = ship:getPosition(),
                faction = ship:getFaction()
            }
            return info
        end
    end
    
    return nil
end

function registerPlayerCallbacks()
    -- Register callbacks for player events
    Player:onJoin(function(player)
        onPlayerJoin(player)
    end)
    
    Player:onCommand(function(player, command, args)
        return onPlayerCommand(player, command, args)
    end)
end