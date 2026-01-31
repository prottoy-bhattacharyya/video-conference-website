const { Room, RoomEvent, Track, VideoPresets } = LivekitClient;

// DOM Elements
const video_container = document.getElementById('video-container');
const messagesContainer = document.getElementById('messages-container');
const member_count_display = document.getElementById('member-count');

const audio_btn = document.getElementById('audio-btn');
const video_btn = document.getElementById('video-btn');
const screen_share_btn = document.getElementById('screen-share-btn');
const leave_btn = document.getElementById('leave-btn');

const livekit_server_url = sessionStorage.getItem('livekitServerUrl');
const token = sessionStorage.getItem('storedToken');

// State
let camera_on = true;
let mic_on = true;
let screen_share_on = false;

const room = new Room({
    adaptiveStream: true,
    dynacast: true,
    videoCaptureDefaults: {
        resolution: VideoPresets.h720.resolution, // 720p is usually better for web-based grid stability
    },
});

async function initialize() {
    try {
        await room.connect(livekit_server_url, token);
        console.log('Connected to Room:', room.name);

        // Publish local tracks
        await room.localParticipant.enableCameraAndMicrophone();
        
        // Handle events
        room
            .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(RoomEvent.ParticipantConnected, updateMemberCountDisplay)
            .on(RoomEvent.ParticipantDisconnected, updateMemberCountDisplay);

        // Display Local Video
        attachTrack(
            room.localParticipant.getTrackPublication(Track.Source.Camera).videoTrack, 
            room.localParticipant,
            true // isLocal flag
        );

        // Handle existing remote participants
        room.remoteParticipants.forEach((participant) => {
            participant.trackPublications.forEach((publication) => {
                if (publication.track) {
                    attachTrack(publication.track, participant);
                }
            });
        });

        updateMemberCountDisplay();
    } catch (error) {
        console.error('Failed to connect:', error);
    }
}

/**
 * Creates the video card UI and attaches the track
 */
function attachTrack(track, participant, isLocal = false) {
    if (!track) return;

    if (track.kind === Track.Kind.Video) {
        // Remove existing video container for this participant if it exists (prevents duplicates)
        const existing = document.getElementById(`container-${participant.identity}`);
        if (existing) existing.remove();

        const container = document.createElement('div');
        container.id = `container-${participant.identity}`;
        container.className = "relative rounded-2xl overflow-hidden bg-slate-800 aspect-video shadow-2xl border border-slate-700 group";

        const element = track.attach();
        element.className = "w-full h-full object-cover";
        if (isLocal) element.style.transform = 'scaleX(-1)'; // Mirror local video

        // Overlay Label
        const label = document.createElement('div');
        label.className = "absolute bottom-3 left-3 bg-slate-900/60 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-medium text-white flex items-center gap-2";
        label.innerHTML = `
            <span class="w-2 h-2 rounded-full ${isLocal ? 'bg-indigo-400' : 'bg-green-400'}"></span>
            ${isLocal ? 'You' : participant.identity}
        `;

        container.appendChild(element);
        container.appendChild(label);
        video_container.appendChild(container);

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

// UI Toggles
audio_btn.addEventListener('click', async () => {
    mic_on = !mic_on;
    await room.localParticipant.setMicrophoneEnabled(mic_on);
    
    // Toggle UI Styles
    audio_btn.classList.toggle('bg-red-500', !mic_on);
    audio_btn.classList.toggle('bg-slate-800', mic_on);
    audio_btn.innerHTML = mic_on ? '<i data-lucide="mic"></i>' : '<i data-lucide="mic-off"></i>';
    lucide.createIcons();
});

video_btn.addEventListener('click', async () => {
    camera_on = !camera_on;
    await room.localParticipant.setCameraEnabled(camera_on);
    
    // Toggle UI Styles
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

// Fire it up
initialize();