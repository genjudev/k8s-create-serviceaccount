# k8s service account creator

## Overview

The `k8s-sa-creator` is a Python script designed to facilitate the creation of a Kubernetes service account along with its associated kubeconfig file. This simplifies the process of managing permissions and accessing a Kubernetes cluster using a service account. The script performs the following tasks:

1. Checks if the specified namespace exists, if not, it creates one.
2. Creates a Service Account.
3. Generates a Role with the specified permissions.
4. Creates a RoleBinding linking the Service Account to the Role.
5. Generates a kubeconfig file for the Service Account.

## Prerequisites

- Python 3.x installed
- `kubectl` installed and configured

## Tested on
- Client Version: v1.27.4
- Kustomize Version: v5.0.1
- Server Version: v1.27.4

## Script Arguments

| Argument             | Required | Description                                                       | Default       | Example                                 |
|----------------------|----------|-------------------------------------------------------------------|---------------|-----------------------------------------|
| `--cluster-url`      | Yes      | Kubernetes cluster URL                                            | None          | `https://192.168.1.100:6443`            |
| `--cluster-name`     | Yes      | Name for the Kubernetes cluster                                   | None          | `my-cluster`                            |
| `--namespace`        | Yes      | Namespace where resources will be created                         | None          | `my-namespace`                          |
| `--sa`               | Yes      | Service Account name                                              | None          | `my-sa`                                 |
| `--secret-name`      | No       | Secret name to be generated for the Service Account               | Auto-generated | `my-sa-secret`                          |
| `--role-name`        | No       | Role name                                                         | `<sa>-role`    | `my-role`                               |
| `--role-binding-name`| No       | Role binding name                                                 | `<sa>-role-binding` | `my-role-binding`        |
| `--permissions`      | Yes      | Comma-separated list of permissions (verbs)                       | None          | `list,get,create,delete`                |
| `--resources`        | Yes      | Comma-separated list of resources                                 | None          | `pod,deployment,service`                |
| `--output-file`      | No       | File path where the kubeconfig will be saved                      | stdout        | `./my-sa-kubeconfig.yaml`               |

## Usage Examples

### Basic Usage

```bash
python k8s-sa-creator.py \
    --cluster-url https://192.168.1.100:6443 \
    --cluster-name my-cluster \
    --namespace my-namespace \
    --sa my-sa \
    --permissions list,get \
    --resources pod,service
```

This will generate the kubeconfig file and print it to stdout.

### Advanced Usage

```bash
python k8s-sa-creator.py \
    --cluster-url https://192.168.1.100:6443 \
    --cluster-name my-cluster \
    --namespace my-namespace \
    --sa my-sa \
    --secret-name my-secret \
    --role-name my-role \
    --role-binding-name my-role-binding \
    --permissions list,get,create,delete \
    --resources pod,service,deployment \
    --output-file ./my-sa-kubeconfig.yaml
```

This will generate a kubeconfig file and save it to `./my-sa-kubeconfig.yaml`.
