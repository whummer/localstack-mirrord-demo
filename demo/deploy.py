import os
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
    try:
        ecr_client.create_repository(repositoryName=image_name)
    except Exception as e:
        if "already exists" not in str(e):
            raise
    run(["docker", "tag", image_name, ecr_image])
    run(["docker", "push", ecr_image])


def create_users_table():
    print("Creating Users DynamoDB table ...")
    dynamodb = boto3.resource("dynamodb")
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
    except Exception as e:
        if "already exists" not in str(e):
            raise


def deploy_sample_app_to_k8s():
    print("Deploy sample app to K8S cluster ...")
    for service_dir in ["main-service", "users-service"]:
        run(["kubectl", "apply", "-f", f"demo/services/{service_dir}/k8s.yml"])


def main():
    create_eks_cluster()
    create_users_table()
    build_sample_app_image()
    wait_for_eks_cluster()
    deploy_sample_app_to_k8s()


if __name__ == "__main__":
    main()
