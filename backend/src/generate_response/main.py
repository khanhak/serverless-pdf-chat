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


MEMORY_TABLE = os.environ["MEMORY_TABLE"]
BUCKET = os.environ["BUCKET"]


s3 = boto3.client("s3")
logger = Logger()


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    event_body = json.loads(event["body"])
    file_name = event_body["fileName"]
    human_input = event_body["prompt"]
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

    message_history = DynamoDBChatMessageHistory(
        table_name=MEMORY_TABLE, session_id=conversation_id
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        chat_memory=message_history,
        input_key="question",
        output_key="answer",
        return_messages=True,
    )

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=faiss_index.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )

    res = qa({"question": human_input})
    ans = '''" Based on the context provided, it seems you are asking for more clarification on Form 1098-T and the information it contains. \n\nForm 1098-T is a tuition statement that eligible educational institutions send to students to report payments received for qualified tuition and related expenses in a calendar year. It contains information like:\n\n- The total payments received by the school from any source for the student's qualified tuition and related expenses in the calendar year (Box 1)\n\n- Any reimbursements or refunds made for qualified tuition and related expenses during the year that relate to payments received in the same calendar year (Box 1) \n\n- Any prior year adjustments made by the school for qualified tuition and related expenses reported on a prior year's Form 1098-T (Box 4)\n\n- Total scholarships or grants administered and processed by the school during the calendar year (Box 5)\n\n- Any prior year adjustments made to scholarships or grants reported on a prior year's Form 1098-T (Box 6)\n\nThe student uses this form when completing their tax return to determine eligibility for education tax credits like the American Opportunity Credit or Lifetime Learning Credit. \n\nPlease let me know if you need any clarification on a specific aspect of the",
        "source_documents": [
          "page_content='Box 10. Shows the total amount of reimbursements or refunds of qualified tuition and \\nrelated expenses made by an insurer. The amount of reimbursements or refunds for the \\ncalendar year may reduce the amount of any education credit you can claim for the year \\n(may result in an increase in tax liability for the year of the refund). \\nFuture developments.  For the latest information about developments related to Form \\n1098-T and its instructions, such as legislation enacted after they were published, go to \\nwww.irs.gov/Form1098T . \\nFree File Program.  Go to www.irs.gov/FreeFile to see if you qualify for no-cost online \\nfederal tax preparation, e-filing, and direct deposit or payment options.\\nThe information shown on this form has been provided to the IRS.\\nDetailed financial information is available to the student at Wolverine Access>Student Business\\nhttps://wolverineaccess.umich.edu\\nThe University of Michigan cannot provide individual tax advice and shall not be liable for damages of any' metadata={'source': '/tmp/HANEEF-KHAN-1098T.pdf', 'page': 1}",
          "page_content='Box 2. Reserved for future use. \\nBox 3. Reserved for future use. \\nBox 4. Shows any adjustment made by an eligible educational institution for a prior \\nyear for qualified tuition and related expenses that were reported on a prior year \\nForm 1098-T. This amount may reduce any allowable education creditthat you claimed for the prior year (may result in an increase in tax liability for the year of the\\nrefund). See \"recapture\" in the index to Pub. 970 to report a reduction in your education \\ncredit or tuition and fees deduction. \\nBox 5. Shows the total of all scholarships or grants administered and processed by the \\neligible educational institution. The amount of scholarships or grants for the calendar year \\n(including those not reported by the institution) may reduce the amount of the education \\ncredit you claim for the year. TIP: You may be able to increase the combined value of an \\neducation credit and certain educational assistance (including Pell Grants) if the student' metadata={'source': '/tmp/HANEEF-KHAN-1098T.pdf', 'page': 1}",
          "page_content=\"£CORRECTED\\nFILER'S name, street address, city or town, province or state, country, ZIP or \\nforeign postal code, and telephone number\\nThe University of Michigan\\n2226 Student Activities Bldg\\n515 East Jefferson St\\nAnn Arbor, MI 48109-1316\\nStudent Financial Services: 877/840-47381 Payments received for \\nqualified tuition and related \\nexpenses\\n$ 31223.19OMB No.1545-1574\\n2023\\nForm 1098- TTuition\\nStatement 2  \\nFILER'S federal Identification no.\\n386006309STUDENT'S  taxpayer identification no.\\n*****26673  Copy B\\nFor Student\\n       This is \\nimportant \\n         tax information\\nand is being \\nfurnished to the \\nInternal Revenue \\nService. This form \\nmust be used to \\ncomplete Form 8863\\nto claim education \\ncredits. Give it to the\\ntax preparer or use it\\nto prepare the tax \\nreturn.  STUDENT'S name\\nHaneef  A  Khan  4  Adjustments made for a \\nprior year\\n$ 5  Scholarships or       \\ngrants\\n$ \\nStreet address (including apt. no.)\\n43122 Meadow Grove Dr6  Adjustments to  \\nscholarships or grants for \\na prior year\" metadata={'source': '/tmp/HANEEF-KHAN-1098T.pdf', 'page': 0}",
          "page_content=\"provider. Although the filer or the service provider may be able to answer certain \\nquestions about the statement, do not contact the filer or the service provider for \\nexplanations of the requirements for (and how to figure) any education credit that you\\nmay claim. \\nStudent's taxpayer identification number (TIN) . For your protection, this form may \\nshow only the last four digits of your TIN (SSN, ITIN, ATIN, or EIN). However, the \\nissuer has reported your complete TIN to the IRS. Caution: If your TIN is not shown \\nin this box, your school was not able to provide it. Contact your school if you have \\nquestions. \\nAccount number . May show an account or other unique number the filer assigned to\\ndistinguish your account. \\nBox 1. Shows the total payments received by an eligible educational institution in \\n2023 from any source for qualified tuition and related expenses less any \\nreimbursements or refunds made during 2023 that relate to those payments received \\nduring 2023.\" metadata={'source': '/tmp/HANEEF-KHAN-1098T.pdf', 'page': 1}"'''
    logger.info(res)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
        },
        # "body": json.dumps(res["answer"]),
        "body": json.dumps(ans)
    }
