from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    """
    View untuk login
    """
    # Jika user sudah login, redirect ke dashboard
    if request.user.is_authenticated:
        return redirect('librarian:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login berhasil
            login(request, user)
            messages.success(request, f'Selamat datang, {user.username}!')
            
            # Redirect berdasarkan role
            if user.role == 'admin':
                return redirect('admin:index')
            else:
                return redirect('librarian:dashboard')
        else:
            # Login gagal
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    """
    View untuk logout
    """
    logout(request)
    messages.success(request, 'Anda telah logout.')
    return redirect('home')