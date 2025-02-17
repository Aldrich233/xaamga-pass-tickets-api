from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import *

class EventLoginAPIView(APIView):
    """
    API view for event login.
    """
    def post(self, request):
        """
        Authenticate event and provide authentication token.
        """
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        print("EEEEEEEEEEEEE "+str(username))
        print("EEEEEEEEEEEEE "+str(password))
        # Authenticate partner
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_event:
            # Create or get the authentication token for the partner
            token, _ = Token.objects.get_or_create(user=user)
            response_data = {
                'user_id': user.id,
                'token': token.key,
                'message': 'Event login successful.',
            }
            return Response(response_data, status=200)
        else:
            return Response({'error': 'Invalid credentials'}, status=400)
