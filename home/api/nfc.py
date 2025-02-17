from rest_framework import generics
from ..models import NFCData
from .serializers import NFCDataSerializer,PostNFCDataSerializer
# import nfc
import ndef
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

class NFCWriteView(generics.CreateAPIView):
    serializer_class = PostNFCDataSerializer

    def perform_create(self, serializer):
        nfc_id = serializer.validated_data['nfc_id']
        wallet = serializer.validated_data['wallet']

        # Check if an NFC object with the provided nfc_id already exists
        try:
            nfc_obj = NFCData.objects.get(nfc_id=nfc_id)
            # If it exists, update the wallet value
            nfc_obj.wallet = wallet
            nfc_obj.save()
        except NFCData.DoesNotExist:
            # If it doesn't exist, create a new NFCData object
            NFCData.objects.create(nfc_id=nfc_id, wallet=wallet)

        return Response({"message": "NFC data updated or created successfully"}, status=status.HTTP_201_CREATED)

# class NFCWriteView(generics.CreateAPIView):
#     serializer_class = NFCDataSerializer

#     def post(self, serializer):
#         # content = self.request.data.get('content')
#         nfc_id = self.request.data.get('nfc_id')  # Assuming you receive the NFC ID from the barcode scanner
#         wallet = int(self.request.data.get('wallet'))# Assuming you receive the wallet value from the request
#         # with nfc.ContactlessFrontend('usb') as clf:
#         #     tag = clf.connect(rdwr={'on-connect': None})
#         #     tag.ndef.records = [ndef.TextRecord(content)]
#         #     tag.disconnect()
#         serializer.save(nfc_id=nfc_id, wallet=wallet)

class NFCReadView(APIView):
    def get(self, request, nfc_id):
        try:
            nfc_data = NFCData.objects.get(nfc_id=nfc_id)
            serializer = NFCDataSerializer(nfc_data)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except NFCData.DoesNotExist:
            return Response({"error": f"NFC data with ID {nfc_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from datetime import datetime
# from home.models import PassPurchase

# class CheckInNFCID(APIView):
#     def get(self, request, nfc_id):
#         try:
#             # Assuming you have models PassPurchase and Event defined as mentioned
#             pass_purchase = PassPurchase.objects.get(nfc_id=nfc_id)
#             event = pass_purchase.event

#             if pass_purchase.is_used == False:

#             # Check if today's date is equal to the end date of the event
#                 today_date = datetime.now().date()
#                 if today_date == event.enddatetime:
#                     # Construct the response with event details
#                     event_details = {
#                         "event_name": event.event_name,
#                         "event_place": event.event_place,
#                         "description": event.description,
#                         # Add other event details you want to include in the response
#                     }
#                     pass_purchase.is_used = True
#                     pass_purchase.save()
#                     return Response({"message":"Valid","data":event_details}, status=status.HTTP_200_OK)
#                 else:
#                     return Response({"message":"Invalid"}, status=status.HTTP_404_NOT_FOUND)
#             else:
#                 return Response({"message":"Already Used"}, status=status.HTTP_404_NOT_FOUND)

#         except PassPurchase.DoesNotExist:
#             return Response({"message":"Invalid NFC"}, status=status.HTTP_404_NOT_FOUND)