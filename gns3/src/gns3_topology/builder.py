from gns3_topology.api_client import (
    build_available_project_name,
    connect_nodes,
    create_node,
    create_project,
    get_templates,
)
from gns3_topology.settings import PROJECT_NAME, ROUTER_TEMPLATE_HINTS, SWITCH_TEMPLATE_HINTS
from gns3_topology.topology_plan import build_links, build_node_specs, find_template


class PortAllocator:
    def __init__(self, node_name, ports):
        self.node_name = node_name
        self.available_ports = sorted(
            ports,
            key=lambda port: (port["adapter_number"], port["port_number"]),
        )

    def allocate(self):
        if not self.available_ports:
            raise RuntimeError(f"No free ports left on node '{self.node_name}'")

        port = self.available_ports.pop(0)
        return (
            port["adapter_number"],
            port["port_number"],
            port.get("short_name") or port.get("name", "unknown"),
        )


def create_topology():
    project_name = build_available_project_name(PROJECT_NAME)

    templates = get_templates()
    available_template_names = [template.get("name", "") for template in templates]
    router_template = find_template(templates, ROUTER_TEMPLATE_HINTS)
    switch_template = find_template(templates, SWITCH_TEMPLATE_HINTS)

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

    project = create_project(project_name)
    project_id = project["project_id"]

    print(f"Created project: {project_name}")
    print(f"Router template: {router_template['name']}")
    print(f"Switch template: {switch_template['name']}")

    nodes = {}
    allocators = {}

    for spec in build_node_specs():
        template = router_template if spec["kind"] == "router" else switch_template
        created_node = create_node(project_id, template, spec["name"], spec["x"], spec["y"])
        nodes[spec["name"]] = created_node
        allocators[spec["name"]] = PortAllocator(spec["name"], created_node["ports"])
        print(f"Created node: {spec['name']}")

    for left_name, right_name in build_links():
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

    print("Topology ready: 2 core routers, 4 distribution routers, 14 access switches.")


def main():
    create_topology()
