// Include the LiveKit Client SDK
import { Room, RoomEvent, Track, VideoPreserveAspectRatio } from 'livekit-client';

const url = 'wss://video-conferencing-site-ds6rylzw.livekit.cloud/';
const token = sessionStorage.getItem('storedToken');


async function joinRoom() {
    const room = new Room({
    // automatically manage subscribed video quality
        adaptiveStream: true,

        // optimize publishing bandwidth and CPU for published tracks
        dynacast: true,

        // default capture settings
        videoCaptureDefaults: {
            resolution: VideoPresets.h720.resolution,
        },
    });

    // Setup local video
    await room.connect(url, token);
    const localParticipant = room.localParticipant;
    await localParticipant.setCameraEnabled(true);
    await localParticipant.setMicrophoneEnabled(true);


    room.on(RoomEvent.Connected, () => {
        console.log('connected to room');
    });

    // When someone else joins/publishes video
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        if (track.kind === Track.kind.Video || track.kind === Track.kind.Audio) {
            const element = track.attach();
            document.getElementById('video-container').appendChild(element);
        }
    });

    // When someone leaves
    room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
        track.detach().forEach(el => el.remove());
    });
}

joinRoom().catch(err => {
    console.error('Error joining room:', err);
});