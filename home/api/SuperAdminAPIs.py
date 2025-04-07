import base64
import requests
from django.db import IntegrityError
from django.db.models import Q
from drf_spectacular.openapi import AutoSchema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import CustomUser, Partner
from .serializers import *
import random
import string
from rest_framework.exceptions import ValidationError
from itertools import groupby
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
import qrcode
from django.http import HttpResponse
from rest_framework.generics import *
from rest_framework.authentication import TokenAuthentication
from io import BytesIO
import qrcode
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
import json


class RandomUserAPIView(APIView):
    schema = AutoSchema()

    """
    This class defines a RandomUserAPIView which is an API view to generate random usernames and passwords.
    It utilizes the generate_random_username and generate_random_password methods to create the username and password.
    The post method is implemented to handle HTTP POST requests, generating and returning a random username and password in the response data.
    """

    def generate_random_username(self):
        # Generate a random username using lowercase letters and digits
        letters_and_digits = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(10))

    def generate_random_password(self):
        # Generate a random password using uppercase letters, lowercase letters, and digits
        password_chars = string.ascii_letters + string.digits
        return ''.join(random.choice(password_chars) for i in range(12))

    def post(self, request):
        # Generate random username and password
        random_username = self.generate_random_username()
        random_password = self.generate_random_password()

        response_data = {
            'username': random_username,
            'password': random_password,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class GetAllUserList(APIView):
    schema = AutoSchema()

    """
    This class defines a GetAllUserList API view which retrieves information about all users.
    The get method is implemented to handle HTTP GET requests and returns data including the total number of users,
    active user count, inactive user count, and serialized data of all users.
    """

    def get(self, request, format=None):
        users = CustomUser.objects.filter(
            is_active=True,
        ).filter(
            Q(is_admin=True) |
            Q(is_partner=True) |
            Q(is_client=True) |
            Q(is_team=True)
        )
        all_users = CustomUser.objects.all().count()

        # active_user_count = CustomUser.objects.filter(is_active=True).count()
        # inactive_user_count = CustomUser.objects.filter(is_active=False).count()

        serializer = GetAllUserSerializer(users,  many=True)

        return Response({'data': serializer.data})

        # return Response(
        #     {'all_users': all_users, 'active_user_count': active_user_count, 'inactive_user_count': inactive_user_count,
        #      "data": serializer.data})


class UpdateAndDeleteUsers(APIView):
    schema = AutoSchema()

    """
    This class defines an UpdateAndDeleteUsers API view which allows updating and deleting users.
    The put method is implemented to handle HTTP PUT requests for updating a user's activation status.
    The delete method is implemented to handle HTTP DELETE requests for deleting a user.
    """

    def put(self, request, format=None):
        user_id = request.data.get('user_id')
        is_active = request.data.get('is_active')

        try:
            user = CustomUser.objects.get(id=user_id)
            user.is_active = is_active
            user.save()
            return Response({'message': 'User updated successfully'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, format=None):
        user_id = request.data.get('user_id')

        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


class PartnerRegister(APIView):
    schema = AutoSchema()

    """
    This class defines a PartnerRegister API view which handles partner registration.
    The get method retrieves all partner objects.
    The post method validates and processes partner registration data, creating a new partner.
    """

    def get(self, request):
        try:
            partner_obj = Partner.objects.all()
            serializer = PartnerSerializer(partner_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    from django.db.utils import IntegrityError
    from django.core.exceptions import ValidationError

    def post(self, request, *args, **kwargs):
        required_fields = ['company_name', 'first_name', 'last_name', 'address', 'telephone_number', 'email',
                           'partner_type', 'username', 'password']

        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)

        username = request.data['username'].lower()
        password = request.data['password']
        company_name = request.data['company_name'].lower()
        first_name = request.data['first_name'].lower()
        last_name = request.data['last_name'].lower()
        address = request.data['address'].lower()
        telephone_number = request.data['telephone_number']
        email = request.data['email'].lower()
        partner_type = request.data['partner_type']

        # Vérifier si un utilisateur avec cet email existe
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists. Please use a different email."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si un utilisateur avec ce username existe
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "User with this username already exists. Please use a different username."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Créer l'utilisateur
            user = CustomUser.objects.create_user(username=username, password=password, email=email)
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.is_partner = True
            user.save()

            # Créer le partenaire
            partner = Partner.objects.create(
                user=user,
                company_name=company_name,
                first_name=first_name,
                last_name=last_name,
                address=address,
                telephone_number=telephone_number,
                email=email,
                partner_type=partner_type,
            )

            # Sérialiser la réponse
            partner_serializer = PartnerSerializer(partner)

            response = {
                "partner": partner_serializer.data,
                "status": 1
            }
            return Response(response, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            error_message = str(e)
            if "unique constraint" in error_message.lower():
                if "username" in error_message.lower():
                    return Response({"error": "Username already exists. Please choose a different one."},
                                    status=status.HTTP_400_BAD_REQUEST)
                elif "email" in error_message.lower():
                    return Response({"error": "Email already exists. Please use another email."},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": f"Database integrity error: {error_message}"}, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({"error": f"Validation error: {e}"}, status=status.HTTP_400_BAD_REQUEST)


# PARTNER UPDATE RETRIEVE DELETE


class PartnerCustomUserDetailAPIView(RetrieveUpdateDestroyAPIView):
    schema = AutoSchema()
    serializer_class = PartnerCustomUserSerializer
    queryset = Partner.objects.all()

    def get(self, request, pk):
        try:
            partner = Partner.objects.get(pk=pk)
            serializer = self.get_serializer(partner)
            return Response(serializer.data)
        except Partner.DoesNotExist:
            return Response({"error": "Partner not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            partner = Partner.objects.get(pk=pk)
            user = partner.user

            # Créer une copie mutable des données
            data = request.data.copy()

            # Séparer les données utilisateur
            user_fields = ['username', 'password', 'email', 'first_name']
            user_data = {k: data.pop(k) for k in user_fields if k in data}

            # Mise à jour du CustomUser
            if user_data:
                user_serializer = CustomUserSerializer(
                    user,
                    data=user_data,
                    partial=True,
                    context={'request': request}  # Important pour la validation
                )
                if user_serializer.is_valid():
                    user_serializer.save()
                else:
                    return Response(
                        {'user_errors': user_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Mise à jour du Partner
            partner_serializer = PartnerSerializer(
                partner,
                data=data,
                partial=True
            )
            if partner_serializer.is_valid():
                partner_serializer.save()
            else:
                return Response(
                    {'partner_errors': partner_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retourner les données complètes mises à jour
            updated_partner = Partner.objects.get(pk=pk)
            serializer = self.get_serializer(updated_partner)
            return Response(serializer.data)

        except Partner.DoesNotExist:
            return Response({"error": "Partner not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            partner = Partner.objects.get(pk=pk)
            user = partner.user
            partner.delete()
            user.delete()
            return Response(
                {"detail": "Partner and User deleted successfully."},
                status=status.HTTP_200_OK
            )
        except Partner.DoesNotExist:
            return Response(
                {"error": "Partner not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminRegister(APIView):
    schema = AutoSchema()

    """
    This class defines an AdminRegister API view which handles admin registration.
    The get method retrieves all admin objects.
    The post method validates and processes admin registration data, creating a new admin.
    """

    def get(self, request):
        try:
            admin_obj = Admin.objects.all()
            serializer = AdminSerializer(admin_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        # Validating and getting data from request
        required_fields = ['first_name', 'last_name', 'address', 'telephone_number', 'email', ]
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)
        username = request.data['username']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        address = request.data['address']
        telephone_number = request.data['telephone_number']
        email = request.data['email']

        is_user = CustomUser.objects.filter(email=email).exists()

        if is_user:
            return Response({"error": "User with this email already exists. Please use a different email."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username, password=password, email=email)
        user.first_name = first_name
        user.last_name = last_name

        admin = Admin.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            address=address,
            telephone_number=telephone_number,
            email=email,
        )

        user.is_active = True
        user.is_admin = True
        user.save()

        admin_serializer = AdminSerializer(admin)

        response = {
            "admin": admin_serializer.data,
            "status": 1
        }
        return Response(response, status=status.HTTP_201_CREATED)


# ADMIN UPDATE
class AdminCustomUserDetailAPIView(RetrieveUpdateDestroyAPIView):
    schema = AutoSchema()

    """
    This class defines an AdminCustomUserDetailAPIView which provides detailed CRUD operations for an Admin and its associated CustomUser.
    """
    serializer_class = AdminCustomUserSerializer

    def get_object(self, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.is_admin:
                admin, created = Admin.objects.get_or_create(user=user)
                return user, admin
            else:
                return None, None
        except CustomUser.DoesNotExist:
            return None, None

    def get(self, request, pk):
        user, admin = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found or not an Admin."}, status=404)
        serializer = AdminCustomUserDetailAPIView(user)
        return Response(serializer.data)

    def patch(self, request, pk):
        user, admin = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found."}, status=404)

        # Update CustomUser fields
        user_serializer = self.get_serializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        # Update Admin fields
        admin_serializer = AdminSerializer(admin, data=request.data, partial=True)
        if admin_serializer.is_valid():
            admin_serializer.save()

        return Response(user_serializer.data)

    def delete(self, request, pk):
        user, admin = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found."}, status=404)

        user.delete()
        admin.delete()
        return Response({"detail": "User and Admin deleted successfully."}, status=204)


# ADMIN LOGIN API

class AdminLoginAPIView(APIView):
    schema = AutoSchema()

    """
    This class defines an AdminLoginAPIView which handles the login functionality for admins.
    """

    def post(self, request):
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Authenticate partner
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_admin:
            # Create or get the authentication token for the partner
            token, _ = Token.objects.get_or_create(user=user)

            # Get the associated Admin object
            try:
                admin_data = Admin.objects.get(user=user)
                admin_info = {
                    'first_name': admin_data.first_name,
                    'last_name': admin_data.last_name,
                    'address': admin_data.address,
                    'telephone_number': admin_data.telephone_number,
                    'email': admin_data.email,
                }
            except Admin.DoesNotExist:
                admin_info = {}

            response_data = {
                'user_id': user.id,
                'token': token.key,
                'message': 'Partner login successful.',
                'admin_info': admin_info  # Include admin data in the response
            }
            return Response(response_data, status=200)
        else:
            return Response({'error': 'Invalid credentials'}, status=400)


class ClientRegister(APIView):
    schema = AutoSchema()

    """
    This class defines a ClientRegister API view which retrieves information about all clients and their associated events.
    """

    def get(self, request):
        try:
            clients = Client.objects.all()
            client_data = []

            for client in clients:
                # Get the events associated with this client
                events = Event.objects.filter(client=client)
                serialized_events = EventSerializer(events, many=True)

                client_data.append({
                    "client": ClientSerializer(client).data,
                    "events": serialized_events.data
                })

            return Response(client_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        # Validating and getting data from request
        #Le username represente l'identifiant
        required_fields = ['company_name', 'first_name', 'last_name', 'address', 'telephone_number', 'email']
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)
        username = request.data['username']
        password = request.data['password']
        partner = request.data['partner']
        company_name = request.data['company_name']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        address = request.data['address']
        telephone_number = request.data['telephone_number']
        email = request.data['email']

        is_user = CustomUser.objects.filter(email=email).exists()
        partner_obj = Partner.objects.get(id=partner)

        if is_user:
            return Response({"error": "User with this email already exists. Please use a different email."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username, password=password, email=email)
        user.first_name = first_name
        user.last_name = last_name

        client = Client.objects.create(
            user=user,
            partner=partner_obj,
            company_name=company_name,
            first_name=first_name,
            last_name=last_name,
            address=address,
            telephone_number=telephone_number,
            email=email,
        )

        user.is_active = True
        user.is_client = True
        user.save()

        client_serializer = ClientSerializer(client)

        response = {
            "client": client_serializer.data,
            "status": 1
        }
        return Response(response, status=status.HTTP_201_CREATED)


# CLIENT UPDATE RETRIEVE DELETE
class ClientCustomUserDetailAPIView(RetrieveUpdateDestroyAPIView):
    schema = AutoSchema()

    """
    This class defines a ClientCustomUserDetailAPIView which provides detailed CRUD operations for a Client and its associated CustomUser.
    """
    serializer_class = ClientCustomUserSerializer
    queryset = Client.objects.all()  # Define the queryset for the Client model

    def get(self, request, pk):
        try:
            client = Client.objects.get(pk=pk)
            # Access the associated CustomUser for the client
            user = client.user
            serializer = ClientCustomUserSerializer(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        print("\n=== DEBUT DE LA REQUETE PATCH ===")
        print(f"Données reçues (raw): {request.data}")

        try:
            # Debug 1 - Vérification de l'existence du client
            client = Client.objects.get(pk=pk)
            print(f"\nDebug 1 - Client trouvé: ID={client.id}, Nom={client.company_name}")
            print(f"User associé: ID={client.user.id}, Username={client.user.username}")

            # Debug 2 - Initialisation du serializer
            serializer = ClientSerializer(client, data=request.data, partial=True)
            print("\nDebug 2 - Serializer initialisé")
            print(f"Données fournies au serializer: {serializer.initial_data}")

            # Debug 3 - Validation
            is_valid = serializer.is_valid(raise_exception=False)
            print(f"\nDebug 3 - Validation du serializer: {is_valid}")
            if not is_valid:
                print(f"Erreurs de validation: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Debug 4 - Sauvegarde
            print("\nDebug 4 - Avant sauvegarde")
            print(f"Données validées: {serializer.validated_data}")

            instance = serializer.save()
            print("\nDebug 5 - Après sauvegarde")
            print(f"Instance Client mise à jour: {instance.__dict__}")
            print(f"User associé mis à jour: {instance.user.__dict__}")

            # Debug 6 - Vérification en base
            client_refreshed = Client.objects.get(pk=pk)
            user_refreshed = client_refreshed.user
            print("\nDebug 6 - Vérification en base de données")
            print(f"Client en base: {client_refreshed.__dict__}")
            print(f"User en base: {user_refreshed.__dict__}")

            return Response(serializer.data)

        except Client.DoesNotExist:
            print("\nDebug ERROR - Client non trouvé")
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"\nDebug ERROR - Exception inattendue: {str(e)}")
            raise


    def delete(self, request, pk):
        try:
            client = Client.objects.get(pk=pk)
            # Access the associated CustomUser for the client
            user = client.user
            client.delete()
            user.delete()
            return Response({"detail": "Client and User deleted successfully."}, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)


class CreateEvent(APIView):
    schema = AutoSchema()

    """
    This class defines a CreateEvent API view which handles the creation of events.
    """

    def generate_qr_code(self, event_details):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(event_details)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        return ContentFile(buffer.getvalue())

    def get(self, request):
        try:
            event_obj = Event.objects.all()
            serializer = EventSerializer(event_obj, many=True)
            # Add QR code to each event in the response
            for event in serializer.data:
                event_details = f"{event['event_name']} - {event['event_place']} - {event['begindatetime']}"

                # print("EVENTTTTTTT " + str(event['begindatetime']))
                qr_code_file = self.generate_qr_code(event_details)
                event['qr_code'] = base64.b64encode(qr_code_file.read()).decode('utf-8')

            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        # Validate and create the event
        event_data = {
            "partner": request.data.get("partner"),
            "client": request.data.get("client"),
            "event_type": request.data.get("event_type"),
            "event_name": request.data.get("event_name"),
            "event_place": request.data.get("event_place"),
            "description": request.data.get("description"),
            "type_of_event": request.data.get("type_of_event"),
            "begindatetime": request.data.get("begindatetime"),
            "enddatetime": request.data.get("enddatetime"),
            "is_resourses_added": request.data.get("is_resourses_added"),
            # "event_image_1": request.data.get("event_image_1"),
            # "event_image_2": request.data.get("event_image_2"),
            # "event_image_3": request.data.get("event_image_3"),
        }

        # Check if the event name already exists
        is_event_exists = Event.objects.filter(event_name=event_data["event_name"]).exists()

        if is_event_exists:
            return Response({"error": "An event with this name already exists. Please choose a different event name."},
                            status=status.HTTP_400_BAD_REQUEST)

        # If you need to create a user, uncomment and modify the following lines
        # username = event_data["event_name"]
        # password = "<your_password>"
        # user = CustomUser.objects.create_user(username=username, password=password)
        # user.is_event = True
        # user.save()
        # event_data["user"] = user.id

        event_serializer = EventSerializer(data=event_data)

        try:
            event_serializer.is_valid(raise_exception=True)
            event_serializer.save()
            return Response(event_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        #     # Create EventPass
        #     event_pass_data = {
        #         "event": event_serializer.instance.id,
        #         "pass_total_quantity": request.data.get("pass_total_quantity"),
        #         "simple_pass": request.data.get("simple_pass"),
        #         "vip_pass": request.data.get("vip_pass"),
        #         "gold_pass": request.data.get("gold_pass"),
        #         "prestige_pass": request.data.get("prestige_pass"),
        #         "is_nfc": request.data.get("is_nfc_pass"),
        #     }
        #     event_pass_serializer = EventPassSerializer(data=event_pass_data)
        #     event_pass_serializer.is_valid(raise_exception=True)
        #     event_pass_serializer.save()

        #  # Create EventBracelet
        #     event_bracelet_data = {
        #         "event": event_serializer.instance.id,
        #         "bracelet_total_quantity": request.data.get("bracelet_total_quantity"),
        #         "blue": request.data.get("blue_bracelet"),
        #         "yellow": request.data.get("yellow_bracelet"),
        #         "red": request.data.get("red_bracelet"),
        #         "purple": request.data.get("purple_bracelet"),
        #         "is_nfc": request.data.get("is_nfc_bracelet"),
        #     }
        #     event_bracelet_serializer = EventBraceletSerializer(data=event_bracelet_data)
        #     event_bracelet_serializer.is_valid(raise_exception=True)
        #     event_bracelet_serializer.save()

        #     # Create EventBadges
        #     event_badges_data = {
        #         "event": event_serializer.instance.id,
        #         "simple_paper": request.data.get("simple_paper_badges"),
        #         "personalized_badge": request.data.get("personalized_badges"),
        #         "is_nfc": request.data.get("is_nfc_badges"),
        #     }
        #     event_badges_serializer = EventBadgesSerializer(data=event_badges_data)
        #     event_badges_serializer.is_valid(raise_exception=True)
        #     event_badges_serializer.save()

        #     # Create CheckInPoint
        #     check_in_point_data = {
        #         "event": event_serializer.instance.id,
        #         "check_in_point_quantity": request.data.get("check_in_point_quantity"),
        #     }
        #     check_in_point_serializer = CheckInPointSerializer(data=check_in_point_data)
        #     check_in_point_serializer.is_valid(raise_exception=True)
        #     check_in_point_serializer.save()

        #     # Create ExhibitionPoint
        #     exhibition_point_data = {
        #         "event": event_serializer.instance.id,
        #         "exhibition_point_quantity": request.data.get("exhibition_point_quantity"),
        #     }
        #     exhibition_point_serializer = ExhibitionPointSerializer(data=exhibition_point_data)
        #     exhibition_point_serializer.is_valid(raise_exception=True)
        #     exhibition_point_serializer.save()

        #     # Create ActivityPoint
        #     activity_point_data = {
        #         "event": event_serializer.instance.id,
        #         "activity_point_quantity": request.data.get("activity_point_quantity"),
        #     }
        #     activity_point_serializer = ActivityPointSerializer(data=activity_point_data)
        #     activity_point_serializer.is_valid(raise_exception=True)
        #     activity_point_serializer.save()

        #     # Create GuichetPoint
        #     guichet_point_data = {
        #         "event": event_serializer.instance.id,
        #         "guichet_point_quantity": request.data.get("guichet_point_quantity"),
        #     }
        #     guichet_point_serializer = GuichetPointSerializer(data=guichet_point_data)
        #     guichet_point_serializer.is_valid(raise_exception=True)
        #     guichet_point_serializer.save()

        #     # Create DrinksPoint
        #     drinks_point_data = {
        #         "event": event_serializer.instance.id,
        #         "drinks_point_quantity": request.data.get("drinks_point_quantity"),
        #     }
        #     drinks_point_serializer = DrinksPointSerializer(data=drinks_point_data)
        #     drinks_point_serializer.is_valid(raise_exception=True)
        #     drinks_point_serializer.save()

        #     # Create WorkshopPoint
        #     workshop_point_data = {
        #         "event": event_serializer.instance.id,
        #         "workshop_point_quantity": request.data.get("workshop_point_quantity"),
        #     }
        #     workshop_point_serializer = WorkshopPointSerializer(data=workshop_point_data)
        #     workshop_point_serializer.is_valid(raise_exception=True)
        #     workshop_point_serializer.save()

        #     response = {
        #         "event": event_serializer.data,
        #         "event_pass": event_pass_serializer.data,
        #         "event_bracelet": event_bracelet_serializer.data,
        #         "event_badges": event_badges_serializer.data,
        #         "check_in_point": check_in_point_serializer.data,
        #         "exhibition_point": exhibition_point_serializer.data,
        #         "activity_point": activity_point_serializer.data,
        #         "guichet_point": guichet_point_serializer.data,
        #         "drinks_point": drinks_point_serializer.data,
        #         "workshop_point": workshop_point_serializer.data,
        #     }
        #     return Response(response, status=status.HTTP_201_CREATED)
        # response = {
        #     "event": event_serializer.data,
        #     "event_pass": event_pass_serializer.data if event_type == "with_resources" else None,
        #     # Add other related models to the response here...
        # }
        # return Response(response, status=status.HTTP_201_CREATED)


class CreateEventRelatedModels(APIView):
    schema = AutoSchema()

    """
    This class defines a CreateEventRelatedModels API view which handles the creation of related models for an event.
    """

    def post(self, request, *args, **kwargs):
        try:
            event_instance = Event.objects.get(id=request.data.get("event"))
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create EventPass
        event_pass_data = {
            "event": event_instance.id,
            "pass_total_quantity": request.data.get("pass_total_quantity"),
            "simple_pass": request.data.get("simple_pass"),
            "vip_pass": request.data.get("vip_pass"),
            "gold_pass": request.data.get("gold_pass"),
            "prestige_pass": request.data.get("prestige_pass"),
            "is_nfc": request.data.get("is_nfc_pass"),
        }
        event_pass_serializer = EventPassSerializer(data=event_pass_data)
        event_pass_serializer.is_valid(raise_exception=True)
        event_pass_serializer.save()

        # Create EventBracelet
        event_bracelet_data = {
            "event": event_instance.id,
            "bracelet_total_quantity": request.data.get("bracelet_total_quantity"),
            "blue": request.data.get("blue_bracelet"),
            "yellow": request.data.get("yellow_bracelet"),
            "red": request.data.get("red_bracelet"),
            "purple": request.data.get("purple_bracelet"),
            "is_nfc": request.data.get("is_nfc_bracelet"),
        }
        event_bracelet_serializer = EventBraceletSerializer(data=event_bracelet_data)
        event_bracelet_serializer.is_valid(raise_exception=True)
        event_bracelet_serializer.save()

        # Create EventBadges
        event_badges_data = {
            "event": event_instance.id,
            "simple_paper": request.data.get("simple_paper_badges"),
            "personalized_badge": request.data.get("personalized_badges"),
            "is_nfc": request.data.get("is_nfc_badges"),
        }
        event_badges_serializer = EventBadgesSerializer(data=event_badges_data)
        event_badges_serializer.is_valid(raise_exception=True)
        event_badges_serializer.save()

        # Create CheckInPoint
        check_in_point_data = {
            "event": event_instance.id,
            "check_in_point_quantity": request.data.get("check_in_point_quantity"),
        }
        check_in_point_serializer = CheckInPointSerializer(data=check_in_point_data)
        check_in_point_serializer.is_valid(raise_exception=True)
        check_in_point_serializer.save()

        # Create ExhibitionPoint
        exhibition_point_data = {
            "event": event_instance.id,
            "exhibition_point_quantity": request.data.get("exhibition_point_quantity"),
        }
        exhibition_point_serializer = ExhibitionPointSerializer(data=exhibition_point_data)
        exhibition_point_serializer.is_valid(raise_exception=True)
        exhibition_point_serializer.save()

        # Create ActivityPoint
        activity_point_data = {
            "event": event_instance.id,
            "activity_point_quantity": request.data.get("activity_point_quantity"),
        }
        activity_point_serializer = ActivityPointSerializer(data=activity_point_data)
        activity_point_serializer.is_valid(raise_exception=True)
        activity_point_serializer.save()

        # Create GuichetPoint
        guichet_point_data = {
            "event": event_instance.id,
            "guichet_point_quantity": request.data.get("guichet_point_quantity"),
        }
        guichet_point_serializer = GuichetPointSerializer(data=guichet_point_data)
        guichet_point_serializer.is_valid(raise_exception=True)
        guichet_point_serializer.save()

        # Create DrinksPoint
        drinks_point_data = {
            "event": event_instance.id,
            "drinks_point_quantity": request.data.get("drinks_point_quantity"),
        }
        drinks_point_serializer = DrinksPointSerializer(data=drinks_point_data)
        drinks_point_serializer.is_valid(raise_exception=True)
        drinks_point_serializer.save()

        # Create WorkshopPoint
        workshop_point_data = {
            "event": event_instance.id,
            "workshop_point_quantity": request.data.get("workshop_point_quantity"),
        }
        workshop_point_serializer = WorkshopPointSerializer(data=workshop_point_data)
        workshop_point_serializer.is_valid(raise_exception=True)
        workshop_point_serializer.save()

        response = {
            "event": EventSerializer(event_instance).data,
            "event_pass": EventPassSerializer(event_pass_serializer.instance).data,
            "event_bracelet": EventBraceletSerializer(event_bracelet_serializer.instance).data,
            "event_badges": EventBadgesSerializer(event_badges_serializer.instance).data,
            "check_in_point": CheckInPointSerializer(check_in_point_serializer.instance).data,
            "exhibition_point": ExhibitionPointSerializer(exhibition_point_serializer.instance).data,
            "activity_point": ActivityPointSerializer(activity_point_serializer.instance).data,
            "guichet_point": GuichetPointSerializer(guichet_point_serializer.instance).data,
            "drinks_point": DrinksPointSerializer(drinks_point_serializer.instance).data,
            "workshop_point": WorkshopPointSerializer(workshop_point_serializer.instance).data,
        }
        return Response(response, status=status.HTTP_201_CREATED)


# EVENT DELETE UPDATE RETEIEVE

class EventCustomUserDetailAPIView(RetrieveUpdateDestroyAPIView):
    schema = AutoSchema()

    """
    This class defines an EventCustomUserDetailAPIView which handles the retrieval, update, and deletion of users associated with events.
    """
    serializer_class = EventCustomUserSerializer

    def get_object(self, pk):
        """
        Retrieve the user and event objects associated with the provided primary key.

        Args:
            pk (int): Primary key of the user.

        Returns:
            tuple: A tuple containing user and event objects.
        """
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.is_event:
                event, created = Event.objects.get_or_create(user=user)
                return user, event
            else:
                return None, None
        except CustomUser.DoesNotExist:
            return None, None

    def get(self, request, pk):
        """
        Get method to retrieve details of the user associated with the event.

        Args:
            request: Request object.
            pk (int): Primary key of the user.

        Returns:
            Response: JSON response containing user details.
        """
        user, event = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found or not an event."}, status=404)
        serializer = EventCustomUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, pk):
        """
        Patch method to update details of the user associated with the event.

        Args:
            request: Request object.
            pk (int): Primary key of the user.

        Returns:
            Response: JSON response containing updated user details.
        """
        user, event = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found."}, status=404)

        # Update CustomUser fields
        user_serializer = self.get_serializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        # Update Admin fields
        event_serializer = EventSerializer(event, data=request.data, partial=True)
        if event_serializer.is_valid():
            event_serializer.save()

        return Response(user_serializer.data)

    def delete(self, request, pk):
        """
        Delete method to delete the user associated with the event.

        Args:
            request: Request object.
            pk (int): Primary key of the user.

        Returns:
            Response: JSON response indicating successful deletion.
        """
        user, event = self.get_object(pk)
        if user is None:
            return Response({"error": "User not found."}, status=404)

        user.delete()
        event.delete()
        return Response({"detail": "User and Partner deleted successfully."}, status=204)


# LIST APIS

class PartnerListView(APIView):
    schema = AutoSchema()

    """
    This class defines a PartnerListView API view which handles the retrieval of partner information.
    """

    def get(self, request):
        """
        Get method to retrieve partner information.

        Args:
            request: Request object.

        Returns:
            Response: JSON response containing partner information.
        """

        partners = Partner.objects.all()

        # if not partners:  # Check if there are no partners
        #     return Response({"message": "No partners found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PartnerCompanyNameSerializer(partners, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PartnerDetailsView(APIView):
    schema = AutoSchema()

    """
    This class defines a PartnerDetailsView API view which handles the retrieval of partner details.
    """

    def get(self, request, pk):
        """
        Get method to retrieve partner details.

        Args:
            request: Request object.
            pk (int): Primary key of the partner.

        Returns:
            Response: JSON response containing partner details.
        """
        try:
            partner_obj = Partner.objects.get(id=pk)
        except Partner.DoesNotExist:
            return Response({"error": "Partner not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid partner ID."}, status=status.HTTP_400_BAD_REQUEST)

        email = partner_obj.email
        telephone_number = partner_obj.telephone_number
        first_name = partner_obj.first_name
        return Response(
            {"message": "success", "email": email, "telephone_number": telephone_number, "first_name": first_name},
            status=status.HTTP_200_OK)


class ClientListView(APIView):
    schema = AutoSchema()

    """
    This class defines a ClientListView API view which handles the retrieval of client information.
    """

    def get(self, request):
        """
        Get method to retrieve client information.

        Args:
            request: Request object.

        Returns:
            Response: JSON response containing client information.
        """
        client = Client.objects.all()

        if not client:  # Check if there are no partners
            return Response({"message": "No partners found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClientCompanyNameSerializer(client, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientDetailsView(APIView):
    schema = AutoSchema()

    """
    This class defines a ClientDetailsView API view which handles the retrieval and deletion of client details.
    """

    def get(self, request, pk):
        """
        Get method to retrieve client details.

        Args:
            request: Request object.
            pk (int): Primary key of the client.

        Returns:
            Response: JSON response containing client details.
        """
        try:
            client_obj = Client.objects.get(id=pk)
        except Client.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid partner ID."}, status=status.HTTP_400_BAD_REQUEST)

        email = client_obj.email
        telephone_number = client_obj.telephone_number
        first_name = client_obj.first_name
        return Response(
            {"message": "success", "email": email, "telephone_number": telephone_number, "first_name": first_name},
            status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete method to delete the client and associated user.

        Args:
            request: Request object.
            pk (int): Primary key of the client.

        Returns:
            Response: JSON response indicating successful deletion.
        """
        try:
            client_obj = Client.objects.get(id=pk)
            client_obj.delete()  # This will delete the associated user as well
            return Response({"message": "Client deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Client.DoesNotExist:
            return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid client ID."}, status=status.HTTP_400_BAD_REQUEST)


# TEAM APIS

class EventTeamCreateView(APIView):
    schema = AutoSchema()

    """
    This class defines an EventTeamCreateView API view which handles the creation and retrieval of event teams.
    """

    def get(self, request, *args, **kwargs):
        """
        Get method to retrieve event teams.

        Args:
            request: Request object.
            args: Additional arguments.
            kwargs: Additional keyword arguments.

        Returns:
            Response: JSON response containing grouped event teams.
        """
        event_teams = EventTeam.objects.all().order_by('team_type')
        grouped_teams = {}

        for team_type, teams in groupby(event_teams, key=lambda x: x.get_team_type_display()):
            grouped_teams[team_type] = EventTeamSerializer(teams, many=True).data

        return Response(grouped_teams)

    def post(self, request, *args, **kwargs):
        """
        Post method to create a new event team member.

        Args:
            request: Request object.
            args: Additional arguments.
            kwargs: Additional keyword arguments.

        Returns:
            Response: JSON response indicating successful creation of the team member.
        """
        # Validate and create the event
        username = request.data['username']
        password = request.data['password']
        event_team_data = {
            "team_type": request.data.get("team_type"),
            "event": request.data.get("event"),
            "member_type": request.data.get("member_type"),
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "member_post": request.data.get("member_post"),
            "member_role": request.data.get("member_role", "C-in Point"),
            "telephone_number": request.data.get("telephone_number"),
            "email": request.data.get("email"),
        }

        # Check if telephone_number already exists
        is_user = EventTeam.objects.filter(telephone_number=event_team_data["telephone_number"]).exists()
        if is_user:
            raise ValidationError(
                {"error": "User with this telephone number already exists. Please use a different telephone number."})

        # Create the user
        user = CustomUser.objects.create_user(username=username, email=event_team_data["email"], password=password)
        user.first_name = event_team_data["first_name"],
        user.last_name = event_team_data["last_name"],
        user.is_team = True
        user.save()
        event_team_data["user"] = user.id

        # Validate and save the event team data
        event_team_serializer = EventTeamSerializer(data=event_team_data)
        event_team_serializer.is_valid(raise_exception=True)
        event_team_serializer.save()

        return Response({"message": "Team member created successfully.",
                         'event_team_serializer': event_team_serializer.data}, status=status.HTTP_201_CREATED)


class EventPriceDetails(APIView):
    schema = AutoSchema()
    """
    This class defines an EventPriceDetails API view to retrieve price details for an event.
    """

    def get(self, request, event_id):
        """
        Get method to retrieve price details for an event.

        Args:
            request: Request object.
            event_id (int): The ID of the event.

        Returns:
            Response: JSON response containing price details for the event.
        """
        try:
            event = Event.objects.get(pk=event_id)

            # Get the event pass and bracelet quantities
            event_pass = EventPass.objects.get(event=event)
            event_bracelet = EventBracelet.objects.get(event=event)

            # Get the pass and bracelet prices associated with the event
            pass_prices = PassPrice.objects.filter(event=event)
            bracelet_prices = BraceletPrice.objects.filter(event=event)

            # Get the pass and bracelet quantities from the respective models
            pass_quantity = event_pass.pass_total_quantity
            bracelet_quantity = event_bracelet.bracelet_total_quantity

            # Calculate the total pass and bracelet prices
            total_pass_price_qr = sum(price.price_with_qr * pass_quantity for price in pass_prices)
            total_pass_price_nfc = sum(price.price_with_nfc * pass_quantity for price in pass_prices)

            total_bracelet_price_qr = sum(price.price_with_qr * bracelet_quantity for price in bracelet_prices)
            total_bracelet_price_nfc = sum(price.price_with_nfc * bracelet_quantity for price in bracelet_prices)

            # Get the service quantities from the respective models
            check_in_point = CheckInPoint.objects.get(event=event).check_in_point_quantity
            exhibition_point = ExhibitionPoint.objects.get(event=event).exhibition_point_quantity
            activity_point = ActivityPoint.objects.get(event=event).activity_point_quantity
            guichet_point = GuichetPoint.objects.get(event=event).guichet_point_quantity
            drinks_point = DrinksPoint.objects.get(event=event).drinks_point_quantity

            # Get the service prices associated with the event
            service_prices = ServicePrice.objects.filter(event=event)

            # Calculate the total service prices
            total_check_in_price = sum(
                price.service_price * check_in_point for price in service_prices if price.service_type == 'Check in')
            total_exhibition_price = sum(price.service_price * exhibition_point for price in service_prices if
                                         price.service_type == 'Exhibition')
            total_activity_price = sum(
                price.service_price * activity_point for price in service_prices if price.service_type == 'Activity')
            total_guichet_price = sum(
                price.service_price * guichet_point for price in service_prices if price.service_type == 'Guichet')
            total_drinks_price = sum(
                price.service_price * drinks_point for price in service_prices if price.service_type == 'Drinks')
            total_price_for_qr = float(
                total_check_in_price + total_exhibition_price + total_activity_price + total_guichet_price + total_drinks_price + total_pass_price_qr + total_bracelet_price_qr)
            total_price_for_nfc = float(
                total_check_in_price + total_exhibition_price + total_activity_price + total_guichet_price + total_drinks_price + total_pass_price_nfc + total_bracelet_price_nfc)
            response = {
                "event_id": event_id,
                "event_name": event.event_name,
                "pass_quantity": pass_quantity,
                "bracelet_quantity": bracelet_quantity,
                "total_pass_price_qr": total_pass_price_qr,
                "total_pass_price_nfc": total_pass_price_nfc,
                "total_bracelet_price_qr": total_bracelet_price_qr,
                "total_bracelet_price_nfc": total_bracelet_price_nfc,
                "check_in_point_quantity": check_in_point,
                "exhibition_point_quantity": exhibition_point,
                "activity_point_quantity": activity_point,
                "guichet_point_quantity": guichet_point,
                "drinks_point_quantity": drinks_point,
                "total_check_in_price": total_check_in_price,
                "total_exhibition_price": total_exhibition_price,
                "total_activity_price": total_activity_price,
                "total_guichet_price": total_guichet_price,
                "total_drinks_price": total_drinks_price,
                'total_price_for_qr': total_price_for_qr,
                'total_price_for_nfc': total_price_for_nfc,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        except EventPass.DoesNotExist:
            return Response({"error": "Event pass not found."}, status=status.HTTP_404_NOT_FOUND)
        except EventBracelet.DoesNotExist:
            return Response({"error": "Event bracelet not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# EVENT QR CODE GENERATION
class EventQRCodeAPIView(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to generate QR code for event credentials.
    """

    def get(self, request, event_id):
        """
        Get method to generate QR code for event credentials.

        Args:
            request: Request object.
            event_id (int): The ID of the event.

        Returns:
            HttpResponse: HTTP response containing the QR code image.
        """
        try:
            # Get the event by ID
            event = Event.objects.get(pk=event_id)

            # Extract username and password from the event
            username = event.user.username
            password = event.user.password

            # Combine username and password
            credentials = f"Username: {username}, Password: {password}"

            # Create a QR code with the credentials
            qr_code = qrcode.make(credentials)

            # Create a response with the image data
            response = HttpResponse(content_type="image/png")
            qr_code.save(response, "PNG")
            return response

        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ADD PASS PRICE

# class PassPriceListCreateView(ListCreateAPIView):
#     """
#     This class defines an API view to list and create pass prices.
#     """
#     queryset = PassPrice.objects.all()
#     serializer_class = PassPriceSerializer

#     def create(self, request, *args, **kwargs):
#         """
#         Method to create pass prices.

#         Args:
#             request: Request object.
#             *args: Additional arguments.
#             **kwargs: Additional keyword arguments.

#         Returns:
#             Response: HTTP response containing the created pass prices data.
#         """
#         serializer = self.get_serializer(data=request.data, many=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# class PassPriceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
#     """
#     This class defines an API view to retrieve, update, and delete pass prices.
#     """
#     queryset = PassPrice.objects.all()
#     serializer_class = PassPriceSerializer


# #Braclet add price

# class BraceletPriceListCreateView(ListCreateAPIView):
#     """
#     This class defines an API view to list and create bracelet prices.
#     """
#     queryset = BraceletPrice.objects.all()
#     serializer_class = BraceletPriceSerializer

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data, many=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# class BraceletPriceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
#     """
#     This class defines an API view to retrieve, update, and delete a bracelet price.
#     """
#     queryset = BraceletPrice.objects.all()
#     serializer_class = BraceletPriceSerializer


# ADD SERVICES PRICE

class ServicePriceListCreateView(ListCreateAPIView):
    schema = AutoSchema()

    """
    This class defines an API view to list and create service prices.
    """
    queryset = ServicePrice.objects.all()
    serializer_class = ServicePriceSerializer

    def create(self, request, *args, **kwargs):
        """
        Creates multiple service prices in bulk.
        """
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ServicePriceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    schema = AutoSchema()

    """
    This class defines an API view to retrieve, update, or delete a service price.
    """
    queryset = ServicePrice.objects.all()
    serializer_class = ServicePriceSerializer


class EventList(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to retrieve a list of events.
    """

    def get(self, request, format=None):
        events = Event.objects.all()
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)


# class UniqueEventTeamList(APIView):
#     """
#     This class defines an API view to retrieve unique team types for a specified event.
#     """
#     def get(self, request, event_id, format=None):
#         # Validate the event_id parameter
#         # if not event_id.isdigit() or int(event_id) <= 0:
#         #     return Response({"error": "Invalid event_id. It must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Check if the event exists in the database
#             event = Event.objects.get(pk=event_id)
#         except Event.DoesNotExist:
#             raise Http404("Event does not exist")

#         # Create a serializer instance
#         serializer = UniqueEventTeamSerializer()

#         # Get unique team types for the specified event
#         team_types = serializer.get_unique_team_types(event_id)

#         if not team_types:
#             return Response({"message": "No team types available for this event."}, status=status.HTTP_204_NO_CONTENT)

#         return Response({"team_types": team_types}, status=status.HTTP_200_OK)


# class EventTeamByTypeAPIView(ListAPIView):
#     """
#     This class defines an API view to retrieve event teams grouped by team type for a specified event.
#     """
#     serializer_class = EventTeamSerializer

#     def get_queryset(self):
#         """
#         Get the queryset of event teams for the specified event.
#         """
#         event_id = self.kwargs.get('event_id')

#         queryset = EventTeam.objects.filter(event_id=event_id)
#         return queryset

#     def list(self, request, *args, **kwargs):
#         """
#         Return a response with event teams grouped by team type.
#         """
#         event_id = self.kwargs.get('event_id')
#         teams_by_type = {}

#         # Retrieve all teams for the given event
#         teams = self.get_queryset()

#         # Group teams by team_type in the response
#         for team in teams:
#             team_type = team.team_type
#             if team_type not in teams_by_type:
#                 teams_by_type[team_type] = []

#             serialized_team = self.get_serializer(team).data
#             teams_by_type[team_type].append(serialized_team)

#         return Response(teams_by_type)


# class EventTeamRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
#     """
#     This class defines an API view to retrieve, update, or delete an event team instance by its primary key.
#     """
#     queryset = EventTeam.objects.all()
#     serializer_class = EventTeamSerializer
#     lookup_field = 'pk'  # Change 'pk' to the actual field used as the primary key

#     def update(self, request, *args, **kwargs):
#         """
#         Update an existing event team instance.
#         """
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def destroy(self, request, *args, **kwargs):
#         """
#         Delete an existing event team instance.
#         """
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response({"message": "Event Team deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class ServicePriceAPIView(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to retrieve service prices for a specific event.
    """

    def get(self, request, event_id):
        """
        Get service prices for a specific event.
        """
        try:
            service_prices = ServicePrice.objects.filter(event_id=event_id)
            serializer = ServicePriceSerializer(service_prices, many=True)
            return Response(serializer.data)
        except ServicePrice.DoesNotExist:
            return Response({"error": "Services not found for this event."}, status=404)


class LogoutView(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to handle user logout.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle user logout.
        """
        request.auth.delete()
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class CreateEvents1(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to create events.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new event.
        """

        try:
            if Event.objects.filter(event_name=request.data.get("event_name")).exists():
                return Response({'error': 'Event name already exist'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                event_data = {
                    "event_name": request.data.get("event_name"),
                    "event_place": request.data.get("event_place"),
                    "description": request.data.get("description"),

                    "partner": Partner.objects.get(id=request.data.get("partner")),  # id required
                    "partner_name": request.data.get("partner_name"),
                    'partner_email': request.data.get("partner_email"),
                    "partner_phonenumber": request.data.get("partner_phonenumber"),
                    "client": Client.objects.get(id=request.data.get("client")),  # id required
                    'client_email': request.data.get("client_email"),
                    "client_phonenumber": request.data.get("client_phonenumber"),

                    "type_of_event": request.data.get("type_of_event"),
                    "begindatetime": request.data.get("begindatetime"),
                    "enddatetime": request.data.get("enddatetime")
                }
                event = Event.objects.create(**event_data)
                return Response({'message': 'successfully created',
                                 'response': EventSerializer(event).data,
                                 }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class CreateEvents2(APIView):
#     """
#     This class defines an API view to create events with or without resources.
#     """
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     def patch(self, request,evnt_id):
#         """
#         Update the event type and create associated resources if required.
#         """
#         try:
#             if request.data.get("event_source")=='with_resources':
#                 try:
#                     event=Event.objects.get(id=evnt_id)
#                     event.event_type='with_resources'
#                     event.save()
#                 except Event.DoesNotExist:
#                     return Response({"error":'Event not exist'}, status=status.HTTP_400_BAD_REQUEST)

#                 # Create EventPass
#                 event_pass_data = {
#                     "event": event,
#                     "pass_total_quantity": request.data.get("pass_total_quantity"),
#                     "simple_pass": request.data.get("simple_pass"),
#                     "vip_pass": request.data.get("vip_pass"),
#                     "gold_pass": request.data.get("gold_pass"),
#                     "prestige_pass": request.data.get("prestige_pass"),
#                     "is_nfc": request.data.get("is_nfc_pass"),
#                 }
#                 EventPass.objects.create(**event_pass_data)

#                 # Create EventBracelet
#                 event_bracelet_data = {
#                     "event": event,
#                     "bracelet_total_quantity": request.data.get("bracelet_total_quantity"),
#                     "blue": request.data.get("blue_bracelet"),
#                     "yellow": request.data.get("yellow_bracelet"),
#                     "red": request.data.get("red_bracelet"),
#                     "purple": request.data.get("purple_bracelet"),
#                     "is_nfc": request.data.get("is_nfc_bracelet"),
#                 }
#                 EventBracelet.objects.create(**event_bracelet_data)

#                 # Create EventBadges
#                 event_badges_data = {
#                     "event": event,
#                     "simple_paper": request.data.get("simple_paper_badges"),
#                     "personalized_badge": request.data.get("personalized_badges"),
#                     "is_nfc": request.data.get("is_nfc_badges"),
#                 }
#                 EventBadges.objects.create(**event_badges_data)

#                 # Create CheckInPoint
#                 check_in_point_data = {
#                     "event": event,
#                     "check_in_point_quantity": request.data.get("check_in_point_quantity"),
#                 }
#                 CheckInPoint.objects.create(**check_in_point_data)

#                 # Create ExhibitionPoint
#                 exhibition_point_data = {
#                     "event": event,
#                     "exhibition_point_quantity": request.data.get("exhibition_point_quantity"),
#                 }
#                 ExhibitionPoint.objects.create(**exhibition_point_data)

#                 # Create ActivityPoint
#                 activity_point_data = {
#                     "event": event,
#                     "activity_point_quantity": request.data.get("activity_point_quantity"),
#                 }
#                 ActivityPoint.objects.create(**activity_point_data)

#                 # Create GuichetPoint
#                 guichet_point_data = {
#                     "event": event,
#                     "guichet_point_quantity": request.data.get("guichet_point_quantity"),
#                 }
#                 GuichetPoint.objects.create(**guichet_point_data)

#                 # Create DrinksPoint
#                 drinks_point_data = {
#                     "event": event,
#                     "drinks_point_quantity": request.data.get("drinks_point_quantity"),
#                 }
#                 DrinksPoint.objects.create(**drinks_point_data)

#                 # Create WorkshopPoint
#                 workshop_point_data = {
#                     "event": event,
#                     "workshop_point_quantity": request.data.get("workshop_point_quantity"),
#                 }
#                 WorkshopPoint.objects.create(**workshop_point_data)

#                 # response = {
#                 #     "event": event,
#                 #     "event_pass": event_pass_serializer.data,
#                 #     "event_bracelet": event_bracelet_serializer.data,
#                 #     "event_badges": event_badges_serializer.data,
#                 #     "check_in_point": check_in_point_serializer.data,
#                 #     "exhibition_point": exhibition_point_serializer.data,
#                 #     "activity_point": activity_point_serializer.data,
#                 #     "guichet_point": guichet_point_serializer.data,
#                 #     "drinks_point": drinks_point_serializer.data,
#                 #     "workshop_point": workshop_point_serializer.data,
#                 # }
#                 return Response({"message":'Successfully created'}, status=status.HTTP_201_CREATED)
#             elif request.data.get("event_source")=='without_resources':
#                 event=Event.objects.get(id=evnt_id)
#                 event.event_type='without_resources'
#                 event.save()
#                 return Response({"message":"successfully added"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error":"event_source field is required",
#                                  "description":'without_resources and with_resources data are required'}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateEvents3(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to generate a QR code for an event and create a user associated with the event.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, evnt_id):
        """
        Get details of an event and generate a QR code.
        """
        try:
            event = Event.objects.get(pk=evnt_id)

            # Create a QR code with the credentials
            data = {
                'event_name': event.event_name,
                "partner": event.partner_name,
                "address": event.event_place,
                "description": event.description,
                "enddatetime": event.enddatetime,
                "begindatetime": event.begindatetime,
            }
            qr_code = qrcode.make(data)
            qr_code_bytes = BytesIO()
            qr_code.save(qr_code_bytes, format="PNG")
            qr_code_base64 = base64.b64encode(qr_code_bytes.getvalue()).decode('utf-8')
            return Response({"details": {**data},
                             "qr_code": qr_code_base64}, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, evnt_id):
        """
        Create a user associated with the event.
        """
        try:
            if not request.data:
                return Response({"error": 'Required fields are missing', "fields": {'username': '', 'password': ''}},
                                status=status.HTTP_400_BAD_REQUEST)

            username = request.data.get('username', '')
            password = request.data.get('password', '')

            if not username or not password:
                return Response({"error": 'Username and password cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

            event = Event.objects.get(id=evnt_id)
            user = CustomUser.objects.create_user(username=username, password=password)
            event.user = user
            event.save()

            return Response({'message': "Successfully created"}, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            return Response({"error": 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateEvents4(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to update event images.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, evnt_id):
        """
        Update event images.
        """
        try:
            event = Event.objects.get(pk=evnt_id)
            event.event_image_1 = request.data['image_1']
            event.event_image_2 = request.data['image_2']
            event.event_image_3 = request.data['image_3']
            event.save()
            return Response({'message': "Successfully added"}, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)


class ActiveDeactiveEvent(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to activate or deactivate an event.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, evnt_id):
        """
        Activate or deactivate an event.
        """
        try:
            event = Event.objects.get(pk=evnt_id)
            event.is_activated = request.data['is_activated']
            event.save()
            return Response({'message': "Successfully updated"}, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)


class ConvertCurrencyView(views.APIView):
    schema = AutoSchema()

    """
    This class defines an API view to convert currencies.
    """

    def get(self, request, *args, **kwargs):
        """
        Convert currencies based on the provided values, base currency, and target currencies.
        """
        values = request.query_params.getlist('values', None)
        if values:
            values = ','.join(values).split(',')
        print(values)
        base_currency = request.query_params.get('base_currency', None)
        currencies = request.query_params.get('currencies', None)
        if not values:
            return Response({"error": "Missing 'values' parameter"}, status=status.HTTP_400_BAD_REQUEST)
        results = []
        for value in values:
            url = f"https://api.currencyapi.com/v3/convert?value={value}&base_currency={base_currency}&currencies={currencies}"
            headers = {"apikey": "cur_live_yK38Z0dmRbkAkYNWfr6wnKv77FRKTS6PCgk2ezQf"}
            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                result = response.json()
                results.append(result)
            except Exception as e:
                print(f"Exception: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"results": results}, status=status.HTTP_200_OK)


class TranslateView(APIView):
    schema = AutoSchema()

    """
    This class defines an API view to translate text.
    """

    def post(self, request, format=None):
        """
        Translate text to the specified target language.
        """
        text = request.data.get('text', [])
        target_lang = request.data.get('target_lang', '')

        # Validate 'text' parameter
        if not isinstance(text, list) or not all(isinstance(item, str) for item in text):
            return Response({"error": "Invalid 'text' parameter. Expected a list of strings."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate 'target_lang' parameter
        valid_languages = ['BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'HU', 'ID', 'IT', 'JA', 'KO',
                           'LT', 'LV', 'NB', 'NL', 'PL', 'PT', 'RO', 'RU', 'SK', 'SL', 'SV', 'TR', 'UK', 'ZH']
        if target_lang not in valid_languages:
            return Response({"error": f"Invalid 'target_lang' parameter. Expected one of {valid_languages}."},
                            status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Authorization': 'DeepL-Auth-Key 3be778f4-29d2-ebf5-c903-01b1664920d2',
            'Content-Type': 'application/json',
        }

        data = {
            'text': text,
            'target_lang': target_lang,
        }

        try:
            response = requests.post('https://api.deepl.com/v2/translate', headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an exception if the status code is not 200
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({"error": f"API request failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
