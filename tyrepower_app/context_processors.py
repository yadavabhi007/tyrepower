from .models import Notification, Cart, timezone
import datetime

def notification_context_processor(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(receiver=request.user).order_by('-id')
        total_notifications = notifications.exclude(is_seen=request.user).count()
        return {'notifications':notifications, 'total_notifications':total_notifications}
    return {}

def cart_context_processor(request):
    if request.user.is_authenticated:
        total_in_cart = Cart.objects.filter(user=request.user, status='Pending', created_at__gte=datetime.datetime.now()-datetime.timedelta(minutes=30), created_at__lte=datetime.datetime.now()).count()
        return {'total_in_cart':total_in_cart}
    return {}
