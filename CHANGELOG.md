# Changelog

The changelog lists most feature changes between each release. Search GitHub issues and pull requests for smaller issues.


## 1.1.0 (under development)
- feature: agency's download urls are now configured via agency conf option `offers_download_url`. This allows adding new agencies providing a standard amarillo download endpoint for syncing via config only.
- feature: Addition to the carpool model: `exceptionDates` now allow to provide exceptions to a regular, weekly schedule by specifying added or removed dates (https://github.com/mfdz/amarillo/commit/ab6e715cc6a7e0079e256e6a0735829f637fe763). 
- feature: support - on a per agency basis - disabling stop snapping/addition (https://github.com/mfdz/amarillo/commit/4a5399f5cea21ec8a463126bf4f901cbbf332547). 

## 1.0.0
- Initial release providing core functionality to ingest carpool offers via push/pull, enhance them by the probable route and stops close by. This data can be exported as GTFS/GTFS-RT feeds.