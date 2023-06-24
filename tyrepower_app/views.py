from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .models import *
from django.db.models import Q
import json
import pdfkit
import re
import math
import datetime
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from tablib import Dataset
from .resources import ProxyTyreResource, ProxyTyreStockResource
from django.http import FileResponse, Http404
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required




@method_decorator(login_required, name='dispatch')
class TyreView(View):
    def get(self, request):
        if not request.user.is_superuser:
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            tyre = ProxyTyre.tyres.tyre()
            for proxytyre in tyre:
                proxytyre.net_price = float(proxytyre.list_price)-float(((proxytyre.list_price)*discount)/100)
                proxytyre.net_price = ('{0:.2f}'.format(proxytyre.net_price))
                if Manufacturer.objects.filter(name=proxytyre.brand):
                    manufacturer = Manufacturer.objects.get(name=proxytyre.brand)
                    proxytyre.logo = manufacturer.logo
                    proxytyre.color = manufacturer.color
                else:
                    proxytyre.color = "#000000"
            brands = tyre.order_by('brand').values_list('brand', flat=True).distinct()
            paginator = Paginator(tyre, per_page=20)
            page_number = request.GET.get('page')
            page_obj= paginator.get_page(page_number)
            return render (request, 'tyrepower_app/index.html', {'page_obj':page_obj, 'brands':brands, 'total':tyre.count()})
        return redirect ('dashboard')                                                            


