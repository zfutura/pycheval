# Security Policy

## Supported Versions

We provide security fixes for the current version of PyCheval only. Security
vulnerabilities are addressed by releasing a new version based on the latest
code. Previous versions do not receive security updates.

We recommend always using the latest version to ensure you have the most recent
security fixes.

## Reporting a Vulnerability

If you discover a security vulnerability in PyCheval, please report it to us
privately to allow for responsible disclosure.

### How to Report

Please send an email to **security@zfutura.de** with the following information:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes (if you have them)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report
  within 72 hours
- **Initial Assessment**: We will provide an initial assessment within
  5 business days
- **Resolution**: We aim to resolve critical security issues within 30 days

### Disclosure Policy

- Please do not publicly disclose the vulnerability until we have had a
  chance to address it.
- We will coordinate with you on the timing of public disclosure.
- We will credit you in our security advisories (unless you prefer to remain
  anonymous).

## Security Considerations for PyCheval

### PDF and XML Processing Security

PyCheval processes PDF files that may contain embedded XML data. When using
this library:

- **Input Validation**: Always validate and sanitize PDF or XML files from
  untrusted sources.
- **File Size Limits**: Implement appropriate file size limits to prevent
  resource exhaustion.
- **[XML Bomb](https://en.wikipedia.org/wiki/Billion_laughs_attack)
  Protection**: Large or deeply nested XML files could cause memory issues.
- **Data Validation**: Always validate the business logic of parsed invoice
  data. PyCheval implements very limited validation of the rules defined
  in the Factur-X standard. It is up to the user to ensure that the data
  complies with these rules.

### Known Security Considerations

- PDF parsing relies on the [pypdf library](https://pypdf.readthedocs.io/) –
  ensure you're using a recent version and follow its security updates.
- This library is in early development (alpha stage) – use with appropriate
  caution in production.
- Invoice data may contain sensitive financial information – handle with care.

## Security Updates

Security updates will be released as patch versions and announced through
the [CHANGELOG.md](CHANGELOG.md) file, GitHub release notes, and GitHub
Security Advisories.

## Questions?

If you have questions about this security policy, please
[open an issue](https://github.com/zfutura/pycheval/issues) or contact us via
**security@zfutura.de**.
