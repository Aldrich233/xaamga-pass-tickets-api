from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import CustomUser
from .serializers import *
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import qrcode
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .custom_permissions import IsEndUser, IsEvent, IsTeam
import base64
from io import BytesIO
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone

# from datetime import timedelta, timezone
from django.contrib.auth.models import User
import random
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  
from datetime import timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist  

class TeamLoginAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate partner
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_team:
            try:
                # Get the associated EventTeam instance for the user
                event_team = EventTeam.objects.get(user=user)
                
                    # Create or get the authentication token for the partner
                token, _ = Token.objects.get_or_create(user=user)
                response_data = {
                        'user_id': user.id,
                        'token': token.key,
                        'message': 'User login successful.',
                        'team_type':  event_team.team_type,
                    }
                return Response(response_data, status=status.HTTP_200_OK)
            except EventTeam.DoesNotExist:
                return Response({'error': 'No associated EventTeam found for the user'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class EventTeamProfileAPIView(APIView):
    permission_classes = [IsAuthenticated,IsTeam]  # Only authenticated users can access

    def get(self, request):
        user = request.user

        try:
            # Get the associated EventTeam instance for the user
            event_team = EventTeam.objects.get(user=user)

            serialized_data = {
                'user_id': user.id,
                'first_name': event_team.first_name,
                'second_name': event_team.second_name,
                'team_type': event_team.team_type,
                'member_type': event_team.member_type,
                'member_post': event_team.member_post,
                'member_role': event_team.member_role,
                'telephone_number': event_team.telephone_number,
                'email': event_team.email,
                'created_at': event_team.created_at,
                'updated_at': event_team.updated_at,
            }

            return Response(serialized_data, status=status.HTTP_200_OK)
        except EventTeam.DoesNotExist:
            return Response({'error': 'No associated EventTeam found for the user'}, status=status.HTTP_404_NOT_FOUND)





class GetPassesOfEventGuichet(APIView):
    permission_classes = [IsAuthenticated,IsTeam]

    def get(self,request):
        # user = CustomUser.objects.get(id=request.user.id)
        print(request.user)
        team = EventTeam.objects.get(user=request.user)
        print(team.event.id)
        event=Event.objects.get(id=team.event.id)
        print(event)


        # print(user)
        queryset = PassPrice.objects.filter(event=event)
        serializer=ListPassPriceSerializer(queryset,many=True)
        return Response({"data":serializer.data})

class GetBracletOfEventGuichet(APIView):
    permission_classes = [IsAuthenticated,IsTeam]

    def get(self,request):
        # user = CustomUser.objects.get(id=request.user.id)
        print(request.user)
        team = EventTeam.objects.get(user=request.user)
        event=Event.objects.get(id=team.event.id)
        # print(user)
        queryset = BraceletPrice.objects.filter(event=event)
        serializer=BraceletPriceSerializer(queryset,many=True)
        return Response({"data":serializer.data})