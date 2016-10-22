from django.db import models

from db.models import DocumentBase, DocumentID
from utils.upload import set_upload_to_random_filename


class Image(DocumentBase):
    subject = models.ForeignKey(DocumentID, related_name="images")
    image = models.ImageField(
        max_length=512,
        upload_to=set_upload_to_random_filename('images')
    )

    REPUTATION_VALUE = 1
