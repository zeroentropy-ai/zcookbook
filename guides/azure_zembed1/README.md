# Deploy zembed-1 on Azure AKS

This notebook shows how to deploy `zembed-1` from Azure Marketplace to an Azure Kubernetes Service (AKS) cluster with an H100 GPU node. You will create the cluster, install the NVIDIA device plugin, deploy the Marketplace extension, and test the local embedding endpoint through `kubectl port-forward`.

Executable notebook: [azure_zembed1.ipynb](azure_zembed1.ipynb)

## Prerequisites

- An Azure subscription with quota for `Standard_NC40ads_H100_v5`
- Azure CLI (`az`) installed and authenticated with `az login`
- `kubectl` installed
- `jq` installed for JSON inspection
- Permission to create AKS clusters and Azure Kubernetes extensions
- A resource group in the subscription, or permission to create one

## What you will do

- Check the Azure Marketplace terms and H100 quota
- Create a single-node AKS cluster with one H100 GPU
- Install the NVIDIA Kubernetes device plugin
- Deploy `zembed-1` through the Azure Marketplace extension
- Verify the pod, service, GPU allocation, and health endpoint
- Send sample embedding requests to `/invocations`


## 1. Configure deployment values

Set these values before running the command cells. The Python cell exports them to the notebook process and defines a small `run()` helper for shell commands.

The Marketplace values below correspond to the public `zembed-1` listing: extension type `zeroentropy.zembedextension`, offer `zeroentropy-zembed-1`, and plan `embedding-monthly-plan`. Set `AZURE_SUBSCRIPTION` explicitly so quota checks and cluster creation run against the same subscription.



```python
import os
import subprocess

config = {
    "AZURE_SUBSCRIPTION": "<your-subscription-name-or-id>",
    "AZURE_RESOURCE_GROUP": "<your-resource-group>",
    "AKS_CLUSTER_NAME": "<your-cluster-name>",
    "AZURE_LOCATION": "WestUS3",
    "AKS_NODE_SIZE": "Standard_NC40ads_H100_v5",
    "AKS_NODE_COUNT": "1",
    "AKS_ZONE": "1",
    "AKS_NODE_OSDISK_TYPE": "Managed",
    "AKS_NODE_OSDISK_SIZE_GB": "512",
    "AKS_NETWORK_PLUGIN": "kubenet",
    "ZEMBED_EXTENSION_NAME": "<your-extension-name>",
    "ZEMBED_EXTENSION_TYPE": "zeroentropy.zembedextension",
    "ZEMBED_PLAN_NAME": "embedding-monthly-plan",
    "ZEMBED_PLAN_PRODUCT": "zeroentropy-zembed-1",
    "ZEMBED_PLAN_PUBLISHER": "zeroentropy",
    "ZEMBED_NAMESPACE": "zembed-1",
    "LOCAL_PORT": "8080",
}

for key, value in config.items():
    os.environ[key] = value

def run(command: str):
    return subprocess.run(
        ["bash", "-e", "-u", "-o", "pipefail", "-c", command],
        check=True,
        text=True,
    )

missing = [key for key, value in config.items() if value.startswith("<") and value.endswith(">")]
if missing:
    print("Update these values before running the deployment cells:")
    for key in missing:
        print(f"  - {key}")
else:
    print("Configuration loaded.")

```

## 2. Check Marketplace terms and quota

Confirm that the Marketplace terms are accepted for the subscription. If `accepted` is `false`, run the following opt-in cell after reviewing the terms in Azure Marketplace.



```python
run("""\
az term show \
  --subscription "$AZURE_SUBSCRIPTION" \
  --publisher "$ZEMBED_PLAN_PUBLISHER" \
  --product "$ZEMBED_PLAN_PRODUCT" \
  --plan "$ZEMBED_PLAN_NAME" \
  --query '{accepted:accepted,publisher:publisher,product:product,plan:plan}' \
  -o json
""")

```

If the previous cell prints `"accepted": false`, set `accept_marketplace_terms = True` and run this cell. Leave it as `False` if the terms are already accepted or you are not ready to accept them.


```python
accept_marketplace_terms = False

if accept_marketplace_terms:
    run("""\
    az term accept \
      --subscription "$AZURE_SUBSCRIPTION" \
      --publisher "$ZEMBED_PLAN_PUBLISHER" \
      --product "$ZEMBED_PLAN_PRODUCT" \
      --plan "$ZEMBED_PLAN_NAME" \
      -o json
    """)
else:
    print("Marketplace term acceptance skipped.")

```

Check that the target region has both regional vCPU quota and `Standard NCadsH100v5 Family vCPUs` quota. One `Standard_NC40ads_H100_v5` node requires 40 vCPUs.


```python
run("""\
echo "SKU availability:"
az vm list-skus \
  --subscription "$AZURE_SUBSCRIPTION" \
  --location "$AZURE_LOCATION" \
  --size "$AKS_NODE_SIZE" \
  --all \
  --query "[?name=='$AKS_NODE_SIZE'].{name:name,locations:locations,restrictions:restrictions[].reasonCode}" \
  -o json

echo "Quota usage:"
az vm list-usage \
  --subscription "$AZURE_SUBSCRIPTION" \
  --location "$AZURE_LOCATION" \
  --query "[?name.value=='cores' || contains(name.localizedValue, 'H100')].{name:name.localizedValue,value:name.value,limit:limit,current:currentValue}" \
  -o table
""")

```

