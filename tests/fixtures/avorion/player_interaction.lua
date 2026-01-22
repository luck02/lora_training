-- Player connection handler
function Player.onConnect(player)
    print("Player connected: " .. player:getName())

    -- Initialize player data
    player:setAttribute("health", 100)
    player:setAttribute("energy", 50)
end

-- Player disconnect handler
function Player.onDisconnect(player)
    print("Player disconnected: " .. player:getName())

    -- Save player data
    savePlayerData(player)
end

-- Player command handler
function Player.onCommand(player, command, args)
    if command == "heal" then
        player:setAttribute("health", 100)
        player:sendChatMessage("You have been healed!")
    elseif command == "spawn_ship" then
        spawnPlayerShip(player, args.ship_type)
    end
end