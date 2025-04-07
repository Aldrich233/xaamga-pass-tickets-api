from smtplib import SMTPException

from drf_spectacular.openapi import AutoSchema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from .serializers import *
import logging
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import qrcode
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .custom_permissions import IsEndUser
import base64
import zlib
from io import BytesIO
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
import pyshorteners
# from datetime import timedelta, timezone
from django.contrib.auth.models import User
from django.db import transaction
import random
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  
from datetime import timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sessions.models import Session
import json
from datetime import datetime
from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from django.core.mail import EmailMultiAlternatives
import secrets
import string

logger = logging.getLogger(__name__)

def generate_secure_code(length=6):
    # Définir les caractères possibles pour le code
    characters = string.ascii_letters + string.digits
    code = ''.join(secrets.choice(characters) for _ in range(length))
    return code


@transaction.atomic
def send_verification_email(user):
    
    try:
        if not hasattr(user, 'first_name') or not hasattr(user, 'email'):
            print("L'utilisateur n'a pas les attributs requis.")
            return
        name = user.first_name
        email = user.email,
        verification_url = f"{settings.FRONTEND_URL}/verify/?token={user.email_verification_token}&email={email[0]}"
        # verification_url = f"{settings.FRONTEND_URL}/login/?token={user.email_verification_token}&email={email[0]}"
        subject = 'Email Verification'
        message = f"Please verify your email by clicking on the following link: {verification_url}"
        
        print("User object:", user.first_name)
        print("email: "+str(email[0]))
        print("verification_url: "+str(verification_url))
        print("message: "+str(message))
        # Message HTML avec un bouton
        message_html = format_html(
            """
            <p>Hello</p>
            <p>Pour continuer votre inscription, cliquez ci-dessous pour vérifier votre adresse email:</p>
            <p><a href="{url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            """, name=email[0], url=verification_url
        )
        
        from_email = f"Xaamga Ticket <{settings.DEFAULT_FROM_EMAIL}>"
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message, 
            from_email=from_email,
            to=[email[0]],
            headers={'Reply-To': ''},
        )

        email_message.attach_alternative(message_html, "text/html")
        email_message.send(fail_silently=False)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    return True


# class EndUserRegisterAPIView(APIView):
#     """
#     This class handles end user registration.
#     """
#     def get(self, request):
#         """
#         Get all registered end users.
#         """
#         try:
#             end_user_obj = EndUserDetail.objects.all()
#             serializer = EndUserSerializer(end_user_obj, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     @transaction.atomic
#     def post(self, request, *args, **kwargs):
#         """
#         Register a new end user.
#         """
#         # Validate required fields
#         required_fields = ['first_name', 'last_name', 'address', 'password']
#         for field in required_fields:
#             if field not in request.data:
#                 return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)

#         telephone_number = request.data.get('telephone_number')
#         email = request.data.get('email')

#         if not telephone_number and not email:
#             return Response({"error": "Le numéro de téléphone ou l'email doit être fourni.", "status": status.HTTP_400_BAD_REQUEST},
#                             status=status.HTTP_400_BAD_REQUEST)
        
#         # Vérifier si le numéro de téléphone existe déjà
#         if telephone_number and CustomUser.objects.filter(phone_number=telephone_number).exists():
#             return Response({"error": "Un utilisateur avec ce numéro de téléphone existe déjà. Veuillez utiliser un autre numéro.", "status": status.HTTP_409_CONFLICT},
#                             status=status.HTTP_409_CONFLICT)
        
#         # Vérifier si l'email existe déjà
#         if email and CustomUser.objects.filter(email=email).exists():
#             return Response({
#                 "error": "Un utilisateur avec cet email existe déjà. Veuillez utiliser un autre email.",
#                 "status": status.HTTP_409_CONFLICT
#                 },
#                             status=status.HTTP_409_CONFLICT)

#         try:
#             with transaction.atomic():
#                 # Créez l'utilisateur avec les informations fournies
#                 user = CustomUser.objects.create_user(
#                     username=telephone_number or email,  # Utilisez le numéro de téléphone ou l'email comme username
#                     password=request.data['password'],
#                     email=email,
#                     first_name = request.data.get('first_name', ''),
#                     last_name = request.data.get('last_name', ''),
#                     is_active = True,
#                     is_enduser = True,
#                     phone_number = telephone_number
#                 )

#                 # Créez l'EndUserDetail associé à l'utilisateur
#                 # endUser = EndUserDetail.objects.create(
#                 #     user=user,
#                 #     first_name=user.first_name,
#                 #     second_name=user.last_name,
#                 #     address=request.data.get('address', ''),
#                 #     telephone_number=telephone_number,
#                 #     email=email,
#                 #     password=request.data.get('password', '')
#                 # )
#                 token = default_token_generator.make_token(user)
#                 user.email_verification_token = token
#                 user.save()
                
#                 print("TESTTTT "+str(user.email))

#                 send_verification_email(user)

#                 if 'response' not in locals():
#                     # If 'response' is not defined, it means no gift redemption occurred
#                     response = {
#                         "message": "Veuillez vérifier votre mail, un lien de vérification vous a été envoyé",
#                         "status": status.HTTP_201_CREATED
#                     }
                
