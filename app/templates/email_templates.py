# ruff: noqa: E501

from html import escape


def render_password_reset_email(*, reset_link: str) -> str:
    safe_reset_link = escape(reset_link, quote=True)

    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reset your password</title>
  </head>
  <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5eaf2;">
            <tr>
              <td style="padding:32px 32px 20px;background:#0f766e;color:#ffffff;">
                <h1 style="margin:0;font-size:24px;line-height:32px;font-weight:700;">Reset your password</h1>
                <p style="margin:8px 0 0;font-size:14px;line-height:22px;color:#d9fffb;">Blog API account security</p>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 16px;font-size:16px;line-height:26px;">
                  We received a request to reset your password. Click the button below to choose a new password.
                </p>

                <table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0;">
                  <tr>
                    <td style="border-radius:8px;background:#0f766e;">
                      <a href="{safe_reset_link}" style="display:inline-block;padding:14px 22px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:8px;">
                        Reset password
                      </a>
                    </td>
                  </tr>
                </table>

                <p style="margin:0 0 12px;font-size:14px;line-height:22px;color:#526173;">
                  This link will expire soon. If you did not request a password reset, you can safely ignore this email.
                </p>

                <p style="margin:24px 0 0;font-size:13px;line-height:20px;color:#697789;">
                  If the button does not work, copy and paste this link into your browser:
                </p>
                <p style="margin:8px 0 0;font-size:13px;line-height:20px;word-break:break-all;">
                  <a href="{safe_reset_link}" style="color:#0f766e;text-decoration:underline;">{safe_reset_link}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e5eaf2;">
                <p style="margin:0;font-size:12px;line-height:18px;color:#7a8699;">
                  This is an automated email. Please do not reply.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()


def render_email_verification_email(*, verification_link: str) -> str:
    safe_verification_link = escape(verification_link, quote=True)

    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Verify your email</title>
  </head>
  <body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fb;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5eaf2;">
            <tr>
              <td style="padding:32px 32px 20px;background:#2563eb;color:#ffffff;">
                <h1 style="margin:0;font-size:24px;line-height:32px;font-weight:700;">Verify your email</h1>
                <p style="margin:8px 0 0;font-size:14px;line-height:22px;color:#dbeafe;">Welcome to Blog API</p>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 16px;font-size:16px;line-height:26px;">
                  Thanks for creating an account. Please verify your email address to activate your account and continue using Blog API.
                </p>

                <table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0;">
                  <tr>
                    <td style="border-radius:8px;background:#2563eb;">
                      <a href="{safe_verification_link}" style="display:inline-block;padding:14px 22px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:8px;">
                        Verify email
                      </a>
                    </td>
                  </tr>
                </table>

                <p style="margin:0 0 12px;font-size:14px;line-height:22px;color:#526173;">
                  This verification link is valid for a limited time. If you did not create this account, you can ignore this email.
                </p>

                <p style="margin:24px 0 0;font-size:13px;line-height:20px;color:#697789;">
                  If the button does not work, copy and paste this link into your browser:
                </p>
                <p style="margin:8px 0 0;font-size:13px;line-height:20px;word-break:break-all;">
                  <a href="{safe_verification_link}" style="color:#2563eb;text-decoration:underline;">{safe_verification_link}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e5eaf2;">
                <p style="margin:0;font-size:12px;line-height:18px;color:#7a8699;">
                  This is an automated email. Please do not reply.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
