import requests

from gns3_topology.settings import (
    ETHERNET_SWITCH_SYMBOL,
    GNS3_SERVER,
    PASSWORD,
    USERNAME,
    VPCS_SYMBOL,
)


def request(method, url, **kwargs):
    auth = (USERNAME, PASSWORD) if USERNAME and PASSWORD else None

    try:
        response = requests.request(
            method,
            f"{GNS3_SERVER}{url}",
            auth=auth,
            timeout=10,
            **kwargs,
        )
    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Cannot connect to GNS3 server at {GNS3_SERVER}. "
            "Check that GNS3 is running and the API port is correct."
        ) from error

    if response.status_code == 401:
        raise RuntimeError("Authentication failed. Check USERNAME/PASSWORD in settings.py")

    if response.status_code >= 400:
        raise RuntimeError(f"GNS3 API error {response.status_code}: {response.text}")

    if not response.text:
        return {}

    return response.json()


def list_projects():
    return request("GET", "/v2/projects")


def find_project_by_name(project_name):
    for project in list_projects():
        if project.get("name") == project_name:
            return project
    return None


def open_project(project_id):
    return request("POST", f"/v2/projects/{project_id}/open")


def create_project(project_name):
    return request("POST", "/v2/projects", json={"name": project_name})


def get_templates():
    return request("GET", "/v2/templates")


def get_project_nodes(project_id):
    return request("GET", f"/v2/projects/{project_id}/nodes")


def get_project_links(project_id):
    return request("GET", f"/v2/projects/{project_id}/links")


def get_project_drawings(project_id):
    return request("GET", f"/v2/projects/{project_id}/drawings")


def delete_node(project_id, node_id):
    return request("DELETE", f"/v2/projects/{project_id}/nodes/{node_id}")


def delete_link(project_id, link_id):
    return request("DELETE", f"/v2/projects/{project_id}/links/{link_id}")


def delete_drawing(project_id, drawing_id):
    return request("DELETE", f"/v2/projects/{project_id}/drawings/{drawing_id}")


def create_node(project_id, template, name, x, y):
    if template.get("template_type") == "ethernet_switch":
        payload = {
            "name": name,
            "node_type": "ethernet_switch",
            "compute_id": "local",
            "x": x,
            "y": y,
            "symbol": ETHERNET_SWITCH_SYMBOL,
            "properties": {},
        }
        return request("POST", f"/v2/projects/{project_id}/nodes", json=payload)

    if template.get("template_type") == "vpcs":
        payload = {
            "name": name,
            "node_type": "vpcs",
            "compute_id": "local",
            "x": x,
            "y": y,
            "symbol": VPCS_SYMBOL,
            "properties": {},
        }
        return request("POST", f"/v2/projects/{project_id}/nodes", json=payload)

    payload = {
        "name": name,
        "x": x,
        "y": y,
    }
    return request(
        "POST",
        f"/v2/projects/{project_id}/templates/{template['template_id']}",
        json=payload,
    )


def update_node(project_id, node_id, **fields):
    return request("PUT", f"/v2/projects/{project_id}/nodes/{node_id}", json=fields)


def create_drawing(project_id, x, y, svg, z=0):
    payload = {
        "x": x,
        "y": y,
        "z": z,
        "svg": svg,
    }
    return request("POST", f"/v2/projects/{project_id}/drawings", json=payload)


def connect_nodes(project_id, left_node_id, left_adapter, left_port, right_node_id, right_adapter, right_port):
    payload = {
        "nodes": [
            {
                "node_id": left_node_id,
                "adapter_number": left_adapter,
                "port_number": left_port,
            },
            {
                "node_id": right_node_id,
                "adapter_number": right_adapter,
                "port_number": right_port,
            },
        ]
    }
    return request("POST", f"/v2/projects/{project_id}/links", json=payload)