@method_decorator(login_required, name='dispatch')
class FilterTyreView(View):
    def get(self, request, brand):
        if not request.user.is_superuser:
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            brands = ProxyTyre.objects.filter(brand=brand)
            for tyre in brands:
                tyre.net_price = float(tyre.list_price)-float(((tyre.list_price)*discount)/100)
                tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
                if Manufacturer.objects.filter(name=tyre.brand):
                    manufacturer = Manufacturer.objects.get(name=tyre.brand)
                    tyre.logo = manufacturer.logo
                    tyre.color = manufacturer.color
                else:
                    tyre.color = "#000000"
            paginator = Paginator(brands, per_page=20)
            page_number = request.GET.get('page')
            page_obj= paginator.get_page(page_number)
            messages.info(request, f'Total {brands.count()} Items of Brand {brand}')
            return render (request, 'tyrepower_app/filter-index.html', {'page_obj':page_obj, 'total':brands.count()})
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class SearchResultView(View):
    def get(self, request):
        if not request.user.is_superuser:
            try:
                search = request.session['tyre-search']
                ids_list = request.session['ids-list']
                user_tier = User.objects.get(id = request.user.id).tier
                discount = Tier.objects.get(tier=user_tier).discount_percentage
                tyres = ProxyTyre.tyres.tyre()
                tyre = tyres.filter(Q(Q(Q(name__icontains=search) | Q(brand__icontains=search)) | Q(Q(code__icontains=search) | Q(size__icontains=search))) | Q(id__in=ids_list))
                for proxytyre in tyre:
                    proxytyre.net_price = float(proxytyre.list_price)-float(((proxytyre.list_price)*discount)/100)
                    proxytyre.net_price = ('{0:.2f}'.format(proxytyre.net_price))
                    if Manufacturer.objects.filter(name=proxytyre.brand):
                        manufacturer = Manufacturer.objects.get(name=proxytyre.brand)
                        proxytyre.logo = manufacturer.logo
                        proxytyre.color = manufacturer.color
                    else:
                        proxytyre.color = "#000000"
                paginator = Paginator(tyre, per_page=20)
                page_number = request.GET.get('page')
                page_obj= paginator.get_page(page_number)
                messages.info(request, f'Total {tyre.count()} Items Related To Your Search')
                return render (request, 'tyrepower_app/filter-index.html', {'page_obj':page_obj, 'total':tyre.count()})
            except KeyError:
                messages.error(request, 'Please! Search Again')
                return redirect ('tyre')
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_superuser:
            search = request.POST.get('search')
            if search:
                TopSearch.objects.create(word=search, retailer=request.user)
                strsearch = str(search)
                new_search = strsearch.replace('/', '').replace('.', '').replace('-', '').replace(' ', '')
                re_search = re.sub(r'[A-Z]', '', new_search)
                request.session['tyre-search'] = search
                tyres = ProxyTyre.tyres.tyre()
                ids_list = []
                for tyresize in tyres:
                    size=tyresize.size
                    id = tyresize.id
                    strzize = str(size)
                    new_size = strzize.replace('/', '').replace('.', '').replace('-', '').replace(' ', '')
                    re_size = re.sub(r'[A-Z]', '', new_size)
                    if re_search == re_size:              
                        ids_list.append(id)
                request.session['ids-list'] = ids_list
                if tyres.filter(Q(Q(Q(name__icontains=search) | Q(brand__icontains=search)) | Q(Q(code__icontains=search) | Q(size__icontains=search))) | Q(id__in=ids_list)):
                    tyre = tyres.filter(Q(Q(Q(name__icontains=search) | Q(brand__icontains=search)) | Q(Q(code__icontains=search) | Q(size__icontains=search))) | Q(id__in=ids_list))
                    user_tier = User.objects.get(id = request.user.id).tier
                    discount = Tier.objects.get(tier=user_tier).discount_percentage
                    for proxytyre in tyre:
                        proxytyre.net_price = float(proxytyre.list_price)-float(((proxytyre.list_price)*discount)/100)
                        proxytyre.net_price = ('{0:.2f}'.format(proxytyre.net_price))
                        if Manufacturer.objects.filter(name=proxytyre.brand):
                            manufacturer = Manufacturer.objects.get(name=proxytyre.brand)
                            proxytyre.logo = manufacturer.logo
                            proxytyre.color = manufacturer.color
                        else:
                            proxytyre.color = "#000000"
                    paginator = Paginator(tyre, per_page=20)
                    page_number = request.GET.get('page')
                    page_obj= paginator.get_page(page_number)
                    messages.info(request, f'Total {tyre.count()} Items Related To Your Search')
                    return render (request, 'tyrepower_app/filter-index.html', {'page_obj':page_obj, 'total':tyre.count()})
                messages.error(request, 'Exact Match Not Found, But You Can See Some Related Results')
                return redirect ('tyre')
            messages.error(request, 'Please Enter Some Text')
            return redirect ('tyre')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class TyreDetailView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
            if ProxyTyre.tyres.filter(id=id).exists():
                tyre = ProxyTyre.tyres.get(id=id)
                user_tier = User.objects.get(id = request.user.id).tier
                discount = Tier.objects.get(tier=user_tier).discount_percentage
                tyre.net_price = float(tyre.list_price)-float(((tyre.list_price)*discount)/100)
                tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
                if Manufacturer.objects.filter(name=tyre.brand):
                    manufacturer = Manufacturer.objects.get(name=tyre.brand)
                    tyre.logo = manufacturer.logo
                    tyre.color = manufacturer.color
                else:
                    tyre.color = "#000000"
                total = tyre.total
                if total is not 0:
                    stock = f'Total {total} in Stock'
                else:
                    stock = 'Out of Stock'
                return render (request, 'tyrepower_app/tyredetail.html', {'tyre':tyre, 'stock':stock})
            messages.error(request, 'Item Is Not Available')
            return redirect ('tyre')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class MyOrderView(View):
    def get(self, request):
        if not request.user.is_superuser:
            orders = Order.objects.filter(user=request.user).order_by('-id')[:25]
            for order in orders:
                order.total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                order.total_price = ('{0:.2f}'.format(order.total_price))
            return render (request, 'tyrepower_app/my-order.html', {'orders':orders})        
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class CartView(View):
    def get(self, request):
        if not request.user.is_superuser:
            carts = Cart.objects.filter(user=request.user, status='Pending', created_at__gte=datetime.datetime.now()-datetime.timedelta(minutes=30), created_at__lte=datetime.datetime.now()).order_by('-id')
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            for cart in carts:
                cart.tyre.net_price = float(cart.tyre.list_price)-float(((cart.tyre.list_price)*discount)/100)
                cart.tyre.net_price = ('{0:.2f}'.format(cart.tyre.net_price))
                if Manufacturer.objects.filter(name=cart.tyre.brand):
                    manufacturer = Manufacturer.objects.get(name=cart.tyre.brand)
                    cart.tyre.logo = manufacturer.logo
                    cart.tyre.color = manufacturer.color
                else:
                    cart.tyre.color = "#000000"
            return render (request, 'tyrepower_app/carts.html', {'carts':carts})        
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class DeleteItemView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
            Cart.objects.filter(id=id).delete()
            messages.error(request, 'Item Removed From Your Cart')
            return redirect ('cart')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class AddToCartView(View):
    def post(self, request, id):
        if not request.user.is_superuser:
            tyre = ProxyTyre.tyres.get(id=id)
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            if not Cart.objects.filter(user=request.user, tyre__code=tyre.code, status='Pending', created_at__gte=datetime.datetime.now()-datetime.timedelta(minutes=30), created_at__lte=datetime.datetime.now()).exists():
                total = float(tyre.total)
                total_number = int(request.POST.get('total_number'))
                tyre.net_price = float(tyre.list_price)-float(((tyre.list_price)*discount)/100)
                tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
                price = float(tyre.net_price)
                total_price = float(price*total_number)
                total_price = ('{0:.2f}'.format(total_price))
                if total >= total_number:
                    Cart.objects.create(user=request.user, tyre=tyre, total_number=total_number, total_price=total_price)
                    messages.info(request, 'Item Added In Your Cart')
                    return redirect ('tyre')
                messages.error(request, 'Not Enough In Stock')
                return redirect ('tyre')
            messages.error(request, 'Item ALready Added, You Can Manage Quantity')
            return redirect ('cart')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class CartValueView(View):
    def post(self, request, id):
        if not request.user.is_superuser:
            cart_value = request.POST.get('cartValue')
            cart = Cart.objects.get(id=id)
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            net_price = float(cart.tyre.list_price)-float(((cart.tyre.list_price)*discount)/100)
            net_price = ('{0:.2f}'.format(net_price))
            total = cart.tyre.total
            if total >= int(cart_value):
                new_total_price = float(cart_value)*float(net_price)
                new_total_price = ('{0:.2f}'.format(new_total_price))
                data = {'new_total_price':new_total_price, 'message':'Cart Value Updated'}
                Cart.objects.filter(id=id).update(total_number=cart_value, total_price=new_total_price)
                return JsonResponse(data, safe=False)
            data = {'message':'Number Is Out Of Stock'}
            return JsonResponse(data, safe=False)
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class AddToMyOrderView(View):
    def get(self, request):
        if not request.user.is_superuser:
            addresses = Address.objects.filter(retailer=request.user)
            return render (request, 'tyrepower_app/order-detail.html', {'addresses':addresses})
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_superuser:
            carts = Cart.objects.filter(user=request.user, status='Pending', created_at__gte=datetime.datetime.now()-datetime.timedelta(minutes=30), created_at__lte=datetime.datetime.now()).order_by('-id')
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            net_price_list = []
            for cart in carts:
                cart.tyre.net_price = float(cart.tyre.list_price)-float(((cart.tyre.list_price)*discount)/100)
                cart.tyre.net_price = ('{0:.2f}'.format(cart.tyre.net_price))
                net_price_list.append(float(cart.tyre.net_price)*cart.total_number)
            net_price_sum = math.fsum(net_price_list)
            total_price = float('{0:.2f}'.format(net_price_sum))
            vat = ((total_price)/100)*15
            vat = ('{0:.2f}'.format(vat))
            total = (total_price)+float(vat)
            product_delivery = request.POST.get('product_delivery')
            driver_name = request.POST.get('driver_name')
            vehical_name = request.POST.get('vehical_name')
            vehical_number = request.POST.get('vehical_number')
            shipping_address_id = request.POST.get('shipping_address')
            if shipping_address_id:
                shipping_address = Address.objects.get(id=shipping_address_id)
            else:
                shipping_address = None
            request.session['product_delivery'] = product_delivery
            request.session['driver_name'] = driver_name
            request.session['vehical_name'] = vehical_name
            request.session['vehical_number'] = vehical_number
            request.session['shipping_address_id'] = shipping_address_id
            return render (request, 'tyrepower_app/confirm-order.html', {'carts':carts, 'total_price':total_price, 'vat':vat, 'total':total, 'product_delivery':product_delivery, 'driver_name':driver_name, 'vehical_name':vehical_name, 'vehical_number':vehical_number, 'shipping_address':shipping_address})



