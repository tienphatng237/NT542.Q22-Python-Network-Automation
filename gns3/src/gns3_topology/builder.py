from gns3_topology.api_client import (
    connect_nodes,
    create_drawing,
    create_node,
    create_project,
    delete_drawing,
    delete_link,
    delete_node,
    find_project_by_name,
    get_project_drawings,
    get_templates,
    get_project_links,
    get_project_nodes,
    open_project,
    update_node,
)
from gns3_topology.settings import (
    ETHERNET_SWITCH_SYMBOL,
    PC_TEMPLATE_HINTS,
    PROJECT_NAME,
    ROUTER_SYMBOL,
    ROUTER_TEMPLATE_HINTS,
    SWITCH_TEMPLATE_HINTS,
    VPCS_SYMBOL,
)
from gns3_topology.topology_plan import (
    MANAGED_DRAWING_TAG,
    build_layer_drawings,
    build_links,
    build_node_specs,
    find_template,
)


class PortAllocator:
    def __init__(self, node_name, ports, used_ports=None):
        self.node_name = node_name
        used_ports = used_ports or set()
        self.available_ports = [
            port
            for port in sorted(
                ports,
                key=lambda port: (port["adapter_number"], port["port_number"]),
            )
            if (port["adapter_number"], port["port_number"]) not in used_ports
        ]

    def allocate(self):
        if not self.available_ports:
            raise RuntimeError(f"No free ports left on node '{self.node_name}'")

        port = self.available_ports.pop(0)
        return (
            port["adapter_number"],
            port["port_number"],
            port.get("short_name") or port.get("name", "unknown"),
        )


def link_key(left_name, right_name):
    return tuple(sorted((left_name, right_name)))


def build_link_inventory(project_id, node_id_to_name):
    links_by_key = {}

    for link in get_project_links(project_id):
        endpoints = []
        for endpoint in link["nodes"]:
            node_name = node_id_to_name.get(endpoint["node_id"])
            if node_name:
                endpoints.append(node_name)

        if len(endpoints) == 2:
            links_by_key[link_key(endpoints[0], endpoints[1])] = link

    return links_by_key


def get_or_create_project():
    project = find_project_by_name(PROJECT_NAME)
    if project:
        project = open_project(project["project_id"])
        print(f"Using existing project: {PROJECT_NAME}")
        return project

    project = create_project(PROJECT_NAME)
    print(f"Created project: {PROJECT_NAME}")
    return project


def desired_symbol(kind):
    if kind == "router":
        return ROUTER_SYMBOL
    if kind == "switch":
        return ETHERNET_SWITCH_SYMBOL
    if kind == "pc":
        return VPCS_SYMBOL
    return None


def build_existing_state(project_id):
    nodes = {}
    node_id_to_name = {}

    for node in get_project_nodes(project_id):
        node_name = node["name"]
        if node_name in nodes:
            print(f"Skipping duplicate node name in project: {node_name}")
            continue

        nodes[node_name] = node
        node_id_to_name[node["node_id"]] = node_name

    used_ports = {node_name: set() for node_name in nodes}
    existing_links = set()

    for link in get_project_links(project_id):
        endpoints = []
        for endpoint in link["nodes"]:
            node_name = node_id_to_name.get(endpoint["node_id"])
            if not node_name:
                continue

            used_ports.setdefault(node_name, set()).add(
                (endpoint["adapter_number"], endpoint["port_number"])
            )
            endpoints.append(node_name)

        if len(endpoints) == 2:
            existing_links.add(link_key(endpoints[0], endpoints[1]))

    return nodes, existing_links, used_ports


def remove_extra_nodes(project_id, desired_names):
    removed_any = False
    for node in get_project_nodes(project_id):
        if node["name"] not in desired_names:
            delete_node(project_id, node["node_id"])
            print(f"Removed extra node: {node['name']}")
            removed_any = True

    return removed_any


def remove_extra_links(project_id, desired_link_keys):
    nodes = get_project_nodes(project_id)
    node_id_to_name = {node["node_id"]: node["name"] for node in nodes}
    links_by_key = build_link_inventory(project_id, node_id_to_name)

    removed_any = False
    for current_link_key, link in links_by_key.items():
        if current_link_key not in desired_link_keys:
            delete_link(project_id, link["link_id"])
            print(f"Removed extra link: {current_link_key[0]} <-> {current_link_key[1]}")
            removed_any = True

    return removed_any


