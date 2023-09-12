import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from plugins.SearchPlugin import SearchPlugin
from plugins.MSSalesPlugin import MSSalesPlugin
from keyvault import KeyVault
from flask import Flask, render_template, request
import logging

def get_message_history(messages):
    # join messages with line breaks into one string
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])


def detect_intent(messages: dict) -> str:
    logging.info("Detecting intent...")
    intent_vars = sk.ContextVariables()
    intent_vars["history"] = get_message_history(messages)
    intent = orchestrator_plugin["getIntent"].invoke(variables=intent_vars)
    intent_result = intent.result.replace("<|im_end|>", "").strip()
    logging.info(f"Intent: {intent_result}")
    return intent_result


def extract_account(messages: dict) -> str:
    query_vars = sk.ContextVariables()
    query_vars["history"] = get_message_history(messages)
    query = orchestrator_plugin["getQuery"].invoke(variables=query_vars)
    query_clean = query.result.replace("<|im_end|>", "").strip()
    logging.info(f"Searching accounts for '{query_clean}'...")
    return query_clean


def search_accounts(query: str) -> str:
    search_result = search_plugin["getAccount"].invoke(query)
    logging.info(f"Search result: {search_result.result}")
    return search_result.result


def get_account_id(account_name: str) -> str:
    logging.info(f"Getting account ID for {account_name} from MSSales...")
    account_id = mssales_plugin["getAccountID"].invoke(account_name)
    logging.info(f"Account ID: {account_id}")
    return account_id.result


def get_opportunities(account_id: str) -> str:
    logging.info(f"Getting opportunities for account ID {account_id} from MSSales...")
    opportunities = mssales_plugin["getOpportunities"].invoke(account_id)
    logging.info(f"Opportunities: {opportunities.result}")
    return opportunities.result


def generate_answer(user_input: str, messages: dict, context: str = "") -> dict:
    answer_vars = sk.ContextVariables()
    answer_vars["input"] = user_input
    answer_vars["context"] = context
    logging.info("Generating answer...")
    answer = answer_plugin["getAnswer"].invoke(variables=answer_vars)
    answer = answer.result.strip()
    messages.append({'role': 'assistant', 'content': answer})
    logging.info(f"Assistant: {answer}")
    return messages


# Create Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Key vault secrets names
OPENAI_KEY_NAME = 'AzureOAIKey'
OPENAI_ENDPOINT_NAME = 'AzureOAIEndpoint'

keyvault = KeyVault()

# Get key vault secrets
openai_key = keyvault.get_secret(OPENAI_KEY_NAME)
openai_endpoint = keyvault.get_secret(OPENAI_ENDPOINT_NAME)

# Instantiate your kernel
logging.info("Instantiating kernel...")
kernel = sk.Kernel()

# Prepare Azure OpenAI service
logging.info("Adding Azure OpenAI service...")
aoai_deployment = 'gpt-35-turbo'
kernel.add_chat_service("chat", AzureTextCompletion(aoai_deployment, openai_endpoint, openai_key))

# Register plugins
logging.info("Registering plugins...")
search_plugin = kernel.import_skill(SearchPlugin(), skill_name="search_plugin")
mssales_plugin = kernel.import_skill(MSSalesPlugin(), skill_name="mssales_plugin")
answer_plugin = kernel.import_semantic_skill_from_directory("plugins", "AnswerPlugin")
orchestrator_plugin = kernel.import_semantic_skill_from_directory("plugins", "OrchestratorPlugin")

# Set up initial message
messages = [{'role': 'assistant', 'content': 'Hi, what can I help you with?'}]
logging.info("Application ready.")


@app.route('/')
def hello_world():
    return render_template('index.html', messages=messages)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    
    # Get user input from web form
    ask = request.form['message']
    global messages
    messages.append({'role': 'user', 'content': ask})
    logging.info(f"User: {ask}")

    # Detect user intent
    intent_result = detect_intent(messages)

    answer_context = ""

    # If user is asking question about account or opportunity
    if intent_result in ["AccountQuery", "OpportunityQuery"]:

        # Extract organization name to use as search query
        account_name = extract_account(messages)

        # If user is asking about account, search information in search index
        if intent_result == "AccountQuery":
            # Search for the account assignments
            try:
                answer_context = search_accounts(account_name)
            except Exception as e:
                logging.error(e)
                answer_context = f"The application looked for accounts named '{account_name}' but none were found."
        else:
            # If user is asking about opportunity, search information in CRM
            try:
                account_id = get_account_id(account_name)
                opportunities = get_opportunities(account_id)
                answer_context = "Opportunities:\n" + opportunities
            except Exception as e:
                logging.error(e)
                answer_context = f"The application looked for opportunities for accounts named '{account_name}' but none were found."

    # Generate answer
    messages = generate_answer(ask, messages, answer_context)

    return render_template('index.html', messages=messages)


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    logging.info("Resetting conversation...")
    global messages
    messages = [{'role': 'assistant', 'content': 'Hi, what can I help you with?'}]
    return render_template('index.html', messages=messages)