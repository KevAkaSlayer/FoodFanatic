from django.shortcuts import render,redirect
from .forms import UserForm
from django.views.generic import CreateView
from django.contrib.auth.models import User
from .models import AccountModel
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import uuid



def send_verification_email(user,token ,template):
        message = render_to_string(template, {
            'user' : user,
            'token' : token
            
        })
        send_email = EmailMultiAlternatives('Please Confirm your Email', '', to=[user.email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()


class signup_user(CreateView):
    model = User
    template_name = 'register.html'
    form_class= UserForm
    success_url= reverse_lazy('login')
    def form_valid(self, form):
            our_user = super().form_valid(form)
            obj = AccountModel.objects.create(user=self.object,email_token=str(uuid.uuid4()))
            send_verification_email(self.object,obj.email_token,'registercnfrm.html')
            messages.success(self.request,'Please check your email for verification')
            
            return our_user


def verify(request,token):
    try :
        user_obj = AccountModel.objects.get(email_token=token)
        user_obj.is_activated=True
        user_obj.save() 
        messages.success(request,'Email verification successfull!')
        return redirect('login')
    except Exception as e:
        messages.error(request,'Invalid Token')
        return redirect('login')




class login_user(LoginView):
    template_name = 'login.html'
    def get_success_url(self):
        return reverse_lazy('home')
    def form_valid(self, form):
        # return super().form_valid(form)
        user_data = form.cleaned_data['username']
        user_obj = User.objects.get(username =user_data)
        account_obj = AccountModel.objects.get(user=user_obj)
        if account_obj.is_activated:
            return super().form_valid(form)
        else :
            messages.error(self.request,'Please verify your email')
            return redirect('login')
    
    def form_invalid(self, form):
        messages.error(self.request,"Credentials doesn't match")
        return super().form_invalid(form)
    

@login_required(login_url='login')
def userlogout(request):
    logout(request)
    messages.warning(request,'Logged out Successfully')
    return redirect('home')


# @login_required(login_url='login')
# def profile(request):

#     user = request.user
#     account = AccountModel.objects.get(user =user)

#     return render(request,'profile.html',{'user':user})