class ConfirmOrderView(View):
    def post(self, request):
        if not request.user.is_superuser:
            try:
                product_delivery = request.session['product_delivery']
                driver_name = request.session['driver_name']
                vehical_name = request.session['vehical_name']
                vehical_number = request.session['vehical_number']
                shipping_address_id = request.session['shipping_address_id']
                if shipping_address_id:
                    shipping_address = Address.objects.get(id=shipping_address_id)
                else:
                    shipping_address = None
                print(product_delivery)
                print(shipping_address)
                carts = Cart.objects.filter(user=request.user, status='Pending', created_at__gte=datetime.datetime.now()-datetime.timedelta(minutes=30), created_at__lte=datetime.datetime.now()).order_by('-id')
                tyres_id = carts.values_list('tyre', flat=True).distinct()
                tyres = ProxyTyre.tyres.filter(id__in=tyres_id)
                tyre_list_total = []
                for tyre in tyres:
                    total = tyre.total
                    tyre_list_total.append(total)
                cart_list_number = []
                for cart in carts:
                    total_number = cart.total_number
                    cart_list_number.append(total_number)
                remaining_total = []   
                for total, total_number in zip(tyre_list_total, cart_list_number):
                    remaining_total.append(total - total_number)
                Order.objects.create(user=request.user, shipping_address=shipping_address, product_delivery=product_delivery, driver_name=driver_name, vehical_name=vehical_name, vehical_number=vehical_number).tyre.set(carts)
                for cart in carts:
                    cart.status = 'Ordered'
                    cart.save()
                for proxytyre, remaining in zip(tyres, remaining_total):
                    proxytyre.total=remaining
                    proxytyre.save()
                messages.success(request, 'You Have Successfully Ordered The Items')
                return redirect ('my-order')
            except KeyError:
                messages.error(request, 'Something Went Wrong! Try Again')
                return redirect ('cart')
        return redirect ('dashboard')



@method_decorator(login_required, name='dispatch')
class InvoiceView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
            order = Order.objects.get(id=id)
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            net_price_list = []
            for tyre in order.tyre.all():
                tyre.net_price = float(tyre.tyre.list_price)-float(((tyre.tyre.list_price)*discount)/100)
                tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
                net_price_list.append(tyre.net_price)
            total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
            total_price = float('{0:.2f}'.format(total_price))
            vat = ((total_price)/100)*15
            vat = ('{0:.2f}'.format(vat))
            total = (total_price)+float(vat)
            return render (request, 'tyrepower_app/invoice.html', {'order':order, 'vat':vat, 'total_price':total_price, 'total':total, 'net_price_list':net_price_list})
        return redirect ('dashboard')


