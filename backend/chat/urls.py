from django.urls import path
from .views import RoomListView, MessageListView, MessageSendView

urlpatterns = [
    path("rooms/", RoomListView.as_view(), name="room-list"),
    path("rooms/<int:room_id>/messages/", MessageListView.as_view(), name="list-messages"),
    path("messages/send/", MessageSendView.as_view(), name="send-message"),
]
