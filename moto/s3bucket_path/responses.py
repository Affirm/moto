from moto.s3.responses import ResponseObject as S3ResponseObject
from .models import s3bucket_path_backend

class ResponseObject(S3ResponseObject):
    def __init__(self, backend):
        super(ResponseObject, self).__init__(backend)

    def subdomain_based_buckets(self, request):
        return False


S3ResponseInstance = ResponseObject(s3bucket_path_backend)