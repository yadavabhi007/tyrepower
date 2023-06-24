from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, Order
from django.db.models import Sum
from django.core.mail import send_mail
from django.db.models.signals import m2m_changed


@receiver(m2m_changed, sender=Order.tyre.through)
def order_notification(sender, instance, **kwargs):
    order_id = instance.order_id
    status = instance.status
    user = instance.user
    tyres = instance.tyre.all()
    total_tyre = tyres.aggregate(Sum('total_number'))['total_number__sum']
    total_price = tyres.aggregate(Sum('total_price'))['total_price__sum']
    if total_price:
        Notification.objects.create(heading=f'Order {status}', message=f'Hello! {user}, Your order having order id {order_id} is {status} now for total {total_tyre} tyres of R {total_price}').receiver.add(user)
        send_mail(
        'TyrePower Order',
        f'Hello! {user},\n\nYour order having order id {order_id} is {status} now for total {total_tyre} tyres of R {total_price}',
        ('EMAIL_HOST_USER'),
        [str(user.email)],
        fail_silently=False,
        )

