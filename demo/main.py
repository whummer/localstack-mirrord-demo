import os
import tempfile
import time
import boto3
from localstack.utils.run import run

os.environ["AWS_ENDPOINT_URL"] = "http://localhost.localstack.cloud:4566"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

table_name = "Users"
cluster_name = "ls-mirrord-demo"
image_name = "localstack-mirrord-demo"
ecr_image = (
    f"000000000000.dkr.ecr.us-east-1.localhost.localstack.cloud:4566/{image_name}"
)

main_service_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ls-mirrord-demo-main-service
  labels:
    app: ls-mirrord-demo-main-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ls-mirrord-demo-main-service
  template:
    metadata:
      labels:
        app: ls-mirrord-demo-main-service
    spec:
      containers:
      - name: ls-mirrord-demo-main-service
        image: {ecr_image}
        command: [python]
        args: ["/tmp/services/main_service.py"]
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: main-service
spec:
  selector:
    app: ls-mirrord-demo-main-service
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx
  annotations:
    ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
    - http:
        paths:
          - path: /main
            pathType: Prefix
            backend:
              service:
                name: main-service
                port:
                  number: 80
"""
users_service_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ls-mirrord-demo-users-service
  labels:
    app: ls-mirrord-demo-users-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ls-mirrord-demo-users-service
  template:
    metadata:
      labels:
        app: ls-mirrord-demo-users-service
    spec:
      containers:
      - name: ls-mirrord-demo-users-service
        image: {ecr_image}
        command: [python]
        args: ["/tmp/services/users_service.py"]
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: users-service
spec:
  selector:
    app: ls-mirrord-demo-users-service
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
"""


def create_eks_cluster():
    print("Creating EKS cluster ...")
    eks_client = boto3.client("eks")
    eks_client.create_cluster(
        name=cluster_name,
        roleArn="arn:aws:iam::000000000000:role/r1",
        resourcesVpcConfig={},
    )


def wait_for_eks_cluster():
    print("Waiting for cluster to become available ...")
    eks_client = boto3.client("eks")
    for i in range(15):
        result = eks_client.describe_cluster(name=cluster_name)
        if result["cluster"]["status"] == "ACTIVE":
            break
        time.sleep(5)
    result = eks_client.describe_cluster(name=cluster_name)
    assert result["cluster"]["status"] == "ACTIVE"

    # update local kubectl config with cluster info
    run(["awslocal", "eks", "update-kubeconfig", "--name", cluster_name])


def build_sample_app_image():
    print("Building sample app Docker image ...")
    run(["docker", "build", "-t", image_name, "."])
    ecr_client = boto3.client("ecr")
    ecr_client.create_repository(repositoryName=image_name)
    run(["docker", "tag", image_name, ecr_image])
    run(["docker", "push", ecr_image])


def deploy_sample_app_to_k8s():
    print("Deploy sample app to K8S cluster ...")
    for yaml_file in [main_service_yaml, users_service_yaml]:
        with tempfile.NamedTemporaryFile() as f:
            f.write(yaml_file.encode())
            f.flush()
            run(["kubectl", "apply", "-f", f.name])


def create_users_table():
    print("!Creating Users DynamoDB table ...")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()


def start_mirrord_proxy():
    # run(["mirrord", "proxy"])
    pass


def main():
    create_eks_cluster()
    create_users_table()
    build_sample_app_image()
    wait_for_eks_cluster()
    deploy_sample_app_to_k8s()
    start_mirrord_proxy()


if __name__ == "__main__":
    main()
