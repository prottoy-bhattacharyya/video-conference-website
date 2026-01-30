const { Room, RoomEvent, Track, VideoPresets } = LivekitClient;

const video_container = document.getElementById('video-container');
const messagesContainer = document.getElementById('messages-container');
const member_count_display = document.getElementById('member-count');

const audio_btn = document.getElementById('audio-btn');
const video_btn = document.getElementById('video-btn');
const screen_share_btn = document.getElementById('screen-share-btn');
const leave_btn = document.getElementById('leave-btn');

const livekit_server_url = sessionStorage.getItem('livekitServerUrl');
const token = sessionStorage.getItem('storedToken');

var camera_on = true;
var mic_on = true;
var screen_share_on = false; 
var member_count = 1;

const room = new Room(
    {
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
            resolution: VideoPresets.h1080.resolution,
        },
    }
);

async function initialize() {
    room.prepareConnection(livekit_server_url, token);

    await room.connect(livekit_server_url, token);
    console.log('Connected to LiveKit room: ', room.name);

    await room.localParticipant.enableCameraAndMicrophone();
    console.log('You enabled camera and microphone.');

    room
        .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
        .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);

    
    const localVideoTrack = room.localParticipant
        .getTrackPublication(Track.Source.Camera)
        .videoTrack;

    if (localVideoTrack) {
        const videoElement = localVideoTrack.attach();
        videoElement.style.width = '300px';
        videoElement.style.transform = 'scaleX(-1)';
        video_container.appendChild(videoElement);
    }

    room.remoteParticipants.forEach((participant) => {
        member_count += 1;
        participant.trackPublications.forEach((publication) => {
            if (publication.track) {
                attachTrack(publication.track, participant);
            }
        });
    });

    member_count_display.innerHTML = `${member_count} Members Online`;
}


function attachTrack(track, participant) {
    if (track.kind === Track.Kind.Video || track.kind === Track.Kind.Audio) {
        const element = track.attach();
        element.style.width = '300px';
        element.setAttribute('data-participant-id', participant.identity);
        element.innerHTML = participant.identity;
        video_container.appendChild(element);
    }
}

function handleTrackSubscribed(track, publication, participant) {
    messagesContainer.innerHTML += `<div style="color: green;">${participant.identity} Joined the room</div>`;
    attachTrack(track, participant);
    updateMemberCountDisplay();
}

function handleTrackUnsubscribed(track, publication, participant) {
    track.detach();
    updateMemberCountDisplay();
    messagesContainer.innerHTML += `<div style="color: red;">${participant.identity} Disconnected from room</div>`;
}

function updateMemberCountDisplay() {
    member_count = 1;
    room.remoteParticipants.forEach((participant) => {
        member_count += 1;
    });
    member_count_display.innerHTML = `${member_count} Members Online`;
}

audio_btn.addEventListener('click',async () => {
    mic_on = !mic_on;
    await room.localParticipant.setMicrophoneEnabled(mic_on);
    audio_btn.textContent = mic_on ? 'Mute Audio' : 'Unmute Audio';
});

video_btn.addEventListener('click',async () => {
    camera_on = !camera_on;
    await room.localParticipant.setCameraEnabled(camera_on);
    video_btn.textContent = camera_on ? 'Mute Video' : 'Unmute Video';
});

screen_share_btn.addEventListener('click',async () => {
    screen_share_on = !screen_share_on;
    try {
        await room.localParticipant.setScreenShareEnabled(screen_share_on);
    } catch (error) {
        console.error('Error toggling screen share:', error);
        screen_share_on = false;
    }
    screen_share_btn.textContent = screen_share_on ? 'Stop Screen Share' : 'Start Screen Share';

});

initialize();