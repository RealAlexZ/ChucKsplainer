import base64

css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
    width: 20%;
}
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
}
.chat-message .message {
    width: 80%;
    padding: 0 1.5rem;
    color: #fff;
}
'''

def get_image_as_base64(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

ai_logo = get_image_as_base64("assets/ai-logo.png")
human_logo = get_image_as_base64("assets/human-logo.png")

bot_template = f'''
<div class="chat-message bot">
    <div class="avatar">
        <img src="data:image/png;base64,{ai_logo}" alt="Bot Avatar" style="max-height: 50px; max-width: 50px; object-fit: cover;">
    </div>
    <div class="message">{{{{MSG}}}}</div>
</div>
'''

user_template = f'''
<div class="chat-message user">
    <div class="avatar">
        <img src="data:image/png;base64,{human_logo}" alt="User Avatar" style="max-height: 50px; max-width: 50px; object-fit: cover;">
    </div>    
    <div class="message">{{{{MSG}}}}</div>
</div>
'''