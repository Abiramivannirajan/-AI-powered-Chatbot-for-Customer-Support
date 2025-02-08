from tkinter import Tk, Button, Label, Frame, Entry
from PIL import Image, ImageTk
import os

class ChatbotAvatar:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatbot Avatar Customization")

        self.avatar_path = ""
        self.selected_avatar_label = Label(root, text="Selected Avatar: None")
        self.selected_avatar_label.pack()

        # Avatar display area
        self.avatar_display_label = Label(root)
        self.avatar_display_label.pack()

        # Name input section, initially hidden
        self.name_input_label = Label(root, text="Enter Avatar Name: ")
        self.name_input_label.pack_forget()  # Hide by default
        self.name_input_field = Entry(root)
        self.name_input_field.pack_forget()  # Hide by default
        self.save_name_button = Button(root, text="Save Name", command=self.save_avatar_name)
        self.save_name_button.pack_forget()  # Hide by default

        # Available avatars section
        self.avatars_frame = Frame(root)
        self.avatars_frame.pack()
        self.available_avatars = ["avatar1.png", "avatar2.png", "avatar3.png", "avatar4.png", "avatar5.png", "avatar6.png"]  # Add more as needed
        self.avatar_names = {}
        self.display_available_avatars()

    def select_avatar(self, avatar_path):
        self.avatar_path = avatar_path
        avatar_name = self.avatar_names.get(avatar_path, "Unknown Avatar")
        self.selected_avatar_label.config(text=f"Selected Avatar: {avatar_name}")

        # Show selected avatar image
        img = Image.open(avatar_path).resize((100, 100))
        img = ImageTk.PhotoImage(img)
        self.avatar_display_label.config(image=img)
        self.avatar_display_label.image = img  # Keep a reference

        # Show name input section
        self.name_input_label.pack()
        self.name_input_field.pack()
        self.save_name_button.pack()

    def display_available_avatars(self):
        for avatar in self.available_avatars:
            if os.path.exists(avatar):
                img = Image.open(avatar).resize((50, 50))
                img = ImageTk.PhotoImage(img)
                
                # Create a frame for the avatar
                avatar_frame = Frame(self.avatars_frame)
                avatar_frame.pack(side="left")
                
                # Display the avatar image
                btn = Button(avatar_frame, image=img, command=lambda a=avatar: self.select_avatar(a))
                btn.image = img  # Keep a reference
                btn.pack()

    def save_avatar_name(self):
        # Save the name for the selected avatar
        name = self.name_input_field.get()
        if name:
            self.avatar_names[self.avatar_path] = name
            self.selected_avatar_label.config(text=f"Selected Avatar: {name}")

        # Clear the name input field and hide it
        self.name_input_field.delete(0, 'end')
        self.name_input_label.pack_forget()
        self.name_input_field.pack_forget()
        self.save_name_button.pack_forget()

if __name__ == "__main__":
    root = Tk()
    app = ChatbotAvatar(root)
    root.mainloop()
