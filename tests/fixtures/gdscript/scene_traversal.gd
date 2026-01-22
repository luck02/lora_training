extends Node

# Find all children of a specific type
func find_children_by_type(parent_node, node_type):
    var found_nodes = []
    for child in parent_node.get_children():
        if child is node_type:
            found_nodes.append(child)
        # Recursively search children
        found_nodes.append_array(find_children_by_type(child, node_type))
    return found_nodes

# Get the root node of the scene
func get_scene_root():
    return get_tree().get_root()

# Find a specific node by name
func find_node_by_name(name):
    return find_node(name, true, false)