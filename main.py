import os
from tkinter import Toplevel, Tk
from tkinter.ttk import Label, Button, Style, Frame, Separator, Treeview, Progressbar
from tkinter.filedialog import askdirectory, askopenfilenames
from PIL import Image
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def bring_to_front(root):
    root.attributes('-topmost', 1)
    root.after(500, lambda: root.attributes('-topmost', 0))

def load_config():
    global folder_path, image_paths
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            folder_path = config.get("save_folder", "")
    else:
        folder_path = ""
    image_paths = []

def save_config():
    with open(CONFIG_FILE, "w") as file:
        json.dump({"save_folder": folder_path}, file)

def select_folder():
    global folder_path
    folder_path = askdirectory()
    if folder_path:
        folder_label.config(text=f"Save To: {folder_path}")
        save_config()

def add_padding(image_path, save_path):
    try:
        img = Image.open(image_path)
        width, height = img.size

        if abs(width - height) > 25:
            # If the difference is significant, add padding as before
            max_size = max(width, height)
            new_img = Image.new("RGB", (max_size, max_size), "black")
            paste_position = ((max_size - width) // 2, (max_size - height) // 2)
            new_img.paste(img, paste_position)
        else:
            # If the difference is small, stretch the smaller dimension
            if width > height:
                new_img = img.resize((width, width))  # Stretch height
            else:
                new_img = img.resize((height, height))  # Stretch width

        new_img.save(save_path)

    except Exception as e:
        return os.path.basename(image_path), str(e)

    return None

def select_images():
    global image_paths
    selected_images = askopenfilenames(
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff")]
    )
    add_unique_images(selected_images)

def select_folder_images():
    global image_paths
    folder_selected = askdirectory()
    if folder_selected:
        selected_images = [
            os.path.join(folder_selected, f) for f in os.listdir(folder_selected)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"))
        ]
        add_unique_images(selected_images)

def add_unique_images(selected_images):
    global image_paths
    existing_filenames = {os.path.basename(path) for path in image_paths}
    for img in selected_images:
        if os.path.basename(img) not in existing_filenames:
            image_paths.append(img)
    update_preview()

def reset_selection():
    global image_paths
    image_paths = []
    preview_list.delete(*preview_list.get_children())
    selected_count_label.config(text="Images Selected: 0")

def update_preview():
    preview_list.delete(*preview_list.get_children())
    for img in image_paths:
        item_id = preview_list.insert("", "end", values=(os.path.basename(img), "X"), tags=("redtag",))
        item_path_map[item_id] = img
    folder_label.config(text=f"Save To: {folder_path if folder_path else 'Not Selected'}")
    selected_count_label.config(text=f"Images Selected: {len(image_paths)}")

def show_large_messagebox(title, message, error=False):
    popup = Toplevel(root)
    popup.configure(bg="white", highlightthickness=0)
    popup.title(title)
    popup.geometry("600x150")
    popup.resizable(False, False)
    Label(popup, text=message, wraplength=550, style="Popup.TLabel").pack(pady=20, padx=20)
    Button(popup, text="OK", command=popup.destroy, style="Large.TButton").pack(pady=10)

def on_single_click(event):
    item_id = preview_list.identify_row(event.y)
    if not item_id:
        return
    column = preview_list.identify_column(event.x)
    if column == "#2":
        full_path = item_path_map.get(item_id)
        if full_path in image_paths:
            image_paths.remove(full_path)
        preview_list.delete(item_id)
        selected_count_label.config(text=f"Images Selected: {len(image_paths)}")

def on_double_click(event):
    item_id = preview_list.identify_row(event.y)
    if not item_id:
        return
    column = preview_list.identify_column(event.x)
    if column == "#1":
        full_path = item_path_map.get(item_id)
        try:
            img = Image.open(full_path)
            img.show()
        except Exception as e:
            show_large_messagebox("Preview Error", f"Failed to open image: {e}", error=True)
    elif column == "#2":
        full_path = item_path_map.get(item_id)
        if full_path in image_paths:
            image_paths.remove(full_path)
        preview_list.delete(item_id)
        selected_count_label.config(text=f"Images Selected: {len(image_paths)}")

def process_images():
    global image_paths
    if not image_paths:
        show_large_messagebox("Error", "No images selected! Please select images to process.", error=True)
        return
    if not folder_path:
        show_large_messagebox("Error", "No destination folder selected! Please select a save location.", error=True)
        return
    placeholder_label.pack_forget()
    progress_bar.pack()
    progress_bar["value"] = 0
    progress_bar["maximum"] = len(image_paths)
    errors = []
    processed_count = 0
    for i, img in enumerate(image_paths, start=1):
        progress_bar["value"] = i
        # Updated line: using update() to ensure the progress bar refreshes properly on macOS.
        root.update()  
        save_name = os.path.join(folder_path, os.path.basename(img))
        error = add_padding(img, save_name)
        if error:
            errors.append(error)
        else:
            processed_count += 1
    progress_bar.pack_forget()
    placeholder_label.pack(fill="both", expand=True)
    if processed_count > 0:
        success_message = f"Successfully processed {processed_count} image(s)."
        if errors:
            success_message += "\nHowever, the following image(s) failed to process:\n" + "\n".join([f"{err[0]}: {err[1]}" for err in errors])
        show_large_messagebox("Process Complete", success_message)
    else:
        error_message = "All images failed to process:\n" + "\n".join([f"{err[0]}: {err[1]}" for err in errors])
        show_large_messagebox("Processing Error", error_message, error=True)

def exit_app():
    root.destroy()

root = Tk()
root.title("Image Padding App")
root.geometry("800x800")
root.minsize(100, 100)
root.after(100, lambda: bring_to_front(root))
load_config()
style = Style()
style.theme_use("clam")
style.layout("NoHeading.Treeview.Heading", [])
style.configure("NoHeading.Treeview.Heading", borderwidth=0)
style.configure("TButton", padding=10, font=("Arial", 13), background="#dcdcdc", foreground="black")
style.configure("Large.TButton", padding=12, font=("Arial", 15), background="#dcdcdc", foreground="black")
style.configure("TLabel", font=("Arial", 13, "bold"))
style.configure("Popup.TLabel", background="white", font=("Arial", 13))
style.configure("green.Horizontal.TProgressbar", foreground="green", background="green")
frame = Frame(root, padding=20)
frame.pack(fill="both", expand=True)
def create_separator():
    Separator(frame, orient="horizontal").pack(fill="x", pady=15)
Label(frame, text="Select Images to Process").pack()
select_buttons_frame = Frame(frame)
select_buttons_frame.pack(fill="x", pady=10)
select_btn = Button(select_buttons_frame, text="Select Individual Image(s)", command=select_images)
select_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
select_folder_images_btn = Button(select_buttons_frame, text="Select Folder of Images", command=select_folder_images)
select_folder_images_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
selected_count_label = Label(frame, text="Images Selected: 0", wraplength=600, font=("Arial", 12, "bold"))
selected_count_label.pack()
preview_list = Treeview(
    frame,
    columns=("filename", "remove"),
    show="headings",
    height=10,
    style="NoHeading.Treeview"
)
preview_list.column("filename", anchor="w", width=600, stretch=True)
preview_list.column("remove", anchor="center", width=20, minwidth=20, stretch=False)
preview_list.pack(fill="both", expand=True, pady=10)
item_path_map = {}
preview_list.bind("<Button-1>", on_single_click)
preview_list.bind("<Double-Button-1>", on_double_click)
reset_btn = Button(frame, text="Reset Image Selection", command=reset_selection)
reset_btn.pack(fill="x", pady=10)
create_separator()
Label(frame, text="Select Destination Folder").pack()
folder_btn = Button(frame, text="Select Folder", command=select_folder)
folder_btn.pack(fill="x", pady=10)
folder_label = Label(
    frame,
    text=f"Save To: {folder_path if folder_path else 'Not Selected'}",
    wraplength=600,
    font=("Arial", 12)
)
folder_label.pack()
create_separator()
progress_bar_frame = Frame(frame, height=30)
progress_bar_frame.pack(fill="x", pady=(10, 10))
placeholder_label = Label(progress_bar_frame, text="")
placeholder_label.pack(fill="both", expand=True)
progress_bar = Progressbar(
    progress_bar_frame,
    orient="horizontal",
    length=300,
    mode="determinate",
    style="green.Horizontal.TProgressbar"
)
buttons_frame = Frame(frame)
buttons_frame.pack(fill="x", pady=10)
exit_btn = Button(buttons_frame, text="Exit Application", command=exit_app)
exit_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
process_btn = Button(buttons_frame, text="Process Images", command=process_images)
process_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
root.mainloop()
