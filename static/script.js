const ws = new WebSocket("ws://localhost:8888/ws");

const messagesDiv = document.getElementById("chat-messages");
const userList = document.getElementById("user-items");
const messageField = document.getElementById("message-field");
const sendBtn = document.getElementById("send-btn");
const errorMsg = document.getElementById("error-msg");

ws.onmessage = handleMessage;
ws.onopen = handleOpen;
ws.onerror = handleError;
ws.onclose = handleClose;

sendBtn.addEventListener('click', handleSend);

messageField.disabled = true;
sendBtn.disabled = true;

let myClientId = null;

function handleMessage(event) {
    console.log("Received data:", event.data);

    try {
        const data = JSON.parse(event.data);
        console.log("Parsed data:", data);

        switch (data.type) {
            case "client_id":
                myClientId = data.client_id;  
                console.log("Получен мой ID: ", myClientId);
                break;
            case "clients":
                updateClientsList(data.clients);
                break;
            case "message":
                addMessage(data.content);
                break;
            default:
                console.warn("Unknown message type:", data.type);
        }
    } catch (error) {
        console.error("Error parsing message:", error);
    }
}

function updateClientsList(clients) {
    userList.innerHTML = "";
    clients.forEach(client => {
        const clientItem = document.createElement("li");

        if (client.includes(myClientId)) {
            clientItem.textContent = `${client} (это вы)`;
            clientItem.style.fontWeight = 'bold';
        } else {
            clientItem.textContent = client;
        }

        userList.appendChild(clientItem);
    });
}

function handleOpen() {
    addMessage("Подключено к чату.");
    messageField.disabled = false;
    sendBtn.disabled = false;
}

function handleError(error) {
    addMessage("Ошибка соединения.");
}

function handleClose() {
    addMessage("Соединение потеряно.");
    messageField.disabled = true;
    sendBtn.disabled = true;
}

function handleSend() {
    const message = messageField.value.trim();
    if (message) {
        try {
            console.log("Sending message:", message);
            ws.send(message);
            messageField.value = "";
            clearError();
        } catch (error) {
            console.error("Error sending message:", error);
        }
    } else {
        showError("Пожалуйста, введите сообщение перед отправкой.");
    }
}

function addMessage(message) {
    const messageDiv = document.createElement("div");
    messageDiv.textContent = message;
    messageDiv.classList.add("chat-message");
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showError(message) {
    if (errorMsg) {
        errorMsg.textContent = message;
        messageField.classList.add("error");
    }
}

function clearError() {
    if (errorMsg) {
        errorMsg.textContent = "";
        messageField.classList.remove("error");
    }
}
