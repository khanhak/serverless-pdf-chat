import os
import json
import boto3
from aws_lambda_powertools import Logger
from langchain.llms.bedrock import Bedrock
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain


BUCKET = os.environ["BUCKET"]


s3 = boto3.client("s3")
logger = Logger()


def get_response_no_history(qa, question):
    return qa({"question": question, "chat_history": []})["answer"]


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    event_body = json.loads(event["body"])
    file_name = event_body["fileName"]
    # human_input = event_body["prompt"]
    conversation_id = event["pathParameters"]["conversationid"]

    user = event["requestContext"]["authorizer"]["claims"]["sub"]

    s3.download_file(
        BUCKET, f"{user}/{file_name}/index.faiss", "/tmp/index.faiss")
    s3.download_file(BUCKET, f"{user}/{file_name}/index.pkl", "/tmp/index.pkl")

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )

    embeddings, llm = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        client=bedrock_runtime,
        region_name="us-east-1",
    ), Bedrock(
        model_id="anthropic.claude-v2", client=bedrock_runtime, region_name="us-east-1"
    )
    faiss_index = FAISS.load_local("/tmp", embeddings)

    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=faiss_index.as_retriever(),
        return_source_documents=True,
        verbose=True,
        condense_question_llm=llm,
        chain_type="stuff",
        get_chat_history=lambda h: h,
    )
    qa.combine_docs_chain.llm_chain.prompt.template = '''
"Use the following pieces of context to answer the question at the end. 
If the answer is not present, say "Don't know", don't try to make up an answer. 
Respond in the shortest manner possible. 
If you respond in a concise answer that fully answers the question, you get $25.
If you respond with a response that makes up information, you lost $200.
If you respond with a response that says "Don't know", you lose $0.
For every extra character in your response that is unnecessary, you lose $1.
If you are able to respond in a manner that is fully parseable by python's json.loads function,
you will gain an additional $5. Remember to have a descriptive JSON key, and the value should be your response. 
Do not include the context you used in your answer, 
nor any extra English or detail\n\n{context}\n\nQuestion: {question}\n
Helpful Answer:"'''

    age = get_response_no_history(
        qa,
        "What is the patient's age using their date of birth (DOB) or directly as stated? Remember to keep your output as short as possible while fully answering the question. Output a single number or 'Don't know'",
    )
    name = get_response_no_history(
        qa,
        "What is the patient's name using their medical record or directly as stated? Remember to keep your output as short as possible while fully answering the question. Output only their name and no extra information",
    )
    meds = get_response_no_history(
        qa,
        "What are all the medications the patient has taken in the past or present using their medical record or directly as stated? Remember to keep your output as short as possible while fully answering the question. Your JSON should have 2 keys - 'past' and 'present'. Output only the JSON of their medications and dosages and no extra information",
    )
    injury = get_response_no_history(
        qa,
        "What was the injury or cause of pain as determined by the healthcare team using their medical record or directly as stated? Remember to keep your output as short as possible while fully answering the question. Your JSON should have a single key 'diagnosis'. Output only their final diagnosis and no extra information",
    )
    res_dict = {
        "age": age,
        "name": name,
        "meds": meds,
        "injury": injury
    }
    logger.info({"res dict": res_dict})

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
        },
        "body": json.dumps(res_dict),
    }
