from .amarillo import AmarilloImporter


class BessermitfahrenImporter(AmarilloImporter):
    def __init__(self, url):
        super().__init__("bessermitfahren", url)

    def _get_data_from_json_response(self, json_response):
        return json_response.get("data")

    @staticmethod
    def _is_weekday(depatureDate):
        return depatureDate in {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

    def _extract_departure_date(self, offer) -> str | list[str]:
        """
        Bessermitfahren returns individual dates in an array.
        If departureDate is a list and not contains only weekdays, we assume
        a single date and return this. If the assumption is wrong, this will
        be raised by pydantic validation later on.
        """
        departureDate = offer.get("departureDate")
        all_entries_are_weekdays = isinstance(departureDate, list) and all(
            BessermitfahrenImporter._is_weekday(entry) for entry in departureDate
        )

        return departureDate if all_entries_are_weekdays else departureDate[0]
