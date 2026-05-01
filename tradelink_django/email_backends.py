import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.utils.functional import cached_property


class InsecureTLSEmailBackend(SMTPEmailBackend):
    """
    Development-only SMTP backend that disables TLS certificate verification.
    Use only when local machine/proxy CA chain is broken.
    """

    @cached_property
    def ssl_context(self):
        context = ssl._create_unverified_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
