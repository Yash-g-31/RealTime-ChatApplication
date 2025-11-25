from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Message, Block
from .serializers import MessageSerializer
from django.db import models


class MessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET /api/chat/messages/?user_id=2[&after=10]
        Returns messages between logged-in user and user_id.
        If 'after' is passed, only return messages with id > after.
        """
        other_user_id = request.query_params.get('user_id')
        if not other_user_id:
            return Response(
                {"detail": "user_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        after_id = request.query_params.get('after')

        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        qs = Message.objects.filter(
            sender__in=[user, other_user],
            receiver__in=[user, other_user],
        ).order_by('id')  # order by id so 'after' makes sense

        # Mark all messages FROM otherUser TO currentUser as read
        Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        if after_id:
            qs = qs.filter(id__gt=after_id)

        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        POST /api/chat/messages/
        body: { "receiver": 2, "content": "hello" }
        sender = request.user
        """
        receiver_id = request.data.get("receiver")
        if not receiver_id:
            return Response(
                {"detail": "receiver is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Receiver not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 1) You blocked them → you can't send
        if Block.objects.filter(blocker=request.user, blocked=receiver).exists():
            return Response(
                {"detail": "You blocked this user."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2) They blocked you → you can't send
        if Block.objects.filter(blocker=receiver, blocked=request.user).exists():
            return Response(
                {"detail": "This user has blocked you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageSerializer(
            data=request.data,
            context={'request': request}  # 👈 pass request to serializer
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlockView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        POST /api/chat/block/
        body: { "user_id": 3 }
        -> current user blocks user_id
        """
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if str(request.user.id) == str(user_id):
            return Response(
                {"detail": "You cannot block yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        Block.objects.get_or_create(
            blocker=request.user,
            blocked=other_user
        )

        return Response({"blocked": True}, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        DELETE /api/chat/block/?user_id=3
        -> current user unblocks user_id
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        Block.objects.filter(
            blocker=request.user,
            blocked_id=user_id
        ).delete()

        return Response({"blocked": False}, status=status.HTTP_200_OK)


class BlockStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET /api/chat/block/status/?user_id=3

        Returns:
        {
          "blocked_by_me": true/false,
          "blocked_me": true/false
        }
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        blocked_by_me = Block.objects.filter(
            blocker=request.user,
            blocked=other_user
        ).exists()

        blocked_me = Block.objects.filter(
            blocker=other_user,
            blocked=request.user
        ).exists()

        return Response(
            {
                "blocked_by_me": blocked_by_me,
                "blocked_me": blocked_me,
            },
            status=status.HTTP_200_OK
        )

class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Returns unread messages count grouped by sender.
        Example:
        [
           { "user_id": 2, "count": 5 },
           { "user_id": 4, "count": 1 }
        ]
        """
        unread = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).values('sender').annotate(count=models.Count('id'))

        data = [
            {"user_id": item['sender'], "count": item['count']}
            for item in unread
        ]

        return Response(data, status=200)
