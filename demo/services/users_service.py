import os
import time

from flask import Flask, request, jsonify
import boto3
import uuid

os.environ["AWS_ENDPOINT_URL"] = "http://localhost.localstack.cloud:4566"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

app = Flask(__name__)

DYNAMODB_TABLE_NAME = "Users"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


@app.route("/users", methods=["POST"])
def create_user():
    """
    Endpoint to create a new user in DynamoDB. Expects a JSON body with 'username' and 'email'.
    Example:
    {
        "username": "john_doe",
        "email": "john.doe@example.com"
    }
    """
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "Missing 'username' or 'email' in request body"}), 400

    # generate a unique user ID
    user_id = str(uuid.uuid4())

    # put item into DynamoDB
    table.put_item(
        Item={
            "user_id": user_id,
            "username": username,
            "email": email,
            "created_at": time.time(),
        },
    )
    return jsonify(
        {
            "message": "User saved successfully",
            "user_id": user_id,
            "username": username,
        }
    ), 201


@app.route("/users/<string:username>", methods=["GET"])
def get_user(username):
    """
    Endpoint to fetch a user by their username from DynamoDB.
    """
    response = table.get_item(Key={"username": username})
    item = response.get("Item")
    if not item:
        return jsonify({"message": f"User with username '{username}' not found"}), 404
    return jsonify(item), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
