.PHONY: validate build deploy clean \
        invoke-send invoke-manage \
        logs-send logs-manage

STACK_NAME = wetter-bericht

SEND_LAMBDA = SendForecastFunction
MANAGE_LAMBDA = ManageSubscriptionsFunction
DISPATCH_LAMBDA = WeatherDispatcherFunction

validate:
	sam validate

build:
	@echo "Building Lambda functions..."
	sam build

#################################
# Local Invocation
#################################

runSend: build
	sam local invoke $(SEND_LAMBDA) --event events/snsDispatchEvent.json

runManage: build
	sam local invoke $(MANAGE_LAMBDA) --event events/snsEvent.json

runDispatch: build
	sam local invoke $(DISPATCH_LAMBDA) 

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