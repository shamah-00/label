from django.db import models


class QuickBooksConnection(models.Model):
    """Encrypted OAuth credentials for one authorized QuickBooks company."""

    realm_id = models.CharField(max_length=100, unique=True)
    encrypted_access_token = models.TextField()
    encrypted_refresh_token = models.TextField()
    access_token_expires_at = models.DateTimeField()
    refresh_token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_by = models.CharField(max_length=150, blank=True)
    connected_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "QuickBooks connection"
        verbose_name_plural = "QuickBooks connection"

    def __str__(self):
        return f"QuickBooks company {self.realm_id}"
