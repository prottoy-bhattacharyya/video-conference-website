import random
import redis
from django.shortcuts import redirect, render
from django.contrib import messages
from . import livekit_api, values
# Create your views here.

"""
4 session variables

username :for login
password :for login
nickname :name for join group, default: username
group :for group id
"""

def login(request):
    if request.session.get('name') and request.session.get('password'):
        return redirect('/home/')
    if request.method == 'POST':
        name = request.POST.get('username')
        password = request.POST.get('password')

        # cheak credentials

        request.session['name'] = name
        request.session['password'] = password
        return redirect('/home/')
    return render(request, 'conference_app/login.html')

def signin(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        password = request.POST.get('password')

        # add credentials

        request.session['name'] = name
        request.session['password'] = password
        return redirect('/home/')
    return render(request, 'conference_app/signin.html')

def home(request):
    if not request.session.get('name') and not request.session.get('password'):
        return redirect('/')
    if request.session.get('name') and request.session.get('group'):
        return redirect('/conference/')

    if request.method == 'POST':
        if request.POST.get('action') == 'create_room':
            group = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))

            print("Created group: ", group)
            request.session['group'] = group
        
        elif request.POST.get('action') == 'join_room':
            request.session['nickname'] = request.POST.get('input_name').strip()
            request.session['group'] = request.POST.get('input_group').strip()

        return redirect('/conference/')
    
    context = {
        'name': request.session.get('name'),
    }
    return render(request, 'conference_app/home.html', context=context)

def conference(request):
    if not request.session.get('name') or not request.session.get('group'):
        print("Invalid Request")
        messages.error(request, "Please enter a valid name and group.")
        return redirect('/home/')

    name = request.session.get('nickname') or request.session.get('name')
    group = request.session.get('group')

    token = livekit_api.get_join_token(group, name)
    context = {
        "name": name,
        "group": group,
        "token": token,
        "livekit_server_url": values.livekit_server_url
    }
    return render(request, 'conference_app/conference.html', context=context)
    
def leave(request):
    request.session.pop('nickname', None)
    request.session.pop('group', None)
    messages.info(request, "You have left the conference.")
    return redirect('/home/')

def logout(request):
    request.session.flush()
    return redirect('/')