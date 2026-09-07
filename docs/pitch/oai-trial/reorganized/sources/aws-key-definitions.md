# Proposed key management and keyed pseudonyms

AWS Key Management Service (KMS) protects cryptographic keys and controls access to their use.

HMAC means Hash-based Message Authentication Code. It computes a keyed hash; in the proposed pseudonymization design, a secret key would help derive repeatable substitutes. It is not encryption or a general anonymity guarantee, and it does not replace a shared collision-allocation plan.

Key management and keyed pseudonyms are proposed—not implemented locally.

Official references:
- https://docs.aws.amazon.com/kms/latest/developerguide/overview.html
- https://docs.aws.amazon.com/kms/latest/developerguide/hmac.html

These definitions explain the proposed role. They do not claim that KMS integration, HMAC, key rotation, or production deployment was executed in the local trial.
