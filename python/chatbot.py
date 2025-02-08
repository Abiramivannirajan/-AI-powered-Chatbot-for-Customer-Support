import pickle

# Load the trained model
with open("chatbot_model.pkl", "rb") as f:
    vectorizer, model, questions, answers = pickle.load(f)

def get_answer(user_question):
    """Find the best answer for a given question."""
    user_vector = vectorizer.transform([user_question])
    _, index = model.kneighbors(user_vector)
    return answers[index[0][0]]

# Example usage
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Chatbot: Goodbye!")
        break
    response = get_answer(user_input)
    print(f"Chatbot: {response}")
# chatbot_avatar.py
from tkinter import Tk, Label, Button, filedialog
from PIL import Image, ImageTk

class ChatbotAvatar:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot Avatar Customization")

        self.avatar_path = "default-avatar.png"
        self.avatar_label = Label(root)
        self.avatar_label.pack()
        self.update_avatar()

        self.upload_button = Button(root, text="Change Avatar", command=self.change_avatar)
        self.upload_button.pack()

    def update_avatar(self):
        image = Image.open(self.avatar_path)
        image = image.resize((100, 100))
        self.avatar_image = ImageTk.PhotoImage(image)
        self.avatar_label.config(image=self.avatar_image)

    def change_avatar(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.avatar_path = file_path
            self.update_avatar()

if __name__ == "__main__":
    root = Tk()
    app = ChatbotAvatar(root)
    root.mainloop()
