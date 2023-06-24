from django.db import models
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin




class CustomUserManager(BaseUserManager):
    def create_user(self, username, phone, first_name, last_name, email, password=None):
        if not username:
            raise ValueError('User must have Username')
        if not email:
            raise ValueError('User must have Email')
        if not phone:
            raise ValueError('User must have Phone')
        if not first_name:
            raise ValueError("User must have a First Name")
        if not last_name:
            raise ValueError("User must have a Last Name")
               
        user = self.model(
            username = username,
            first_name = first_name,
            last_name = last_name,
            email = email,
            phone = phone,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username, phone, first_name, last_name, email, password=None):
        """
        Creates and saves a superuser with the given username, email, first_name, password.
        """
        user = self.create_user(
            username = username,
            first_name = first_name,
            last_name = last_name,
            email = email,
            phone = phone,
            password = password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using = self._db)
        return user    


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(max_length=100, unique=True, validators=[username_validator], error_messages={'unique': "A user with that username already exists.",})
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.PositiveIntegerField(validators=[MaxValueValidator(99999999999999)])
    tier = models.ForeignKey('Tier', on_delete=models.CASCADE, related_name='user_tier')
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'phone']

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Retailer'
        verbose_name_plural = 'Retailers'


class BaseModel(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    abstract = True


class Address(BaseModel):
    retailer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_address')
    name = models.CharField(max_length=100)
    phone = models.PositiveIntegerField(validators=[MaxValueValidator(99999999999999)])
    house_and_street = models.CharField(max_length=100)
    suburb = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postcode = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.name}, {self.phone}, {self.suburb}, {self.postcode}'
        

class Tier(BaseModel):
    tier = models.CharField(max_length=100, unique=True)
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(99)])

    def __str__(self):
        return self.tier
    
    class Meta:
        verbose_name = 'Tier And Pricing'
        verbose_name_plural = 'Tiers And Pricing'


class Manufacturer(BaseModel):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logo')
    color = ColorField()

    def __str__(self):
        return self.name

    def image_tag(self):
        if self.logo:
            return mark_safe('<img src="{}" width="100" height="100"/>'.format(self.logo.url))
        return None
    image_tag.short_description = 'Logo'
    image_tag.allow_tags = True


class CustomTyreManager(models.Manager):
    def tyre(self):
        return super().get_queryset().all()


class Tyre(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)
    brand = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    weight = models.CharField(max_length=100, null=True, blank=True)
    oe_need = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    total = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    list_price = models.FloatField(validators=[MinValueValidator(0)], help_text='Prices are in ZAR')
    offer = models.BooleanField(default=False)

    def __str__(self):
        return self.code



class ProxyTyre(Tyre):
    # object = models.Manager()
    tyres = CustomTyreManager()
    class Meta:
        proxy = True
        ordering = ['id']


class Cart(BaseModel):
    STATUS = [
        ("Pending", 'Pending'),
        ("Ordered", 'Ordered'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_user')
    tyre = models.ForeignKey(Tyre, on_delete=models.CASCADE, related_name='cart_tyre')
    total_number = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    total_price = models.FloatField(validators=[MinValueValidator(0)], help_text='Prices are in ZAR')
    status = models.CharField(max_length=100, choices=STATUS, default='Pending')

    def __str__(self):
        return self.tyre.code
    

class Order(BaseModel):
    STATUS = [
        ("Pending", 'Pending'),
        ("Delivered", 'Delivered'),
        ("Picked By Self", 'Picked By Self'),
        ("Canceled", 'Canceled'),
    ]
    DELIVERY = [
        ("Self Pickup", 'Self Pickup'),
        ("Courier Service", 'Courier Service'),
    ]
    order_id = models.CharField(unique=True, max_length=8, null=True, blank=True)
    PO_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_user')
    tyre = models.ManyToManyField(Cart, related_name='order_cart')
    status = models.CharField(max_length=100, choices=STATUS, default='Pending')
    product_delivery = models.CharField(max_length=100, choices=DELIVERY, default='Self Pickup')
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    vehical_name = models.CharField(max_length=100, null=True, blank=True)
    vehical_number = models.CharField(max_length=100, null=True, blank=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='order_shipping_address', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            latest_id = Order.objects.aggregate(models.Max('id'))['id__max'] or 0
            new_id = int(latest_id) + int(1)
            self.order_id = "TP{:06d}".format(new_id)
        super().save(*args, **kwargs)



class Notification(BaseModel):
    heading = models.CharField(max_length=100)
    message = models.TextField(max_length=500)
    receiver = models.ManyToManyField(User, related_name='notification_receiver')
    is_seen = models.ManyToManyField(User, blank=True, related_name='is_seen_notification')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_sender', null=True, blank=True)


class TopSearch(BaseModel):
    word = models.CharField(max_length=100)
    retailer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_search_retailer')

    class Meta:
        verbose_name = 'Top Search'
        verbose_name_plural = 'Top Searches'


class PrivacyPolicy(BaseModel):
    privacy_policy = models.FileField(upload_to='privacy_policy')
    
    class Meta:
        verbose_name = 'Privacy Policy'
        verbose_name_plural = 'Privacy Policies'


class TermAndCondition(BaseModel):
    terms = models.FileField(upload_to='terms')

    class Meta:
        verbose_name = 'Term And Condition'
        verbose_name_plural = 'Terms And Conditions'

