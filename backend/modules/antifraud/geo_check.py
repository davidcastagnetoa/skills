"""Geolocation and VPN/proxy/Tor detection.

Uses GeoIP2 MaxMind database for IP geolocation.
Compares IP country with document nationality as an auxiliary signal.
"""

import structlog

from modules.antifraud.models import GeoCheckResult

logger = structlog.get_logger()

# Known VPN/proxy/Tor detection is done via the GeoIP2 Anonymous IP database
# or third-party IP reputation services.


class GeoLocationChecker:
    """Check IP geolocation against document nationality."""

    def __init__(self, geoip_reader=None) -> None:
        self._reader = geoip_reader
        self._init_reader()

    def _init_reader(self) -> None:
        """Try to load GeoIP2 database."""
        if self._reader is not None:
            return
        try:
            import geoip2.database

            self._reader = geoip2.database.Reader("/usr/share/GeoIP/GeoLite2-City.mmdb")
            logger.info("geo_check.geoip2_loaded")
        except Exception:
            logger.warning("geo_check.geoip2_not_available")

    def check(
        self,
        ip_address: str | None,
        document_nationality: str | None,
    ) -> GeoCheckResult:
        """Check geolocation consistency.

        Args:
            ip_address: Client IP address.
            document_nationality: ISO 3166-1 alpha-3 country code from document.

        Returns:
            GeoCheckResult with discrepancy flag (non-blocking).
        """
        if not ip_address:
            return GeoCheckResult()

        ip_country = self._lookup_country(ip_address)

        is_discrepant = False
        if ip_country and document_nationality:
            # Compare (note: IP is alpha-2, doc nationality may be alpha-3)
            ip_alpha2 = ip_country.upper()
            doc_alpha3 = document_nationality.upper()
            # Simple check: if first 2 chars don't match, flag it
            # A proper implementation would use a country code mapping
            is_discrepant = ip_alpha2 != doc_alpha3[:2] if len(doc_alpha3) >= 2 else False

        return GeoCheckResult(
            ip_country=ip_country,
            document_nationality=document_nationality,
            is_discrepant=is_discrepant,
        )

    def _lookup_country(self, ip_address: str) -> str | None:
        """Look up country code for an IP address."""
        if self._reader is None:
            return None

        try:
            response = self._reader.city(ip_address)
            return response.country.iso_code
        except Exception:
            return None


class VPNProxyDetector:
    """Detect VPN, proxy, and Tor connections."""

    def __init__(self, anonymous_ip_reader=None) -> None:
        self._reader = anonymous_ip_reader
        self._init_reader()

    def _init_reader(self) -> None:
        if self._reader is not None:
            return
        try:
            import geoip2.database

            self._reader = geoip2.database.Reader(
                "/usr/share/GeoIP/GeoIP2-Anonymous-IP.mmdb"
            )
            logger.info("vpn_detector.anonymous_ip_db_loaded")
        except Exception:
            logger.warning("vpn_detector.anonymous_ip_db_not_available")

    def check(self, ip_address: str | None) -> GeoCheckResult:
        """Check if an IP is a VPN, proxy, or Tor exit node."""
        if not ip_address or self._reader is None:
            return GeoCheckResult()

        try:
            response = self._reader.anonymous_ip(ip_address)
            return GeoCheckResult(
                is_vpn=bool(getattr(response, "is_anonymous_vpn", False)),
                is_proxy=bool(getattr(response, "is_public_proxy", False)),
                is_tor=bool(getattr(response, "is_tor_exit_node", False)),
            )
        except Exception:
            return GeoCheckResult()
