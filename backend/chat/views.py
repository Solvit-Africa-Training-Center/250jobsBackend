from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Message, Room
from .serializers import MessageSerializer, RoomSerializer
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from drf_yasg.utils import swagger_auto_schema

User = get_user_model()


class RoomListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Chat"], operation_summary="List my chat rooms")
    def get_queryset(self):
        return Room.objects.filter(participants=self.request.user).order_by("-created_at")

    @swagger_auto_schema(tags=["Chat"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Chat"], operation_summary="List messages in a room")
    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Message.objects.none()
        
        if self.request.user not in room.participants.all():
            return Message.objects.none()
        
        return Message.objects.filter(room=room).order_by("timestamp")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and not Room.objects.filter(id=self.kwargs["room_id"]).exists():
            return Response({"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
        if not queryset.exists():
            return Response({"error": "You are not allowed in this room."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Chat"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class MessageSendView(generics.GenericAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(tags=["Chat"], operation_summary="Send a message (creates room if needed)")
    def post(self, request):
        sender = request.user
        recipient_id = request.data.get("recipient_id")
        content = request.data.get("content")

        if not recipient_id or not content:
            return Response(
                {"error": "recipient_id and content are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

        room = (Room.objects.filter(participants=sender).filter(participants=recipient).first())
        if not room:
            if sender.role == "employer" and recipient.role == "technician":
                room = Room.objects.create()
                room.participants.add(sender, recipient)
            else:
                return Response(
                    {"error": "You cannot create a room with this user."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            if sender not in room.participants.all():
                return Response(
                    {"error": "You are not a participant in this room."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        message = Message.objects.create(room=room, sender=sender, content=content)

        # Best-effort websocket broadcast; don't fail API if channel layer isn't available
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{room.id}",
                    {
                        "type": "chat.message",
                        "message": {
                            "id": message.id,
                            "room": room.id,
                            "sender": {
                                "id": sender.id,
                                "username": sender.username,
                                "email": sender.email,
                                "role": sender.role,
                            },
                            "content": message.content,
                            "timestamp": message.timestamp.isoformat(),
                            "read": message.read,
                        },
                    },
                )
        except Exception:
            # Skip broadcast errors (e.g., Redis down) to keep HTTP flow working
            pass

        return Response(
            {
                "room": RoomSerializer(room).data,
                "message": MessageSerializer(message).data,
            },
            status=status.HTTP_201_CREATED,
        )
