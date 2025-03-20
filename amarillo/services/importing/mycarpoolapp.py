from .amarillo import AmarilloImporter


class MyCarpoolAppImporter(AmarilloImporter):
    def __init__(self, url):
        super().__init__("mycarpoolapp", url)

    def _get_data_from_json_response(self, json_response):
        return [cp for cp in json_response.get("data") if not cp.get('isTest') == 1]
