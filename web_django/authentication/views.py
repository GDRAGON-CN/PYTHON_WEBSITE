from tokenize import generate_tokens
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import EmailMessage,send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from product.models import Category, Product
from product.views import render_stars_home
from .tokens import generate_token
from .models import Profile
from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse

def is_strong_password(password):
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special
def valid_email(email):
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def signup(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        next_url = request.POST.get("next", "")
        
        # Validate password match
        if password1 != password2:
            messages.error(request, "Mật khẩu không khớp.")
            if next_url:
                return redirect(f"{reverse('signup')}?next={next_url}")
            return redirect("signup")
        
        # Check email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email đã được đăng ký.")
            if next_url:
                return redirect(f"{reverse('signup')}?next={next_url}")
            return redirect("signup")
        
        # Validate password strength
        if not is_strong_password(password1):
            messages.error(request, "Mật khẩu phải có ít nhất 8 ký tự, chứa chữ hoa, số và ký tự đặc biệt.")
            if next_url:
                return redirect(f"{reverse('signup')}?next={next_url}")
            return redirect("signup")
        
        # Validate email format
        if not valid_email(email):
            messages.error(request, "Email không hợp lệ.")
            if next_url:
                return redirect(f"{reverse('signup')}?next={next_url}")
            return redirect("signup")
        
        # Create user
        myuser = User.objects.create_user(username=email, email=email, password=password1)
        myuser.is_active = False
        myuser.save()
        
        messages.success(request, "Tài khoản của bạn đã được tạo thành công. Một mã xác thực (OTP) đã được gửi tới địa chỉ email của bạn. Vui lòng kiểm tra hộp thư và nhập mã để hoàn tất.")
        
        # Welcome email
        subject = "Chào mừng bạn đến với trang web Sport Clothes của chúng tôi"
        message = "Xin chào, cảm ơn bạn đã đăng ký! Vui lòng xác thực email để hoàn tất."
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        # OTP Code Email
        current_site = get_current_site(request)
        email_subject = "Confirm your email"
        message2 = render_to_string('email_confirmation.html', {
            'name': myuser.email.split('@')[0],
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser),
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.content_subtype = "html"
        email.fail_silently = True
        email.send()
        
        # Redirect về signin với next parameter
        if next_url:
            return redirect(f"{reverse('signup')}?next={next_url}")
        return redirect("signup")
    
    # GET request
    next_url = request.GET.get("next", "")
    
    # Lấy thông tin category/filter từ next_url để load đúng products
    product_list = Product.objects.all()
    
    # Parse category từ next_url nếu có
    if next_url and '/category/' in next_url:
        try:
            # Lấy category slug từ URL
            category_slug = next_url.split('/category/')[1].split('/')[0]
            category = Category.objects.get(slug=category_slug)
            product_list = Product.objects.filter(category=category)
        except:
            pass
    
    if 'sort=' in next_url:
        pass
    paginator = Paginator(product_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    products = product_list.order_by('id')
    for p in products:
        p.stars_html = render_stars_home(p.rating)
    
    return render(request, "Authentication/signup.html", {
        "page_obj": page_obj,
        "categories": categories,
        "products": products,
        "next": next_url
    })

# Đăng nhập
def signin(request):
    if request.method == "POST":
        email = request.POST.get("Email")
        password = request.POST.get("password")
        next_url = request.POST.get("next")
        
        user = authenticate(username=email, password=password)
        if user is not None:
            login(request, user)
            request.session["accountname"] = email.split('@')[0]
            
            if next_url and next_url != '':
                return redirect(next_url)
            return redirect("main")
        else:
            messages.error(request, "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.")
            if next_url:
                return redirect(f"{reverse('signin')}?next={next_url}")
            return redirect("signin")
    
    # GET request
    next_url = request.GET.get("next", "")
    
    # Lấy thông tin category/filter từ next_url
    product_list = Product.objects.all()
    
    # Parse category từ next_url nếu có
    if next_url and '/category/' in next_url:
        try:
            category_slug = next_url.split('/category/')[1].split('/')[0]
            category = Category.objects.get(slug=category_slug)
            product_list = product_list.filter(category=category)
        except:
            pass
    
    # Phân trang
    paginator = Paginator(product_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    # Gắn sao
    for p in page_obj:
        p.stars_html = render_stars_home(p.rating)
    
    return render(request, "Authentication/signin.html", {
        "page_obj": page_obj,
        "categories": categories,
        "products": page_obj,
        "next": next_url
    })

#Đăng xuất
def signout(request):
    logout(request)
    return redirect("main")

# Xác thực email
def activate(request, uidb64, token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser=User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser=None
    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active=True
        myuser.save()
        login(request,myuser)
        request.session['accountname'] = myuser.email.split('@')[0]
        return redirect("main")
    else:
        return render(request,'activation_failed.html')
    
# Đặt lại mật khẩu
def reset_password(request):
    next_url = request.GET.get("next", "")
    current_page = request.GET.get("page", "1")

    # --- POST: Gửi email đặt lại mật khẩu ---
    if request.method == "POST":
        email = request.POST.get("Email")
        try:
            myuser = User.objects.get(email=email)
            if not myuser.is_active:
                messages.error(request, "Tài khoản chưa kích hoạt, không thể đặt lại mật khẩu.")
                return redirect(f"reset_password?next={next_url}&page={current_page}")

            # Gửi email đặt lại mật khẩu
            current_site = get_current_site(request)
            mail_subject = "Yêu cầu đặt lại mật khẩu - Sport Clothes"
            message = render_to_string(
                'Authentication/Forget_password/reset_password_email.html',
                {
                    'name': myuser.email.split('@')[0],
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
                    'token': generate_token.make_token(myuser),
                }
            )

            email_obj = EmailMessage(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [myuser.email],
            )
            email_obj.content_subtype = "html"
            email_obj.fail_silently = True
            email_obj.send()

            messages.success(request, "Đã gửi email đặt lại mật khẩu.")
        except User.DoesNotExist:
            messages.error(request, "Email không tồn tại trong hệ thống.")
            return redirect(f"reset_password?next={next_url}&page={current_page}")

    # --- GET: Hiển thị sản phẩm + danh mục ---
    product_list = Product.objects.all()

    # Lọc theo danh mục nếu next_url có chứa '/category/'
    if next_url and '/category/' in next_url :
        try:
            category_slug = next_url.split('/category/')[1].split('/')[0]
            category = Category.objects.get(slug=category_slug)
            product_list = product_list.filter(category=category)
        except Category.DoesNotExist:
            pass

    # Sắp xếp và phân trang
    paginator = Paginator(product_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Lấy danh mục
    categories = Category.objects.all()

    # Gắn sao hiển thị cho từng sản phẩm
    for p in page_obj:
        p.stars_html = render_stars_home(p.rating)

    # Render template
    return render(request, "Authentication/Forget_password/reset_password.html", {
        "page_obj": page_obj,
        "categories": categories,
        "products": page_obj,
        "next": next_url,
    })

# Xác nhận đặt lại mật khẩu
def reset_password_confirm(request, uidb64, token):
    next_url = request.GET.get('next', '/')
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None
    
    if myuser is not None and generate_token.check_token(myuser, token):
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            next_url = request.POST.get("next_url", "/")
            
            if password1 and password1 == password2 and is_strong_password(password1):
                myuser.set_password(password1)
                myuser.save()
                messages.success(request, "Mật khẩu đã được thay đổi thành công.")
                return redirect(next_url)
            else:
                messages.error(request, "Mật khẩu không hợp lệ hoặc không khớp. Vui lòng thử lại.")
        
        product_list = Product.objects.all()
        if next_url and '/category/' in next_url:
            try:
                category_slug = next_url.split('/category/')[1].split('/')[0]
                category = Category.objects.get(slug=category_slug)
                product_list = product_list.filter(category=category)
            except Category.DoesNotExist:
                pass
        categories = Category.objects.all()             
        paginator = Paginator(product_list, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        return render(request, "Authentication/Forget_password/reset_password_confirm.html", {
            "page_obj": page_obj,
            "categories": categories, # type: ignore
            "products": page_obj,
            "next": next_url,
            "uidb64": uidb64,
            "token": token,
        })
    else:
        return render(request, "activation_failed.html")
    
#Sửa Profile
def update_profile(request):
    if request.method == "POST":
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        birthday = request.POST.get("birthday")
        gender = request.POST.get("gender")
        profile.full_name=full_name
        profile.phone = phone
        profile.gender = gender
        profile.birthday = birthday if birthday else None
        profile.save()
        messages.success(request, "Cập nhật thông tin thành công 🎉")
        return redirect("profile")
    return render(request, "profile.html")

#Trang hỗ trợ           
def guide(request):
    return render(request, "Authentication/guide.html")
def policy(request):
    return render(request, "Authentication/Forget_password/policy.html")
def profile(request):
    return render(request, "profile.html")
