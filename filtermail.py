# Use GPT to respond with a certain json format
# { 
#   isInterview: True or False,
#   lengthOfInterview: some time, default to 90
#   importance: "High", "Medium", or "Low"
# }

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Create a client
client = OpenAI(api_key=api_key)


def filterEmail(sender, subject, body):

    # Provide a prompt
    prompt = f"""You are a professional fraud detection reader. You are going to be reading \
    emails, and provide a json response with the following format. [isInterview: True or False, 
    lengthOfInterview: some time, default to 90 if not provided (represents minutes), importance: High (interview needs to be done in next 3 days), Medium (needs to be done in next week (needs to be done in next two weeks) ], defaults to Low. Here is the information.   \
    Sender: {sender}
    Subject: {subject}
    Body: {body}
    Provide the json and nothing else.
"""

    # Send to API
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # or "gpt-4o" / "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    print(response.choices[0].message.content)




