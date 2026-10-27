from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QTabBar, QVBoxLayout, QWidget

from views.page_journal import PageJournal
from views.page_parametres import PageParametres
from views.page_synthese import PageSynthese
from views.widgets import FondApplication, Logo, bouton

PAGES = ["Synthèse", "Journal", "Paramètres"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OdinFinance")
        self.resize(1320, 820)
        self.setMinimumSize(1080, 680)

        fond = FondApplication()
        self.setCentralWidget(fond)
        layout = QVBoxLayout(fond)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._creer_entete())

        self.pages = QStackedWidget()
        self.page_synthese = PageSynthese()
        self.page_journal = PageJournal()
        self.page_parametres = PageParametres()
        for page in (self.page_synthese, self.page_journal, self.page_parametres):
            self.pages.addWidget(page)
        layout.addWidget(self.pages, 1)
        self.navigation.currentChanged.connect(self.pages.setCurrentIndex)

        self.message_etat = QLabel()
        self.statusBar().addWidget(self.message_etat, 1)
        self.statusBar().setSizeGripEnabled(False)

        for i in range(len(PAGES)):
            QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self, activated=lambda i=i: self.navigation.setCurrentIndex(i))

    def _creer_entete(self) -> QWidget:
        entete = QWidget()
        entete.setObjectName("entete")
        entete.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ligne = QHBoxLayout(entete)
        ligne.setContentsMargins(24, 0, 16, 0)
        ligne.setSpacing(12)

        ligne.addWidget(Logo())
        ligne.addSpacing(20)
        self.navigation = QTabBar()
        self.navigation.setObjectName("navigation")
        self.navigation.setDrawBase(False)
        self.navigation.setExpanding(False)
        self.navigation.setUsesScrollButtons(False)
        for i, nom in enumerate(PAGES):
            self.navigation.addTab(nom)
            self.navigation.setTabToolTip(i, f"{nom} (Ctrl+{i + 1})")
        ligne.addWidget(self.navigation, 0, Qt.AlignmentFlag.AlignBottom)
        ligne.addStretch()

        self.label_exercice = QLabel()
        self.label_exercice.setObjectName("exercice_entete")
        ligne.addWidget(self.label_exercice)
        ligne.addSpacing(8)
        self.btn_theme = bouton("", "discret", "theme", "Changer de thème (Ctrl+T)")
        self.btn_exporter = bouton("Exporter le bilan", "primaire", "exporter",
                                   "Exporter le bilan financier de l'exercice au format Excel (Ctrl+E)")
        ligne.addWidget(self.btn_theme)
        ligne.addWidget(self.btn_exporter)
        return entete

    def afficher_message(self, texte: str):
        self.message_etat.setText(texte)

    def afficher_page(self, index: int):
        self.navigation.setCurrentIndex(index)
