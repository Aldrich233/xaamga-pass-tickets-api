from drf_spectacular.openapi import AutoSchema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import *
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .custom_permissions import *

class PartnerLoginAPIView(APIView):
    schema = AutoSchema()

    def post(self, request):
        serializer = PartnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Authenticate partner
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_partner:
            # Create or get the authentication token for the partner
            token, _ = Token.objects.get_or_create(user=user)
            response_data = {
                'user_id': user.id,
                'token': token.key,
                'message': 'Partner login successful.',
            }
            return Response(response_data, status=200)
        else:
            return Response({'error': 'Invalid credentials'}, status=400)


#EVENT CREATED BY PARTNER 

class CreateEventByPartner(APIView):
    schema = AutoSchema()

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated , IsPartner]
    def get(self, request):
        try:
            partner_obj = Partner.objects.get(user=request.user)
            print(partner_obj)
            event_obj = Event.objects.filter(partner=partner_obj.id)
            print(event_obj)
            serializer = EventSerializer(event_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        # Validate and create the event
        username = request.data['username']
        password = request.data['password']
        partner_obj = Partner.objects.get(user=request.user)
        event_data = {
            "partner": partner_obj.id,
            "client": request.data.get("client"),
            "event_type": request.data.get("event_type"),
            "event_name": request.data.get("event_name"),
            "event_place": request.data.get("event_place"),
            "description": request.data.get("description"),
            "type_of_event": request.data.get("type_of_event"),
            "begindatetime": request.data.get("begindatetime"),
            "enddatetime": request.data.get("enddatetime"),
            "event_image_1": request.data.get("event_image_1"),
            "event_image_2": request.data.get("event_image_2"),
            "event_image_3": request.data.get("event_image_3"),
        }

        is_user = Event.objects.filter(event_name=event_data["event_name"]).exists()

        if is_user:
            return Response({"error": "User with this event_name already exists. Please use a different email."}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username,password=password)
        user.is_event=True
        user.save()
        event_data["user"] = user.id
        event_type =event_data['event_type']
        if event_type == "without_resources":
            event_serializer = EventSerializer(data=event_data)
            event_serializer.is_valid(raise_exception=True)
            event_serializer.save()
        else:
            event_serializer = EventSerializer(data=event_data)
            event_serializer.is_valid(raise_exception=True)
            event_serializer.save()

            # Create EventPass
            event_pass_data = {
                "event": event_serializer.instance.id,
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
                "event": event_serializer.instance.id,
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
                "event": event_serializer.instance.id,
                "simple_paper": request.data.get("simple_paper_badges"),
                "personalized_badge": request.data.get("personalized_badges"),
                "is_nfc": request.data.get("is_nfc_badges"),
            }
            event_badges_serializer = EventBadgesSerializer(data=event_badges_data)
            event_badges_serializer.is_valid(raise_exception=True)
            event_badges_serializer.save()

            # Create CheckInPoint
            check_in_point_data = {
                "event": event_serializer.instance.id,
                "check_in_point_quantity": request.data.get("check_in_point_quantity"),
            }
            check_in_point_serializer = CheckInPointSerializer(data=check_in_point_data)
            check_in_point_serializer.is_valid(raise_exception=True)
            check_in_point_serializer.save()

            # Create ExhibitionPoint
            exhibition_point_data = {
                "event": event_serializer.instance.id,
                "exhibition_point_quantity": request.data.get("exhibition_point_quantity"),
            }
            exhibition_point_serializer = ExhibitionPointSerializer(data=exhibition_point_data)
            exhibition_point_serializer.is_valid(raise_exception=True)
            exhibition_point_serializer.save()

            # Create ActivityPoint
            activity_point_data = {
                "event": event_serializer.instance.id,
                "activity_point_quantity": request.data.get("activity_point_quantity"),
            }
            activity_point_serializer = ActivityPointSerializer(data=activity_point_data)
            activity_point_serializer.is_valid(raise_exception=True)
            activity_point_serializer.save()

            # Create GuichetPoint
            guichet_point_data = {
                "event": event_serializer.instance.id,
                "guichet_point_quantity": request.data.get("guichet_point_quantity"),
            }
            guichet_point_serializer = GuichetPointSerializer(data=guichet_point_data)
            guichet_point_serializer.is_valid(raise_exception=True)
            guichet_point_serializer.save()

            # Create DrinksPoint
            drinks_point_data = {
                "event": event_serializer.instance.id,
                "drinks_point_quantity": request.data.get("drinks_point_quantity"),
            }
            drinks_point_serializer = DrinksPointSerializer(data=drinks_point_data)
            drinks_point_serializer.is_valid(raise_exception=True)
            drinks_point_serializer.save()

            # Create WorkshopPoint
            workshop_point_data = {
                "event": event_serializer.instance.id,
                "workshop_point_quantity": request.data.get("workshop_point_quantity"),
            }
            workshop_point_serializer = WorkshopPointSerializer(data=workshop_point_data)
            workshop_point_serializer.is_valid(raise_exception=True)
            workshop_point_serializer.save()
            
            response = {
                "event": event_serializer.data,
                "event_pass": event_pass_serializer.data,
                "event_bracelet": event_bracelet_serializer.data,
                "event_badges": event_badges_serializer.data,
                "check_in_point": check_in_point_serializer.data,
                "exhibition_point": exhibition_point_serializer.data,
                "activity_point": activity_point_serializer.data,
                "guichet_point": guichet_point_serializer.data,
                "drinks_point": drinks_point_serializer.data,
                "workshop_point": workshop_point_serializer.data,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        response = {
            "event": event_serializer.data,
            "event_pass": event_pass_serializer.data if event_type == "with_resources" else None,
            # Add other related models to the response here...
        }
        return Response(response, status=status.HTTP_201_CREATED)
    

class ClientRegisterByPartner(APIView):
    # schema = AutoSchema()

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated , IsPartner]
    def get(self, request):
        try:
            partner_obj = Partner.objects.get(user=request.user)
            client_obj = Client.objects.filter(partner=partner_obj.id)
            serializer = ClientSerializer(client_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Partner.DoesNotExist:
            return Response({"error": "Partner not found"}, status=status.HTTP_404_NOT_FOUND)
        except Client.DoesNotExist:
            return Response({"error": "No clients found for this partner"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, *args, **kwargs):
        # Validating and getting data from request
        required_fields = ['company_name', 'first_name', 'last_name', 'address', 'telephone_number', 'email']
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: '{field}'"}, status=status.HTTP_400_BAD_REQUEST)
        partner_obj = Partner.objects.get(user=request.user)
        username = request.data['username']
        password = request.data['password']
        print(partner_obj)
        company_name = request.data['company_name']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        address = request.data['address']
        telephone_number = request.data['telephone_number']
        email = request.data['email']

        is_user = CustomUser.objects.filter(email=email).exists()
        if is_user:
            return Response({"error": "User with this email already exists. Please use a different email."}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username,password=password,email=email)
        user.first_name = first_name
        user.last_name = last_name

        client = Client.objects.create(
            user=user,
            partner=partner_obj,
            company_name=company_name,
            first_name=first_name,
            second_name=last_name,
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
    
    
class PartnerDescriptionUpdate(APIView):
    schema = AutoSchema()

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        # Get the partner object associated with the logged-in user
        try:
            partner = Partner.objects.get(user=user)
        except Partner.DoesNotExist:
            return Response({"error": "Partner not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the partner is updating their own description
        if partner.user != user:
            return Response({"error": "You are not authorized to update this description."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PartnerDescriptionUpdateSerializer(partner, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Description updated successfully."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)