@login_required
def generate_invoice_pdf(request, id, format=None):
    print("Hello")
    if not request.user.is_superuser:
        order = Order.objects.get(id=id)
        user_tier = User.objects.get(id = request.user.id).tier
        discount = Tier.objects.get(tier=user_tier).discount_percentage
        net_price_list = []
        for tyre in order.tyre.all():
            tyre.net_price = float(tyre.tyre.list_price)-float(((tyre.tyre.list_price)*discount)/100)
            tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
            net_price_list.append(tyre.net_price)
        total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
        total_price = float('{0:.2f}'.format(total_price))
        vat = ((total_price)/100)*15
        vat = ('{0:.2f}'.format(vat))
        total = (total_price)+float(vat)
        html = render_to_string('tyrepower_app/invoice-pdf.html', {'order': order, 'vat':vat, 'total_price':total_price, 'total':total, 'net_price_list':net_price_list})
        options = {
            'page-size': 'Letter',
            'encoding': "UTF-8",
        }
        # pdfkit.configuration(wkhtmltopdf='/home/mobapps/Desktop') 
        pdf = pdfkit.from_string(html, False, options=options)
        response = HttpResponse(pdf, content_type='application/pdf')
        # response['Content-Disposition'] = 'attachment; filename=" {}.pdf"'.format(responsive_letter)
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
        return response
    return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class NotificationsView(View):
    def get(self, request):
        if not request.user.is_superuser:
            notifications = Notification.objects.filter(receiver=request.user).order_by('-id')
            for notification in notifications:
                notification.is_seen.add(request.user)
            paginator = Paginator(notifications, per_page=20)
            page_number = request.GET.get('page')
            page_obj= paginator.get_page(page_number)
            return render (request, 'tyrepower_app/notifications.html', {'page_obj':page_obj})
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class DeleteNotificationView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
            Notification.objects.filter(id=id).delete()
            messages.error(request, 'Notification Deleted')
            return redirect ('notifications')
        return redirect ('dashboard')      


@method_decorator(login_required, name='dispatch')
class SettingView(View):
    def get(self, request):
        if not request.user.is_superuser:
          return render (request, 'tyrepower_app/setting.html')
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_superuser:
            id = request.user.id
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            if not User.objects.filter(username=username).exclude(username=request.user.username):
                if not User.objects.filter(email=email).exclude(email=request.user.email):
                    if not User.objects.filter(phone=phone).exclude(phone=request.user.phone):
                        User.objects.filter(id=id).update(username=username, email=email, first_name=first_name, last_name=last_name, phone=phone)
                        messages.info(request, 'User Detail Updated')
                        return JsonResponse({'message':'User Detail Updated'})
                    messages.error(request, 'Phone Already Exists')
                    return JsonResponse({'message':'Phone Already Exists'})
                messages.error(request, 'Email Already Exists')
                return JsonResponse({'message':'Email Already Exists'})
            messages.error(request, 'Username Already Exists')
            return JsonResponse({'message':'Username Already Exists'})
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class AddressView(View):
    def get(self, request):
        if not request.user.is_superuser:
          addresses = Address.objects.filter(retailer=request.user)
          return render (request, 'tyrepower_app/address.html', {'addresses':addresses})
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_superuser:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            house_and_street = request.POST.get('house_and_street')
            suburb = request.POST.get('suburb')
            province = request.POST.get('province')
            postcode = request.POST.get('postcode')
            Address.objects.create(retailer=request.user, name=name, phone=phone, house_and_street=house_and_street, suburb=suburb, province=province, postcode=postcode)
            messages.success(request, 'Address Added Successfully')
            return redirect('address')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class UpdateAddressView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
          address = Address.objects.get(id=id)
          return render (request, 'tyrepower_app/update-address.html', {'address':address})
        return redirect ('dashboard')
    def post(self, request, id):
        if not request.user.is_superuser:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            house_and_street = request.POST.get('house_and_street')
            suburb = request.POST.get('suburb')
            province = request.POST.get('province')
            postcode = request.POST.get('postcode')
            Address.objects.filter(id=id).update(name=name, phone=phone, house_and_street=house_and_street, suburb=suburb, province=province, postcode=postcode)
            messages.success(request, 'Address Updated Successfully')
            return redirect('address')
        return redirect ('dashboard')
    

@method_decorator(login_required, name='dispatch')
class DeleteAddressView(View):
    def get(self, request, id):
        if not request.user.is_superuser:
            Address.objects.get(id=id).delete()
            messages.error(request, 'Address Has Deleted')
            return redirect ('address')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    def get(self, request):
        if not request.user.is_superuser:
          return render (request, 'tyrepower_app/change-password.html')
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_superuser:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if old_password and new_password and confirm_password:
                if request.user.check_password(old_password):
                    if new_password == confirm_password:
                        user = User.objects.get(username=request.user.username)
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, 'Password Change Successfully')
                        return redirect('change-password')
                    messages.error(request, 'New Password and Confirm Password Did Not Match')
                    return redirect('change-password')
                messages.error(request, 'Old Password Is Incorrect')
                return redirect('change-password')
            messages.error(request, 'We required Old Oassword and New Password and Confirm Password fields')
            return redirect('change-password')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class PrivacyPolicyView(View):
    def get(self, request):
        if not request.user.is_superuser:
            try:
                file = PrivacyPolicy.objects.latest('id')
                return FileResponse(open('media/'+ str(file.privacy_policy), 'rb'), content_type='application/pdf')
            except:
                messages.error(request, 'No File Found')
                return redirect ('tyre')
        return redirect ('dashboard')