def reconcile_managed_drawings(project_id, node_specs):
    for drawing in get_project_drawings(project_id):
        if MANAGED_DRAWING_TAG in drawing.get("svg", ""):
            delete_drawing(project_id, drawing["drawing_id"])
            print("Removed managed drawing")

    for drawing in build_layer_drawings(node_specs):
        create_drawing(project_id, drawing["x"], drawing["y"], drawing["svg"], drawing["z"])
        print("Created managed drawing")


def create_topology():
    templates = get_templates()
    available_template_names = [template.get("name", "") for template in templates]
    router_template = find_template(templates, ROUTER_TEMPLATE_HINTS)
    switch_template = find_template(templates, SWITCH_TEMPLATE_HINTS)
    pc_template = find_template(templates, PC_TEMPLATE_HINTS)

    if not router_template:
        raise RuntimeError(
            f"Router template not found. Update ROUTER_TEMPLATE_HINTS in settings.py. "
            f"Current hints: {ROUTER_TEMPLATE_HINTS}. "
            f"Available templates: {available_template_names}"
        )

    if not switch_template:
        raise RuntimeError(
            f"Switch template not found. Update SWITCH_TEMPLATE_HINTS in settings.py. "
            f"Current hints: {SWITCH_TEMPLATE_HINTS}. "
            f"Available templates: {available_template_names}"
        )

    if not pc_template:
        raise RuntimeError(
            f"PC template not found. Update PC_TEMPLATE_HINTS in settings.py. "
            f"Current hints: {PC_TEMPLATE_HINTS}. "
            f"Available templates: {available_template_names}"
        )

    project = get_or_create_project()
    project_id = project["project_id"]

    print(f"Router template: {router_template['name']}")
    print(f"Switch template: {switch_template['name']}")
    print(f"PC template: {pc_template['name']}")

    desired_specs = build_node_specs()
    desired_node_names = {spec["name"] for spec in desired_specs}
    desired_link_keys = {link_key(left_name, right_name) for left_name, right_name in build_links()}

    remove_extra_nodes(project_id, desired_node_names)
    remove_extra_links(project_id, desired_link_keys)

    nodes, existing_links, used_ports = build_existing_state(project_id)
    for spec in desired_specs:
        if spec["name"] in nodes:
            current_node = nodes[spec["name"]]
            desired_x = spec["x"]
            desired_y = spec["y"]
            desired_node_symbol = desired_symbol(spec["kind"])
            needs_update = (
                current_node.get("x") != desired_x
                or current_node.get("y") != desired_y
                or current_node.get("symbol") != desired_node_symbol
            )

            if needs_update:
                updated_node = update_node(
                    project_id,
                    current_node["node_id"],
                    x=desired_x,
                    y=desired_y,
                    symbol=desired_node_symbol,
                )
                nodes[spec["name"]] = updated_node
                print(f"Updated node layout: {spec['name']}")

            print(f"Keep node: {spec['name']}")
            continue

        if spec["kind"] == "router":
            template = router_template
        elif spec["kind"] == "switch":
            template = switch_template
        else:
            template = pc_template

        created_node = create_node(project_id, template, spec["name"], spec["x"], spec["y"])
        nodes[spec["name"]] = created_node
        used_ports.setdefault(spec["name"], set())
        print(f"Created node: {spec['name']}")

    nodes, existing_links, used_ports = build_existing_state(project_id)

    allocators = {
        node_name: PortAllocator(node_name, node["ports"], used_ports.get(node_name))
        for node_name, node in nodes.items()
    }

    for left_name, right_name in build_links():
        if link_key(left_name, right_name) in existing_links:
            print(f"Keep link: {left_name} <-> {right_name}")
            continue

        left_node = nodes[left_name]
        right_node = nodes[right_name]

        left_adapter, left_port, left_port_name = allocators[left_name].allocate()
        right_adapter, right_port, right_port_name = allocators[right_name].allocate()

        connect_nodes(
            project_id,
            left_node["node_id"],
            left_adapter,
            left_port,
            right_node["node_id"],
            right_adapter,
            right_port,
        )
        print(
            f"Linked {left_name} ({left_port_name}) "
            f"<-> {right_name} ({right_port_name})"
        )
        existing_links.add(link_key(left_name, right_name))

    reconcile_managed_drawings(project_id, desired_specs)
    print("Topology ready: 2 core routers, 2 distribution routers, 6 access switches, 6 PCs.")


def main():
    create_topology()
