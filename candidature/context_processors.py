from .models import Message, Notification


def notifications_context(request):
    if request.user.is_authenticated:
        return {
            'unread_messages': Message.objects.filter(destinataire=request.user, lu=False).count(),
            'unread_notifications': Notification.objects.filter(utilisateur=request.user, lu=False).count(),
        }
    return {'unread_messages': 0, 'unread_notifications': 0}
