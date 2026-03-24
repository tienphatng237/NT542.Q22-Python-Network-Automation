from gns3_topology.settings import ACCESS_COUNT, CORE_COUNT, DISTRIBUTION_COUNT


def find_template(templates, hints):
    normalized_hints = [hint.lower() for hint in hints]

    for hint in normalized_hints:
        for template in templates:
            template_name = template.get("name", "").lower()
            if template_name == hint:
                return template

    for hint in normalized_hints:
        for template in templates:
            template_name = template.get("name", "").lower()
            if hint in template_name:
                return template

    return None


def build_node_specs():
    specs = []

    core_x_positions = [-250, 250]
    for index in range(CORE_COUNT):
        specs.append(
            {
                "name": f"CORE{index + 1}",
                "kind": "router",
                "x": core_x_positions[index],
                "y": -250,
            }
        )

    dist_x_positions = [-600, -200, 200, 600]
    for index in range(DISTRIBUTION_COUNT):
        specs.append(
            {
                "name": f"DIST{index + 1}",
                "kind": "router",
                "x": dist_x_positions[index],
                "y": -20,
            }
        )

    access_x_positions = [-900, -600, -300, 0, 300, 600, 900]
    for index in range(ACCESS_COUNT):
        row = index // len(access_x_positions)
        column = index % len(access_x_positions)
        specs.append(
            {
                "name": f"SW{index + 1:02d}",
                "kind": "switch",
                "x": access_x_positions[column],
                "y": 260 + (row * 180),
            }
        )

    return specs


def build_links():
    links = [("CORE1", "CORE2")]

    for dist_name in ("DIST1", "DIST2", "DIST3", "DIST4"):
        links.append(("CORE1", dist_name))
        links.append(("CORE2", dist_name))

    access_groups = {
        "DIST1": ["SW01", "SW02", "SW03", "SW04"],
        "DIST2": ["SW05", "SW06", "SW07", "SW08"],
        "DIST3": ["SW09", "SW10", "SW11"],
        "DIST4": ["SW12", "SW13", "SW14"],
    }

    for dist_name, access_list in access_groups.items():
        for access_name in access_list:
            links.append((dist_name, access_name))

    return links