@method_decorator(login_required, name='dispatch')
class TermsAndConditionsView(View):
    def get(self, request):
        if not request.user.is_superuser:
            try:
                file = TermAndCondition.objects.latest('id')
                return FileResponse(open('media/'+ str(file.terms), 'rb'), content_type='application/pdf')
            except:
                messages.error(request, 'No File Found')
                return redirect ('tyre')
        return redirect ('dashboard')



########################################################################################################

@method_decorator(login_required, name='dispatch')
class Dasboard(View):
    def get(self, request):
        if request.user.is_superuser:
            total_users = User.objects.all().count()
            total_tyres = ProxyTyre.objects.all().count()
            total_carts = Cart.objects.all().count()
            total_orders = Order.objects.all().count()
            pending_orders = Order.objects.filter(status='Pending').count()
            total_notifications = Order.objects.all().count()
            return render (request, 'admin/index.html', {'total_users': total_users, 'total_tyres':total_tyres, 'total_carts':total_carts, 'total_orders':total_orders, 'pending_orders':pending_orders, 'total_notifications':total_notifications})
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class RetailerDetails(View):
    def get(self, request, id):
        if request.user.is_superuser:
            retailer = User.objects.get(id=id)
            orders = Order.objects.filter(user=retailer, status__in=['Delivered', 'Picked By Self'])
            total_price_list = []
            total_number_list = []
            for order in orders:
                price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                number = order.tyre.aggregate(Sum('total_number'))['total_number__sum']
                total_price_list.append(price)
                total_number_list.append(number)
            total_price = math.fsum(total_price_list)
            total_number = math.fsum(total_number_list)
            return render (request, 'admin/retailer-details.html', {'retailer':retailer, 'total_price':total_price, 'total_number':total_number})
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class PendingOrders(View):
    def get(self, request, id):
        if request.user.is_superuser:
            user = User.objects.get(id=id)
            orders = Order.objects.filter(user=user, status='Pending')
            total_price_list = []
            for order in orders:
                order.price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                order.number = order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                total_price_list.append(order.price)
            total_price = math.fsum(total_price_list)
            return render (request, 'admin/user-pending-orders.html', {'orders':orders, 'user':user, 'total_price':total_price})
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class TotalOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            user = User.objects.get(id=id)
            orders = Order.objects.filter(user=user).order_by('-id')
            for order in orders:
                order.total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
            paginator = Paginator(orders, per_page=20)
            page_number = request.GET.get('page')
            page_obj= paginator.get_page(page_number)
            return render (request, 'admin/user-orders.html', {'page_obj':page_obj, 'user':user})        
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class UserInvoiceView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            user_tier = User.objects.get(id = request.user.id).tier
            discount = Tier.objects.get(tier=user_tier).discount_percentage
            net_price_list = []
            for tyre in order.tyre.all():
                tyre.net_price = float(tyre.tyre.list_price)-float(((tyre.tyre.list_price)*discount)/100)
                tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
                net_price_list.append(tyre.net_price)
            total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
            total_price = float('{0:.2f}'.format(total_price))
            vat = ((total_price)/100)*15
            vat = ('{0:.2f}'.format(vat))
            total = (total_price)+float(vat)
            return render (request, 'admin/user-invoice.html', {'order':order, 'vat':vat, 'total_price':total_price, 'total':total, 'net_price_list':net_price_list})
        return redirect ('tyre')


