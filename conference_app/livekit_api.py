from livekit import api

def get_join_token(room_name, participant_name):

    # Define permissions
    grant = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        
    )

    api_key = "API9r6SPyZXeghQ"
    api_secret = "DMxyVKyyacnxMLNdIoF0Mx4WTNwgXalyOifoXOxKrxS"
    # Generate token (Valid for 24 hours)
    access_token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_name) \
        .with_grants(grant)

    return access_token.to_jwt()