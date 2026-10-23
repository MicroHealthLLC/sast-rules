using System.Net;

class Client
{
    void Disabled()
    {
        // ruleid: csharp.crypto.certificate-validation-disabled
        ServicePointManager.ServerCertificateValidationCallback += (sender, cert, chain, errors) => true;
        // ruleid: csharp.crypto.certificate-validation-disabled
        ServicePointManager.ServerCertificateValidationCallback += (object sender, X509Certificate cert, X509Chain chain, SslPolicyErrors errors) => true;
    }

    void Checked()
    {
        // ok: csharp.crypto.certificate-validation-disabled
        ServicePointManager.ServerCertificateValidationCallback += (sender, cert, chain, errors) => errors == SslPolicyErrors.None;
    }
}
