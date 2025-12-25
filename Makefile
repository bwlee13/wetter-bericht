.PHONY: validate build deploy clean \
        invoke-send invoke-manage \
        logs-send logs-manage

STACK_NAME = wetter-bericht

SEND_LAMBDA = SendForecastFunction
MANAGE_LAMBDA = ManageSubscriptionsFunction

validate:
	sam validate

build:
	@echo "Building Lambda functions..."
	sam build

#################################
# Local Invocation
#################################

runSend: build
	sam local invoke $(SEND_LAMBDA)

runManage: build
	sam local invoke $(MANAGE_LAMBDA) --event events/snsEvent.json

#################################
# Deploy
#################################

deploy: build
	@echo "Deploying to AWS..."
	sam deploy

#################################
# Logs
#################################

logs-send:
	sam logs -n $(SEND_LAMBDA) --stack-name $(STACK_NAME) --tail

logs-manage:
	sam logs -n $(MANAGE_LAMBDA) --stack-name $(STACK_NAME) --tail

#################################
# Cleanup
#################################

clean:
	rm -rf .aws-sam