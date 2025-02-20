from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils.crypto import get_random_string
from django_countries.fields import CountryField


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('superadmin', 'SuperAdmin'),
        ('organizer', 'Organizer'),
        ('talent', 'Talent'),
        ('partner', 'Partner'),
        ('team', 'Team'),
        ('gest', 'Gest'),
    ]
    email = models.EmailField(unique=False, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True, null=True)
    is_partner = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_team = models.BooleanField(default=False)
    is_enduser = models.BooleanField(default=False)
    is_event = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_google = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        if self.username:
            return self.username
        elif self.email:
            return self.email
        # else:
        #     return f"User {self.first_name}"


class Owner(CustomUser):
    class Meta:
        verbose_name = "Owner"
        verbose_name_plural = "Owners"


class SuperAdmin(CustomUser):
    class Meta:
        verbose_name = "Super Admin"
        verbose_name_plural = "Super Admins"


class EventOrganizer(CustomUser):
    class Meta:
        verbose_name = "Organizer"
        verbose_name_plural = "Organizers"


class EventTalent(CustomUser):
    class Meta:
        verbose_name = "Talent"
        verbose_name_plural = "Talents"


class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    second_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    telephone_number = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.email} - {self.first_name}"


class Partner(models.Model):
    PARTNER_TYPE_CHOICES = (
        ('patner_1', 'Partner 1'),
        ('patner_2', 'Partner 2'),
        ('patner_3', 'Partner 3')
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='partner')
    company_name = models.CharField(max_length=255, default="Non spécifié")
    first_name = models.CharField(max_length=255, default="Non spécifié")
    second_name = models.CharField(max_length=255, default="Non spécifié")
    address = models.CharField(max_length=255, default="Non spécifié")
    telephone_number = models.CharField(max_length=255, default="Non spécifié")
    email = models.EmailField(default="Non spécifié")
    partner_type = models.CharField(max_length=255 , choices=PARTNER_TYPE_CHOICES)
    company_description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} - {self.first_name}"


class EventPartner(CustomUser):
    PARTNER_TYPE_CHOICES = (
        ('patner_1', 'Partner 1'),
        ('patner_2', 'Partner 2'),
        ('patner_3', 'Partner 3')
    )
    company_name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=255, choices=PARTNER_TYPE_CHOICES)
    company_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} - {self.first_name}"


class EventTeam(CustomUser):
    team_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"


class Client(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True, related_name="client_partner")
    company_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    second_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    telephone_number = models.CharField(max_length=255)
    email = models.EmailField()
    company_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} - {self.first_name}"


class Gest(CustomUser):
    class Meta:
        verbose_name = "Gest"
        verbose_name_plural = "Guests"


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True)
    description = models.TextField(null=True)
    services = models.ManyToManyField('EventService', related_name="categories")

    class Meta:
        verbose_name_plural = "Categories"


class PassCategory(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True)
    qr_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    nfc_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = models.TextField(null=True)

    class Meta:
        verbose_name = "pass_category"


# class Country(models.Model):
#     code = models.IntegerField(unique=True)
#     name = models.CharField()


class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ('with_resources', 'With Resources'),
        ('without_resources', 'Without Resources'),
    )
    event_code = models.CharField(max_length=255, unique=True, null=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    event_type = models.CharField(max_length=255, choices=EVENT_TYPE_CHOICES, default='')
    event_name = models.CharField(max_length=255)
    event_country = CountryField(max_length=255, default='Senegal')
    event_place = models.CharField(max_length=255)
    # New fields for geolocation
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    description = models.TextField()
    # type_of_event = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True)
    event_partner = models.ForeignKey(
        EventPartner, on_delete=models.CASCADE, blank=True, null=True, related_name="partner_events"
    )
    organizer = models.ForeignKey(
        EventOrganizer, on_delete=models.CASCADE, blank=True, null=True, related_name="organized_events"
    )
    talents = models.ManyToManyField(
        'EventTalent', related_name="events", blank=True
    )
    begindatetime = models.DateTimeField()
    enddatetime = models.DateTimeField()
    event_image_1 = models.FileField(upload_to="event/images", blank=True, null=True)
    event_image_2 = models.FileField(upload_to="event/images", blank=True, null=True)
    event_image_3 = models.FileField(upload_to="event/images", blank=True, null=True)
    is_resourses_added = models.BooleanField(default=False)
    is_payment_done = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event_name} - is activated {self.is_activated}"