@login_required
def generate_user_invoice_pdf(request, id, format=None):
    print("Hello")
    if request.user.is_superuser:
        order = Order.objects.get(id=id)
        user_tier = User.objects.get(id = request.user.id).tier
        discount = Tier.objects.get(tier=user_tier).discount_percentage
        net_price_list = []
        for tyre in order.tyre.all():
            tyre.net_price = float(tyre.tyre.list_price)-float(((tyre.tyre.list_price)*discount)/100)
            tyre.net_price = ('{0:.2f}'.format(tyre.net_price))
            net_price_list.append(tyre.net_price)
        total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
        total_price = float('{0:.2f}'.format(total_price))
        vat = ((total_price)/100)*15
        vat = ('{0:.2f}'.format(vat))
        total = (total_price)+float(vat)
        html = render_to_string('admin/user-invoice-pdf.html', {'order': order, 'vat':vat, 'total_price':total_price, 'total':total, 'net_price_list':net_price_list})
        options = {
            'page-size': 'Letter',
            'encoding': "UTF-8",
        }
        # pdfkit.configuration(wkhtmltopdf='/home/mobapps/Desktop') 
        pdf = pdfkit.from_string(html, False, options=options)
        response = HttpResponse(pdf, content_type='application/pdf')
        # response['Content-Disposition'] = 'attachment; filename=" {}.pdf"'.format(responsive_letter)
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
        return response
    return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class PriceReportsView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'admin/reports.html')
        return redirect ('tyre')
    def post(self, request):
        if request.user.is_superuser:
            start_date = request.POST.get('start_date')
            end_date = (request.POST.get('end_date'))
            request.session['start_date'] = start_date
            request.session['end_date'] = end_date
            pending_orders = Order.objects.filter(status='Pending', created_at__date__gte=start_date, created_at__date__lte=end_date)
            pending_pri_list = []
            pending_sto_list = []
            for pending_order in pending_orders:
                pending_pri = pending_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                pending_sto = pending_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                pending_pri_list.append(pending_pri)
                pending_sto_list.append(pending_sto)
            pending_prices = math.fsum(pending_pri_list)
            pending_stocks = math.fsum(pending_sto_list)
            delivered_orders = Order.objects.filter(status='Delivered', created_at__date__gte=start_date, created_at__date__lte=end_date)
            delivered_pri_list = []
            delivered_sto_list = []
            for delivered_order in delivered_orders:
                delivered_pri = delivered_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                delivered_sto = delivered_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                delivered_pri_list.append(delivered_pri)
                delivered_sto_list.append(delivered_sto)
            delivered_prices = math.fsum(delivered_pri_list)
            delivered_stocks = math.fsum(delivered_sto_list)
            picked_by_self_orders = Order.objects.filter(status='Picked By Self', created_at__date__gte=start_date, created_at__date__lte=end_date)
            picked_by_self_pri_list = []
            picked_by_self_sto_list = []
            for picked_by_self_order in picked_by_self_orders:
                picked_by_self_pri = picked_by_self_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                picked_by_self_sto = picked_by_self_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                picked_by_self_pri_list.append(picked_by_self_pri)
                picked_by_self_sto_list.append(picked_by_self_sto)
            picked_by_self_prices = math.fsum(picked_by_self_pri_list)
            picked_by_self_stocks = math.fsum(picked_by_self_sto_list)
            canceled_orders = Order.objects.filter(status='Canceled', created_at__date__gte=start_date, created_at__date__lte=end_date)
            canceled_pri_list = []
            canceled_sto_list = []
            for canceled_order in canceled_orders:
                canceled_pri = canceled_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                canceled_sto = canceled_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                canceled_pri_list.append(canceled_pri)
                canceled_sto_list.append(canceled_sto)
            canceled_prices = math.fsum(canceled_pri_list)
            canceled_stocks = math.fsum(canceled_sto_list)
            return render (request, 'admin/reports-final.html', {'start_date':start_date, 'end_date':end_date, 'pending_prices':pending_prices, 'delivered_prices':delivered_prices, 'pending_stocks':pending_stocks, 'delivered_stocks':delivered_stocks, 'picked_by_self_prices':picked_by_self_prices, 'picked_by_self_stocks':picked_by_self_stocks, 'canceled_prices':canceled_prices, 'canceled_stocks':canceled_stocks})
        return redirect ('tyre')


@login_required
def generate_reports_pdf(request, format=None):
    print("Hello")
    if request.user.is_superuser:
        try:
            start_date = request.session['start_date']
            end_date = request.session['end_date']
            pending_orders = Order.objects.filter(status='Pending', created_at__date__gte=start_date, created_at__date__lte=end_date)
            pending_pri_list = []
            pending_sto_list = []
            for pending_order in pending_orders:
                pending_pri = pending_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                pending_sto = pending_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                pending_pri_list.append(pending_pri)
                pending_sto_list.append(pending_sto)
            pending_prices = math.fsum(pending_pri_list)
            pending_stocks = math.fsum(pending_sto_list)
            delivered_orders = Order.objects.filter(status='Delivered', created_at__date__gte=start_date, created_at__date__lte=end_date)
            delivered_pri_list = []
            delivered_sto_list = []
            for delivered_order in delivered_orders:
                delivered_pri = delivered_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                delivered_sto = delivered_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                delivered_pri_list.append(delivered_pri)
                delivered_sto_list.append(delivered_sto)
            delivered_prices = math.fsum(delivered_pri_list)
            delivered_stocks = math.fsum(delivered_sto_list)
            picked_by_self_orders = Order.objects.filter(status='Picked By Self', created_at__date__gte=start_date, created_at__date__lte=end_date)
            picked_by_self_pri_list = []
            picked_by_self_sto_list = []
            for picked_by_self_order in picked_by_self_orders:
                picked_by_self_pri = picked_by_self_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                picked_by_self_sto = picked_by_self_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                picked_by_self_pri_list.append(picked_by_self_pri)
                picked_by_self_sto_list.append(picked_by_self_sto)
            picked_by_self_prices = math.fsum(picked_by_self_pri_list)
            picked_by_self_stocks = math.fsum(picked_by_self_sto_list)
            canceled_orders = Order.objects.filter(status='Canceled', created_at__date__gte=start_date, created_at__date__lte=end_date)
            canceled_pri_list = []
            canceled_sto_list = []
            for canceled_order in canceled_orders:
                canceled_pri = canceled_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
                canceled_sto = canceled_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
                canceled_pri_list.append(canceled_pri)
                canceled_sto_list.append(canceled_sto)
            canceled_prices = math.fsum(canceled_pri_list)
            canceled_stocks = math.fsum(canceled_sto_list)
            html = render_to_string('admin/reports-pdf.html', {'start_date':start_date, 'end_date':end_date, 'pending_prices':pending_prices, 'delivered_prices':delivered_prices, 'pending_stocks':pending_stocks, 'delivered_stocks':delivered_stocks, 'picked_by_self_prices':picked_by_self_prices, 'picked_by_self_stocks':picked_by_self_stocks, 'canceled_prices':canceled_prices, 'canceled_stocks':canceled_stocks})
            options = {
                'page-size': 'Letter',
                'encoding': "UTF-8",
            }
            # pdfkit.configuration(wkhtmltopdf='/home/mobapps/Desktop') 
            pdf = pdfkit.from_string(html, False, options=options)
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename=" {}.pdf"'.format(responsive_letter)
            response['Content-Disposition'] = 'attachment; filename="reports.pdf"'
            return response
        except KeyError:
            return redirect ('price-reports')
    return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class RetailerReportsView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'admin/retailer-reports.html')
        return redirect ('tyre')
    def post(self, request):
        if request.user.is_superuser:
            retailer_start_date = request.POST.get('start_date')
            retailer_end_date = (request.POST.get('end_date'))
            request.session['retailer_start_date'] = retailer_start_date
            request.session['retailer_end_date'] = retailer_end_date
            retailers = User.objects.all()
            id_list = []
            orders_list = []
            for retailer in retailers:
                id = retailer.id
                order = Order.objects.filter(user=retailer, status__in=['Delivered', 'Picked By Self'], created_at__date__gte=retailer_start_date, created_at__date__lte=retailer_end_date).aggregate(Sum('total_price'))['total_price__sum']
                if order:
                    id_list.append(id)
                    orders_list.append(order)
            result_dict = {key: value for key, value in zip(id_list, orders_list)}
            sorted_list = sorted(result_dict.items(), key=lambda x: x[1], reverse=True)[:15]
            final_id = [x[0] for x in sorted_list]
            final_price = [x[1] for x in sorted_list]
            request.session['final-id'] = final_id
            request.session['final-price'] = final_price
            retailers_list = []
            for id, price in zip(final_id, final_price):
                retailer = User.objects.get(id=id)
                retailer.price = price
                retailers_list.append(retailer)
            return render (request, 'admin/retailer-reports-final.html', {'retailers_list':retailers_list, 'retailer_start_date':retailer_start_date, 'retailer_end_date':retailer_end_date})
        return redirect ('tyre')


