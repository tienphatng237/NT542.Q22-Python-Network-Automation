import requests

from gns3_topology.settings import ETHERNET_SWITCH_SYMBOL, GNS3_SERVER, PASSWORD, USERNAME


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


def build_available_project_name(base_name):
    existing_names = {project.get("name") for project in list_projects()}
    if base_name not in existing_names:
        return base_name

    suffix = 2
    while True:
        candidate = f"{base_name}-{suffix}"
        if candidate not in existing_names:
            return candidate
        suffix += 1


def create_project(project_name):
    return request("POST", "/v2/projects", json={"name": project_name})


def get_templates():
    return request("GET", "/v2/templates")


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