## 3. Create the AKS cluster

Create a single-node AKS cluster backed by `Standard_NC40ads_H100_v5`. If you already have a suitable cluster, skip this cell and run the `az aks get-credentials` cell below.

The cluster location must have quota for both total regional vCPUs and `Standard NCadsH100v5 Family vCPUs`. The command pins one availability zone and uses managed OS disks plus `kubenet`; this avoids common H100 allocation failures caused by ephemeral OS disk constraints.



```python
run("""\
az aks create \
  --subscription "$AZURE_SUBSCRIPTION" \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --location "$AZURE_LOCATION" \
  --node-count "$AKS_NODE_COUNT" \
  --node-vm-size "$AKS_NODE_SIZE" \
  --node-osdisk-type "$AKS_NODE_OSDISK_TYPE" \
  --node-osdisk-size "$AKS_NODE_OSDISK_SIZE_GB" \
  --network-plugin "$AKS_NETWORK_PLUGIN" \
  --zones "$AKS_ZONE" \
  --generate-ssh-keys
""")

```

Connect `kubectl` to the cluster.


```python
run("""\
az aks get-credentials \
  --subscription "$AZURE_SUBSCRIPTION" \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$AKS_CLUSTER_NAME" \
  --overwrite-existing

kubectl get nodes
""")

```

## 4. Install the NVIDIA device plugin

The device plugin advertises GPU resources to Kubernetes. After installation, wait about one minute for the allocatable GPU count to appear on the node.



```python
run("""\
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.0/deployments/static/nvidia-device-plugin.yml
""")

```

Verify that Kubernetes sees the GPU. The kubelet may need a minute to refresh node allocatable resources after the plugin registers. This cell retries until it sees `"gpu": "1"`.



```python
run("""\
for i in {1..12}; do
  gpu_count=$(kubectl get nodes -o json | jq -r '.items[0].status.allocatable["nvidia.com/gpu"] // ""')
  if [ "$gpu_count" = "1" ]; then
    kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, gpu: .status.allocatable["nvidia.com/gpu"]}'
    exit 0
  fi
  echo "Waiting for GPU allocatable resource..."
  sleep 10
done

kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, gpu: .status.allocatable["nvidia.com/gpu"]}'
exit 1
""")

```

## 5. Deploy zembed-1 from Azure Marketplace

