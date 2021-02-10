# Signalen security policies

Signalen development team is strongly committed to responsible reporting and disclosure of security-related issues. As such, we’ve adopted and follow a set of policies which conform to that ideal and are geared toward allowing us to deliver timely security updates to the official distribution of Signalen.

## Reporting security issues

**Short version: please report security issues by emailing signalen-security@lists.publiccode.net.**

If you discover security issues in Signalen we request you to disclose these in a *responsible* way by e-mailing to signalen-security@lists.publiccode.net.

It is extremely useful if you have a reproducible test case and/or clear steps on how to reproduce the vulnerability.

Please do not report security issues on the public Github issue tracker, as this makes it visible which exploits exist before a fix is available, potentially comprising a lot of unprotected instances.

Once you’ve submitted an issue via email, you should receive an acknowledgment from a member of the security team as soon as possible, and depending on the action to be taken, you may receive further followup emails.

## Timeline of the process

Signalen has a technical steering group, of which all members are involved in the handling of security issues.

1. The recipients of the report first validate if there is indeed a (possible) issue.

2. After validation, we confirm that we received the report and if it is indeed a valid issue.

3. We have a private Github repository accessible to the technical steering group. In this repository, an issue is created for the vulnerability where the impact and possible solutions are discussed.

4. The next step is to create a (draft) Github security advisory, which is only visible to the repository administrators and technical steering group. Severity and impact will be established here.

5. If appropriate, we request a [CVE identifier](https://cve.mitre.org/cve/identifiers/) from Github.

6. A patch is implemented, reviewed and tested in a private fork.

7. During the patch development process, known service providers are contacted to inform them of the vulnerability and coordinate the release date and rollout of the fix.

8. When the fix is tested and release coordination is done, the fix is merged into the primary repository. The security advisory and release are published. Service providers update their managed instances.

9. The release and security vulnerability are communicated to the community. This includes a message to the mailing list and announcements on the Common Ground Slack.
