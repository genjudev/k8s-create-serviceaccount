"""
k8s-sa-creator: Create Service Account and generate a kubeconfig

This module automates the generation of a kubeconfig file for Kubernetes service accounts.
The script performs the following tasks:
1. Checks for the existence of the specified namespace, and creates one if not found.
2. Creates a service account (SA) in the specified namespace.
3. Creates a role and rolebinding for the SA with the given permissions and resources.
4. Generates a kubeconfig file for the SA.

Usage:
    Run the script with the necessary command-line arguments.
    Example: python k8s-sa-creator.py --cluster-url https://localhost:6443 --cluster-name my-cluster --namespace my-namespace --sa my-sa --permissions list,get,create,delete --resources pod,deployment,service --output-file /path/to/save/kubeconfig.yaml

License:
    MIT License

Copyright (c) 2023 [Your Company or Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Author: Lars Feldeisen
Date: 09.22.2023
"""

import argparse
import subprocess
import base64
import time

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, None, e.stderr.strip()

def wait_for_token(secret_name, namespace, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        return_code, stdout, stderr = execute_command(f"kubectl get secret {secret_name} -n {namespace}  -o jsonpath='{{.data.token}}'")
        if stdout:
            return base64.b64decode(stdout).decode("utf-8")
        time.sleep(1)
    print("Timeout waiting for token.")
    exit(1)

def validate_resources(sa, namespace, role_name, role_binding_name):
    sa_exists = subprocess.getoutput(f"kubectl get sa {sa} -n {namespace}")
    role_exists = subprocess.getoutput(f"kubectl get role {role_name} -n {namespace}")
    role_binding_exists = subprocess.getoutput(f"kubectl get rolebinding {role_binding_name} -n {namespace}")

    if not sa_exists or not role_exists or not role_binding_exists:
        print("Some resources were not created successfully.", "SA:", sa_exists, "Role:", role_exists, "RoleBinding:", role_binding_exists)
        exit(1)

def create_kubeconfig(args):
    # Create namespace
    return_code = execute_command(f"kubectl get namespace {args.namespace}")
    if(return_code == 0):
        print(f"Namespace {args.namespace} already exists.")
    else:
        execute_command(f"kubectl create namespace {args.namespace} --save-config")
        
    execute_command(f"kubectl create sa {args.sa} -n {args.namespace} --save-config")

    role_name = args.role_name if args.role_name else f"{args.sa}-role"
    role_binding_name = args.role_binding_name if args.role_binding_name else f"{args.sa}-role-binding"

    verbs = args.permissions.split(",")
    verbs = args.permissions.split(",")
    resources = args.resources.split(",")
    execute_command(f"kubectl create role {role_name} -n {args.namespace} --verb={','.join(verbs)} --resource={','.join(resources)} --save-config")
    execute_command(f"kubectl create rolebinding {role_binding_name} -n {args.namespace} --role={role_name} --serviceaccount={args.namespace}:{args.sa} --save-config")
    
    if args.secret_name:
        generated_secret_name = args.secret_name
    else:
        generated_secret_name = f"{args.sa}-token"
    # Create Secret
    secret_yaml = f"""apiVersion: v1
kind: Secret
metadata:
  name: {generated_secret_name}
  annotations:
    kubernetes.io/service-account.name: {args.sa}
  namespace: {args.namespace}
type: kubernetes.io/service-account-token"""
    execute_command(f"echo '{secret_yaml}' | kubectl apply -f -")

    token_decoded = wait_for_token(generated_secret_name, args.namespace)
    validate_resources(args.sa, args.namespace, role_name, role_binding_name)

    ca_cert = subprocess.getoutput(f"kubectl get configmap -n kube-system kube-root-ca.crt -o jsonpath='{{.data.ca\\.crt}}'")
    if not ca_cert:
        print("CA certificate is empty.")
        exit(1)

    config = f"""apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: {base64.b64encode(ca_cert.encode()).decode()}
    server: {args.cluster_url}
  name: {args.cluster_name}
contexts:
- context:
    cluster: {args.cluster_name}
    user: {args.sa}
    namespace: {args.namespace}
  name: {args.cluster_name}
current-context: {args.cluster_name}
users:
- name: {args.sa}
  user:
    token: {token_decoded}
"""
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(config)
            print(f"kubeconfig file has been generated: {args.output_file}")
    else:
        print(config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Kubernetes kubeconfig for a service account.")
    parser.add_argument("--cluster-url", dest="cluster_url", required=True, help="Kubernetes cluster URL")
    parser.add_argument("--cluster-name", dest="cluster_name", required=True, help="Kubernetes cluster name")
    parser.add_argument("--namespace", required=True, help="Namespace for the resources")
    parser.add_argument("--sa", required=True, help="Service Account name")
    parser.add_argument("--secret-name", default=None, dest="secret_name", help="secret name (token for sa)")
    parser.add_argument("--role-name", dest="role_name", default=None, help="Role name (optional)")
    parser.add_argument("--role-binding-name", dest="role_binding_name", default=None, help="Role binding name (optional)")
    parser.add_argument("--permissions", required=True, help="Comma-separated list of permissions like 'list,get,create,delete'")
    parser.add_argument("--resources", required=True, help="Comma-separated list of resources like 'pod,deployment,service'")
    parser.add_argument("--output-file", dest="output_file", default=None, help="Path where kubeconfig will be saved")

    args = parser.parse_args()
    create_kubeconfig(args)
