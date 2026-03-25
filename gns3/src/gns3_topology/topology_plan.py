from gns3_topology.settings import ACCESS_COUNT, CORE_COUNT, DISTRIBUTION_COUNT, PC_COUNT


MANAGED_DRAWING_TAG = "HW03_MANAGED"


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


def build_access_groups():
    if CORE_COUNT != 2 or DISTRIBUTION_COUNT != 2 or ACCESS_COUNT != 6 or PC_COUNT != 6:
        raise RuntimeError(
            "This compact layout is defined for 2 core, 2 distribution, 6 access, 6 PCs. "
            "Update topology_plan.py if you want a different topology size."
        )

    return {
        "DIST1": ["SW01", "SW02", "SW03"],
        "DIST2": ["SW04", "SW05", "SW06"],
    }


def build_node_specs():
    specs = [
        {"name": "CORE1", "kind": "router", "x": -380, "y": -320},
        {"name": "CORE2", "kind": "router", "x": 380, "y": -320},
        {"name": "DIST1", "kind": "router", "x": -380, "y": -90},
        {"name": "DIST2", "kind": "router", "x": 380, "y": -90},
        {"name": "SW01", "kind": "switch", "x": -620, "y": 160},
        {"name": "SW02", "kind": "switch", "x": -380, "y": 160},
        {"name": "SW03", "kind": "switch", "x": -140, "y": 160},
        {"name": "SW04", "kind": "switch", "x": 140, "y": 160},
        {"name": "SW05", "kind": "switch", "x": 380, "y": 160},
        {"name": "SW06", "kind": "switch", "x": 620, "y": 160},
        {"name": "PC1", "kind": "pc", "x": -620, "y": 470},
        {"name": "PC2", "kind": "pc", "x": -380, "y": 470},
        {"name": "PC3", "kind": "pc", "x": -140, "y": 470},
        {"name": "PC4", "kind": "pc", "x": 140, "y": 470},
        {"name": "PC5", "kind": "pc", "x": 380, "y": 470},
        {"name": "PC6", "kind": "pc", "x": 620, "y": 470},
    ]
    return specs


def build_links():
    links = [("CORE1", "CORE2")]

    for dist_name in ("DIST1", "DIST2"):
        links.append(("CORE1", dist_name))
        links.append(("CORE2", dist_name))

    for dist_name, switch_names in build_access_groups().items():
        for switch_name in switch_names:
            links.append((dist_name, switch_name))

    for index in range(1, PC_COUNT + 1):
        links.append((f"SW{index:02d}", f"PC{index}"))

    return links


def build_layer_drawings(node_specs):
    shared_left = -760
    shared_width = 1520
    shared_gap = 70

    core_top = -400
    core_height = 170
    dist_top = core_top + core_height + shared_gap
    dist_height = 190
    access_top = dist_top + dist_height + shared_gap
    access_height = 190
    end_top = access_top + access_height + shared_gap
    end_height = 260

    drawings = [
        _build_fixed_box(
            "Core Layer",
            shared_left,
            core_top,
            shared_width,
            core_height,
            "#2563eb",
        ),
        _build_fixed_box(
            "Distribution Layer",
            shared_left,
            dist_top,
            shared_width,
            dist_height,
            "#059669",
        ),
        _build_fixed_box(
            "Access Layer",
            shared_left,
            access_top,
            shared_width,
            access_height,
            "#d97706",
        ),
        _build_fixed_box(
            "End Devices",
            shared_left,
            end_top,
            shared_width,
            end_height,
            "#7c3aed",
        ),
    ]

    return drawings


def _build_fixed_box(label, left, top, width, height, stroke_color):
    svg = f"""
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <!-- {MANAGED_DRAWING_TAG} -->
  <rect x="0" y="0" width="{width}" height="{height}" rx="16" ry="16"
        fill="{stroke_color}" fill-opacity="0.05"
        stroke="{stroke_color}" stroke-width="3"/>
  <rect x="16" y="12" width="170" height="30" rx="8" ry="8"
        fill="{stroke_color}" fill-opacity="0.14" stroke="none"/>
  <text x="30" y="33" font-size="18" font-family="Arial" font-weight="bold"
        fill="{stroke_color}">{label}</text>
</svg>
""".strip()

    return {
        "x": left,
        "y": top,
        "z": 0,
        "svg": svg,
    }
