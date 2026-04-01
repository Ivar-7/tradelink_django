import uuid
from django.conf import settings
from django.db import models


KENYA_COUNTIES = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Kiambu',
    'Machakos', 'Kajiado', 'Murang\'a', 'Nyeri', 'Meru', 'Embu',
    'Garissa', 'Kwale', 'Kilifi', 'Taita Taveta', 'Kakamega', 'Bungoma',
    'Vihiga', 'Trans Nzoia', 'Uasin Gishu', 'Nandi', 'Kericho', 'Bomet',
    'Narok', 'Kisii', 'Nyamira', 'Homa Bay', 'Migori', 'Siaya', 'Busia',
    'Other'
]


class ProfileAddress(models.Model):
    """Saved address for a user profile."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    label = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    county = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    line1 = models.CharField(max_length=255, blank=True)
    postal_address = models.CharField(max_length=255)
    user_email = models.EmailField()
    user_contact = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'label')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.label or self.city} - {self.user.email}'

