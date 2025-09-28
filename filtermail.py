# All good

import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from scheduleInterview import schedule_from_payload

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def filterEmail(sender, subject, body):

    # can alter the prompt to get different desired json results
    # This file calls the schedule_from_payload fxn from scheduleInterview.py
    # filterEmail gets called by pullnewemail.py which looks at all emails
    prompt = f"""
    You are an assistant that reads emails and extracts scheduling information
    for interviews. You must ONLY return a valid JSON object matching this schema:

    {{
    "isInterview": true or false,       // whether this email is about an interview
    "lengthOfInterview": number,        // minutes, default 90 if not provided
    "importance": "High" | "Medium" | "Low",  // High = interview in next 3 days,
                                                // Medium = within a week,
                                                // Low = within 2 weeks, Low if not provided
    "nameOfMeeting": string,            // descriptive meeting name based on company name
    "Time zone": "Continent/City"       // e.g. "America/Los_Angeles", if not provided, set to "America/Los_Angeles"
    }}

    Input email:
    Sender: {sender}
    Subject: {subject}
    Body: {body}

    Return ONLY the JSON payload. No extra text.
    """

    # OpenAI GPT call
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # e.g. "gpt-4o" / "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # check is response loads into json
    content = response.choices[0].message.content
    try:
        json_object = json.loads(content)
    except json.JSONDecodeError:
        print("Could not parse response as JSON:", content)
        return None

    # debug print statement
    print("Parsed interview payload:", json_object)

    # call schedule from payload only if it is marked as interview
    if json_object.get("isInterview", False):
        scheduled_event = schedule_from_payload(json_object)
        print("Scheduled event:", scheduled_event)
        return scheduled_event

    return json_object






