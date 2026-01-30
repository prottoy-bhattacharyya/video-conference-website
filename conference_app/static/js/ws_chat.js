var ws_url = `wss://${window.location.host}/ws/socket-server/`;

if (window.location.protocol === 'http:') {
    ws_url = `ws://${window.location.host}/ws/socket-server/`;
}
const chatSocket = new WebSocket(ws_url);
const leaveBtn = document.getElementById('leave-btn');



form = document.getElementById('form');
form.addEventListener('submit', (e)=>{
    e.preventDefault();
    // message = e.target.input_msg.value;
    message = document.getElementById('input-msg').value.trim();
    
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'message': message
    }));
    console.log('Sent:', message);
    e.target.input_msg.value = '';
});

chatSocket.onmessage = async function(e) {
    const data = JSON.parse(e.data);
    console.log('Received:', data);
    
    // Handle different messages
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
    if (storedName == data.name) {
        data.name = "You";
    }
    messagesContainer.innerHTML += `<div> 
                                        ${data.name}: ${data.message} 
                                        [${data.time}]
                                    </div>`;    
}
