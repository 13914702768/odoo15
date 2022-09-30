# -*- coding: UTF-8 -*-
from odoo import api, fields, models, tools, _
import smtplib
import logging
import sys

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools import ustr, pycompat, formataddr, email_normalize, encapsulate_email, email_domain_extract, email_domain_normalize

_logger = logging.getLogger(__name__)
_test_logger = logging.getLogger('odoo.tests')

def is_ascii(s):
    return all(ord(cp) < 128 for cp in s)

class IrMailServerInheritXks(models.Model):
    _inherit = "ir.mail_server"

    @api.model
    def _get_default_bounce_address(self):
        '''Compute the default bounce address.

        The default bounce address is used to set the envelop address if no
        envelop address is provided in the message.  It is formed by properly
        joining the parameters "mail.bounce.alias" and
        "mail.catchall.domain".

        If "mail.bounce.alias" is not set it defaults to "postmaster-odoo".

        If "mail.catchall.domain" is not set, return None.

        '''
        get_param = self.env['ir.config_parameter'].sudo().get_param
        postmaster = get_param('mail.bounce.alias', default='postmaster-odoo')
        domain = get_param('mail.catchall.domain')
        if postmaster and domain:
            return '%s@%s' % (postmaster, domain)


    def _find_mail_server(self, email_from, mail_servers=None):
        """Find the appropriate mail server for the given email address.

        Returns: Record<ir.mail_server>, email_from
        - Mail server to use to send the email (None if we use the odoo-bin arguments)
        - Email FROM to use to send the email (in some case, it might be impossible
          to use the given email address directly if no mail server is configured for)
        """
        email_from_normalized = email_normalize(email_from)
        email_from_domain = email_domain_extract(email_from_normalized)
        notifications_email = email_normalize(self._get_default_from_address())
        notifications_domain = email_domain_extract(notifications_email)

        if mail_servers is None:
            mail_servers = self.sudo().search([], order='sequence')

        # 1. Try to find a mail server for the right mail from
        mail_server = mail_servers.filtered(lambda m: email_normalize(m.from_filter) == email_from_normalized)
        if mail_server:
            return mail_server[0], email_from

        mail_server = mail_servers.filtered(lambda m: email_domain_normalize(m.from_filter) == email_from_domain)
        if mail_server:
            return mail_server[0], email_from

        # 2. Try to find a mail server for <notifications@domain.com>
        if notifications_email:
            mail_server = mail_servers.filtered(lambda m: email_normalize(m.from_filter) == notifications_email)
            if mail_server:
                return mail_server[0], notifications_email

            mail_server = mail_servers.filtered(lambda m: email_domain_normalize(m.from_filter) == notifications_domain)
            if mail_server:
                return mail_server[0], notifications_email

        # 3. Take the first mail server without "from_filter" because
        # nothing else has been found... Will spoof the FROM because
        # we have no other choices
        mail_server = mail_servers.filtered(lambda m: not m.from_filter)
        if mail_server:
            for server in mail_server:
                start = email_from.index('<') + 1
                end = email_from.index('>')
                _logger.info(email_from[start: end])
                _logger.info(server.smtp_user)
                if email_from[start: end] == server.smtp_user:
                    return server, email_from
            return mail_server[0], email_from

        # 4. Return the first mail server even if it was configured for another domain
        if mail_servers:
            return mail_servers[0], email_from

        # 5: SMTP config in odoo-bin arguments
        from_filter = self.env['ir.config_parameter'].sudo().get_param(
            'mail.default.from_filter', tools.config.get('from_filter'))

        if self._match_from_filter(email_from, from_filter):
            return None, email_from

        if notifications_email and self._match_from_filter(notifications_email, from_filter):
            return None, notifications_email

        return None, email_from

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_ssl_certificate=None, smtp_ssl_private_key=None,
                   smtp_debug=False, smtp_session=None):
        """Sends an email directly (no queuing).

        No retries are done, the caller should handle MailDeliveryException in order to ensure that
        the mail is never lost.

        If the mail_server_id is provided, sends using this mail server, ignoring other smtp_* arguments.
        If mail_server_id is None and smtp_server is None, use the default mail server (highest priority).
        If mail_server_id is None and smtp_server is not None, use the provided smtp_* arguments.
        If both mail_server_id and smtp_server are None, look for an 'smtp_server' value in server config,
        and fails if not found.

        :param message: the email.message.Message to send. The envelope sender will be extracted from the
                        ``Return-Path`` (if present), or will be set to the default bounce address.
                        The envelope recipients will be extracted from the combined list of ``To``,
                        ``CC`` and ``BCC`` headers.
        :param smtp_session: optional pre-established SMTP session. When provided,
                             overrides `mail_server_id` and all the `smtp_*` parameters.
                             Passing the matching `mail_server_id` may yield better debugging/log
                             messages. The caller is in charge of disconnecting the session.
        :param mail_server_id: optional id of ir.mail_server to use for sending. overrides other smtp_* arguments.
        :param smtp_server: optional hostname of SMTP server to use
        :param smtp_encryption: optional TLS mode, one of 'none', 'starttls' or 'ssl' (see ir.mail_server fields for explanation)
        :param smtp_port: optional SMTP port, if mail_server_id is not passed
        :param smtp_user: optional SMTP user, if mail_server_id is not passed
        :param smtp_password: optional SMTP password to use, if mail_server_id is not passed
        :param smtp_ssl_certificate: filename of the SSL certificate used for authentication
        :param smtp_ssl_private_key: filename of the SSL private key used for authentication
        :param smtp_debug: optional SMTP debug flag, if mail_server_id is not passed
        :return: the Message-ID of the message that was just sent, if successfully sent, otherwise raises
                 MailDeliveryException and logs root cause.
        """
        smtp = smtp_session
        if not smtp:
            smtp = self.connect(
                smtp_server, smtp_port, smtp_user, smtp_password, smtp_encryption,
                smtp_from=message['From'], ssl_certificate=smtp_ssl_certificate, ssl_private_key=smtp_ssl_private_key,
                smtp_debug=smtp_debug, mail_server_id=mail_server_id, )

        smtp_from, smtp_to_list, message = self._prepare_email_message(message, smtp)

        # Do not actually send emails in testing mode!
        if self._is_test_mode():
            _test_logger.info("skip sending email in test mode")
            return message['Message-Id']

        try:
            message_id = message['Message-Id']

            if sys.version_info < (3, 7, 4):
                # header folding code is buggy and adds redundant carriage
                # returns, it got fixed in 3.7.4 thanks to bpo-34424
                message_str = message.as_string()
                message_str = re.sub('\r+(?!\n)', '', message_str)

                mail_options = []
                if any((not is_ascii(addr) for addr in smtp_to_list + [smtp_from])):
                    # non ascii email found, require SMTPUTF8 extension,
                    # the relay may reject it
                    mail_options.append("SMTPUTF8")
                smtp.sendmail(smtp_from, smtp_to_list, message_str, mail_options=mail_options)
            else:
                smtp.send_message(message, smtp_from, smtp_to_list)

            # do not quit() a pre-established smtp_session
            if not smtp_session:
                smtp.quit()
        except smtplib.SMTPServerDisconnected:
            raise
        except Exception as e:
            params = (ustr(smtp_server), e.__class__.__name__, ustr(e))
            msg = _("Mail delivery failed via SMTP server '%s'.\n%s: %s", *params)
            _logger.info(msg)
            raise MailDeliveryException(_("Mail Delivery Failed"), msg)
        return message_id