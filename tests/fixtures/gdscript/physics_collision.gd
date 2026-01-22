extends Area2D

# Collision signal handler
func _on_body_entered(body):
    if body.has_method("take_damage"):
        body.take_damage(10)
        print("Damage dealt to:", body.name)

    # Play sound effect
    play_collision_sound()

# Handle collision exit
func _on_body_exited(body):
    print("Body exited:", body.name)

# Play collision sound effect
func play_collision_sound():
    # Implementation here
    pass