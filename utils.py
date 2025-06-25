from openai import OpenAI
import requests
import json

# Set up OpenAI client (with Google Generative Language API)
client = OpenAI(
    api_key="AIzaSyBgqZ-sviBt6ILloqImL6HYRYaGrDNtvcs",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)



# Define the tools
def get_closest_hospital(latitude: float, longitude: float, radius: int = 500):
    # Construct the URL for Nearby Search
    while radius < 10000:
        url = (
            f'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
            f'?location={latitude},{longitude}'
            f'&radius={radius}'  # radius in meters
            f'&type=hospital'
            f'&key=AIzaSyADtffUlT1nIzumXQ6UzPNl2GzSV7k8rpU'
        )

        response = requests.get(url)
        results = response.json().get('results', [])
        if len(results) > 0:
            return results[:3]
        radius += 500
    return results[:3]  # Return the first 3 hospitals if found, else return an empty list


# Define the tool schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_closest_hospital",
            "description": "Get the closest hospital to the given latitude and longitude.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location. as a float"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location. as a float"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in meters.",
                        "default": 500
                    }
                },
                "required": ["latitude", "longitude"]
            }
        }
    }
]

avaiable_functions = {
    "get_closest_hospital": get_closest_hospital
}

def execute_tool(tool_name, parameters):
    if tool_name in avaiable_functions:
        function = avaiable_functions[tool_name]
        return function(**parameters)
    else:
        raise ValueError(f"Tool {tool_name} not found.")

def chat(prompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=prompt,
        temperature=0,
        tools=tools,
        tool_choice="auto",
    )
    return response.choices[0].message

system_prompt = {
    "role": "system",
    "content": """You are **DebeekCare**, a medical chat assistant developed by **Yusuf Idris Labaran**. Your purpose is to help users understand medical conditions, identify symptoms, and suggest possible treatments. You can also perform basic diagnostic evaluations based on user input.
    In cases of critical or emergency conditions, you may request the user's location to search for nearby hospitals using your integrated tool. If no hospital is found within the default radius, feel free to increase the search radius to provide meaningful results.
    You have access to one tool:
    - get_closest_hospital: Retrieves a list of the closest hospitals based on the user's latitude and longitude. You can also specify a custom radius in meters to expand the search area.
    - also  provide the user with direction to the hospital using the Google Maps API. with template: "https://www.google.com/maps/dir/?api=1&destination={hospital_latitude},{hospital_longitude}"
    - style your responses in a friendly and professional manner, ensuring that the user feels comfortable and supported throughout the conversation.
    - use markdown instead. wrap links in markdown format, like this: [link text](url)
        The location of the user will be appended to every user message in the following format:
        {"role": "user", "content": "{{user}}: {user_input}, location: {location}}"}
        if location is not provided, ask the user to provide allow site location access.
    If asked about your origin, state that you are an AI model fine-tuned by **Yusuf Idris Labaran**."""
}

