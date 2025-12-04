import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FleetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Pega o usuário logado (o AuthMiddlewareStack popula o scope['user'])
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        # Define o grupo baseado no Tenant do usuário
        # Se for superuser sem tenant, entra num grupo global 'admin_global'
        if hasattr(self.user, 'profile') and self.user.profile.tenant:
            self.room_group_name = f"tenant_{self.user.profile.tenant.id}"
        else:
            self.room_group_name = "admin_global"

        # Entra no grupo (sala)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Sai do grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recebe mensagem do Redis (via webhook) e manda para o WebSocket (Frontend)
    async def vehicle_update(self, event):
        message = event['message']

        # Envia para o WebSocket
        await self.send(text_data=json.dumps({
            'type': 'vehicle_update',
            'data': message
        }))