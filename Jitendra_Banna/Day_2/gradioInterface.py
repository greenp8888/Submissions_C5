import gradio as gr

# def greet(name):
#     return "Hello, " + name + "!"


def greet_with_age(name, age):
    return f"Hello, {name}! You are {age} years old."

def analyze_text(text):
    word_count = len(text.split())
    char_count = len(text)
    return f"Word Count: {word_count}", f"Character Count: {char_count}"

def echo_text(text):
    return text

def double_number(number):
    return number * 2

def add_ten(value):
    return value + 10

def check_status(is_checked):
    return f"Checkbox is {'checked' if is_checked else 'unchecked'}"

def show_choice(choice):
    return f"You selected: {choice}"

def process_image(image):
    # In a real application, you would process the image here
    # For this example, we just return the image
    return image

def greet_custom(name):
    return "Hello, " + name + "!"

def greet(name):
    return "Hello, " + name + "!"

# Create the interface
# inputs='text' specifies a textbox input
# outputs='text' specifies a textbox output
demo = gr.Interface(fn=greet, inputs="text", outputs="text", flagging_mode="never")

# Inputs as a list: [textbox for name, number input for age]
demo1 = gr.Interface(fn=greet_with_age, inputs=["text", "number"], outputs="text", flagging_mode="never")

# Outputs as a list: [textbox for word count, textbox for character count]
demo2 = gr.Interface(fn=analyze_text, inputs="text", outputs=["text", "text"],flagging_mode="auto")



demo_textbox = gr.Interface(
    fn=echo_text,
    inputs=gr.Textbox(label="Enter some text"),
    outputs=gr.Textbox(label="Echoed text"),
    title="Textbox Example"
)

demo_number = gr.Interface(
    fn=double_number,
    inputs=gr.Number(label="Enter a number"),
    outputs=gr.Number(label="Doubled number"),
    title="Number Example"
)

demo_splider = gr.Interface(
    fn=add_ten,
    inputs=gr.Slider(minimum=0,maximum=100, label='Select a Value :'),
    outputs=gr.Number(label="Value + 10"),
    title="Slider Example"
)

demo_checkbox = gr.Interface(
    fn=check_status,
    inputs=gr.Checkbox(label="Check this box"),
    outputs=gr.Textbox(label="Status"),
    title="Checkbox Example"
)

demo_dropdown = gr.Interface(
    fn=show_choice,
    inputs=gr.Dropdown(["Option A", "Option B", "Option C"], label="Choose an option"),
    outputs=gr.Textbox(label="Your choice"),
    title="Dropdown Example"
)

demo_image = gr.Interface(
    fn=process_image,
    inputs=gr.Image(label="Upload an image"),
    outputs=gr.Image(label="Processed image"),
    title="Image Example"
)

demo_custom = gr.Interface(
    fn=greet_custom,
    inputs=gr.Textbox(label="Enter Your Name", placeholder="Type here...", lines=2),
    outputs=gr.Textbox(label="Greeting Output"),
    title="Customized Greeting App"
)

demo_greet = gr.Interface(fn=greet, inputs="text", outputs="text")
# Launch the interface
# The launch() method starts a local server
# You can access the interface at the displayed URL
#demo.launch()
# demo1.launch()
# demo2.launch()
# demo_textbox.launch()
# demo_number.launch()
# demo_splider.launch()
# demo_checkbox.launch()
# demo_dropdown.launch()
# demo_image.launch()
# demo_custom.launch()
demo_greet.launch()