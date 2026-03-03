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

let camera_on = true;
let mic_on = true;
let screen_share_on = false;

const room = new Room({
    adaptiveStream: true,
    dynacast: true,
    videoCaptureDefaults: {
        resolution: VideoPresets.h720.resolution,
        resolution: VideoPresets.h1080.resolution,
    },
});

async function initialize() {
    try {
        await room.connect(livekit_server_url, token);
        // Add existing participants
        room.remoteParticipants.forEach((participant) => {
            participant.trackPublications.forEach((publication) => {
                if (publication.track) {
                    attachTrack(publication.track, participant);
                }
            });
        });
        console.log('Connected to Room:', room.name);

        // Take Permission and Publish Local Tracks
        await room.localParticipant.enableCameraAndMicrophone();
        
        
        room
            .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(RoomEvent.ParticipantConnected, updateMemberCountDisplay)
            .on(RoomEvent.ParticipantDisconnected, updateMemberCountDisplay);

        // Local Video
        attachTrack(
            room.localParticipant.getTrackPublication(Track.Source.Camera).videoTrack, 
            room.localParticipant,
            true // isLocal flag
        );

        updateMemberCountDisplay();
    } catch (error) {
        console.error('Failed to connect:', error);
    }
}



function attachTrack(track, participant, isLocal = false) {
    if (!track) return;

    if (track.kind === Track.Kind.Video) {
        const participantId = `container-${participant.identity}`;
        let container = document.getElementById(participantId);

       
        if (!container) {
            container = document.createElement('div');
            container.id = participantId;
            container.className = "relative rounded-2xl overflow-hidden bg-slate-900 aspect-video shadow-2xl border border-slate-800 group flex items-center justify-center";
        
            const initials = participant.identity.charAt(0).toUpperCase();
            const placeholder = document.createElement('div');
            placeholder.id = `fallback-${participant.identity}`;
            placeholder.className = "w-20 h-20 rounded-full bg-gradient-to-br from-indigo-600 to-slate-700 flex items-center justify-center text-3xl font-bold text-white shadow-inner border-4 border-slate-800/50 z-0";
            placeholder.innerHTML = `<span>${initials}</span>`;
            

            const label = document.createElement('div');
            label.className = "absolute bottom-3 left-3 bg-slate-900/60 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-medium text-white flex items-center gap-2 z-10";
            label.innerHTML = `
                <span class="w-2 h-2 rounded-full ${isLocal ? 'bg-indigo-400' : 'bg-green-400'}"></span>
                ${isLocal ? 'You' : participant.identity}
            `;

            container.appendChild(placeholder);
            container.appendChild(label);
            video_container.appendChild(container);
        }


        const element = track.attach();
        element.id = `video-${participant.identity}`;
        element.className = "absolute inset-0 w-full h-full object-cover z-5 transition-opacity duration-300";
        if (isLocal) element.style.transform = 'scaleX(-1)';


        element.style.opacity = track.isMuted ? "0" : "1";
        
        container.appendChild(element);


        track.on('muted', () => {
            element.style.opacity = "0";
        });

        track.on('unmuted', () => {
            element.style.opacity = "1";
        });

    } else if (track.kind === Track.Kind.Audio) {
        const audioElement = track.attach();
        document.body.appendChild(audioElement); 
    }
}

function handleTrackSubscribed(track, publication, participant) {
    attachTrack(track, participant);
    updateMemberCountDisplay();
}

function handleTrackUnsubscribed(track, publication, participant) {
    track.detach();
    const container = document.getElementById(`container-${participant.identity}`);
    if (container) container.remove();
    updateMemberCountDisplay();
}

function updateMemberCountDisplay() {
    const count = room.remoteParticipants.size + 1;
    member_count_display.innerHTML = `${count} Member${count !== 1 ? 's' : ''} Online`;
}


audio_btn.addEventListener('click', async () => {
    mic_on = !mic_on;
    await room.localParticipant.setMicrophoneEnabled(mic_on);
    

    audio_btn.classList.toggle('bg-red-500', !mic_on);
    audio_btn.classList.toggle('bg-slate-800', mic_on);
    audio_btn.innerHTML = mic_on ? '<i data-lucide="mic"></i>' : '<i data-lucide="mic-off"></i>';
    lucide.createIcons();
});

video_btn.addEventListener('click', async () => {
    camera_on = !camera_on;
    await room.localParticipant.setCameraEnabled(camera_on);
    

    video_btn.classList.toggle('bg-red-500', !camera_on);
    video_btn.classList.toggle('bg-slate-800', camera_on);
    video_btn.innerHTML = camera_on ? '<i data-lucide="video"></i>' : '<i data-lucide="video-off"></i>';
    lucide.createIcons();
});

screen_share_btn.addEventListener('click', async () => {
    screen_share_on = !screen_share_on;
    try {
        await room.localParticipant.setScreenShareEnabled(screen_share_on);
        
        screen_share_btn.classList.toggle('bg-indigo-600', screen_share_on);
        screen_share_btn.classList.toggle('bg-slate-800', !screen_share_on);
    } catch (error) {
        console.error('Screen share error:', error);
        screen_share_on = false;
    }
});


initialize();