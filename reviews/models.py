# import uuid
# from django.db import models
# from django.core.validators import MinValueValidator, MaxValueValidator


# class Review(models.Model):
#     review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     product = models.ForeignKey(
#         "Product",
#         on_delete=models.CASCADE,
#         related_name="reviews"
#     )

#     user = models.ForeignKey(
#         "auth.User",
#         on_delete=models.CASCADE
#     )

#     rating_value = models.IntegerField(
#         validators=[MinValueValidator(1), MaxValueValidator(5)]
#     )

#     comment = models.TextField(blank=True)

#     date_created = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Review {self.review_id}"