from moto.s3.models import S3Backend


# Needs to be implemented so that the urls module is mapped properly
class S3BucketPathBackend(S3Backend):
    def __init__(self):
        super(S3BucketPathBackend, self).__init__()

s3bucket_path_backend = S3BucketPathBackend()
