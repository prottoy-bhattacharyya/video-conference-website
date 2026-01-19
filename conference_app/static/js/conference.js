const url = `ws://${window.location.host}/ws/socket-server/`;
const chatSocket = new WebSocket(url);
const leaveBtn = document.getElementById('leave-btn');
const file_upload = document.getElementById('file-upload');
const file_descriptions = document.getElementById('file-descriptions');
const messagesContainer = document.getElementById('messages-container');

let localStream;
let remoteStream;
let peerConnection;
const videoUser1 = document.getElementById('video-user-1');
const videoUser2 = document.getElementById('video-user-2');


//TODO: Add handle file uploads


async function create_peer_connection() {
    console.log("Value of localStream:", localStream);
    peerConnection = new RTCPeerConnection();
    localStream.getTracks().forEach(track => 
        peerConnection.addTrack(track, localStream)
    );
    peerConnection.ontrack = (event) => {
        videoUser2.style.width = '30em';
        videoUser2.srcObject = event.streams[0];
    }

    peerConnection.onicecandidate = (event) => {
        if(event.candidate){
            console.log("Candidate: ",event.candidate);
            candidateData ={
                'type': 'candidate',
                'candidate': event.candidate
            };
            chatSocket.send(JSON.stringify(candidateData));
        }
    };
}

async function initiate_call() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
    });
    } catch (error) {
        console.error("Error accessing media devices:", error);
    }
    
    videoUser1.style.width = '30em';
    videoUser1.srcObject = localStream;
    create_peer_connection();
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    console.log("Offer: ", offer);
    offerData = {
        'type': 'offer',
        'offer': offer
    };
    chatSocket.send(JSON.stringify(offerData));
}

form = document.getElementById('form');
form.addEventListener('submit', (e)=>{
    e.preventDefault();
    // message = e.target.input_msg.value;
    message = document.getElementById('input-msg').value.trim();
    if (!message && !file_upload.files.length) {
        return;
    }
    
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
        show_connection_message(data);
        initiate_call();
    }

    else if (data.type === 'chat_message') {
        display_message(data);
    }

    // WebRTC signaling messages
    else if (data.type === 'offer') {
        if (!peerConnection) create_peer_connection();

        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.offer)
        );
        console.log("Offer received:", data.offer);
        
        
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        chatSocket.send(JSON.stringify({ 'type': 'answer', 'answer': answer }));
        console.log("Answer sent:", answer);
    }
    else if (data.type === 'answer') {
        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.answer)
        );
        console.log("Answer received:", data.answer);

    } 
    else if (data.type === 'candidate') {
        if (peerConnection) {
            await peerConnection.addIceCandidate(
                new RTCIceCandidate(data.candidate)
            );
        }
        console.log("Candidate received:", data.candidate);
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

function show_connection_message(data) {
    if (data.type === 'connected') {
        messagesContainer.innerHTML += `<div style="color: green;">${data.message}</div>`;
        return;
    }
}