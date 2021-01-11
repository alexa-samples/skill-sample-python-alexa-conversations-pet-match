import logging
import json
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# read mock data
with open('PetMatch.json', 'r') as myfile:
    jsonData = myfile.read()

data = json.loads(jsonData)


class GetRecommendationAPIHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.request_util.get_request_type(handler_input) == 'Dialog.API.Invoked' and handler_input.request_envelope.request.api_request.name == 'getRecommendation'


    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        api_request = handler_input.request_envelope.request.api_request

        energy = resolveEntity(api_request.slots, "energy")
        size = resolveEntity(api_request.slots, "size")
        temperament = resolveEntity(api_request.slots, "temperament")

        recommendationResult = {}

        if energy != None and size != None and temperament != None:
            key = energy + '-' + size + '-' + temperament
            databaseResponse = data[key]

            print("Response from mock database ", databaseResponse)

            recommendationResult['name'] = databaseResponse['breed']
            recommendationResult['size'] = api_request.arguments['size']
            recommendationResult['energy'] = api_request.arguments['energy']
            recommendationResult['temperament'] = api_request.arguments['temperament']

        response = buildSuccessApiResponse(recommendationResult)
        
        return response


# Formats JSON for return
# You can use the private SDK methods like "setApiResponse()", but for this template for now, we just send back
# the JSON. General request and response JSON format can be found here:
# https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html
def buildSuccessApiResponse(returnEntity):
    return { "apiResponse": returnEntity }

# *****************************************************************************
# Generic session-ended handling logging the reason received, to help debug in error cases.
# Ends Session if there is an error 
class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


# *****************************************************************************
# Resolves catalog value using Entity Resolution
def resolveEntity(resolvedEntity, slotName):
    erAuthorityResolution = resolvedEntity[slotName].resolutions.resolutions_per_authority[0]
    value = None

    if erAuthorityResolution.status.code.value == 'ER_SUCCESS_MATCH':
        value = erAuthorityResolution.values[0].value.name

    return value

# The intent reflector is used for interaction model testing and debugging.
# It will simply repeat the intent the user said. You can create custom handlers
# for your intents by defining them above, then also adding them to the request
# handler chain below.
class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open for the user to respond")
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


# *****************************************************************************
# These simple interceptors just log the incoming and outgoing request bodies to assist in debugging.

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        print("Request received: {}".format(
            handler_input.request_envelope.request))


class LoggingResponseInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        print("Response generated: {}".format(response))


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
sb = SkillBuilder()

# register request / intent handlers
sb.add_request_handler(GetRecommendationAPIHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())

# register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# register interceptors
sb.add_global_request_interceptor(LoggingRequestInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()
