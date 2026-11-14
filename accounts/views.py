from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("events:list")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to Eventora, {user.first_name}!")
        return redirect("events:dashboard" if user.is_organizer else "events:list")
    return render(request, "accounts/signup.html", {"form": form})


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
