from django.shortcuts import redirect, render
from django.contrib import messages
# Create your views here.

def join(request):
    if request.method == 'POST':
        name = request.POST.get('input_name')
        group = request.POST.get('input_group')

        request.session['name'] = name
        request.session['group'] = group

        context = {'name': name, 'group': group}
        return redirect('/conference/')
    return render(request, 'conference_app/join.html')

def conference(request):
    if not request.session.get('name') or not request.session.get('group'):
        print("Invalid Request")
        messages.error(request, "Please enter a valid name and group.")
        return redirect('/')

    context = {
        "name": request.session.get('name'),
        "group": request.session.get('group'),
    }
    return render(request, 'conference_app/conference.html', context=context)

def leave(request):
    request.session.flush()
    messages.info(request, "You have left the conference.")
    return redirect('/')