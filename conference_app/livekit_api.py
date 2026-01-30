from livekit import api
from . import values
def get_join_token(room_name, participant_name):
    grant = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        
    )

    api_key = values.api_key
    api_secret = values.api_secret

    access_token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_name) \
        .with_grants(grant)

    # valid for 24 hours
    return access_token.to_jwt()