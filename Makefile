VENV_BIN = python3 -m venv
VENV_DIR ?= .venv
VENV_ACTIVATE = $(VENV_DIR)/bin/activate
VENV_RUN = . $(VENV_ACTIVATE)
PIP_CMD ?= pip
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

usage:			## Shows usage for this Makefile
	@cat Makefile | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: $(VENV_ACTIVATE)

$(VENV_ACTIVATE): pyproject.toml
	test -d .venv || $(VENV_BIN) .venv

install: venv   ## Install project dependencies
	@which mirrord || curl -fsSL https://raw.githubusercontent.com/metalbear-co/mirrord/main/scripts/install.sh | bash
	@which kubectl || (echo "Error: Please install the kubectl CLI"; exit 1)
	$(VENV_RUN); $(PIP_CMD) install -e .

format:		    ## Run ruff to format the whole codebase
	($(VENV_RUN); python -m ruff format .; python -m ruff check --output-format=full --fix .)

debug-main-service:   ## Use mirrord to attach and debug the Main service
	pod_name=$$(kubectl get pods -o custom-columns=":metadata.name" | grep demo-main-service); \
		mirrord exec -t pod/$$pod_name --steal python demo/services/main-service/service.py

debug-users-service:   ## Use mirrord to attach and debug the Users service
	export pod_name=$$(kubectl get pods -o custom-columns=":metadata.name" | grep demo-users-service); \
		mirrord exec -t pod/$$pod_name --steal -- python -Xfrozen_modules=off demo/services/users-service/service.py

status:         ## Show the deployment status of the app
	$(VENV_RUN); kubectl get pods

deploy:         ## Run the demo app deployment script
	$(VENV_RUN); python demo/deploy.py

clean:		    ## Clean the project
	rm -rf .venv/

.PHONY: usage venv install clean deploy format debug-main-service debug-users-service