You can deploy through the [zembed-1 Azure Marketplace listing](https://marketplace.microsoft.com/en-us/product/zeroentropy.zeroentropy-zembed-1?tab=Overview) or create the Kubernetes extension from the CLI.

The command below uses the Marketplace extension type and plan published for `zembed-1`.



```python
run("""\
az k8s-extension create \
  --subscription "$AZURE_SUBSCRIPTION" \
  --name "$ZEMBED_EXTENSION_NAME" \
  --cluster-name "$AKS_CLUSTER_NAME" \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --cluster-type managedClusters \
  --extension-type "$ZEMBED_EXTENSION_TYPE" \
  --scope cluster \
  --release-train stable \
  --release-namespace "$ZEMBED_NAMESPACE" \
  --plan-name "$ZEMBED_PLAN_NAME" \
  --plan-product "$ZEMBED_PLAN_PRODUCT" \
  --plan-publisher "$ZEMBED_PLAN_PUBLISHER"
""")

```

## 6. Verify the deployment

Wait until the pod is ready. The first startup can take several minutes while the image is pulled and the model loads.



```python
run("""\
kubectl wait \
  --for=condition=ready pod \
  -n "$ZEMBED_NAMESPACE" \
  -l app.kubernetes.io/name=zembed-1 \
  --timeout=900s

kubectl get pods -n "$ZEMBED_NAMESPACE" -o wide
""")

```

List services in the namespace. The request cells below find the `zembed-1` service by label, so the commands keep working if the service name changes.


```python
run("""\
kubectl get svc -n "$ZEMBED_NAMESPACE" -o wide
""")

```

Check recent logs if the pod is not ready.


```python
run("""\
kubectl logs -n "$ZEMBED_NAMESPACE" -l app.kubernetes.io/name=zembed-1 --tail=100
""")

```

## 7. Port-forward the service

This starts `kubectl port-forward` from the notebook kernel and discovers the service name automatically.



```python
import os
import subprocess
import time

namespace = os.environ["ZEMBED_NAMESPACE"]
local_port = os.environ["LOCAL_PORT"]

service_name = subprocess.check_output(
    [
        "kubectl",
        "get",
        "svc",
        "-n",
        namespace,
        "-l",
        "app.kubernetes.io/name=zembed-1",
        "-o",
        "jsonpath={.items[0].metadata.name}",
    ],
    text=True,
).strip()

if "zembed1_port_forward" in globals() and zembed1_port_forward.poll() is None:
    zembed1_port_forward.terminate()
    zembed1_port_forward.wait(timeout=10)

zembed1_port_forward = subprocess.Popen(
    [
        "kubectl",
        "port-forward",
        "-n",
        namespace,
        f"svc/{service_name}",
        f"{local_port}:80",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

time.sleep(3)
if zembed1_port_forward.poll() is not None:
    output = zembed1_port_forward.stdout.read() if zembed1_port_forward.stdout else ""
    raise RuntimeError(f"port-forward exited early:\n{output}")

print(f"Forwarding localhost:{local_port} to service/{service_name}:80")

```

## 8. Test the embedding endpoint

Send a sample document embedding request to `/invocations`. The response contains base64-encoded f16 embeddings, token counts, and request usage metadata.



```python
import base64
import json
import math
import os
import struct
import urllib.request


def post_json(path: str, payload: dict):
    url = f"http://localhost:{os.environ['LOCAL_PORT']}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def decode_embedding(value):
    if isinstance(value, str):
        raw = base64.b64decode(value)
        return list(struct.unpack(f"<{len(raw) // 2}e", raw))
    return value

payload = {
    "embedding_type": "document",
    "input": [
        "ZeroEntropy zembed-1 creates dense embeddings for retrieval and semantic search.",
        "A rain gauge measures precipitation over time.",
    ],
    "dimensions": 320,
}

response = post_json("/invocations", payload)
embeddings = [decode_embedding(item) for item in response["embeddings"]]

assert len(embeddings) == len(payload["input"])
assert all(len(vector) == payload["dimensions"] for vector in embeddings)
assert len(response["num_tokens"]) == len(payload["input"])

print(json.dumps({
    "embedding_count": len(embeddings),
    "embedding_dimensions": [len(vector) for vector in embeddings],
    "num_tokens": response["num_tokens"],
}, indent=2))

```

Run a query/document similarity check. Use `embedding_type="query"` for the query and `embedding_type="document"` for corpus text.


```python
query = "Which document is about semantic search embeddings?"
documents = [
    "zembed-1 maps text to vectors for semantic search and RAG.",
    "H100 GPUs provide high throughput for model inference.",
    "Garden soil moisture changes after rainfall.",
]

query_response = post_json("/invocations", {
    "embedding_type": "query",
    "input": [query],
    "dimensions": 320,
})
doc_response = post_json("/invocations", {
    "embedding_type": "document",
    "input": documents,
    "dimensions": 320,
})

q_vec = decode_embedding(query_response["embeddings"][0])
d_vecs = [decode_embedding(item) for item in doc_response["embeddings"]]


def cosine(left, right):
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm)

ranked = sorted(
    enumerate(cosine(q_vec, vector) for vector in d_vecs),
    key=lambda item: item[1],
    reverse=True,
)

print(f"Query: {query}\n")
for rank, (index, score) in enumerate(ranked, 1):
    print(f"{rank}. score={score:.4f}  doc={documents[index]}")

assert ranked[0][0] == 0, "Expected the semantic-search document to rank first."

```

## 9. Check service health

The health endpoint returns service status, model configuration, and endpoint type.



```python
run("""\
curl "http://localhost:${LOCAL_PORT}/health"
""")

```

Stop the port-forward process when you are done testing.


```python
if "zembed1_port_forward" in globals() and zembed1_port_forward.poll() is None:
    zembed1_port_forward.terminate()
    zembed1_port_forward.wait(timeout=10)
    print("Stopped port-forward.")
else:
    print("No running port-forward process found.")

```

## Troubleshooting

- If AKS creation fails with quota errors, confirm that `AZURE_SUBSCRIPTION` and `AZURE_LOCATION` have quota for both total regional vCPUs and `Standard NCadsH100v5 Family vCPUs`. One `Standard_NC40ads_H100_v5` node requires 40 vCPUs.
- If AKS creation fails with `OverconstrainedAllocationRequest`, keep `AKS_NODE_OSDISK_TYPE=Managed`, keep `AKS_NETWORK_PLUGIN=kubenet`, and try another supported `AKS_ZONE` from the SKU availability output.
- If Marketplace terms are not accepted, review the listing and run the opt-in term acceptance cell.
- If GPU allocation shows `null`, rerun the GPU verification cell. If it still shows `null`, inspect the NVIDIA device plugin pod in `kube-system`.
- If the Marketplace extension type fails, list the current ZeroEntropy extension registrations with `az k8s-extension extension-types list-by-cluster --subscription "$AZURE_SUBSCRIPTION" --cluster-name "$AKS_CLUSTER_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --cluster-type managedClusters`.
- If `kubectl port-forward` fails, rerun the service listing cell and confirm the `zembed-1` service exists.
- If `/invocations` returns a dimension error, use one of the supported dimensions: `40`, `80`, `160`, `320`, `640`, `1280`, or `2560`.
- If `/invocations` fails after the pod is ready, inspect `/health` and recent logs. A healthy zembed deployment should report `{"status":"healthy","model":"zembed-1","endpoint":"embed"}`.

Because GPU-backed AKS clusters are expensive, delete unused test clusters from the Azure portal or with `az aks delete` after you finish.