class EventOccurrence(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="occurrences")
    event_country = CountryField(max_length=255, default='Senegal')
    event_place = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    begin_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    def __str__(self):
        return f"{self.event.name} at {self.event_place} on {self.begin_datetime}"


class EventPassCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_pass_categories')
    pass_category = models.ForeignKey(PassCategory, on_delete=models.CASCADE, related_name='event_pass_categories')
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.PositiveBigIntegerField(default=0)
    with_nfc = models.BooleanField(default=False, null=True)

    class Meta:
        unique_together = ('event', 'pass_category')
        verbose_name = "event_pass_category"

    def __str__(self):
        return f"{self.event.name} - {self.pass_category.name}"


class EndUserDetail(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    second_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    telephone_number = models.CharField(max_length=255, null=True)
    email = models.EmailField(null=True)
    email_or_phone = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_google = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.telephone_number} - {self.first_name}"


class EventService(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
# class EventPass(models.Model):
#     event = models.OneToOneField(Event , on_delete=models.CASCADE , related_name='pass_event')
#     pass_total_quantity = models.PositiveBigIntegerField(default=0)
#     simple_pass = models.PositiveIntegerField(default=0)
#     vip_pass = models.PositiveIntegerField(default=0)
#     gold_pass = models.PositiveIntegerField(default=0)
#     prestige_pass = models.PositiveIntegerField(default=0)
#     is_nfc =  models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.event.event_name} - pass {self.pass_total_quantity}x"


# class EventBracelet(models.Model):
#     event = models.ForeignKey(Event , on_delete=models.CASCADE , related_name='event_bracelet')
#     bracelet_total_quantity = models.PositiveBigIntegerField(default=0)
#     blue = models.PositiveIntegerField(default=0)
#     yellow = models.PositiveIntegerField(default=0)
#     red = models.PositiveIntegerField(default=0)
#     purple = models.PositiveIntegerField(default=0)
#     is_nfc =  models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.event.event_name} - bracelet {self.bracelet_total_quantity}x"


# class EventBadges(models.Model):
#     event = models.ForeignKey(Event , on_delete=models.CASCADE , related_name='event_badges')
#     simple_paper = models.PositiveIntegerField(default=0)
#     personalized_badge = models.PositiveIntegerField(default=0)
#     is_nfc =  models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.event.event_name} -  {self.simple_paper}x - {self.personalized_badge}x"


# class CheckInPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='check_in_points')
#     check_in_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Check-in Point for {self.event.event_name}"

# class ExhibitionPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='exhibition_points')
#     exhibition_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Exhibition Point for {self.event.event_name}"


# class ActivityPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='activity_points')
#     activity_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Activity Point for {self.event.event_name}"


# class GuichetPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='guichet_points')
#     guichet_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Guichet Point for {self.event.event_name}"


# class DrinksPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='drinks_points')
#     drinks_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Drinks Point for {self.event.event_name}"

# class WorkshopPoint(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='workshop_points')
#     workshop_point_quantity = models.IntegerField(default=0)

#     def __str__(self):
#         return f"Workshop Point for {self.event.event_name}"

# class EventTeam(models.Model):
#     TEAM_TYPE_CHOICES= (
#         ('check in', 'Check In'),
#         ('guichet', 'Guichet'),
#         ('drinks', 'Drinks'),
#         ('food court', 'Food Court'),
#         ('activities', 'Activities'),
#         ('other services', 'Other Services'),
#     )
#     MEMBER_TYPE_CHOICES=(
#         ('team', 'Team'),
#         ('manager', 'Manager'),
#     )
#     user = models.OneToOneField(CustomUser , on_delete=models.CASCADE)
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_team')
#     team_type = models.CharField(max_length=255 , choices=TEAM_TYPE_CHOICES)
#     member_type = models.CharField(max_length=255,choices=MEMBER_TYPE_CHOICES)
#     first_name = models.CharField(max_length=255)
#     second_name = models.CharField(max_length=255)
#     member_post  = models.CharField(max_length=255)
#     member_role  = models.CharField(max_length=255,default='C-in Point')
#     telephone_number = models.CharField(max_length=255)
#     email= models.EmailField()
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

#     def __str__(self):
#         return f"{self.first_name} - {self.member_type}"

# class PassPrice(models.Model):
#     PASS_TYPE_CHOICES = (
#         ('Simple', 'Simple'),
#         ('Gold', 'Gold'),
#         ('Vip', 'Vip'),
#         ('Prestige', 'Prestige'),
#     )
#     event = models.ForeignKey(Event , on_delete=models.CASCADE, related_name='event_pass_price', blank=True , null=True)
#     pass_type = models.CharField(max_length=50, choices=PASS_TYPE_CHOICES)
#     price_with_qr = models.DecimalField(max_digits=10, decimal_places=2)
#     price_with_nfc = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.pass_type} - QR: {self.price_with_qr}, NFC: {self.price_with_nfc}"

# class BraceletPrice(models.Model):
#     BRACELET_TYPE_CHOICES = (
#         ('Blue', 'Blue'),
#         ('Yellow', 'Yellow'),
#         ('Red', 'Red'),
#         ('Purple', 'Purple'),
#     )
#     event = models.ForeignKey(Event , on_delete=models.CASCADE, related_name='event_braclet_price', blank=True , null=True)
#     bracelet_type = models.CharField(max_length=50, choices=BRACELET_TYPE_CHOICES)
#     price_with_qr = models.DecimalField(max_digits=10, decimal_places=2)
#     price_with_nfc = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.bracelet_type} - QR: {self.price_with_qr}, NFC: {self.price_with_nfc}"


class ServicePrice(models.Model):
    SERVICE_TYPE_CHOICES = (
        ('Check in', 'Check in'),
        ('Guichet', 'Guichet'),
        ('Drinks', 'Drinks'),
        ('Food Court', 'Food Court'),
        ('Activity', 'Activity'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_service_price', blank=True,
                              null=True)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.service_type} - {self.service_price}"


# class PassPurchase(models.Model):
#     PASS_TYPE_CHOICES = (
#         ('Simple', 'Simple'),
#         ('Gold', 'Gold'),
#         ('Vip', 'Vip'),
#         ('Prestige', 'Prestige'),
#     )

#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='pass_purchases')
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,blank=True,null=True)  # Assuming you have a CustomUser model for authentication
#     pass_type = models.CharField(max_length=50, choices=PASS_TYPE_CHOICES)
#     quantity = models.PositiveIntegerField(default=0)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     purchase_date = models.DateTimeField(auto_now_add=True)
#     is_payment_done = models.BooleanField(default=False)
#     nfc_id = models.UUIDField(default=uuid.uuid4, editable=False)
#     is_used = models.BooleanField(default=False)
#     def __str__(self):
#         return f"{self.user.username} - {self.pass_type} for {self.event.event_name}"


