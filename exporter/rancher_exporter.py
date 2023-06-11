#!/usr/bin/env python3
import requests
import urllib3
import yaml
import os

TOKEN = os.environ.get("rancher_token")
ENDPOINT = os.environ.get("rancher_endpoint")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def api_request(endpoint: str) -> dict:
    data = {}
    headers = {"Authorization": "Bearer " + str(TOKEN)}
    endpoint = str(ENDPOINT) + endpoint
    return requests.get(endpoint, data=data, headers=headers, verify=False).json()

def get_clusters_list() -> list:
    info = []
    request = 'clusters'
    answer = api_request(request)
    if answer["data"]:
        for item in answer["data"]:
            info.append(item["id"])
    return info

def get_cluster(id: str) -> dict:
    answer = api_request('cluster/' + id)
    return answer

def get_nodes() -> dict:
    answer = api_request('nodes')
    return answer

def memory_format(value: str) -> str:
    if value.endswith('Ki'):
        result = float(value[:-2]) / 1024 / 1024
    elif value.endswith('Mi'):
        result = float(value[:-2]) / 1024
    elif value.endswith('Gi'):
        result = float(value[:-2])
    elif value.endswith('m'):
        result = float(value[:-1]) / 1024 / 1024 / 1024 / 1024
    elif value.endswith('k'):
        result = float(value[:-1]) / 1024 / 1024 / 1024 / 1024 / 1024
    else:
        result = float(value) / 1024 / 1024 / 1024
    return str(format(result, '.3f'))

def cpu_format(value: str) -> str:
    if value.endswith('m'):
        result = float(value[:-1]) / 1000
    else:
        result = float(value)
    return str(format(result, '.3f'))

def add_metric(name: str, tags: dict, value) -> str:
    tags_set = []
    metrics = ""
    for key in tags:
        if tags[key] != "":
            tags_set.append(key + '=' + '"' + tags[key] + '"')
    metrics = name + '{' + ', '.join(tags_set) + '}' + ' ' + str(value)
    return metrics

def metrics() -> str:
    exporter_info = []
    clusters_id = get_clusters_list()
    nodes_info = get_nodes()

    for cluster_id in clusters_id:
        if not ['', 'local'].__contains__(cluster_id):
            cluster_info = get_cluster(cluster_id)
            name = cluster_info["appliedSpec"]["displayName"]
            exporter_info.append(add_metric(name="cluster_allocatable_pods", tags={'cluster': name},
                                           value=cluster_info["allocatable"]["pods"]))
            exporter_info.append(add_metric(name="cluster_allocatable_cpu", tags={'cluster': name},
                                           value=cpu_format(cluster_info["allocatable"]["cpu"])))
            exporter_info.append(add_metric(name="cluster_allocatable_memory", tags={'cluster': name},
                                           value=memory_format(cluster_info["allocatable"]["memory"])))
            exporter_info.append(add_metric(name="cluster_requested_pods", tags={'cluster': name},
                                           value=cluster_info["requested"]["pods"]))
            exporter_info.append(add_metric(name="cluster_requested_cpu", tags={'cluster': name},
                                           value=cpu_format(cluster_info["requested"]["cpu"])))
            exporter_info.append(add_metric(name="cluster_requested_memory", tags={'cluster': name},
                                           value=memory_format(cluster_info["requested"]["memory"])))
            exporter_info.append(add_metric(name="cluster_limits_cpu", tags={'cluster': name},
                                           value=cpu_format(cluster_info["limits"]["cpu"])))
            exporter_info.append(add_metric(name="cluster_limits_memory", tags={'cluster': name},
                                           value=memory_format(cluster_info["limits"]["memory"])))

            for condition in cluster_info["agentFeatures"]:
                status_val = 0
                if str(cluster_info["agentFeatures"][condition]) == 'True':
                    status_val = 1
                exporter_info.append(
                    add_metric(name="cluster_agent_features", tags={'cluster': name, 'cluster_agent_feature': condition},
                              value=status_val))

            for condition in cluster_info['conditions']:
                status_val = 0
                if condition['status'] == 'True':
                    status_val = 1
                exporter_info.append(
                    add_metric(name="cluster_condition", tags={'cluster': name, 'cluster_condition': condition['type']},
                              value=status_val))

            node_names = []
            try:
                if cluster_info['appliedSpec']['rancherKubernetesEngineConfig']['nodes']:
                    for node_info in cluster_info['appliedSpec']['rancherKubernetesEngineConfig']['nodes']:
                        node_names.append(node_info['hostnameOverride'])
            except KeyError:
                pass

            if nodes_info['data']:
                for node_detail in nodes_info['data']:
                    if node_detail['clusterId'] == cluster_id and node_detail['hostname'] in node_names:

                        node_allocatable = node_detail["allocatable"]
                        if "pods" in node_allocatable:
                            exporter_info.append(add_metric(name="node_allocatable_pods",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=node_allocatable["pods"]))
                        if "cpu" in node_allocatable:
                            exporter_info.append(add_metric(name="node_allocatable_cpu",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=cpu_format(node_allocatable["cpu"])))
                        if "memory" in node_allocatable:
                            exporter_info.append(add_metric(name="node_allocatable_memory",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=memory_format(node_allocatable["memory"])))

                        node_requested = node_detail["requested"]
                        if "pods" in node_requested:
                            exporter_info.append(add_metric(name="node_requested_pods",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=node_requested["pods"]))
                        if "cpu" in node_requested:
                            exporter_info.append(add_metric(name="node_requested_cpu",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=cpu_format(node_requested["cpu"])))
                        if "memory" in node_requested:
                            exporter_info.append(add_metric(name="node_requested_memory",
                                                           tags={'cluster': name, 'node_name': node_detail['hostname']},
                                                           value=memory_format(node_requested["memory"])))

                        for node_condition in node_detail['conditions']:
                            if node_condition['type'] != 'Ready' or (node_condition['type'] == 'Ready' and 'lastHeartbeatTime' in str(node_condition)):
                                status_val = 0
                                if node_condition['status'] == 'True':
                                    status_val = 1
                                exporter_info.append(add_metric(name="node_component_status",
                                                            tags={'cluster': name,'node_name': node_detail['hostname'],
                                                                    'node_component': node_condition['type']},value=status_val))

    return "\n".join(exporter_info)
    
#print(metrics())