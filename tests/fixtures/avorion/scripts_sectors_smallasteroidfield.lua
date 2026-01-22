
package.path = package.path .. ";data/scripts/lib/?.lua"
package.path = package.path .. ";data/scripts/?.lua"

local OperationExodus = include ("story/operationexodus")
local SectorGenerator = include ("SectorGenerator")
local Placer = include("placer")
include("music")

local SectorTemplate = {}

-- must be defined, will be used to get the probability of this sector
function SectorTemplate.getProbabilityWeight(x, y, seed, factionIndex, innerArea)
    if factionIndex then
        if innerArea then
            return 250
        else
            return 200
        end
    else
        return 250
    end
end

function SectorTemplate.offgrid(x, y)
    return true
end

-- this function returns whether or not a sector should have space gates
function SectorTemplate.gates(x, y)
    return false
end

function SectorTemplate.contents(x, y)
    local seed = Seed(string.join({GameSeed(), x, y, "smallasteroidfield"}, "-"))
    math.randomseed(seed)

    local random = random()

    local contents = {ships = 0, stations = 0, seed = tostring(seed)}
    contents.resourceAsteroids = random:getInt(0, 2)
    local maximum = random:getInt(0, 1)
    contents.claimableAsteroids = random:multitest(maximum, 0.33)

    local generator = SectorGenerator(x, y)
    contents.asteroidEstimation = generator:estimateAsteroidNumbers(2.5 + contents.resourceAsteroids + contents.claimableAsteroids, 5)

    return contents, random
end

function SectorTemplate.musicTracks()
    local good = {
        primary = combine(TrackCollection.Neutral(), TrackCollection.Desolate()),
        secondary = combine(TrackCollection.Happy(), TrackCollection.Neutral()),
    }

    local neutral = {
        primary = combine(TrackCollection.Neutral(), TrackCollection.Desolate()),
        secondary = TrackCollection.All(),
    }

    local bad = {
        primary = combine(TrackCollection.Middle(), TrackCollection.Desolate()),
        secondary = TrackCollection.Neutral(),
    }

    return good, neutral, bad
end

-- player is the player who triggered the creation of the sector (only set in start sector, otherwise nil)
function SectorTemplate.generate(player, seed, x, y)
    local contents, random = SectorTemplate.contents(x, y)

    local generator = SectorGenerator(x, y)

    -- create filled asteroids
    local numFields = random:getInt(0, 2)

    for i = 1, numFields do
        generator:createAsteroidField(0.1);
    end

    for i = 1, contents.resourceAsteroids do
        local position = generator:createAsteroidField()
        generator:createBigAsteroid(position)
    end

    local numSmallFields = random:getInt(1, 5)
    for i = 1, numSmallFields do
        generator:createSmallAsteroidField()
    end

    -- create empty asteroids
    local numFields = random:getInt(1, 2)

    for i = 1, numFields do
        generator:createEmptyAsteroidField();
    end

    local numAsteroids = random:getInt(1, 2)
    for i = 1, numAsteroids do
        generator:createEmptyBigAsteroid();
    end

    local numSmallFields = random:getInt(1, 2)
    for i = 1, numSmallFields do
        generator:createEmptySmallAsteroidField()
    end

    for i = 1, contents.claimableAsteroids do
        local mat = generator:createAsteroidField()
        local asteroid = generator:createClaimableAsteroid()
        asteroid.position = mat
    end

    OperationExodus.tryGenerateBeacon(generator)

    if random:test(generator:getWormHoleProbability()) then generator:createRandomWormHole() end

    Sector():addScriptOnce("data/scripts/sector/eventscheduler.lua", "events/pirateattack.lua")
    Sector():addScriptOnce("data/scripts/sector/background/respawnresourceasteroids.lua")

    generator:addOffgridAmbientEvents()
    Placer.resolveIntersections()
end

return SectorTemplate
