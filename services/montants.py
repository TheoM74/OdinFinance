"""Montants en centimes (entiers) : saisie et affichage au format français."""
from decimal import Decimal, InvalidOperation

ESPACE_INSECABLE = "\u00a0"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def _lire_decimal(texte: str) -> Decimal:
    nettoye = (texte or "").strip().replace("€", "").replace("−", "-")
    for espace in (" ", ESPACE_INSECABLE, "\u202f"):
        nettoye = nettoye.replace(espace, "")
    nettoye = nettoye.replace(",", ".")
    if not nettoye:
        raise ValueError("Saisissez un montant.")
    try:
        valeur = Decimal(nettoye)
    except InvalidOperation:
        raise ValueError("Montant illisible : utilisez des chiffres, par exemple 45,90.") from None
    if not valeur.is_finite():
        raise ValueError("Montant illisible : utilisez des chiffres, par exemple 45,90.")
    if valeur.as_tuple().exponent < -2:
        raise ValueError("Deux décimales au maximum (centimes).")
    if abs(valeur) >= Decimal("100000000"):
        raise ValueError("Montant trop élevé.")
    return valeur


def parser_montant(texte: str) -> int:
    """« 1 234,5 € » -> 123450. Lève ValueError avec un message lisible si la saisie est invalide."""
    valeur = _lire_decimal(texte)
    if valeur <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    return int(valeur * 100)


def parser_montant_signe(texte: str) -> int:
    """Comme parser_montant, mais un champ vide vaut zéro et les valeurs négatives sont admises (soldes)."""
    if not (texte or "").replace("€", "").strip():
        return 0
    return int(_lire_decimal(texte) * 100)


def formater_montant(centimes: int, signe: bool = False, symbole: bool = True) -> str:
    """123456 -> « 1 234,56 € ». signe=True ajoute « + » aux montants positifs."""
    negatif = centimes < 0
    euros, cents = divmod(abs(centimes), 100)
    entier = f"{euros:,}".replace(",", ESPACE_INSECABLE)
    texte = f"{entier},{cents:02d}"
    if negatif:
        texte = "−" + texte
    elif signe and centimes > 0:
        texte = "+" + texte
    return f"{texte}{ESPACE_INSECABLE}€" if symbole else texte


def formater_saisie(centimes: int) -> str:
    """Valeur remise dans un champ de saisie : « 1234,56 »."""
    signe = "-" if centimes < 0 else ""
    euros, cents = divmod(abs(centimes), 100)
    return f"{signe}{euros},{cents:02d}"


def nom_mois(annee: int, mois: int) -> str:
    return f"{MOIS[mois - 1]} {annee}"
