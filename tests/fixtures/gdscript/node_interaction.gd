extends Node

# Signal for when player enters area
signal player_entered_area(player)

# Called when the node enters the scene tree for the first time.
func _ready():
    # Connect signals
    connect("player_entered_area", self, "_on_player_entered_area")

# Handle player entering area
func _on_player_entered_area(player):
    print("Player entered area:", player.name)
    # Activate some functionality
    activate_area()

# Activate the area functionality
func activate_area():
    # Implementation here
    pass