class MyCart(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='my_cart')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    pass_category = models.ForeignKey(PassCategory, on_delete=models.CASCADE, related_name='my_cart', null=True)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # def __str__(self):
    #     return f"{self.user.username} - {self.pass_category} for {self.event.event_name}"


# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('paid', 'Paid'),
#         ('cancelled', 'Cancelled'),
#     ]
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     payment_done = models.BooleanField(default=False)
#     payment_reference = models.CharField(max_length=100, blank=True, null=True)
#     payment_stripe_token = models.CharField(max_length=255, default="", null=True, blank=True)
#
#
#     def __str__(self):
#         return f"Order {self.ordering} by {self.user.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_done = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_stripe_token = models.CharField(max_length=255, default="", null=True, blank=True)
    order_id = models.CharField(max_length=10, unique=True, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    due_date = models.DateTimeField(auto_now=True,null=True, blank=True)
    # order_id = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True)


    def __str__(self):
        return f"Order {self.order_id} by {self.user.name}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        super().save(*args, **kwargs)

    def generate_order_id(self):
        """ Génère un ID unique sous la forme XM-0123 """
        prefix = "XM-"
        while True:
            unique_number = get_random_string(4, allowed_chars="0123456789")
            new_order_id = f"{prefix}{unique_number}"
            if not Order.objects.filter(order_id=new_order_id).exists():
                return new_order_id


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    pass_category = models.ForeignKey(PassCategory, on_delete=models.CASCADE, related_name='order_items', null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.quantity} x {self.pass_category} for {self.event} in Order {self.order.name}"


class Ticket(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='%(class)s_ticket')
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='%(class)s_ticket')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True,
                             related_name='%(class)s_ticket')  # Assuming you have a CustomUser model for authentication
    pass_category = models.ForeignKey(PassCategory, on_delete=models.CASCADE, related_name='%(class)s_ticket',
                                      null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.CharField(max_length=12, default=1)
    purchase_date = models.DateTimeField(null=True)
    is_payment_done = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    control_date = models.DateTimeField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    due_date = models.DateTimeField(auto_now=True,null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

    def generate_ticket_number(self):
        return get_random_string(20)

    def __str__(self):
        return f"Ticket {self.ticket_number} for {self.event} ({self.pass_category})"


class ETicket(Ticket):
    qr_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiration_date = models.DateTimeField(null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='etickets', null=True, blank=True)



class PhysicalTicket(Ticket):
    qr_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)
    nfc_tag_1 = models.CharField(max_length=100, null=True, blank=True)
    nfc_tag_2 = models.CharField(max_length=100, null=True, blank=True)
    is_loaded = models.BooleanField(default=False)


class ThermalTicket(Ticket):
    qr_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)
    is_loaded = models.BooleanField(default=False)


