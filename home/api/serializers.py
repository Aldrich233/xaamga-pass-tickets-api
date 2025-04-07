from requests import Response
from rest_framework import serializers
# from django.core.exceptions import ValidationError
from ..models import *
from django.conf import settings
from rest_framework import serializers
from .facebook import Facebook
from .register import register_social_user
# from rest_framework.exceptions import*
from rest_framework.response import Response
from rest_framework import status

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class AdminCustomUserSerializer(serializers.ModelSerializer):
    admin = AdminSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'email', 'first_name', 'admin']


    # def update(self, instance, validated_data):
    #     admin_data = validated_data.pop('admin', {})
    #     instance.email = validated_data.get('email', instance.email)
    #     instance.first_name = validated_data.get('first_name', instance.first_name)
    #     # Update other fields of CustomUser model as needed...
    #     instance.save()

    #     admin = instance.admin
    #     admin_serializer = AdminSerializer(admin, data=admin_data, partial=True)
    #     if admin_serializer.is_valid():
    #         admin_serializer.save()

    #     return instance


class PartnerSerializer(serializers.ModelSerializer):
    # telephone_number  = serializers.CharField()
    class Meta:
        model = Partner
        fields = '__all__'
    def validate_telephone_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Telephone number must be exactly 10 numeric digits.")
        return value


# class PartnerCustomUserSerializer(serializers.ModelSerializer):
#     partner = PartnerSerializer()
#
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'username', 'password', 'email', 'first_name', 'partner']

class PartnerCustomUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    password = serializers.CharField(
        source='user.password',
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Partner
        fields = ['id', 'username', 'password', 'email', 'first_name',
                  'company_name', 'last_name', 'address', 'telephone_number',
                  'partner_type', 'company_description', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Mise à jour du mot de passe séparément si besoin
        password = user_data.pop('password', None)
        if password:
            user.set_password(password)

        # Mise à jour des autres champs utilisateur
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Mise à jour du Partner
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class PartnerCompanyNameSerializer(serializers.ModelSerializer):

    user = CustomUserSerializer()

    # Add fields for client and event counts
    event_count = serializers.SerializerMethodField()
    clients_count = serializers.SerializerMethodField() #(nombre de clients uniques liés à ces événements) .distinct().count() → Compte le nombre de clients uniques.
    # username = serializers.SerializerMethodField()
    # password = serializers.SerializerMethodField()

    class Meta:
        model = Partner
        fields = '__all__'

    def get_event_count(self, obj):
        # Count the related Event objects
        return obj.handles_partner_events.count()

    def get_clients_count(self, obj):
        # Count the related Client objects
        return obj.handles_partner_events.values('client').distinct().count()



    # def get_username(self, obj):
        # Access the username from the related CustomUser model
        # return obj.user.username

    # def get_password(self, obj):
    #     # Access the password from the related CustomUser model
    #     return obj.user.password

class PartnerDescriptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['company_description']


class ClientSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Client
        fields = ['id', 'company_name', 'username', 'email',
                  'first_name', 'last_name', 'address', 'telephone_number', 'partner']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        # Synchronisation bidirectionnelle
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data['first_name']
        elif 'first_name' not in validated_data and 'first_name' in user_data:
            validated_data['first_name'] = user_data['first_name']

        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data['last_name']
        elif 'last_name' not in validated_data and 'last_name' in user_data:
            validated_data['last_name'] = user_data['last_name']

        # Mise à jour User
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Mise à jour Client
        instance = super().update(instance, validated_data)

        return instance















# class ClientSerializer(serializers.ModelSerializer):
#     # username = serializers.SerializerMethodField(read_only = True)
#     # password = serializers.SerializerMethodField(read_only = True)
#     username = serializers.CharField(source='user.username', required=False)
#     password = serializers.CharField(source='user.password', required=False, write_only=True)
#     email = serializers.EmailField(source='user.email', required=False)
#     first_name = serializers.CharField(source='user.first_name', required=False)
#     last_name = serializers.CharField(source='user.last_name', required=False)
#
#     class Meta:
#         model = Client
#         fields = '__all__'
#
#     def get_username(self, obj):
#         # Access the username from the related CustomUser model
#         return obj.user.username
#
#     def get_password(self, obj):
#         # Access the password from the related CustomUser model
#         return obj.user.password
#
#     def update(self, instance, validated_data):
#         user_data = validated_data.pop('user', None)
#         if user_data:
#             user = instance.user
#             # Gestion spéciale pour le password (hachage)
#             if 'password' in user_data:
#                 user.set_password(user_data['password'])
#                 user_data.pop('password')
#
#             # Mise à jour des autres champs user
#             for attr, value in user_data.items():
#                 setattr(user, attr, value)
#             user.save()
#
#         # Mise à jour des champs Client
#         return super().update(instance, validated_data)


class ClientCustomUserSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'email', 'first_name', 'client']

class ClientCompanyNameSerializer(serializers.ModelSerializer):
    # user = CustomUserSerializer()
    password = serializers.CharField(source='user.password',  read_only=True)
    username = serializers.CharField(source='user.username',  read_only=True)
    partner = PartnerSerializer()
    event_count = serializers.SerializerMethodField()
    class Meta:
        model = Client
        # fields = ['id','company_name',"company_description"]
        fields = '__all__'

    def get_event_count(self, obj):
        return Event.objects.filter(user=obj.user).count()

class PartnerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Both username and password are required.")

        return data
    

class TypeOfEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['type_of_event', 'event_image_1']

    class Meta:
        model = Event
        fields = ['type_of_event', 'event_image_1']


class PassCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PassCategory
        fields = ['id', 'name', 'qr_price', 'nfc_price', 'description']
  
        
class EventPassCategorySerializer(serializers.ModelSerializer):
    pass_category_name = serializers.CharField(source='pass_category.name')
    pass_category_id = serializers.IntegerField(source='pass_category.id')

    class Meta:
        model = EventPassCategory
        fields = ['pass_category_id', 'pass_category_name', 'price', 'quantity', 'with_nfc']

             
class EventSerializer(serializers.ModelSerializer):
    event_pass_categories = EventPassCategorySerializer(many=True)
    event_name = serializers.CharField()
    begindatetime = serializers.DateTimeField()
    enddatetime = serializers.DateTimeField()
    event_image_1 = serializers.CharField(read_only=True)
    event_image_2 = serializers.CharField(read_only=True)
    event_image_3 = serializers.CharField(read_only=True)
    client_first_name = serializers.CharField(source='client.first_name', read_only=True)
    client_last_name = serializers.CharField(source='client.last_name', read_only=True)
    partner_first_name = serializers.CharField(source='partner.first_name', read_only=True)
    partner_last_name = serializers.CharField(source='partner.last_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 
            'event_type', 
            'event_name', 
            'event_place',
            'begindatetime',
            'enddatetime',
            'latitude',
            'longitude',
            'description', 
            'event_image_1', 
            'event_image_2', 
            'event_image_3',
            'client_first_name', 
            'client_last_name', 
            'partner_first_name', 
            'partner_last_name', 
            'category_name', 
            'event_pass_categories'
        ]


class CategorySerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True, source='event_set')
    class Meta:
        model = Category
        fields = ['name', 'description', 'events']
        

