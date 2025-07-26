import requests
from flask import Flask

app = Flask(__name__)


@app.route("/main", methods=["GET"])
def create_user():
    user_name = "john_doe"
    payload = {"username": user_name, "email": "john.doe@example.com"}
    # create user
    response = requests.post("http://users-service:80/users", json=payload)
    if not response.ok:
        raise Exception(response.text)
    # get user
    response = requests.get(f"http://users-service:80/users/{user_name}", json=payload)
    if not response.ok:
        raise Exception(response.text)
    # return response
    return response.json()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
