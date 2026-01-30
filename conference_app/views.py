from django.shortcuts import redirect, render
from django.contrib import messages
from . import livekit_api
# Create your views here.

def join(request):
    if request.session.get('name') or request.session.get('group'):
        return redirect('/conference/')

    if request.method == 'POST':
        name = request.POST.get('input_name')
        group = request.POST.get('input_group').strip()

        request.session['name'] = name
        request.session['group'] = group

        return redirect('/conference/')
    return render(request, 'conference_app/join.html')

def conference(request):
    if not request.session.get('name') or not request.session.get('group'):
        print("Invalid Request")
        messages.error(request, "Please enter a valid name and group.")
        return redirect('/')

    name = request.session.get('name')
    group = request.session.get('group')

    token = livekit_api.get_join_token(group, name)
    context = {
        "name": name,
        "group": group,
        "token": token,
    }
    return render(request, 'conference_app/conference.html', context=context)
    
def leave(request):
    request.session.flush()
    messages.info(request, "You have left the conference.")
    return redirect('/')