@login_required
def generate_retailers_reports_pdf(request, format=None):
    print("Hello")
    if request.user.is_superuser:
        try:
            final_id = request.session['final-id']
            final_price = request.session['final-price']
            retailer_start_date = request.session['retailer_start_date']
            retailer_end_date = request.session['retailer_end_date']
            retailers_list = []
            for id, price in zip(final_id, final_price):
                retailer = User.objects.get(id=id)
                retailer.price = price
                retailers_list.append(retailer)
            html = render_to_string('admin/retailers-reports-pdf.html', {'retailers_list':retailers_list, 'retailer_start_date':retailer_start_date, 'retailer_end_date':retailer_end_date})
            options = {
                'page-size': 'Letter',
                'encoding': "UTF-8",
            }
            # pdfkit.configuration(wkhtmltopdf='/home/mobapps/Desktop') 
            pdf = pdfkit.from_string(html, False, options=options)
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename=" {}.pdf"'.format(responsive_letter)
            response['Content-Disposition'] = 'attachment; filename="top-retailers-reports.pdf"'
            return response
        except KeyError:
            return redirect ('price-reports')
    return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class SearchReportsView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'admin/top-search-reports.html')
        return redirect ('tyre')
    def post(self, request):
        if request.user.is_superuser:
            search_start_date = request.POST.get('start_date')
            search_end_date = (request.POST.get('end_date'))
            request.session['search_start_date'] = search_start_date
            request.session['search_end_date'] = search_end_date
            words = TopSearch.objects.filter(created_at__date__gte=search_start_date, created_at__date__lte=search_end_date).values('word').annotate(count=Count('word')).order_by('-count')[:15]
            carts = Cart.objects.filter(created_at__date__gte=search_start_date, created_at__date__lte=search_end_date).values('tyre__code').annotate(count=Count('tyre__code')).order_by('-count')[:15]
            return render (request, 'admin/top-search-reports-final.html', {'words':words, 'carts':carts, 'search_start_date':search_start_date, 'search_end_date':search_end_date})
        return redirect ('tyre')
    

