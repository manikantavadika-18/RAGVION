document.addEventListener("DOMContentLoaded", () => {
    const newChatBtn = document.getElementById("newChat");
    const chat = document.getElementById("chat");
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const kbCount = document.getElementById("kbCount");
    const syntheticBtn = document.getElementById("syntheticBtn");
    const clearBtn = document.getElementById("clearBtn");

    let conversationHistory = [];

    /* =====================================================
       TOAST
    ====================================================== */

    function showToast(message, type = "") {
        const toast = document.getElementById("toast");

        if (!toast) return;

        toast.textContent = message;
        toast.className = "toast";

        if (type) {
            toast.classList.add(type);
        }

        toast.classList.add("show");

        setTimeout(() => {
            toast.classList.remove("show");
        }, 3000);
    }


    /* =====================================================
       NEW CHAT
    ====================================================== */

    function startNewChat() {
        // Reset conversation history
        conversationHistory = [];

        // Clear input
        if (input) {
            input.value = "";
            input.disabled = false;
        }

        // Enable send button
        if (sendBtn) {
            sendBtn.disabled = false;
        }

        // Restore welcome screen
        if (chat) {
            chat.innerHTML = `
                <div id="welcome" class="welcome">

                    <div class="welcome-icon">
                        ✦
                    </div>

                    <h2>
                        What can I help you understand?
                    </h2>

                    <p>
                        Upload your documents and ask questions.
                        RAGVION retrieves relevant content before
                        generating the answer.
                    </p>

                    <div class="suggestions">

                        <button class="suggestion">
                            Summarize my uploaded document
                        </button>

                        <button class="suggestion">
                            What are the key concepts?
                        </button>

                        <button class="suggestion">
                            Explain this topic simply
                        </button>

                        <button class="suggestion">
                            Create questions from the document
                        </button>

                    </div>

                </div>
            `;

            attachSuggestionEvents();
        }

        // Focus input
        if (input) {
            input.focus();
        }

        showToast("New chat started");
    }


    if (newChatBtn) {
        newChatBtn.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            startNewChat();
        });
    }


    /* =====================================================
       MESSAGE UI
    ====================================================== */

    function addMessage(role, text = "") {
        if (!chat) return null;

        const welcome = document.getElementById("welcome");

        if (welcome) {
            welcome.remove();
        }

        const message = document.createElement("div");

        message.className = `message ${role}`;

        if (role === "user") {
            message.innerHTML = `
                <div class="message-content">
                    ${escapeHtml(text)}
                </div>
            `;
        } else {
            message.innerHTML = `
                <div class="message-content"></div>
            `;
        }

        chat.appendChild(message);

        chat.scrollTop = chat.scrollHeight;

        return message.querySelector(".message-content");
    }


    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }


    /* =====================================================
       SEND MESSAGE
    ====================================================== */

    async function sendMessage(customMessage = null) {

        if (!input || !sendBtn) return;

        const message =
            customMessage !== null
                ? customMessage.trim()
                : input.value.trim();

        if (!message) {
            return;
        }

        const historyBeforeMessage = [...conversationHistory];

        addMessage("user", message);

        input.value = "";

        input.disabled = true;
        sendBtn.disabled = true;

        const assistantElement = addMessage("assistant", "");

        let answer = "";

        try {

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message,
                    history: historyBeforeMessage
                })
            });


            if (!response.ok) {

                let errorMessage = "Request failed.";

                try {
                    const errorData = await response.json();

                    errorMessage =
                        errorData.error ||
                        errorData.message ||
                        errorMessage;

                } catch (_) {}

                throw new Error(errorMessage);
            }


            const reader = response.body.getReader();

            const decoder = new TextDecoder();

            let buffer = "";


            while (true) {

                const { value, done } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, {
                    stream: true
                });


                const events = buffer.split("\n\n");

                buffer = events.pop();


                for (const event of events) {

                    if (!event.startsWith("data:")) {
                        continue;
                    }

                    const dataText = event
                        .replace(/^data:\s*/, "")
                        .trim();

                    if (!dataText) {
                        continue;
                    }


                    let data;

                    try {
                        data = JSON.parse(dataText);
                    } catch (_) {
                        continue;
                    }


                    /* SOURCES */

                    if (data.type === "sources") {

                        continue;
                    }


                    /* TOKEN */

                    if (data.type === "token") {

                        answer += data.text || "";

                        if (assistantElement) {

                            assistantElement.innerHTML =
                                formatAnswer(answer);

                        }

                        chat.scrollTop = chat.scrollHeight;
                    }


                    /* ERROR */

                    if (data.type === "error") {

                        throw new Error(
                            data.message ||
                            "Gemini request failed."
                        );
                    }


                    /* DONE */

                    if (data.type === "done") {

                        continue;
                    }
                }
            }


            if (!answer.trim()) {

                if (assistantElement) {

                    assistantElement.innerHTML =
                        "I couldn't generate an answer.";

                }
            }


            conversationHistory.push({
                role: "user",
                content: message
            });


            conversationHistory.push({
                role: "assistant",
                content: answer
            });


        } catch (error) {

            console.error("Chat error:", error);

            if (assistantElement) {

                assistantElement.innerHTML = `
                    <div class="error-message">
                        ⚠️ ${escapeHtml(
                            error.message ||
                            "Something went wrong."
                        )}
                    </div>
                `;
            }

            showToast(
                error.message ||
                "Something went wrong.",
                "error"
            );

        } finally {

            input.disabled = false;
            sendBtn.disabled = false;

            input.focus();
        }
    }


    /* =====================================================
       FORMAT ANSWER
    ====================================================== */

    function formatAnswer(text) {

        if (!text) {
            return "";
        }

        let safe = escapeHtml(text);

        safe = safe.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );

        safe = safe.replace(
            /\n/g,
            "<br>"
        );

        return safe;
    }


    /* =====================================================
       SEND BUTTON
    ====================================================== */

    if (sendBtn) {

        sendBtn.addEventListener("click", function (event) {

            event.preventDefault();

            sendMessage();

        });

    }


    /* =====================================================
       ENTER KEY
    ====================================================== */

    if (input) {

        input.addEventListener("keydown", function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();

            }

        });

    }


    /* =====================================================
       QUICK SUGGESTIONS
    ====================================================== */

    function attachSuggestionEvents() {

        const suggestions =
            document.querySelectorAll(".suggestion");

        suggestions.forEach(button => {

            button.addEventListener("click", function (event) {

                event.preventDefault();

                const text =
                    this.textContent.trim();

                if (text) {
                    sendMessage(text);
                }

            });

        });

    }


    attachSuggestionEvents();


    /* =====================================================
       FILE UPLOAD
    ====================================================== */

    if (fileInput) {

        fileInput.addEventListener("change", async function () {

            const file = this.files[0];

            if (!file) {
                return;
            }


            if (uploadStatus) {

                uploadStatus.textContent =
                    "Uploading and processing...";

            }


            const formData = new FormData();

            formData.append("file", file);


            try {

                const response = await fetch(
                    "/api/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


                const data = await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        data.message ||
                        "Upload failed."
                    );

                }


                if (uploadStatus) {

                    uploadStatus.textContent =
                        data.message ||
                        "Document uploaded successfully.";

                }


                showToast(
                    "Document uploaded successfully"
                );


                updateKnowledgeBaseCount();


            } catch (error) {

                console.error(
                    "Upload error:",
                    error
                );


                if (uploadStatus) {

                    uploadStatus.textContent =
                        error.message ||
                        "Upload failed.";

                }


                showToast(
                    error.message ||
                    "Upload failed.",
                    "error"
                );

            } finally {

                fileInput.value = "";

            }

        });

    }


    /* =====================================================
       KNOWLEDGE BASE COUNT
    ====================================================== */

    async function updateKnowledgeBaseCount() {

        if (!kbCount) {
            return;
        }


        try {

            const response =
                await fetch("/api/health");


            const data =
                await response.json();


            if (
                response.ok &&
                data.status === "ok"
            ) {

                const count =
                    data.documents || 0;

                kbCount.textContent =
                    `${count} document chunks indexed`;

            } else {

                kbCount.textContent =
                    "Knowledge base unavailable";

            }

        } catch (error) {

            console.error(
                "Health check error:",
                error
            );

            kbCount.textContent =
                "Knowledge base unavailable";

        }

    }


    updateKnowledgeBaseCount();


    /* =====================================================
       CLEAR KNOWLEDGE BASE
    ====================================================== */

    if (clearBtn) {

        clearBtn.addEventListener(
            "click",
            async function (event) {

                event.preventDefault();


                const confirmed =
                    confirm(
                        "Are you sure you want to clear the knowledge base?"
                    );


                if (!confirmed) {
                    return;
                }


                try {

                    const response =
                        await fetch(
                            "/api/clear",
                            {
                                method: "POST"
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.error ||
                            "Failed to clear knowledge base."
                        );

                    }


                    showToast(
                        "Knowledge base cleared"
                    );


                    updateKnowledgeBaseCount();


                } catch (error) {

                    console.error(
                        "Clear error:",
                        error
                    );


                    showToast(
                        error.message ||
                        "Failed to clear knowledge base.",
                        "error"
                    );

                }

            }
        );

    }


    /* =====================================================
       SYNTHETIC Q&A
    ====================================================== */

    if (syntheticBtn) {

        syntheticBtn.addEventListener(
            "click",
            async function (event) {

                event.preventDefault();

                try {

                    syntheticBtn.disabled = true;

                    syntheticBtn.textContent =
                        "🧪 Generating...";


                    const response =
                        await fetch(
                            "/api/synthetic",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },
                                body: JSON.stringify({
                                    count: 5
                                })
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.error ||
                            "Synthetic Q&A generation failed."
                        );

                    }


                    const items =
                        data.items || [];


                    if (!items.length) {

                        showToast(
                            "No synthetic questions generated."
                        );

                        return;

                    }


                    const formatted =
                        items
                            .map(
                                (item, index) =>
                                    `${index + 1}. ${
                                        item.question ||
                                        item.q ||
                                        "Question"
                                    }\n\nAnswer: ${
                                        item.answer ||
                                        item.a ||
                                        "No answer"
                                    }`
                            )
                            .join("\n\n");


                    addMessage(
                        "assistant",
                        formatted
                    );


                } catch (error) {

                    console.error(
                        "Synthetic Q&A error:",
                        error
                    );


                    showToast(
                        error.message ||
                        "Synthetic Q&A failed.",
                        "error"
                    );

                } finally {

                    syntheticBtn.disabled = false;

                    syntheticBtn.textContent =
                        "🧪 Generate synthetic Q&A";

                }

            }
        );

    }


    /* =====================================================
       AUTO RESIZE TEXTAREA
    ====================================================== */

    if (input) {

        input.addEventListener(
            "input",
            function () {

                this.style.height = "auto";

                this.style.height =
                    Math.min(
                        this.scrollHeight,
                        180
                    ) + "px";

            }
        );

    }

});