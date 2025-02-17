from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import *

class ClientLoginAPIView(APIView):
    def post(self, request):
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Authenticate partner
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_client:
            # Create or get the authentication token for the partner
            token, _ = Token.objects.get_or_create(user=user)
            response_data = {
                'user_id': user.id,
                'token': token.key,
                'message': 'client login successful.',
            }
            return Response(response_data, status=200)
        else:
            return Response({'error': 'Invalid credentials'}, status=400)