@login_required
def generate_top_search_reports_pdf(request, format=None):
    print("Hello")
    if request.user.is_superuser:
        try:
            search_start_date = request.session['search_start_date']
            search_end_date = request.session['search_end_date']
            words = TopSearch.objects.filter(created_at__date__gte=search_start_date, created_at__date__lte=search_end_date).values('word').annotate(count=Count('word')).order_by('-count')[:15]
            carts = Cart.objects.filter(created_at__date__gte=search_start_date, created_at__date__lte=search_end_date).values('tyre__code').annotate(count=Count('tyre__code')).order_by('-count')[:15]
            html = render_to_string('admin/top-search-reports-pdf.html', {'words':words, 'carts':carts, 'search_start_date':search_start_date, 'search_end_date':search_end_date})
            options = {
                'page-size': 'Letter',
                'encoding': "UTF-8",
            }
            # pdfkit.configuration(wkhtmltopdf='/home/mobapps/Desktop') 
            pdf = pdfkit.from_string(html, False, options=options)
            response = HttpResponse(pdf, content_type='application/pdf')
            # response['Content-Disposition'] = 'attachment; filename=" {}.pdf"'.format(responsive_letter)
            response['Content-Disposition'] = 'attachment; filename="top-search-reports.pdf"'
            return response
        except KeyError:
            return redirect ('price-reports')
    return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class OrdersView(View):
    def get(self, request):
        if request.user.is_superuser:
            orders = Order.objects.all().order_by('-id')
            paginator = Paginator(orders, per_page=20)
            page_number = request.GET.get('page')
            page_obj= paginator.get_page(page_number)
            return render (request, 'admin/orders.html', {'page_obj':page_obj})
        return redirect ('tyre')
    

@method_decorator(login_required, name='dispatch')
class UpdateOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            total_price = order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
            return render (request, 'admin/order-update.html', {'order':order, 'model':Order, 'total_price':total_price})
        return redirect ('tyre')
    def post(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.filter(id=id)
            my_order = Order.objects.get(id=id)
            total_tyre = my_order.tyre.all().aggregate(Sum('total_number'))['total_number__sum']
            total_price = my_order.tyre.all().aggregate(Sum('total_price'))['total_price__sum']
            po_number = request.POST.get('po_number')
            status = request.POST.get('status')
            if not Order.objects.filter(PO_number=po_number).exclude(PO_number=my_order.PO_number).exists():
                order.update(PO_number=po_number, status=status)
                Notification.objects.create(heading=f'Order {my_order.status}', message=f'Hello! {my_order.user}, Your order having order id {my_order.order_id} is {status} now for total {total_tyre} tyres of R {total_price}').receiver.add(my_order.user)
                send_mail(
                'TyrePower Order',
                f'Hello! {my_order.user},\n\nYour order having order id {my_order.order_id} is {my_order.status} now for total {total_tyre} tyres of R {total_price}',
                ('EMAIL_HOST_USER'),
                [str(my_order.user.email)],
                fail_silently=False,
                )
                messages.success(request, 'Order Updated Successfully')
                return redirect ('orders')
            messages.error(request, 'Provide Valid and Unique PO Number')
            return redirect ('order-update', id)
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class ConfirmDeleteOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            return render (request, 'admin/order-delete.html', {'order':order})
        return redirect ('tyre')


@method_decorator(login_required, name='dispatch')
class DeleteOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Order.objects.filter(id=id).delete()
            messages.error(request, 'Order Has Deleted')
            return redirect ('orders')
        return redirect ('tyre')   


def create_tyrepower_stock_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "code"
    sheet["B1"] = "total"
    return workbook


@method_decorator(login_required, name='dispatch')
class UploadStockXLSXView(View):
    def get(self, request):
        if request.user.is_superuser:
            workbook = create_tyrepower_stock_xlsx()
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=tyrepower.xlsx'
            virtual_workbook = save_virtual_workbook(workbook)
            response.write(virtual_workbook)
            return response
        return redirect ('tyre')
    # def post(self, request):
    #     if request.user.is_superuser:
    #         tyre_resource = ProxyTyreStockResource()
    #         dataset = Dataset()
    #         new_tyres = request.FILES['excel']
    #         dataset.load(new_tyres.read())
    #         result = tyre_resource.import_data(dataset, dry_run=True)
    #         if not result.has_errors():
    #             tyre_resource.import_data(dataset, dry_run=False)
    #             messages.success(request, 'Bulk Data Updated Successfully')
    #             return redirect ('view-xlsx')
    #         messages.error(request, f'Data Upload Unsuccessful')
    #         return redirect ('view-xlsx')
    #     return redirect ('tyre')


def create_tyrepower_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "name"
    sheet["B1"] = "code"
    sheet["C1"] = "brand"
    sheet["D1"] = "size"
    sheet["E1"] = "weight"
    sheet["F1"] = "oe_need"
    sheet["G1"] = "description"
    sheet["H1"] = "total"
    sheet["I1"] = "list_price"
    sheet["J1"] = "offer"
    return workbook


@method_decorator(login_required, name='dispatch')
class UploadXLSXView(View):
    def get(self, request):
        if request.user.is_superuser:
            workbook = create_tyrepower_xlsx()
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=tyrepower.xlsx'
            virtual_workbook = save_virtual_workbook(workbook)
            response.write(virtual_workbook)
            return response
        return redirect ('tyre')
    # def post(self, request):
    #     if request.user.is_superuser:
    #         tyre_resource = ProxyTyreResource()
    #         dataset = Dataset()
    #         new_tyres = request.FILES['excel']
    #         dataset.load(new_tyres.read())
    #         result = tyre_resource.import_data(dataset, dry_run=True)
    #         if not result.has_errors():
    #             tyre_resource.import_data(dataset, dry_run=False)
    #             messages.success(request, 'Bulk Data Updated Successfully')
    #             return redirect ('view-xlsx')
    #         messages.error(request, f'Data Upload Unsuccessful')
    #         return redirect ('view-xlsx')
    #     return redirect ('tyre')

