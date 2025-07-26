import requests
from flask import Flask

app = Flask(__name__)


@app.route("/main", methods=["GET"])
def create_user():
    payload = {"username": "john_doe", "email": "john.doe@example.com"}
    # create user
    requests.post("http://users-service:80/users", json=payload)
    # get user
    response = requests.get("http://users-service:80/users/john_doe", json=payload)
    # return response
    return response.json()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
