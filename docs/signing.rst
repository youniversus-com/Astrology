Signed commits and tags
=======================

Supply-chain hardening for releases uses **OpenPGP-signed Git tags** (required for
releases) and optionally **signed commits** on ``main``.

One-time setup
--------------

1. Create or import a GPG key:

.. code-block:: bash

   gpg --full-generate-key
   gpg --list-secret-keys --keyid-format long

2. Upload the public key to GitHub: **Settings → SSH and GPG keys → New GPG key**

3. Enable signing locally:

.. code-block:: bash

   git config --global user.signingkey YOUR_KEY_ID
   git config --global commit.gpgsign true   # optional: every commit
   git config --global tag.gpgSign true      # recommended: signed tags

Signed release tag
------------------

.. code-block:: bash

   git tag -s v1.1.59 -m "Release 1.1.59"
   git push origin v1.1.59

Verify locally:

.. code-block:: bash

   git tag -v v1.1.59

CI verification
---------------

The workflow ``.github/workflows/verify-release.yml`` imports the trusted release
signing key from ``.github/gpg/release-signing.asc`` and fails if a pushed ``v*`` tag
is **not** signed with that key.

When the release signing key changes, export the new public key and replace
``.github/gpg/release-signing.asc`` before signing the next release tag.

GitHub branch protection (recommended)
--------------------------------------

In **Settings → Branches → Branch protection rules** for ``main``:

- Require signed commits (optional, stricter)
- Require status checks to pass (lint, unit, docs, …)
- Require pull request reviews before merging
