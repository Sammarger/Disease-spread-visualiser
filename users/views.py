from django.shortcuts import render
from django.contrib import messages
from .forms import UserRegisterForm

#If method is post request, program will validate the form data
#If method is GET request, program will display a blank form
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        #form must be validated to know whether the correct information is
        #sent, this includes matching passwords, passwords length and special characters
        if form.is_valid():
            #password hashed
            form.save()
            #Validated data will be in cleaned_data dict
            username = form.cleaned_data.get('username')
            #sends one time alert of succesful validation
            messages.success(request, 'Account created')
            return render(request, 'front/front.html')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login(request):
    return render(request, 'users/login.html')