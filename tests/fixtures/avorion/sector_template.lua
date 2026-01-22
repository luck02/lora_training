function SectorTemplate.getProbabilityWeight(x, y)
    return 5
end

function SectorTemplate.contents(x, y)
    local seed = Seed(string.join({GameSeed(), x, y, "basic"}, "-"))
    math.randomseed(seed)

    local contents = {ships = 0, stations = 0, seed = tostring(seed)}

    return contents, math.random()
end

function SectorTemplate.generate(player, seed, x, y)
    local contents, random = SectorTemplate.contents(x, y)

    -- Generate entities in sector
    local generator = SectorGenerator(x, y)
    generator:createEntities()
end

return SectorTemplate