class EventCustomUserSerializer(serializers.ModelSerializer):
    event = ClientSerializer()

    class Meta:
        model = Event
        # fields = ['id', 'username', 'password', 'email', 'first_name', 'event']
        fields = '__all__'

# class EventPassSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventPass
#         fields = '__all__'

# class EventBraceletSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventBracelet
#         fields = '__all__'

# class EventBadgesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventBadges
#         fields = '__all__'

# class CheckInPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CheckInPoint
#         fields = '__all__'

# class ExhibitionPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ExhibitionPoint
#         fields = '__all__'

# class ActivityPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ActivityPoint
#         fields = '__all__'

# class GuichetPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = GuichetPoint
#         fields = '__all__'

# class DrinksPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DrinksPoint
#         fields = '__all__'

# class WorkshopPointSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkshopPoint
#         fields = '__all__'


# class EventTeamSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source='user.username',read_only=True)
#     password = serializers.CharField(source='user.password',read_only=True)
#     event_name = serializers.CharField(source='event.event_name',read_only=True)
#     partner = serializers.CharField(source='event.partner',read_only=True)
#     client = serializers.CharField(source='event.client',read_only=True)

#     class Meta:
#         model = EventTeam
#         fields = '__all__'

 

# class EndUserSerializer(serializers.Serializer):
#     email_or_phone = serializers.CharField()
#     password = serializers.CharField()

#     def validate(self, data):
#         email_or_phone = data.get('email_or_phone')
#         password = data.get('password')

#         if email_or_phone and password:
#             user = CustomUser.objects.filter(email=email_or_phone).first() or CustomUser.objects.filter(phone_number=email_or_phone).first()
#             if user and user.check_password(password):
#                 if not user.is_email_verified:
#                     raise serializers.ValidationError("Email is not verified.")
                    

#                 data['user'] = user
#             else:
#                 raise serializers.ValidationError("Invalid credentials.")
#         else:
#             raise serializers.ValidationError("Must include email or phone number and password.")
#         return data


# class EndUserSerializer(serializers.Serializer):
# #     email_or_phone = serializers.CharField()
# #     password = serializers.CharField()
# #
# #     def validate(self, data):
# #         email_or_phone = data.get('email_or_phone')
# #         password = data.get('password')
# #
# #         if not email_or_phone or not password:
# #             raise serializers.ValidationError("Le champ email ou téléphone et le mot de passe sont requis.")
# #
# #         user = (CustomUser.objects.filter(email=email_or_phone).first() or
# #                 CustomUser.objects.filter(phone_number=email_or_phone).first())
# #
# #         if user and user.check_password(password):
# #             if not user.is_email_verified:
# #                 raise serializers.ValidationError("Votre email n'a pas encore été vérifié. Veuillez vérifier votre email.")
# #
# #             data['user'] = user
# #         else:
# #             raise serializers.ValidationError("Identifiants invalides.")
# #
# #         return data


class EndUserSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        password = data.get('password', None)

        if not email_or_phone:
            raise serializers.ValidationError("Le champ email ou téléphone est requis.")

        user = (CustomUser.objects.filter(email=email_or_phone).first() or
                CustomUser.objects.filter(phone_number=email_or_phone).first())

        if not user:
            raise serializers.ValidationError("Utilisateur introuvable.")

        # Connexion sans mot de passe pour les comptes Google
        if user.is_google:
            data['user'] = user
            return data

        # Vérification standard avec mot de passe
        if not password:
            raise serializers.ValidationError("Le mot de passe est requis pour ce type de compte.")

        if not user.check_password(password):
            raise serializers.ValidationError("Identifiants invalides.")

        if not user.is_email_verified:
            raise serializers.ValidationError("Votre email n'a pas encore été vérifié. Veuillez vérifier votre email.")

        data['user'] = user
        return data

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()


# class PassPriceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PassPrice
#         fields = '__all__'


# class BraceletPriceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BraceletPrice
#         fields = '__all__'

class ServicePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePrice
        fields = '__all__'


# class PassPurchaseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PassPurchase
#         fields = '__all__'

class TicketSerializer(serializers.Serializer):
    order_item = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())
    ticket_number = serializers.CharField(max_length=20)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), allow_null=True)
    pass_category = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = serializers.DateTimeField(allow_null=True)
    is_payment_done = serializers.BooleanField(default=False)
    is_used = serializers.BooleanField(default=False)
    control_date = serializers.DateTimeField(allow_null=True)
    qr_code = serializers.UUIDField(required=False)
    expiration_date = serializers.DateTimeField(required=False)
    nfc_tag_1 = serializers.CharField(max_length=100, required=False)
    nfc_tag_2 = serializers.CharField(max_length=100, required=False)
    is_loaded = serializers.BooleanField(default=False, required=False)
    
    class Meta:
        model = Ticket
        fields = '__all__'

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
        

class ETicketSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    begindatetime = serializers.DateTimeField(source='event.begindatetime')
    event_image_1 = serializers.CharField(source='event.event_image_1', read_only=True)
    event_image_2 = serializers.CharField(source='event.event_image_2', read_only=True)
    event_image_3 = serializers.CharField(source='event.event_image_3', read_only=True)
    category_event = serializers.CharField(source='event.category.name', read_only=True)
    class Meta:
        model = ETicket 
        fields = '__all__'

class PhysicalTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalTicket
        fields = '__all__' 

class ThermalTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThermalTicket
        fields = '__all__' 

# class BraceletTicketSerializer(TicketSerializer):
#     class Meta(TicketSerializer.Meta):
#         model = BraceletTicket

# class BadgeTicketSerializer(TicketSerializer):
#     class Meta(TicketSerializer.Meta):
#         model = BadgeTicket
       

class MyCartSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    pass_category = PassCategorySerializer()
    
    class Meta:
        model = MyCart
        fields = '__all__'


class ForgotPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email',)


#NFC SERIALIZER
class PostNFCDataSerializer(serializers.Serializer):
    nfc_id = serializers.UUIDField()  # Assuming nfc_id is a UUID field
    wallet = serializers.IntegerField(min_value=0)

class NFCDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFCData
        fields = ["wallet"]


class EndUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EndUserDetail
        fields = '__all__'

class GetAllUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','first_name','last_name', 'username', 'email','password','is_active' ,'is_partner', 'is_client', 'is_team', 'is_enduser', 'is_event', 'is_admin']

class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'event_name', 'event_type']

# class UniqueEventTeamSerializer(serializers.Serializer):
#     event_id = serializers.IntegerField()
#     team_types = serializers.ListField(child=serializers.CharField())

#     def get_unique_team_types(self, event_id):
#         queryset = EventTeam.objects.filter(event_id=event_id).values('team_type').distinct()
#         team_types = [item['team_type'] for item in queryset]
#         return {
#             'event_id': event_id,
#             'team_types': team_types
#         }
    

# class ListPassPriceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PassPrice
#         exclude = ['event']



class FacebookSocialAuthSerializer(serializers.Serializer):
    """Handles serialization of facebook related data"""
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = Facebook.validate(auth_token)

        try:
            user_id = user_data['id']
            email = user_data['email']
            name = user_data['name']
            provider = 'facebook'
        except:

            raise serializers.ValidationError(
                'The token  is invalid or expired. Please login again.'
            )
        return register_social_user(
            provider=provider, user_id=user_id, email=email, name=name)
    


class FavoriteEventSerializer(serializers.ModelSerializer):
    event = EventSerializer()

    class Meta:
        model = FavoriteEvent
        fields = ['id', 'added_on', 'event']


class SendGiftSerializer(serializers.ModelSerializer):

    class Meta:
        model = SentGift
        exclude = ["gifter"]
        