import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from plugins.SearchPlugin import SearchPlugin
from keyvault import KeyVault
from flask import Flask, render_template, request

def get_message_history(messages):
    # join messages with line breaks into one string
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])

# Create Flask app
app = Flask(__name__)

# Key vault secrets names
OPENAI_KEY_NAME = 'AzureOAIKey'
OPENAI_ENDPOINT_NAME = 'AzureOAIEndpoint'

keyvault = KeyVault()

# Get key vault secrets
openai_key = keyvault.get_secret(OPENAI_KEY_NAME)
openai_endpoint = keyvault.get_secret(OPENAI_ENDPOINT_NAME)

# Instantiate your kernel
kernel = sk.Kernel()

# Prepare Azure OpenAI service
aoai_deployment = 'gpt-35-turbo'
kernel.add_chat_service("chat", AzureTextCompletion(aoai_deployment, openai_endpoint, openai_key))

# Register plugins
search_plugin = kernel.import_skill(SearchPlugin(), skill_name="search_plugin")
answer_plugin = kernel.import_semantic_skill_from_directory("plugins", "AnswerPlugin")
orchestrator_plugin = kernel.import_semantic_skill_from_directory("plugins", "OrchestratorPlugin")

# Set up initial message
messages = [{'role': 'assistant', 'content': 'Hi, what can I help you with?'}]


@app.route('/')
def hello_world():
    return render_template('index.html', messages=messages)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    
    # Get user input from web form
    ask = request.form['message']
    messages.append({'role': 'user', 'content': ask})

    # Detect user intent
    intent_vars = sk.ContextVariables()
    intent_vars["input"] = ask
    intent_vars["options"] = "AccountQuery, Other"
    intent_vars["history"] = get_message_history(messages)
    intent = orchestrator_plugin["getIntent"].invoke(variables=intent_vars)
    intent_result = intent.result.strip()

    if intent_result == "AccountQuery":

        # Extract organization name to use as search query
        query_vars = sk.ContextVariables()
        query_vars["input"] = ask
        query_vars["history"] = get_message_history(messages)
        query = orchestrator_plugin["getQuery"].invoke(variables=query_vars)
        query_clean = query.result.replace("<|im_end|>", "").strip()
        #print(f"Query: {query_clean}")

        # Search for the account
        search_result = search_plugin["getAccount"].invoke(query_clean)
        #print(f"Search result: {search_result}")

        # Set up context variables
        answer_vars = sk.ContextVariables()
        answer_vars["input"] = ask
        answer_vars["context"] = search_result.result

        # Generate answer
        answer = answer_plugin["getAnswer"].invoke(variables=answer_vars)
        answer = answer.result.strip()
        messages.append({'role': 'assistant', 'content': answer})
        print(answer)

    else:
        
        # Generate answer
        answer = answer_plugin["getAnswer"].invoke(ask)
        answer = answer.result.strip()
        messages.append({'role': 'assistant', 'content': answer})
        print(answer)

    return render_template('index.html', messages=messages)


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    global messages
    messages = [{'role': 'assistant', 'content': 'Hi, what can I help you with?'}]
    return render_template('index.html', messages=messages)