# return Response(response, status=status.HTTP_201_CREATED) except (SentGift.DoesNotExist, ETicket.DoesNotExist) as
# e: return Response({"error": str(e), "status": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND) except
# Exception as e: return Response({"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR},
# status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EndUserRegisterAPIView(APIView):
    """
    This class handles end user registration.
    """
    def get(self, request):
        """
        Get all registered end users.
        """
        try:
            end_user_obj = EndUserDetail.objects.all()
            serializer = EndUserSerializer(end_user_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Register a new end user.
        """
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'address', 'password']
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)

        telephone_number = request.data.get('telephone_number')
        email = request.data.get('email')
        # role = request.data.get('role')
        

        if not telephone_number and not email:
            return Response({"error": "Le numéro de téléphone ou l'email doit être fourni.", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si le numéro de téléphone existe déjà
        if telephone_number and CustomUser.objects.filter(phone_number=telephone_number).exists():
            return Response({"error": "Un utilisateur avec ce numéro de téléphone existe déjà. Veuillez utiliser un autre numéro.", "status": status.HTTP_409_CONFLICT},
                            status=status.HTTP_409_CONFLICT)
        
        # Vérifier si l'email existe déjà
        if email and CustomUser.objects.filter(email=email).exists():
            return Response({
                "error": "Un utilisateur avec cet email existe déjà. Veuillez utiliser un autre email.",
                "status": status.HTTP_409_CONFLICT
                },
                status=status.HTTP_409_CONFLICT)

        try:
            # Créez un utilisateur temporaire pour l'envoi de l'e-mail
            user = CustomUser(
                username=telephone_number or email,  # Utilisez le numéro de téléphone ou l'email comme username
                email=email,
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
                is_active=True,
                is_enduser=True,
                phone_number = telephone_number
            )

            # Créez le token de vérification avant d'enregistrer l'utilisateur
            token = default_token_generator.make_token(user)
            user.email_verification_token = token

            # Envoyer l'e-mail de vérification avant d'insérer dans la base de données
            send_email_result = send_verification_email(user)
            if not send_email_result:
                return Response({"error": "L'envoi de l'e-mail de vérification a échoué. Aucun utilisateur créé."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Si l'envoi de l'e-mail échoue, ne pas poursuivre
            if user.email_verification_token:  # Vous pouvez adapter cette vérification en fonction de votre logique d'envoi d'e-mail
                # Maintenant, créez l'utilisateur dans la base de données
                user.set_password(request.data['password'])  # Hash le mot de passe
                user.save()

                # Créez l'EndUserDetail associé à l'utilisateur
                end_user_detail = EndUserDetail.objects.create(
                    user=user,
                    first_name=user.first_name,
                    second_name=user.last_name,
                    address=request.data.get('address', ''),
                    telephone_number=telephone_number,
                    email=email,
                    password=request.data.get('password', '')
                )

                response = {
                    "message": "Veuillez vérifier votre mail, un lien de vérification vous a été envoyé",
                    "status": status.HTTP_201_CREATED
                }

                return Response(response, status=status.HTTP_201_CREATED)

            # Si l'envoi de l'e-mail a échoué, ne rien faire
            return Response({"error": "L'envoi de l'e-mail de vérification a échoué. Aucun utilisateur créé."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class EndUserRegisterGoogleAPIView(APIView):
    """
    Cette classe gère l'inscription des utilisateurs finaux avec Google.
    """

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Inscrit un nouvel utilisateur via Google.
        """
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        address = request.data.get('address', '')
        telephone_number = request.data.get('telephone_number', None)

        if not email:
            return Response({
                "error": "L'email est requis pour l'inscription avec Google."
            }, status=status.HTTP_400_BAD_REQUEST)

        existing_user = CustomUser.objects.filter(email=email).first()

        # Si l'utilisateur existe déjà avec Google → on lui demande de se connecter
        if existing_user:
            if existing_user.is_google:
                return Response({
                    "message": "Cet email est déjà enregistré via Google. Veuillez vous connecter.",
                    "status": status.HTTP_409_CONFLICT
                }, status=status.HTTP_409_CONFLICT )
            else:
                return Response({
                    "error": "Cet email est déjà utilisé pour un compte non Google.",
                    "status": status.HTTP_409_CONFLICT
                }, status=status.HTTP_409_CONFLICT)

        try:
            # Création du nouvel utilisateur Google
            user = CustomUser(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_enduser=True,
                is_google=True,  # Marque l'utilisateur comme Google
                phone_number=telephone_number or ""
            )

            # Générer un token de vérification
            token = default_token_generator.make_token(user)
            user.email_verification_token = token
            user.save()

            # Envoi de l'email de vérification
            email_sent = send_verification_email(user)
            if not email_sent:
                return Response({
                    "error": "L'envoi de l'email de vérification a échoué. Aucun utilisateur créé."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Création de l'EndUserDetail associé
            EndUserDetail.objects.create(
                user=user,
                first_name=first_name,
                second_name=last_name,
                address=address,
                telephone_number=telephone_number or "",
                email=email
            )

            return Response({
                "message": "Compte créé avec succès via Google. Veuillez vérifier votre email.",
                "status": status.HTTP_201_CREATED
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
   
          
# class EmailVerificationAPIView(APIView):
#     """
#     Cette classe gère la vérification de l'email via un jeton envoyé par email.
#     """
#     def get(self, request, token):
#         """
#         Vérifier l'email de l'utilisateur en utilisant le jeton du lien de vérification.
#         """
#         email = request.GET.get('email')
#         token = request.GET.get('token')

#         if not email:
#             return Response({'error': 'Paramètre email manquant dans l\'URL'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if not token:
#             return Response({'error': 'Paramètre token manquant dans l\'URL'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             user = CustomUser.objects.get(email=email, email_verification_token=token)
#             user.is_email_verified = True
#             user.email_verification_token = None
#             user.save()
#             return Response({"message": "La vérification de l'email a réussi.", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
#         except CustomUser.DoesNotExist:
#             return Response({'error': 'Jeton de vérification invalide ou email incorrect', "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
  
class EmailVerificationAPIView(APIView):
    def get(self, request):
        email = request.GET.get('email')
        token = request.GET.get('token')

        if not email:
            return Response({'error': 'Paramètre email manquant dans l\'URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not token:
            return Response({'error': 'Paramètre token manquant dans l\'URL'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email, email_verification_token=token)
            user.is_email_verified = True
            user.email_verification_token = None
            user.save()
            return Response({"message": "La vérification de l'email a réussi.", "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Jeton de vérification invalide ou email incorrect', "status": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

# class EndUserLoginAPIView(APIView):
#     """
#     Cette classe gère la connexion des utilisateurs finaux.
#     """
#     def post(self, request):
#         """
#         Authentifier et connecter un utilisateur final.
#         """
#         # Vérifier si le champ requis est présent dans la requête
#         if 'email_or_phone' not in request.data:
#             return Response({
#                   'error': 'Le champ email ou numéro de téléphone est requis.'
#             }, status=status.HTTP_400_BAD_REQUEST)  # Requête incorrecte si ni email ni téléphone n'est fourni
#         serializer = EndUserSerializer(data=request.data)
        
#         try:
#             serializer.is_valid(raise_exception=True)
#         except Exception as e:
#             return Response({
#                 'error': str(e),  # Utiliser str(e) pour convertir l'exception en chaîne de caractères
#             }, status=status.HTTP_400_BAD_REQUEST)  # Requête incorrecte pour les données invalides

#         user = serializer.validated_data['user']

#         # Vérifier si l'utilisateur est actif
#         if not user.is_active:
#             return Response({
#                 'error': 'Votre compte est inactif. Veuillez contacter l\'administrateur.',
#             }, status=status.HTTP_403_FORBIDDEN)  # Interdit pour les comptes inactifs
        
#         # Vérifier si l'email de l'utilisateur a été vérifié
#         if not user.is_email_verified:
#             return Response({
#                 'error': 'Votre email n\'a pas encore été vérifié. Veuillez vérifier votre email.',
#             }, status=status.HTTP_401_UNAUTHORIZED)  # Non autorisé si l'email n'est pas vérifié

#         if user.is_enduser:
#             # Créer ou obtenir le jeton d'authentification pour l'utilisateur
#             token, _ = Token.objects.get_or_create(user=user)
#             response_data = {
#                 'user_id': user.id,
#                 'username': user.username,
#                 'token': token.key,
#                 'message': 'Connexion réussie.',
#             }
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             return Response({
#                 'error': 'Identifiants invalides. Vous ne disposez pas des autorisations d\'accès.',
#             }, status=status.HTTP_401_UNAUTHORIZED)  # Non autorisé pour les utilisateurs non-endusers

class EndUserLoginAPIView(APIView):
    def post(self, request):
        if 'email_or_phone' not in request.data:
            return Response({
                'error': 'Le champ email ou numéro de téléphone est requis.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = EndUserSerializer(data=request.data)

        if not serializer.is_valid():
            # Récupérer le premier message d'erreur comme une chaîne de caractères
            error_message = serializer.errors.get('non_field_errors', serializer.errors)
            if isinstance(error_message, list):
                error_message = error_message[0]  # Utiliser uniquement le premier message si c'est une liste
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        if not user.is_active:
            return Response({
                'error': 'Votre compte est inactif. Veuillez contacter l\'administrateur.',
            }, status=status.HTTP_403_FORBIDDEN)

        if user.is_enduser:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'user_id': user.id,
                'username': user.username,
                'token': token.key,
                'message': 'Connexion réussie.',
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Identifiants invalides. Vous ne disposez pas des autorisations d\'accès.',
        }, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    """
    This class handles the forgot password functionality.
    """
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        """
        Handle POST requests for sending password reset OTP to the user's email.
        """
        email = request.data.get('email')

        try:
            user = CustomUser.objects.filter(email=email)
            if user.exists():
                user=user[0]
                # thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
                current_time = timezone.now()
                thirty_minutes_ago = current_time - timedelta(minutes=30)
                

                otp_count = OTP.objects.filter(user=user, created_at__gte=thirty_minutes_ago).count()
                if otp_count >= 90:
                    return Response({'success': 'false',
                                     'error': 'You have exceeded the maximum number of OTP requests'
                                     }, status=status.HTTP_400_BAD_REQUEST)
                
                otp = str(random.randint(1000, 9999))
                OTP.objects.create(user=user, otp=otp)
                context = {'otp': otp}
                email_html = f'''Hi {user.first_name},
                                \nYour reset password verification code is {otp}.\n\nThank you'''
                email_subject = 'Password Reset OTP'
                
                try:
                    send_mail(
                        email_subject,
                        email_html,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],                   
                        fail_silently=False
                    )
                    
                    return Response(
                        {
                            'msg': 'OTP sent to email address',
                            # 'response': {'attempt': 2 - otp_count}
                        }, 
                        status=status.HTTP_200_OK
                    )

                except SMTPException as e:
                    return Response(
                        {
                            'msg': str(e),
                            
                        }, 
                        status=status.HTTP_404_NOT_FOUND
                    )
   

               
            else:
                return Response({
                'success': 'false',
                'error': 'User does not exist',}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': 'false',
                'error': str(e),}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
def verify_otp(request):
    otp = request.data.get('otp')
    email = request.data.get('email')

    if not otp or not email:
        return Response({'message': 'Invalid data sent!'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(CustomUser, email=email)
    otp_instance = OTP.objects.filter(user=user).order_by('-created_at').first()

    if otp_instance is None:
        return Response({'message': 'No OTP found for this user.'}, status=status.HTTP_404_NOT_FOUND)

    if otp_instance.otp is None:
        return Response({'message': 'This OTP has already been used!'}, status=status.HTTP_400_BAD_REQUEST)

    time_diff = (timezone.now() - otp_instance.created_at).total_seconds()
    if time_diff > 300:
        return Response({'message': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

    if otp_instance.otp != otp:
        return Response({'message': 'OTP is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    # Marquer l'OTP comme utilisé et validé
    otp_instance.otp = None
    otp_instance.is_verified = True  # Marquer comme vérifié
    otp_instance.save()

    return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)

    
    

@permission_classes([AllowAny])
@api_view(['POST'])
def reset_password(request):
    """
    Reset the user's password using the OTP verification.
    """
    
    
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    # if new_password != confirm_password:
    #     return Response({'message': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = get_object_or_404(CustomUser, email=email)
        otp_instance = OTP.objects.filter(user=user).order_by('-created_at').first()
        # Vérifier si l'OTP a été validé avant la réinitialisation
        if  otp_instance.is_verified:
            user = otp_instance.user
            user.password = make_password(new_password)
            user.save()
            otp_instance.delete()
            return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'OTP verification required before resetting password.'}, status=status.HTTP_400_BAD_REQUEST)
    except OTP.DoesNotExist:
        return Response({'message': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
       


class EventPassPriceAPIView(generics.RetrieveAPIView):
    """
    Retrieve the event details along with the associated pass prices.
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


    def get(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        event_serializer = EventSerializer(event)
        event_serializer_data = event_serializer.data

        # Créer le contenu pour le QR code
        event_details = f"{event_serializer_data['event_name']} - {event_serializer_data['event_place']} - {event_serializer_data['begindatetime']}"
        qr_code_file = self.generate_qr_code(event_details)
        # Convertir le fichier QR code en base64
        qr_code_base64 = base64.b64encode(qr_code_file.read()).decode('utf-8')
        # Ajouter le QR code sérialisé aux données de l'événement
        event_serializer_data['qr_code'] = qr_code_base64

        # Retourner les données sérialisées avec le QR code
        return Response(event_serializer_data, status=200)
    

# class BuyPassAPIView(generics.CreateAPIView):
#     """
#     API view to purchase a pass for an event.
#     """
#     serializer_class = ETicketSerializer
#     permission_classes = [IsAuthenticated,IsEndUser]
#
#     def create(self, request, *args, **kwargs):
#         event_id = kwargs.get('event_id')
#         pass_category = request.data.get('pass_category')
#         quantity = request.data.get('quantity', 1)  # Default to 1 if quantity is not provided
#
#         try:
#             event = Event.objects.get(id=event_id)
#             pass_prices = EventPassCategory.objects.filter(event=event)
#             event_pass = PassCategory.objects.get(id=pass_category)
#
#             pass_price = pass_prices.filter(pass_category=event_pass).first()
#
#             if not pass_price:
#                 raise ValidationError({"error": "Invalid pass type for the event"}, code=400)
#
#         except Event.DoesNotExist:
#             return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         except PassCategory.DoesNotExist:
#             return Response({"error": "Pass category not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Check if there are enough passes available
#         available_passes = pass_price.quantity
#         if available_passes < quantity:
#             return Response({"error": "Insufficient passes available"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Get the authenticated user
#         user = request.user
#
#         # Process the pass purchase
#         pass_purchase = ETicket.objects.create(
#             event=event,
#             user=user,
#             pass_type=event_pass.id,
#             price=pass_price.price,
#             quantity=quantity,
#             is_payment_done=True
#         )
#
#         # Decrease the available quantity of passes
#         pass_price.quantity -= quantity
#         pass_price.save()
#
#         # Serialize and return the response
#         serializer = ETicketSerializer(pass_purchase)
#         return Response({
#             "success": "true",
#             "msg": "",
#             "response": {"data": serializer.data}
#         }, status=status.HTTP_201_CREATED)

# class BuyPassAPIView(generics.CreateAPIView):
#     """
#     API view to purchase multiple passes for multiple events in a single request.
#     """
#     serializer_class = ETicketSerializer
#     permission_classes = [IsAuthenticated, IsEndUser]
#
#     def create(self, request, *args, **kwargs):
#         passes_data = request.data  # Supposé être une liste de pass avec event_id
#
#         if not isinstance(passes_data, list):
#             return Response({"error": "Invalid data format, expected a list"}, status=status.HTTP_400_BAD_REQUEST)
#
#         tickets = []  # Liste pour stocker les tickets créés
#         updated_passes = []  # Liste pour suivre les mises à jour des stocks
#         user = request.user
#         if not request.user or not request.user.is_authenticated:
#             return Response({"error": "User must be authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
#
#         # Vérifier la disponibilité avant tout achat
#         for pass_item in passes_data:
#             event_id = pass_item.get("event_id")
#             pass_category = pass_item.get("pass_category")
#             quantity = pass_item.get("quantity", 1)
#
#             try:
#                 event = Event.objects.get(id=event_id)
#                 event_pass = PassCategory.objects.get(id=pass_category)
#                 pass_price = EventPassCategory.objects.filter(event=event, pass_category=event_pass).first()
#
#                 if not pass_price:
#                     return Response({"error": f"Invalid pass type {pass_category} for event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)
#
#                 if pass_price.quantity < quantity:
#                     return Response({"error": f"Insufficient passes available for category {pass_category} in event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)
#
#                 updated_passes.append((event, event_pass, pass_price, quantity))
#
#             except Event.DoesNotExist:
#                 return Response({"error": f"Event {event_id} not found"}, status=status.HTTP_404_NOT_FOUND)
#             except PassCategory.DoesNotExist:
#                 return Response({"error": f"Pass category {pass_category} not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         # Si tout est validé, créer les tickets et mettre à jour les stocks
#         for event, event_pass, pass_price, quantity in updated_passes:
#             ticket = ETicket.objects.create(
#                 event=event,
#                 user=user,
#                 pass_type=event_pass.id,
#                 price=pass_price.price,
#                 quantity=quantity,
#                 is_payment_done=False
#             )
#             tickets.append(ticket)
#
#             # Mise à jour du stock
#             pass_price.quantity -= quantity
#             pass_price.save()
#
#         Order.objects.create(43
#             user=user,
#         )
#
#         # Sérialiser la réponse
#         serializer = ETicketSerializer(tickets, many=True)
#         return Response({
#             "response": {"data": serializer.data},
#             "":
#         }, status=status.HTTP_201_CREATED)


class BuyPassAPIView(generics.CreateAPIView):
    """
    API view to purchase multiple passes for multiple events in a single request.
    """
    serializer_class = ETicketSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Récupérer les données de la requête
        data = request.data
        total_amount = data.get("total_amount")  # Montant total
        passes_data = data.get("passes")  # Liste des passes
        user = request.user

        if not isinstance(passes_data, list):
            return Response({"error": "Invalid data format, expected a list for passes"}, status=status.HTTP_400_BAD_REQUEST)

        if total_amount is None:
            return Response({"error": "Total amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user:
            return Response({"error": "User must be authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        tickets = []  # Liste pour stocker les tickets créés
        updated_passes = []  # Liste pour suivre les mises à jour des stocks
        calculated_total = 0  # Calculer le montant total en fonction des passes

        # Valider les passes et calculer le montant total
        for pass_item in passes_data:
            event_id = pass_item.get("event_id")
            pass_category = pass_item.get("pass_category")
            quantity = pass_item.get("quantity", 1)

            try:
                event = Event.objects.get(id=event_id)
                event_pass = PassCategory.objects.get(id=pass_category)
                pass_price = EventPassCategory.objects.filter(event=event, pass_category=event_pass).first()

                if not pass_price:
                    return Response({"error": f"Invalid pass type {pass_category} for event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)

                # Vérifier la disponibilité avant tout achat
                if pass_price.quantity < quantity:
                    return Response({"error": f"Insufficient passes available for category {pass_category} in event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)

                # Ajouter au montant total calculé
                calculated_total += pass_price.price * quantity

                updated_passes.append((event, event_pass, pass_price, quantity))

            except Event.DoesNotExist:
                return Response({"error": f"Event {event_id} not found"}, status=status.HTTP_404_NOT_FOUND)
            except PassCategory.DoesNotExist:
                return Response({"error": f"Pass category {pass_category} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Vérifier si le montant total calculé correspond à celui envoyé
        if total_amount != calculated_total:
            return Response({"error": "The total amount does not match the sum of the passes"}, status=status.HTTP_400_BAD_REQUEST)

        # Créer la commande (Order)
        order = Order.objects.create(user=user, total_amount=calculated_total, status='pending')

        # Si tout est validé, créer les OrderItems et les tickets, puis mettre à jour les stocks
        for event, event_pass, pass_price, quantity in updated_passes:
            # Créer l'OrderItem correspondant
            order_item = OrderItem.objects.create(
                order=order,
                event=event,
                pass_category=event_pass,
                quantity=quantity,
                price=pass_price.price
            )

            # Créer un ETicket pour chaque quantité
            for _ in range(quantity):
                ticket = ETicket.objects.create(
                    event=event,
                    user=user,
                    pass_category=event_pass,
                    price=pass_price.price,
                    quantity=1,  # Chaque ticket représente une quantité de 1
                    is_payment_done=False,
                    order=order,  # Lier à la commande
                    order_item=order_item  # Lier à l'OrderItem (OBLIGATOIRE)
                )
                tickets.append(ticket)

            # Mise à jour du stock
            pass_price.quantity -= quantity
            pass_price.save()

        # Sérialiser la réponse
        ticket_serializer = ETicketSerializer(tickets, many=True)

        order_data = {
            "order_id": order.order_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_done": order.payment_done
        }

        return Response({
            "response": {
                "data": ticket_serializer.data,
                "order": order_data  # Inclure les informations de la commande dans la réponse
            }
        }, status=status.HTTP_201_CREATED)

# class BuyPassAPIView(generics.CreateAPIView):
#     """
#     API view to purchase multiple passes for multiple events in a single request.
#     """
#     serializer_class = ETicketSerializer
#     permission_classes = [IsAuthenticated, IsEndUser]
#
#     def create(self, request, *args, **kwargs):
#         # Récupérer les données de la requête
#         data = request.data
#         total_amount = data.get("total_amount")  # Montant total
#         passes_data = data.get("passes")  # Liste des passes
#         # user_id = data.get("user_id")  # Liste des passes
#         user = request.user
#
#         if not isinstance(passes_data, list):
#             return Response({"error": "Invalid data format, expected a list for passes"}, status=status.HTTP_400_BAD_REQUEST)
#
#         if total_amount is None:
#             return Response({"error": "Total amount is required"}, status=status.HTTP_400_BAD_REQUEST)
#
#
#         if not request.user:
#             return Response({"error": "User must be authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
#
#         tickets = []  # Liste pour stocker les tickets créés
#         updated_passes = []  # Liste pour suivre les mises à jour des stocks
#         calculated_total = 0  # Calculer le montant total en fonction des passes
#
#         for pass_item in passes_data:
#             event_id = pass_item.get("event_id")
#             pass_category = pass_item.get("pass_category")
#             quantity = pass_item.get("quantity", 1)
#
#             try:
#                 event = Event.objects.get(id=event_id)
#                 event_pass = PassCategory.objects.get(id=pass_category)
#                 pass_price = EventPassCategory.objects.filter(event=event, pass_category=event_pass).first()
#
#                 if not pass_price:
#                     return Response({"error": f"Invalid pass type {pass_category} for event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)
#
#                 # Vérifier la disponibilité avant tout achat
#                 if pass_price.quantity < quantity:
#                     return Response({"error": f"Insufficient passes available for category {pass_category} in event {event_id}"}, status=status.HTTP_400_BAD_REQUEST)
#
#                 # Ajouter au montant total calculé
#                 calculated_total += pass_price.price * quantity
#
#                 updated_passes.append((event, event_pass, pass_price, quantity))
#
#             except Event.DoesNotExist:
#                 return Response({"error": f"Event {event_id} not found"}, status=status.HTTP_404_NOT_FOUND)
#             except PassCategory.DoesNotExist:
#                 return Response({"error": f"Pass category {pass_category} not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         # Vérifier si le montant total calculé correspond à celui envoyé
#         if total_amount != calculated_total:
#             return Response({"error": "The total amount does not match the sum of the passes"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Créer la commande (Order)
#         order = Order.objects.create(user=user, total_amount=calculated_total, status='pending')
#
#         # Si tout est validé, créer les OrderItems et les tickets, puis mettre à jour les stocks
#         for event, event_pass, pass_price, quantity in updated_passes:
#             # Créer l'OrderItem correspondant
#             order_item = OrderItem.objects.create(
#                 order=order,
#                 event=event,
#                 pass_category=event_pass,
#                 quantity=quantity,
#                 price=pass_price.price
#             )
#
#             # Maintenant, on peut créer le ETicket en le liant à OrderItem
#             ticket = ETicket.objects.create(
#                 event=event,
#                 user=user,
#                 pass_category=event_pass,
#                 price=pass_price.price,
#                 quantity=quantity,
#                 is_payment_done=False,
#                 order=order,  # Lier à la commande
#                 order_item=order_item  # Lier à l'OrderItem (OBLIGATOIRE)
#             )
#             tickets.append(ticket)
#
#             # Mise à jour du stock
#             pass_price.quantity -= quantity
#             pass_price.save()
#
#
#         # Sérialiser la réponse
#         ticket_serializer = ETicketSerializer(tickets, many=True)
#
#         order_data = {
#             "order_id": order.order_id,
#             "total_amount": order.total_amount,
#             "status": order.status,
#             "payment_done": order.payment_done
#         }
#
#         return Response({
#             "response": {
#                 "data": ticket_serializer.data,
#                 "order": order_data  # Inclure les informations de la commande dans la réponse
#             }
#         }, status=status.HTTP_201_CREATED)




# Custom JSON encoder to serialize datetime objects
class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects serialization.
    """
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DateTimeEncoder, self).default(o)
    

class GetUserPurchaseTicket(APIView):
    """
    API view to retrieve ticket details for a user.
    """
    permission_classes = [IsAuthenticated, IsEndUser]
    
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
        """
        Retrieve ticket details for the authenticated user.
        """
        user = request.user

        # Retrieve all ticket types for the user
        etickets = ETicket.objects.filter(user=user, is_payment_done=True)
        physical_tickets = PhysicalTicket.objects.filter(user=user)
        thermal_tickets = ThermalTicket.objects.filter(user=user)

        # Serialize the tickets
        eticket_data = ETicketSerializer(etickets, many=True).data
        physical_ticket_data = PhysicalTicketSerializer(physical_tickets, many=True).data
        thermal_ticket_data = ThermalTicketSerializer(thermal_tickets, many=True).data

        # Combine all ticket data
        all_ticket_data = eticket_data + physical_ticket_data + thermal_ticket_data

        ticket_details_with_qr = []

        # Use a static key for Fernet encryption (replace with your actual key)
        static_key = b'_uLkWMtVXLgaGFZhQzoX29hx6tMCzP1AosxMGSCALHM='
        fernet = Fernet(static_key)

        for ticket_obj in all_ticket_data:
            event = Event.objects.get(pk=ticket_obj['event'])

            qr_data = {
                "ticket_number": ticket_obj['ticket_number'],
            }
            qr_data = f"{ticket_obj['ticket_number']}"
            qr_code_file = self.generate_qr_code(qr_data)
            
            ticket_obj['qr_code'] = base64.b64encode(qr_code_file.read()).decode('utf-8')
            ticket_details_with_qr.append(ticket_obj)

        # response_data = {
        #     ticket_details_with_qr,
        # }

        return Response(ticket_details_with_qr, status=status.HTTP_200_OK)

    def shorten_url(url):
        s = pyshorteners.Shortener()
        return s.tinyurl.short(url)


# ADD TO CART

class AddToCart(APIView):
    schema = AutoSchema()

    """
    API view to add passes to the user's cart.
    """
    permission_classes = [IsAuthenticated,IsEndUser]
    def post(self, request):
        """
        Add passes to the user's cart.
        """
        event_id = request.data.get('event_id')
        pass_category_request = request.data.get('pass_category')
        quantity = request.data.get('quantity')
        user = request.user
        pass_category = PassCategory.objects.get(id=pass_category_request)

        if not event_id or not pass_category or not quantity:
            return Response({"message": "Event ID, pass type, and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        quantity = int(quantity)
        if quantity <= 0:
            return Response({"message": "Quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Event, pk=event_id)
        pass_price = EventPassCategory.objects.filter(event=event, pass_category=pass_category).first()

        if not pass_price:
            return Response({"message": "Pass price is not available for this event and pass type."}, status=status.HTTP_204_NO_CONTENT)

        price_per_unit = pass_price.price

        with transaction.atomic():
            existing_item = MyCart.objects.select_for_update().filter(event_id=event_id, pass_category=pass_category, user=user).first()

            if existing_item:
                # If the item already exists in the cart, update the quantity and price fields
                existing_item.quantity += quantity
                existing_item.unit_price = price_per_unit
                existing_item.amount = existing_item.quantity * price_per_unit
                existing_item.save()
                serializer = MyCartSerializer(existing_item)
            else:
                # If the item does not exist in the cart, create a new one
                amount = price_per_unit * quantity
                my_cart_item = MyCart.objects.create(
                    event=event,
                    user=user,
                    pass_category=pass_category,
                    quantity=quantity,
                    unit_price=price_per_unit,
                    amount=amount
                )
                serializer = MyCartSerializer(my_cart_item)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# PURCHASE FROM CART
class BuyPassFromCartAPIView(generics.CreateAPIView):
    """
    API view to purchase passes from the user's cart.
    """
    serializer_class = ETicketSerializer
    permission_classes = [IsAuthenticated, IsEndUser]

    def create(self, request, *args, **kwargs):
        """
        Purchase passes from the user's cart.
        """
        user = request.user
        cart = MyCart.objects.filter(user=user)

        if not cart.exists():
            return Response({"message": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order, pass_purchases, tickets = self.process_cart(user, cart)
            cart.delete()

        serializer = TicketSerializer(tickets, many=True)
        return Response({"message": "purchased", "tickets": [ticket.ticket_number for ticket in tickets], "data": serializer.data}, status=status.HTTP_200_OK)

    def process_cart(self, user, cart):
        """
        Process the cart items to create orders, purchases, and tickets.
        """
        
        order = self.create_order(user)
        pass_purchases, tickets, total_amount = [], [], 0

        for cart_item in cart:
            event, event_pass = self.get_event_and_pass(cart_item)
            event_pass_category = EventPassCategory.objects.get(event=event, pass_category=cart_item.pass_category)
            self.check_quantity(event_pass_category, cart_item.quantity)

            purchases, item_tickets = self.create_pass_purchases_and_tickets(user, order, cart_item, event, event_pass_category)
            pass_purchases.extend(purchases)
            tickets.extend(item_tickets)
            total_amount += cart_item.unit_price * cart_item.quantity

        order.total_amount = total_amount
        order.payment_done = True
        order.save()
        return order, pass_purchases, tickets

    def create_order(self, user):
        """
        Create an order for the user.
        """
        return Order.objects.create(user=user, total_amount=0, status='pending', payment_done=False)

    def get_event_and_pass(self, cart_item):
        """
        Get the event and event pass for the given cart item.
        """
        try:
            event = Event.objects.get(id=cart_item.event_id)
            
        except Event.DoesNotExist:
            raise ValidationError({"error": f"Event with ID {cart_item.event_id} not found"}, code=404)

        try:
            event_pass_category = EventPassCategory.objects.select_for_update().get(event=event, pass_category=cart_item.pass_category)
        except EventPassCategory.DoesNotExist:
            raise ValidationError({"error": "Event passes not found for this event"}, code=404)
        except EventPassCategory.MultipleObjectsReturned:
            event_pass_category = EventPassCategory.objects.select_for_update().filter(event=event, pass_category=cart_item.pass_category).first()

        return event, event_pass_category

    def check_quantity(self, event_pass_category, quantity):
        """
        Check if the requested quantity of passes is available.
        """
        # available_quantity = getattr(event_pass, f"{pass_category.name.lower()}_pass")
        if event_pass_category.quantity < quantity:
            raise ValidationError({"error": f"Insufficient '{event_pass_category.pass_category.name}' passes available"}, code=400)

    def create_pass_purchases_and_tickets(self, user, order, cart_item, event, event_pass_category):
        logger.info(f"Creating tickets for user: {user.id}, event: {event.id}")
        pass_purchases, tickets = [], []
        order_item = OrderItem.objects.create(order=order, event=event, pass_category=cart_item.pass_category, quantity=cart_item.quantity, price=cart_item.amount)
        logger.info(f"Order item created: {order_item.id}")

        for _ in range(cart_item.quantity):
            try:
                ticket = ETicket.objects.create(
                    order_item=order_item,
                    user=user,
                    event=event,
                    pass_category=cart_item.pass_category,
                    price=cart_item.unit_price,
                    is_payment_done=True,
                    purchase_date=datetime.now()
                )
                logger.info(f"Ticket created: {ticket.id}")
                tickets.append(ticket)
                self.decrease_pass_quantity(event_pass_category, 1)
            except Exception as e:
                logger.error(f"Failed to create ticket: {str(e)}")
                raise e

        return pass_purchases, tickets

    def decrease_pass_quantity(self, event_pass_category, quantity):
        """
        Decrease the available quantity of the specified pass type.
        """
        event_pass_category.quantity -= quantity
        event_pass_category.save()
        

class GetCartItems(APIView):
    """
    API view to retrieve items in the user's cart.
    """
    permission_classes = [IsAuthenticated, IsEndUser]

    def get(self, request):
        """
        Retrieve items in the user's cart.
        """
        user = request.user
        cart = MyCart.objects.filter(user=user)
        if not cart.exists():
            return Response([], status=status.HTTP_204_NO_CONTENT)
        
        cart_items = []
        total_cart_price = 0

        for cart_item in cart:
            event = Event.objects.get(id=cart_item.event.id)
            pass_prices = EventPassCategory.objects.filter(pass_category=cart_item.pass_category, event=event)
            # Check if there are any pass prices
            if pass_prices.exists():
                # You can loop through pass prices if needed, but for now, I'm taking the first one
                pass_price = pass_prices.first()
                pass_price_cart = pass_price.price

            total_cart_price += pass_price_cart * cart_item.quantity if pass_price_cart else 0

            event_image = event.event_image_1.url if event.event_image_1 else None
            cart_items.append({
                "cart_id": cart_item.id,
                "event_id": cart_item.event.id,
                "event_name": event.event_name,
                "pass_category": cart_item.pass_category.name,
                "quantity": cart_item.quantity,
                "pass_price": pass_price_cart,
                "event_image": str(event.event_image_1),
                "begindatetime": event.begindatetime,
            })

        return Response({"data": cart_items, "total_cart_price": total_cart_price}, status=status.HTTP_200_OK)


class RemoveOrIncreaseProductFromCartView(generics.DestroyAPIView):
    """
    API view to remove or increase the quantity of a product in the user's cart.
    """
    # authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated,IsEndUser]

    # def put(self, request, *args, **kwargs):
    #     """
    #     Increase the quantity of a product in the user's cart.
    #     """
    #     user = request.user
    #
    #     try:
    #         user = CustomUser.objects.get(id=user.id)
    #         cart_item = MyCart.objects.get(pk=kwargs['pk'],user=user)
    #         event_passes = EventPass.objects.filter(event=cart_item.event)
    #         pass_price = PassPrice.objects.filter(event=cart_item.event, pass_type=cart_item.pass_type).first()
    #
    #         if not pass_price:
    #             return Response({"message": "Pass price is empty"}, status=status.HTTP_204_NO_CONTENT)
    #
    #
    #     except MyCart.DoesNotExist:
    #         return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    #
    #
    #     # Get the requested quantity from the request data
    #     requested_quantity =int(request.data.get('quantity'))
    #     if event_passes.exists():
    #         event_pass = event_passes.first()
    #
    #     # Check if the requested quantity is greater than the available quantity
    #         if requested_quantity is not None and requested_quantity > 0 and requested_quantity > event_pass.pass_total_quantity:
    #             return Response({'detail': 'Requested quantity exceeds available quantity'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #         # Update the cart item quantity
    #         cart_item.quantity += requested_quantity
    #         cart_item.price =pass_price.price_with_qr * int(cart_item.quantity)
    #
    #         cart_item.save()
    #         # serializer = AddProductToCartSerializer(cart_item)
    #         return Response({"message":"Done"},status=status.HTTP_201_CREATED)
    #     else:
    #         return Response({'detail': 'EventPass not found'}, status=status.HTTP_404_NOT_FOUND)
    def delete(self, request, *args, **kwargs):
        """
        Remove a product from the user's cart.
        """
        try:
            user = CustomUser.objects.get(id=self.request.user.id)
            cart_item = MyCart.objects.get(pk=kwargs['pk'], user=user)
       
        except MyCart.DoesNotExist:
            return Response({'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()
        return Response({'detail': 'Item removed from cart'}, status=status.HTTP_200_OK)
    

class DecreaseProductFromCartView(generics.DestroyAPIView):
    """
    API view to decrease the quantity of a product in the user's cart.
    """
    # authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated,IsEndUser]
    # def put(self, request, *args, **kwargs):
    #     """
    #     Decrease the quantity of a product in the user's cart.
    #     """
    #     user = request.user
    #
    #     try:
    #         user = CustomUser.objects.get(id=user.id)
    #         cart_item = MyCart.objects.get(pk=kwargs['pk'],user=user)
    #         event_passes = EventPass.objects.filter(event=cart_item.event)
    #         pass_price = PassPrice.objects.filter(event=cart_item.event, pass_type=cart_item.pass_type).first()
    #
    #         if not pass_price:
    #             return Response({"message": "Pass price is empty"}, status=status.HTTP_204_NO_CONTENT)
    #
    #     except MyCart.DoesNotExist:
    #         return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    #
    #     # Get the requested quantity from the request data
    #     requested_quantity =int(request.data.get('quantity'))
    #     print(requested_quantity)
    #     if event_passes.exists():
    #         event_pass = event_passes.first()
    #
    #
    #          # Check if the requested quantity is greater than the available quantity
    #         if requested_quantity is not None and requested_quantity > 0 and  requested_quantity > event_pass.pass_total_quantity:
    #             return Response({'detail': 'Requested quantity exceeds available quantity'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #          # Update the cart item quantity
    #         cart_item.quantity -= requested_quantity
    #         cart_item.price = pass_price.price_with_qr * int(cart_item.quantity)
    #         cart_item.save()
    #         # serializer = AddProductToCartSerializer(cart_item)
    #         return Response({"message":"Done"},status=status.HTTP_201_CREATED)
    #     else:
    #         return Response({'detail': 'EventPass not found'}, status=status.HTTP_404_NOT_FOUND)


# class TypeOfEventList(APIView):
#     """
#     API view to retrieve distinct event types and their related images.
#     """
#     def get(self, request):
#         """
#         Retrieve distinct event types and their related images.
#         """
#         try:
#             # Get distinct event types and related event_image_1
#             events = TypeOfEvent.objects.all()
#             serializer = TypeOfEventSerializer(events, many=True)

#             return Response({"data":serializer.data}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryEventList(APIView):
    """
    API view to retrieve distinct event types and their related images.
    """
    def get(self, request):
        """
        Retrieve distinct event types and their related images.
        """
        try:
            # Get distinct event types and related event_image_1
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)

            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EventsByCategoryAPIView(APIView):
    """
    API view to retrieve events filtered by category ID.
    """
    def get(self, request, category_id):
        """
        Retrieve events based on the category ID.
        """
        try:
            # Filter events by the given category ID
            events = Event.objects.filter(category_id=category_id)
            serializer = EventSerializer(events, many=True)

            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventsByCategoryNameAPIView(APIView):
    """
    API view to retrieve events filtered by category name passed as a query parameter.
    """
    def get(self, request):
        """
        Retrieve events based on the category name provided as a query parameter.
        """
        category_name = request.query_params.get('name', None)

        if not category_name:
            return Response({"error": "Category name is required as a query parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve the category by name
            category = Category.objects.get(name=category_name)
            
            # Filter events by the retrieved category
            events = Event.objects.filter(category=category)
            serializer = EventSerializer(events, many=True)

            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EventFilterList(APIView):
    """
    API view to filter events based on the type of event.
    """
    def get(self, request):
        """
        Filter events based on the type of event.
        """
        events = Event.objects.filter(category_id=request.query_params['category'])

        serialized_events = EventSerializer(events, many=True)

        return Response({"data":serialized_events.data}, status=status.HTTP_200_OK)
        # if serializer.is_valid():
        #     type_of_event = serializer.validated_data.get('category_id')
        #     events = Event.objects.filter(category_id=category_id).distinct()
        #     serialized_events = EventSerializer(events, many=True)

        #     return Response({"data":serialized_events.data}, status=status.HTTP_200_OK)
        # else:
        #     return Response(serializer.errors, status=400)
        

class UserProfile(APIView):
    """
    API view to retrieve the profile of the authenticated end user.
    """
    permission_classes = [IsAuthenticated,IsEndUser]
    def get(self, request):
        """
        Retrieve the profile of the authenticated end user.
        """
        user = request.user
        try:
            end_user_detail = EndUserDetail.objects.get(user=user)
            serializer = EndUserDetailSerializer(end_user_detail)
            return Response(serializer.data)
        except EndUserDetail.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        

class FavoriteEventList(APIView):
    """
    API view to manage favorite events for authenticated end users.
    """
    permission_classes = [IsAuthenticated,IsEndUser]
    def get(self, request, format=None):
        """
        Retrieve the list of favorite events for the authenticated end user.
        """
        user = request.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return Response({"error": "Authentication is required to access this resource."}, status=status.HTTP_401_UNAUTHORIZED)

        fav_events = FavoriteEvent.objects.filter(user=user)

        # Check if the user has any favorite events
        if not fav_events.exists():
            return Response({"error": "No favorite events found for this user."}, status=status.HTTP_404_NOT_FOUND)

        serializer = FavoriteEventSerializer(fav_events, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Add an event to the user's list of favorite events.
        """
        user = request.user
        event_id = request.data.get('event_id')
        event = Event.objects.filter(id=event_id).first()

        if not event:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        fav_event, created = FavoriteEvent.objects.get_or_create(user=user, event=event)

        if not created:
            return Response({"error": "Event already favorited"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FavoriteEventSerializer(fav_event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class RemoveFavoriteEvent(APIView):
    """
    API view to remove a favorite event for an authenticated end user.
    """
    permission_classes = [IsAuthenticated,IsEndUser]
    def delete(self, request,event_id, format=None):
        """
        Remove a favorite event for the authenticated end user.
        """
        user = request.user
        fav_event = FavoriteEvent.objects.filter(user=user, event__id=event_id).first()

        # Check if the user is authenticated
        if not user.is_authenticated:
            return Response({"error": "Authentication is required to access this resource."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the favorite event exists
        if not fav_event:
            return Response({"error": "Favorite event not found."}, status=status.HTTP_404_NOT_FOUND)

        fav_event.delete()

        return Response({"message": "Favorite event removed successfully."}, status=status.HTTP_200_OK)

def send_gift_email(gift, receiver_email):
    subject = 'You have received a gift!'
    message = f'Dear recipient,\n\nYou have received a gift from {gift.gifter.first_name}.'
    message += '\n\nRedeem your gift using the following links:\n'
    message += 'App: [insert link to app here]\n'
    message += 'Web app: [https://zvkmtpt1-3000.inc1.devtunnels.ms/]\n\n'
    message += '\n\n** Use same email while sign-up to redeem gift sucessfully :\n'
    message += 'Thank you!\n\nBest regards,\nThe Gift Team'

    send_mail(subject, message,settings.EMAIL_HOST_USER, [receiver_email])

class SendGiftAPI(APIView):
    """
    API view to send a gift to another user.
    """
    permission_classes = [IsAuthenticated,IsEndUser]
    # def post(self, request):
    #     """
    #     Send a gift to another user.
    #     """
    #     serializer = SendGiftSerializer(data=request.data)
    #     if serializer.is_valid():
    #         # Create the gift entry
    #         user  = EndUserDetail.objects.get(user=request.user)
    #         gift = serializer.save(gifter=user)
    #         ticket_id = serializer.validated_data['ticket_id']
    #         try:
    #             ticket_obj = PassPurchase.objects.get(user=request.user,id=ticket_id)
    #             ticket_obj.user = None
    #             ticket_obj.save()
    #         except PassPurchase.DoesNotExist:
    #             return Response({'message':"ticket does not exist"}, status=status.HTTP_404_NOT_FOUND)
    #
    #         # Send email to the receiver
    #         receiver_email = serializer.validated_data['reciever_email']
    #         send_gift_email(gift, receiver_email)
    #
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)