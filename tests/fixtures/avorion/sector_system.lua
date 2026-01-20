-- Avorion sector coordinate and entity management
function getSectorEntities(sector, radius)
    local entities = {}
    local coords = sector:getCoordinates()
    
    -- Find entities in nearby sectors
    for x = coords.x - radius, coords.x + radius do
        for y = coords.y - radius, coords.y + radius do
            for z = coords.z - radius, coords.z + radius do
                local nearbySector = Sector:getSector(x, y, z)
                if nearbySector then
                    local sectorEntities = nearbySector:getEntities()
                    for _, entity in ipairs(sectorEntities) do
                        table.insert(entities, entity)
                    end
                end
            end
        end
    end
    
    return entities
end

function createAsteroidField(sector, center, radius, count)
    local field = {}
    
    for i = 1, count do
        local position = Vector3(
            center.x + math.random(-radius, radius),
            center.y + math.random(-radius, radius),
            center.z + math.random(-radius, radius)
        )
        
        local asteroid = sector:createEntity("Asteroid")
        asteroid:setPosition(position)
        asteroid:setSize(math.random(10, 50))
        
        table.insert(field, asteroid)
    end
    
    return field
end

function getSectorStatus(sector)
    local status = {}
    status.coordinates = sector:getCoordinates()
    status.entityCount = sector:getEntityCount()
    status.activeShips = sector:getActiveShips()
    status.resourceDensity = sector:getResourceDensity()
    
    return status
end