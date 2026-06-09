# SPDX-FileCopyrightText: 2026 YoUniverse Astrology contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""gettext catalogs and language metadata."""

import gettext
import os

from astrology_app.paths import DATADIR

# gettext: native language labels and loaded catalogs per locale code
LANGUAGES_LABEL = {
			"ar":"الْعَرَبيّة",
			"pt_BR":"Português brasileiro",
			"bg":"български език",
			"ca":"català",
			"cs":"čeština",
			"da":"dansk",
			"nl":"Nederlands",
			"eo":"Esperanto",
			"en":"English",
			"fi":"suomi",
			"fr":"Français",
			"de":"Deutsch",
			"el":"ελληνικά",
			"hu":"magyar nyelv",
			"it":"Italiano",
			"ja":"日本",
			"nds":"Plattdüütsch",
			"nb":"Bokmål",
			"pl":"język polski",
			"rom":"rromani ćhib",
			"ru":"Русский",
			"es":"Español",
			"sv":"svenska",
            "uk":"українська мова",
            "zh_TW":"正體字"
		}

TDomain = os.path.join(DATADIR, 'locale')
LANGUAGES = list(LANGUAGES_LABEL.keys())
TRANSLATION = {}


def _load_translation(lang=None):
	"""Load gettext catalog for ``lang``, or English, or pass-through if missing."""
	try:
		if lang:
			return gettext.translation('astrology', TDomain, languages=[lang])
		return gettext.translation('astrology', TDomain)
	except (IOError, FileNotFoundError):
		pass
	try:
		return gettext.translation('astrology', TDomain, languages=['en'])
	except (IOError, FileNotFoundError):
		return gettext.NullTranslations()


for i in range(len(LANGUAGES)):
	TRANSLATION[LANGUAGES[i]] = _load_translation(LANGUAGES[i])

TRANSLATION['default'] = _load_translation()
