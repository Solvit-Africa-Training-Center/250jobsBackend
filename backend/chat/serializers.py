from rest_framework import serializers
from .models import Message, Room
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "profile_picture"]


class MessageSerializer(serializers.ModelSerializer):
    recipient_id = serializers.IntegerField(write_only=True)
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "room", "sender", "recipient_id", "content", "timestamp", "read"]
        read_only_fields = ["id", "room", "sender", "timestamp", "read"]

    def get_sender(self, obj):
        return obj.sender.username

    def create(self, validated_data):
        sender = self.context["request"].user
        recipient_id = validated_data.pop("recipient_id")
        content = validated_data["content"]

        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient_id": "User does not exist"})

        room = (Room.objects.filter(participants=sender)
                .filter(participants=recipient)
                .first())

        if not room:
            room = Room.objects.create()
            room.participants.add(sender, recipient)

        message = Message.objects.create(
            room=room, sender=sender, content=content
        )
        return message

class RoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    

    class Meta:
        model = Room
        fields = ['id', 'participants', 'created_at']
