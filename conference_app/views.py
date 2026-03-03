import random
import redis
import re
import datetime
from django.shortcuts import redirect, render
from django.contrib import messages
from . import livekit_api, values, mongo_config
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