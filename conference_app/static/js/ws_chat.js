var ws_url = `wss://${window.location.host}/ws/socket-server/`;

if (window.location.protocol === 'http:') {
    ws_url = `ws://${window.location.host}/ws/socket-server/`;
}
const chatSocket = new WebSocket(ws_url);
const leaveBtn = document.getElementById('leave-btn');


form = document.getElementById('form');
form.addEventListener('submit', (e)=>{
    e.preventDefault();
    message = document.getElementById('input-msg').value.trim();
    
    if (message === '') {
        alert("Cannot send empty message.");
        return;
    }

    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'message': message
    }));
    console.log('Sent:', message);
    document.getElementById('input-msg').value = '';
});

chatSocket.onmessage = async function(e) {
    const data = JSON.parse(e.data);
    console.log('Received:', data);
    
    if (data.type === 'connected') {
        console.log('WebSocket connected:', data.message);
        messagesContainer.innerHTML += `<div style="color: green;">${data.message}</div>`;
    }

    else if (data.type === 'chat_message') {
        display_message(data);
    }
    else if (data.type === 'disconnected') {
        messagesContainer.innerHTML += `<div style="color: red;">${data.message}</div>`;
    }
};

leaveBtn.onclick = function(){
    chatSocket.close();
    window.location.href = window.location.origin + '/leave/';
};

function display_message(data) {
    var storedName = sessionStorage.getItem('storedName');
    let isMe = storedName == data.name;
    let nameLabel = isMe ? "You" : data.name;
    
    messagesContainer.innerHTML += `
        <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'}">
            <span class="text-[12px] text-slate-500 mb-1">${nameLabel} • ${data.time}</span>
            <div class="px-3 py-2 rounded-2xl max-w-[80%] ${isMe ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none'}">
                ${data.message}
            </div>
        </div>`;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
