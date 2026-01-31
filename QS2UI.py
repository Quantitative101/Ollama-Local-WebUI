from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# =========================
# LOCAL CONFIG
# =========================
# Run: ollama pull gemma3:12b
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "gemma3:12b" 
PORT = 8080
# =========================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemma 3 Local Assistant</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root { --bg: #f8f9fa; --primary: #1a73e8; --text: #202124; }
        body { font-family: 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; display: flex; flex-direction: column; height: 100vh; }
        
        header { background: white; padding: 1rem 2rem; border-bottom: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        h2 { margin: 0; font-weight: 500; color: var(--primary); font-size: 1.25rem; }

        #chat-container { flex: 1; overflow-y: auto; padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }
        .message { max-width: 800px; padding: 1rem 1.5rem; border-radius: 12px; line-height: 1.6; }
        .user { background: #e8f0fe; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai { background: white; align-self: flex-start; border-bottom-left-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }

        footer { background: white; padding: 1.5rem 2rem; border-top: 1px solid #ddd; }
        .input-group { max-width: 800px; margin: 0 auto; display: flex; gap: 10px; }
        textarea { flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 8px; resize: none; font-size: 1rem; font-family: inherit; }
        button { background: var(--primary); color: white; border: none; padding: 0 24px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: opacity 0.2s; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        
        pre { background: #f1f3f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        code { font-family: 'Consolas', monospace; font-size: 0.9rem; }
    </style>
</head>
<body>
    <header><h2>Gemma 3 Assistant (12B)</h2></header>

    <div id="chat-container">
        <div class="message ai">Hello! I'm Gemma 3. How can I help you today?</div>
    </div>

    <footer>
        <div class="input-group">
            <textarea id="prompt" rows="1" placeholder="Type your message..." oninput="autoResize(this)"></textarea>
            <button id="send-btn" onclick="sendPrompt()">Send</button>
        </div>
    </footer>

    <script>
    function autoResize(el) {
        el.style.height = 'auto';
        el.style.height = el.scrollHeight + 'px';
    }

    async function sendPrompt() {
        const input = document.getElementById("prompt");
        const chat = document.getElementById("chat-container");
        const btn = document.getElementById("send-btn");
        const text = input.value.trim();

        if (!text) return;

        // Add User Message
        const userDiv = document.createElement("div");
        userDiv.className = "message user";
        userDiv.textContent = text;
        chat.appendChild(userDiv);

        // Prepare AI Response placeholder
        const aiDiv = document.createElement("div");
        aiDiv.className = "message ai";
        aiDiv.textContent = "...";
        chat.appendChild(aiDiv);
        
        input.value = "";
        input.style.height = 'auto';
        btn.disabled = true;
        chat.scrollTop = chat.scrollHeight;

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: text })
            });
            const data = await response.text();
            
            // Render Markdown
            aiDiv.innerHTML = marked.parse(data);
        } catch (e) {
            aiDiv.textContent = "Error: " + e;
        } finally {
            btn.disabled = false;
            chat.scrollTop = chat.scrollHeight;
        }
    }

    // Allow Enter key to send (Shift+Enter for newline)
    document.getElementById("prompt").addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendPrompt();
        }
    });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    prompt = data.get("prompt", "")

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=240) # 12B might take longer to respond
        r.raise_for_status()
        response_json = r.json()
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)