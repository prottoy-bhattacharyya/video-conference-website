import random
import redis
import re
import datetime
import json
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from django.shortcuts import redirect, render
from django.contrib import messages
from . import livekit_api, values, mongo_config
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

"""
4 session variables

username :for login
password :for login
nickname :name for join group, default: username
group :for room id
"""

def login(request):
    if request.session.get('username') and request.session.get('password'):
        return redirect('/home/')
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')


        if not username_or_email or not password:
            messages.error(request, "Username or Password is required.")
            return redirect('/')
        
        # cheak credentials from DB
        usersCollection = usersCollection = mongo_config.get_users_collection()

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if re.match(email_pattern, username_or_email):
            email = username_or_email
            user = usersCollection.find_one({"email": email, "password": password})

        else:
            username = username_or_email
            user = usersCollection.find_one({"username": username, "password": password})

        if not user:
            messages.error(request, "Invalid username or password.")
            return redirect('/')

        # save credentials in session
        request.session['fullname'] = user.get('fullname')
        request.session['username'] = user.get('username')
        request.session['password'] = password
        messages.success(request, "Welcome " + request.session.get('fullname'))
        return redirect('/home/')
    return render(request, 'conference_app/login.html')

def signin(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # add credentials to DB
        usersCollection = mongo_config.get_users_collection()
        if usersCollection.find_one({"$or": [{"username": username}, {"email": email}]}):
            messages.error(request, "Username or Email already exists.")
            return redirect('/signin/')
        
        usersCollection.insert_one({
            "fullname": fullname,
            "username": username,
            "email": email,
            "password": password
        })

        # save credentials in session
        request.session['fullname'] = fullname
        request.session['username'] = username
        request.session['password'] = password
        return redirect('/home/')
    return render(request, 'conference_app/signin.html')

def home(request):
    if not request.session.get('username') or not request.session.get('password'):
        return redirect('/')
    if request.session.get('username') and request.session.get('group'):
        return redirect('/conference/')

    if request.method == 'POST':
        username = request.session.get('username')

        if request.POST.get('action') == 'create_room':
            roomsCollection = mongo_config.get_rooms_collection()
            while True:
                group = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
                room = roomsCollection.find_one(
                    {
                        "room_id": group,
                        "status": "inactive"
                    }
                )
                if not room:
                    break

            x = roomsCollection.insert_one(
                {
                    "room_id": group,
                    "host": username,
                    "status": "active",
                    "created_at": datetime.datetime.now()
                }
            )
            print(f"Room created with id: {x.inserted_id}")
            meeting_logs_collection = mongo_config.meeting_logs_collection()
            meeting_logs_collection.insert_one(
                {
                    "room_object_id": x.inserted_id,
                    "room_id": group,
                    "participants": [
                        {
                            "username": username,
                            "joined_at": datetime.datetime.now(),
                            "left_at": None
                        }
                    ],
                }
            )

            request.session['group'] = group
            print(f"{request.session.get('username')} created room: {request.session.get('group')}")
        
        elif request.POST.get('action') == 'join_room':
            group = request.POST.get('input_group').strip().upper()

            roomsCollection = mongo_config.get_rooms_collection()
            room = roomsCollection.find_one(
                {
                    "room_id": group,
                    "status": "active"
                }
            )
            if not room:
                messages.error(request, "Room not found.")
                return redirect('/home/')

            request.session['group'] = group

            # add participant to meeting logs
            meeting_logs_collection = mongo_config.meeting_logs_collection()
            meeting_logs_collection.update_one(
                {"room_id": group},
                {
                    "$push": {
                        "participants": {
                            "username": username,
                            "joined_at": datetime.datetime.now(),
                            "left_at": None
                        }
                    }
                }
            )


        return redirect('/conference/')
    
    context = {
        'fullname': request.session.get('fullname'),
        'username': request.session.get('username'),
    }
    return render(request, 'conference_app/home.html', context=context)

def conference(request):
    if not request.session.get('username') or not request.session.get('group'):
        print("Invalid Request")
        messages.error(request, "Please enter a valid name and group.")
        return redirect('/home/')

    fullname = request.session.get('fullname')
    name = request.session.get('username')
    group = request.session.get('group')
    print(f"{name} is joining room: {group}")
    token = livekit_api.get_join_token(group, fullname)

    chat_history = mongo_config.get_messages_collection().find(
        {
            "room_id": group
        }
    ).sort("timestamp", 1).limit(100)

    chat_history = list(chat_history)
    
    for message in chat_history:
        message['timestamp'] = message.get('timestamp').strftime("%d %b, %Y %I:%M %p")

    context = {
        "name": name,
        "group": group,
        "token": token,
        "livekit_server_url": values.livekit_server_url,
        "chat_history": chat_history,
    }
    return render(request, 'conference_app/conference.html', context=context)

@csrf_exempt
def toggle_record(request):
    # 1. Check if it's a POST request
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # 2. Extract group from session
    group = request.session.get('group')
    if not group:
        return JsonResponse({"error": "No group found in session"}, status=400)

    # 3. Parse JSON body (since you're using fetch/stringify)
    try:
        data = json.loads(request.body)
        action = data.get('action')
    except json.JSONDecodeError:
        print("Invalid JSON body")
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # 4. Handle Start
    if action == 'start':
        try:
            # We must use async_to_sync because start_recording is an async function
            egress_id = async_to_sync(livekit_api.start_recording)(group)
            request.session['egress_id'] = egress_id
            request.session.modified = True # Ensure session saves
            return JsonResponse({"status": "success", "message": "Recording started", "egress_id": egress_id})
        except Exception as e:
            print(f"Error starting recording: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # 5. Handle Stop
    elif action == 'stop':
        egress_id = request.session.get('egress_id')
        if not egress_id:
            return JsonResponse({"status": "error", "message": "No active recording found in session"}, status=404)

        try:
            success = async_to_sync(livekit_api.stop_room_recording)(egress_id)
            if success:
                del request.session['egress_id']
                return JsonResponse({"status": "success", "message": "Recording stopped"})
            else:
                return JsonResponse({"status": "error", "message": "LiveKit failed to stop egress"}, status=500)
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # 6. Fallback (This prevents the 'Returned None' error)
    return JsonResponse({"error": f"Invalid action: {action}"}, status=400)

def leave(request):
    # update left_at in meeting logs
    meeting_logs_collection = mongo_config.meeting_logs_collection()
    meeting_logs_collection.update_one(
        {
            "room_id": request.session.get('group'),
            "participants.username": request.session.get('username')
        },
        {
            "$set": {
                "participants.$.left_at": datetime.datetime.now()
            }
        }
    )

    request.session.pop('nickname', None)
    request.session.pop('group', None)
    messages.info(request, "You have left the conference.")
    return redirect('/home/')

def delete_inactive_rooms():
    meeting_logs_collection = mongo_config.meeting_logs_collection()
    roomsCollection = mongo_config.get_rooms_collection()
    result = meeting_logs_collection.find(
        {
            "participants": {
                "$not": {
                    "$elemMatch": { "left_at": None }
                }
            }
        },
        {
            "room_id": 1,
            "_id": 0
        }
    )

    for room in result:
        roomsCollection.delete_one(
            {
                "room_id": room.get('room_id')
            }
        )

def logout(request):
    request.session.flush()
    return redirect('/')