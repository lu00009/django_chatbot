from django.shortcuts import render, redirect
from django.http import JsonResponse
import google.generativeai as genai
from django.contrib import auth
from django.contrib.auth.models import User 
from .models import Chat
from django.utils import timezone
import time
from datetime import datetime, timedelta

# Global variable to track last request time
last_request_time = None
MIN_REQUEST_INTERVAL = 2  # Minimum seconds between requests

def ask_genai(message):
    global last_request_time
    
    # Check if we need to wait
    if last_request_time is not None:
        elapsed = (datetime.now() - last_request_time).total_seconds()
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    
    try:
        genai.configure(api_key="AIzaSyAloaU228BS-6KrPzLLNGQxRD3NXdLjHFY")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(message)
        last_request_time = datetime.now()
        return response.text
    except Exception as e:
        error_str = str(e).lower()
        if "rate limit exceeded" in error_str:
            # Fallback response when rate limited
            return ("I apologize, but I'm currently experiencing high traffic and rate limits. "
                   "Here's a simple response: I understand you asked about '{}'. "
                   "Please try again in a few minutes for a more detailed response.").format(message[:50])
        return f"I apologize, but I encountered an error: {str(e)}"


def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_genai(message)
        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except Exception as e:
                error_message = f'Error creating account: {str(e)}'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')
