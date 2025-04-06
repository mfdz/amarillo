from amarillo.services.agencyconf import AgencyConfService


def test_agency_conf():
    service = AgencyConfService()
    assert service.get_agency_conf('matchrider') is not None
    assert len(service.get_agency_conf('matchrider').offers_download_http_headers) > 0
