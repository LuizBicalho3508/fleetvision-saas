from django.db import models
import uuid

class TimeStampedModel(models.Model):
    """
    Classe abstrata que fornece campos auto-atualizáveis de 
    criação e modificação, além de UUID como ID padrão.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True