# E.g. An Nguyen (ms.) 
PAREN_PATTERN = ['\([^\(\)]*\)']

# E.g. An Nguyen , ms.
COMMA_PATTERN = [',.*']

# E.g. a. phuc
abbre_uni_ptn = ['\w\.']

# Name Title

TITLE_TERM = [
    'mr.?',
    'master',
    'miss',
    'm.?s.?',
    'mrs.?',
    'mx',
    'sir',
    'sire',
    'mistress',
    'madam',
    "ma'am",
    'dame',
    'lady',
    'dr',
    'mba',
    'phd',
    'md',
    'do',
    'prof',
    'professor',
    'ci',
    'sci',
    'vice',
    'director',
    'chief',
    'principal',
    'president',
    'pca',
    'cpa',
    'dj',
    'doctor',
    'bsw',
    'msw',
    'ph[\. ]?d\.?',
    'bsee',
    'cissp',
    'bsc',
    'ssca',
    'll.?m.?',
    'mpa'
]

TITLE_PATTERN = COMMA_PATTERN + TITLE_TERM
