# from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
# from allauth.socialaccount.providers.oauth2.client import OAuth2Client
# from rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from ..models import CustomUser, EndUserDetail
from rest_framework.views import APIView
from rest_framework.response import Response
from requests.models import PreparedRequest
import requests

# class GoogleSignup(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = 'http://127.0.0.1'  # Replace with your callback URL
#     client_class = OAuth2Client

#     def complete_signup(self, request, user, **kwargs):
#         # Generate a token for the user
#         token, _ = Token.objects.get_or_create(user=user)

#         # Save user details in the EndUserDetail model
#         end_user_detail = EndUserDetail.objects.create(
#             user=user,
#             first_name=user.first_name,
#             second_name=user.last_name,
#             email=user.email,
#             # Add other fields as necessary
#         )

#         # Return the token
#         return Response({'token': token.key}, status=status.HTTP_201_CREATED)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """
    This view is needed by the dj-rest-auth-library in order to work the google login. It's a bug.
    """

    permanent = False

    def get_redirect_url(self):
        return "redirect-url"


import requests

def exchange_code_for_token(code):
    data = {
        'code': code,
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'redirect_uri': 'http://127.0.0.1',
        'grant_type': 'authorization_code'
    }
    response = requests.post('https://oauth2.googleapis.com/token', data=data)
    return response.json()


class GoogleLogin(APIView):
    def get(self, request, format=None):
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": "182623101044-e6ru6ih7thh2b005hv2kbksqon7f3l87.apps.googleusercontent.com",
            "redirect_uri": "https://857a-2409-40d5-1008-566c-f06b-40e9-2d1-f572.ngrok-free.app/api/google-callback/",
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "include_granted_scopes": "true"
        }
        req = PreparedRequest()
        req.prepare_url(google_auth_url, params)
        return Response({"auth_url": req.url})

class GoogleCallback(APIView):
    def get(self, request, format=None):
        code = request.GET.get('code')
        data = {
            'code': code,
            'client_id': '182623101044-e6ru6ih7thh2b005hv2kbksqon7f3l87.apps.googleusercontent.com',
            'client_secret': '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',
            'redirect_uri': "https://857a-2409-40d5-1008-566c-f06b-40e9-2d1-f572.ngrok-free.app/api/google-callback/",
            'grant_type': 'authorization_code'
        }
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        return Response(response.json())


# class GoogleProfile(APIView):
#     def get(self, request, format=None):
#         access_token = request.GET.get('access_token')
#         headers = {'Authorization': 'Bearer {}'.format(access_token)}
#         response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
#         return Response(response.json())
    
class GoogleProfile(APIView):
    def get(self, request, format=None):
        access_token = request.GET.get('access_token')
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
        data = response.json()

        user, created = CustomUser.objects.get_or_create(username=data['id'], defaults={'email': data['email']})
        if created:
            user.set_unusable_password()
            user.first_name = data['given_name']
            user.last_name = data['family_name']
            user.is_enduser = True
            user.save()

            end_user, created = EndUserDetail.objects.update_or_create(user=user, defaults={
                'first_name': data['given_name'],
                'second_name': data['family_name'],
                'email': data['email'],
            })
            token, _ = Token.objects.get_or_create(user=user)

            if 'email' in data:
                try:
                    gift_obj = SentGift.objects.get(reciever_email=data['email'])
                    pass_purchase_obj = PassPurchase.objects.get(id=gift_obj.ticket_id)
                    pass_purchase_obj.user = user
                    pass_purchase_obj.save()
                    message = "You have redeemed Your Gift"
                    gift_obj.delete()
                except (SentGift.DoesNotExist, PassPurchase.DoesNotExist) as e:
                    message = str(e)

                token, _ = Token.objects.get_or_create(user=user)

                response_data = {
                    "id": end_user.pk, "username": user.first_name,
                    "message": message,
                    "status": 1,
                    "token": token.key
                }
            else:
                response_data = {
                    'token': token.key, "id": end_user.pk, "username": user.first_name,
                    "status": 1
                }

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response({'token': token.key, "id": end_user.pk, "username": user.first_name}, status=status.HTTP_201_CREATED)

from rest_framework.generics import GenericAPIView
from .serializers import*
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

@permission_classes((AllowAny, ))
class FacebookSocialAuthView(GenericAPIView):

    serializer_class = FacebookSocialAuthSerializer

    def post(self, request):
        """
        POST with "auth_token"
        Send an access token as from facebook to get user information
        """

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = ((serializer.validated_data)['auth_token'])
        return Response(data, status=status.HTTP_200_OK)