class BraceletTicket(Ticket):
    bracelet_code = models.CharField(max_length=100)
    uid_1 = models.CharField(max_length=50, null=True)
    uid_2 = models.CharField(max_length=50, null=True)


class BadgeTicket(Ticket):
    BADGE_TYPE_CHOICES = (
        ('salon', 'Badge salon'),
        ('event', 'Badget event'),
    )
    uid_1 = models.CharField(max_length=50, null=True)
    uid_2 = models.CharField(max_length=50, null=True)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPE_CHOICES)


class NFCData(models.Model):
    nfc_id = models.CharField(max_length=500)
    wallet = models.BigIntegerField()

    def __str__(self):
        return f"{self.nfc_id} - {self.wallet}"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)  # Nouveau champ pour suivre l'état de la vérification

    def __str__(self):
        return f'{self.user.name} - {self.otp}'

    class Meta:
        ordering = ['-created_at']


class FavoriteEvent(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f'{self.user.name} favorited {self.event.name}'

 
class SentGift(models.Model):
    gifter = models.ForeignKey(EndUserDetail, on_delete=models.CASCADE, related_name='gifter')
    reciever_name = models.CharField(max_length=255)
    reciever_email = models.EmailField() 
    ticket_id = models.IntegerField()

    def __str__(self):
        return f'{self.gifter.name} {self.reciever_name}'

# class NFCDataRecord(models.Model):
