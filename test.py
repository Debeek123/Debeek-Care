from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# Create a new chatbot instance
chatbot = ChatBot('SimpleBot')

# Train the chatbot using the English corpus data
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train('chatterbot.corpus.english')

# Simple loop for user interaction
print("Chatbot is ready to chat! Type 'exit' to stop.")
while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("SimpleBot: Goodbye!")
        break
    response = chatbot.get_response(user_input)
    print("Bot:", response)
