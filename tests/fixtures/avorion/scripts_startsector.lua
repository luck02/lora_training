
package.path = package.path .. ";data/scripts/lib/?.lua"
package.path = package.path .. ";data/scripts/?.lua"

local SectorGenerator = include ("SectorGenerator")
local Placer = include("placer")
local FactoryPredictor = include("factorypredictor")
local ShipGenerator = include("shipgenerator")
local SectorTemplate = {}

function SectorTemplate.contents(x, y)
    local seed = Seed(string.join({GameSeed(), x, y, "startsector"}, "-"))
    math.randomseed(seed);

    local random = random()
    local contents = {ships = 0, stations = 0, seed = tostring(seed)}

    contents.mines = 1
    contents.equipmentDocks = 1
    contents.resourceDepots = 1
    contents.shipyards = 1
    contents.repairDocks = 1

    -- create ships
    contents.defenders = 5

    contents.ships = contents.defenders
    contents.stations = 5

    return contents, random
end

-- player is the player who triggered the creation of the sector (only set in start sector, otherwise nil)
function SectorTemplate.generate(player, seed, x, y)
    math.randomseed(seed)

    local generator = SectorGenerator(x, y)

    -- create an early ally of the player
    local faction = Galaxy():getNearestFaction(x, y)

    -- create asteroid fields
    for i = 1, 2 do
        local mat = generator:createAsteroidField()
        if math.random() < 0.5 then generator:createStash(mat) end
    end

    -- create big asteroids
    local numSmallFields = math.random(4, 10)
    for i = 1, numSmallFields do
        generator:createSmallAsteroidField()
    end

    generator:createShipyard(faction)
    generator:createRepairDock(faction)
    local station = generator:createEquipmentDock(faction)
    station:removeScript("data/scripts/entity/merchants/fightermerchant.lua")

    -- create an asteroid field with a resource trader inside it, the player will spawn here and immediately have something to mine
    local mat = generator:createAsteroidField()
    local station = generator:createStation(faction, "data/scripts/entity/merchants/resourcetrader.lua");
    station.position = mat

    -- create a mine in the start sector
    -- doesn't have to be predicted by factory map, since it will be the first sector generated
    -- in a multiplayer aspect with differing home sector, predicting where the next home sector might be is impossible anyways
    local productions = FactoryPredictor.generateMineProductions(x, y, 1)

    local station = generator:createStation(faction, "data/scripts/entity/merchants/factory.lua", productions[1])
    local mat = generator:createAsteroidField()
    station.position = mat
    station:addScriptOnce("data/scripts/entity/merchants/consumer.lua", "Mine /*station type*/"%_T,
                          "Mining Robot",
                          "Medical Supplies",
                          "Antigrav Unit",
                          "Fusion Generator",
                          "Acid",
                          "Drill")

    -- create a big asteroid
    local mat = generator:createAsteroidField()
    local asteroid = generator:createClaimableAsteroid()
    asteroid.position = mat

    for i = 1, 5 do
        ShipGenerator.createDefender(faction, generator:getPositionInSector())
    end

    generator:createGates()

    Sector():addScriptOnce("data/scripts/sector/eventscheduler.lua", "events/pirateattack.lua")
    Sector():addScript("data/scripts/sector/background/respawnresourceasteroids.lua")

    generator:addAmbientEvents()
    Sector():removeScript("factionwar/initfactionwar.lua")

    if GameSettings().difficulty <= Difficulty.Normal then
        Sector():addScript("data/scripts/sector/neutralzone.lua")
    end

    Placer.resolveIntersections()
    generator:deleteObjectsFromDockingPositions()

    return {defenders = 5}
end

-- called by respawndefenders.lua
function SectorTemplate.getDefenders(contents, x, y)
    local faction = Galaxy():getNearestFaction(x, y)
    return faction.index, contents.defenders
end

return SectorTemplate
