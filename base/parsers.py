from django.http import QueryDict
import json
from rest_framework import parsers


class MultipartJsonParser(parsers.MultiPartParser):

    def parse(self, *args, **kwargs):
        result = super().parse(*args, **kwargs)
        data = json.loads(result.data["json_data"])
        for k, v in result.files.items():
            data[k] = v
        return parsers.DataAndFiles(data, {})
