function spawnPirateShip(sector, position)
    local ship = sector:createEntity("Ship")
    ship:setPosition(position)
    ship:setTitle("Pirate Ship")
    ship:setFaction("Pirates")

    -- Add turrets
    local turret = ship:addTurret("Railgun")
    turret:setCooldown(2.0)

    return ship
end

function getShipInfo(entity)
    local info = {}
    info.shipType = entity:getType()
    info.position = entity:getPosition()
    info.hull = entity:getHull()
    info.shield = entity:getShield()
    info.faction = entity:getFaction()

    return info
end

function updateShipAI(ship)
    if not ship:isValid() then return end

    local target = ship:getClosestEnemy()
    if target then
        local direction = target:getPosition() - ship:getPosition()
        ship:rotateTowards(direction)
        ship:fireWeapon()
    end
end