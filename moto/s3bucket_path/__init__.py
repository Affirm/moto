from __future__ import unicode_literals
from .models import s3bucket_path_backend

s3bucket_path_backends = {"global": s3bucket_path_backend}
mock_s3bucket_path = s3bucket_path_backend.decorator
mock_s3bucket_path_deprecated = s3bucket_path_backend.deprecated_decorator
