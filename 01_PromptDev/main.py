import json
from app import PromptApp

# Set key and create app
TEST_OPENAI_API_KEY = "PUT YOUR KEY HERE"
PromptApp = PromptApp(TEST_OPENAI_API_KEY)


if __name__ == "__main__":
    prompt = "Remembering the past and rethinking your feelings"
    universe = {
        "characters": {
            "Alice": "7 years old girl, very curious",
            "Jack": "Alice's brother, 10 years old, likes to play with his friends",
            "Bob": "Alice's father, a programmer",
            "Mary": "Alice's mother, a teacher",
        },
        "locations": {
            "reception": "a big room in Alice's house with a big table, TV and a fireplace",
            "kitchen": "a cosy kitchen in Alice's house",
            "hall": "a long hall in Alice's house",
            "park": "a park near Alice's house",
        },
        "emotions": ["happy", "sad", "angry", "surprised", "scared"],
    }

    generated_script = PromptApp.generate_movie_script(prompt, universe)

    print(generated_script)

    # print(json.dumps(generated_script, indent=4))
