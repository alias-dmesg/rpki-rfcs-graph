[A Profile for Route Origin Authorizations (ROAs)](https://tools.ietf.org/html/rfc6482 "A Profile for Route Origin Authorizations (ROAs)")
========================================

# Content

## Targets
Relaying Parties, RIRs

## Terminology
* Route Origination Authorization (ROA)
* RPKI
* CMS
* Internet X.509 Public Key Infrastructure Certificate and Certificate Revocation List (CRL) Profile
* [X.509 Extensions for IP Addresses and AS Identifiers RFC3779](https://tools.ietf.org/html/rfc5652)
* Signed Object Template for the Resource Public Key Infrastructure (RPKI)
* A Profile for X.509 PKIX Resource Certificates RFC6487
* eContentType
* encapContentInfo
* Content-Type
* SignerInfo
* eContent
* routeOriginAuthz

## Summary
Route Origination Authorization (ROA) is the component of RPKI that allow relaying parties to validate signed announcement/object. ROA format and generic validation procedure are based on [Crytopgraphic Message Syntax (CMS) RFC5652](https://tools.ietf.org/html/rfc5652) according to [Signed Object Template for the Resource Public Key Infrastructure (RPKI) RFC6488](https://tools.ietf.org/html/rfc6488). A ROA is composed of:

* The OID within the eContentType from the encapContentInfo object that identifies the signed object as being a ROA. The OID must also be present in the Content-Type signed attribute in the SignerInfo object.
* The eContent i.e. the payload that specifies the AS being authorized to originate routes as well as the prefixes to which the AS may originate routes.
* An additional step required to validate ROAs.

An overview of the Signed Object Template for a ROA can been seen [here](figure/rfc6482_roa_template.pdf). Picture below give lower resolution of Signed Object Template for a ROA
![Signed Object Template for a ROA](figure/rfc6482_roa_template.jpg)



ROA Content-Type is defined as routeOriginAuthz with numerical value of 1.2.840.113549.1.9.16.1.24(registered by IANA to RPKI ROA).The ROA eContent is unique per AS. If the address space holder needs to authorize multiple ASes to advertise the same set of address prefixes, the holder issues multiple ROAs, one per AS number. The ROA encapContentInfo in eContent is defined with:

* IPAddress
* ROAIPAddress: sequence of IPAddresswith an optional maxLength. When present, the maxLength specifies the maximum length of the IP address prefix that the AS is authorized to advertise. Note that a valid ROA may contain an IP address prefix (within a ROAIPAddress element) that is encompassed by another IP address prefix (within a separate ROAIPAddress element)
* ROAIPAddressFamily: sequence of ROAIPAddress, each with his address family(IPv4 or IPv6)
* ASID: AS number
* RouteOriginAttestation: sequence of ASID and set of ROAIPAddressFamily with a default version parameterset as 0.

ROA validation follow checking describe in [Signed Object Template for the Resource Public Key Infrastructure (RPKI) RFC6488](https://tools.ietf.org/html/rfc6488) as well as following additional ROA specific validation step.
Following RPKI access control,only allowed relaying party can create a ROA associate with his resources. Also prefixes in ROA must match those in EE certificate. Prefixes in ROA are contained in a set of IP addresses specified in the IP address delegation extension of the EE certificate.
Since ROA is part of RPKI and the goal of RPKI is authorization, there is no assumption of confidentiality or authentication for the data in ROA. Nevertheless, integrity of signed object like ROA must be guaranteed by taking advantage of the RPKI security mechanisms like the CMS.