Hosting documentation
=====================

Read the Docs
-------------

HTML, PDF, and EPUB builds are configured via ``.readthedocs.yaml`` in the repository root.

**One-time setup**

1. Sign in at https://readthedocs.org with GitHub.
2. **Import a project** → select ``YOUR_ORG/astrology``.
3. Set the **Documentation type** to *Sphinx* and confirm the config file path: ``docs/conf.py``.
4. Optional: change the project **slug** (URL). Update the README badge if you change it.
5. Enable **Build pull requests** for doc preview on PRs.

**Local build** (same sources as RTD):

.. code-block:: bash

   make docs
   # open docs/_build/html/index.html

**Badge** (replace ``SLUG`` with your Read the Docs project slug):

.. code-block:: markdown

   [![Documentation](https://readthedocs.org/projects/SLUG/badge/?version=latest)](https://SLUG.readthedocs.io/en/latest/)

GitHub Discussions
------------------

Enable **Discussions** under repository **Settings → General → Features**.

Templates live in ``.github/DISCUSSION_TEMPLATE/``:

- **Q&A** — usage and development questions
- **Ideas** — feature suggestions
- **General** — community topics

Link in README: ``https://github.com/YOUR_ORG/astrology/discussions``

GitHub Sponsors
---------------

``/.github/FUNDING.yml`` links the **Sponsor** button to ``# github: YOUR_GITHUB_USERNAME``.

Enable Sponsors at https://github.com/sponsors and complete profile setup before publishing.

Signed releases
---------------

See :doc:`signing` for GPG setup. CI workflow ``verify-release.yml`` rejects unsigned ``v*`` tags.

REUSE / SPDX
------------

- ``REUSE.toml`` — REUSE 3 specification annotations
- ``LICENSES/`` — full license texts referenced by REUSE
- Source files carry ``SPDX-FileCopyrightText`` / ``SPDX-License-Identifier`` headers

Refresh headers after adding files:

.. code-block:: bash

   make spdx

Optional lint (install `reuse <https://reuse.software/>`_):

.. code-block:: bash

   make reuse-lint
