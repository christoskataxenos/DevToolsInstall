import os
import queue
import shutil
import subprocess
import threading
import webbrowser
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from SystemChecker import SystemSpecChecker
from SkillsManager import SkillsManager
from AIDiagnosticAgent import AIDiagnosticAgent

import tkinter as tk
from tkinter import ttk

"""
DevTools Installer - Developer Tools Management Application
==============================================================
Main Features:
- Tool installation via winget
- Settings backup and restore
- Predefined environment stacks (Python, React, C/Systems, etc.)
- Check for installed tools
- Export/Import selection to JSON

Author: Christos Kataxenos
Version: 2.1
"""

TOOL_STATUS = {
    "PENDING": "[ ]",
    "INSTALLED": "[OK]",
    "RUNNING": "[...]",
    "ERROR": "[ERR]",
}

TOOLS_REGISTRY: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {   'Browsers': {   'Google Chrome': {   'id': 'Google.Chrome',
                                         'url': 'https://www.google.com/chrome/',
                                         'note': {   'el': 'Ο πιο δημοφιλής '
                                                           'περιηγητής ιστού '
                                                           'από την Google.',
                                                     'en': 'The most popular '
                                                           'web browser from '
                                                           'Google.'}},
                    'Mozilla Firefox': {   'id': 'Mozilla.Firefox',
                                           'url': 'https://www.mozilla.org/firefox/',
                                           'note': {   'el': 'Περιηγητής ιστού '
                                                             'με έμφαση στην '
                                                             'ιδιωτικότητα και '
                                                             'τον ανοιχτό '
                                                             'κώδικα.',
                                                       'en': 'Web browser with '
                                                             'an emphasis on '
                                                             'privacy and open '
                                                             'source.'}},
                    'Brave Browser': {   'id': 'Brave.Brave',
                                         'url': 'https://brave.com/',
                                         'note': {   'el': 'Περιηγητής που '
                                                           'εστιάζει στην '
                                                           'ταχύτητα και τον '
                                                           'αποκλεισμό '
                                                           'διαφημίσεων.',
                                                     'en': 'Browser that '
                                                           'focuses on speed '
                                                           'and ad blocking.'}},
                    'Vivaldi Browser': {   'id': 'Vivaldi.Vivaldi',
                                           'url': 'https://vivaldi.com/',
                                           'note': {   'el': 'Ευρωπαϊκός '
                                                             'περιηγητής με '
                                                             'απαράμιλλη '
                                                             'δυνατότητα '
                                                             'παραμετροποίησης.',
                                                       'en': 'European browser '
                                                             'with '
                                                             'unparalleled '
                                                             'customization '
                                                             'capabilities.'}}},
    'Office & Documents': {   'Microsoft 365': {   'id': 'Microsoft.Office',
                                                   'url': 'https://www.office.com/',
                                                   'note': {   'el': 'Η σουίτα '
                                                                     'εφαρμογών '
                                                                     'γραφείου '
                                                                     'της '
                                                                     'Microsoft '
                                                                     '(Word, '
                                                                     'Excel, '
                                                                     'κλπ).',
                                                               'en': "Microsoft's "
                                                                     'office '
                                                                     'application '
                                                                     'suite '
                                                                     '(Word, '
                                                                     'Excel, '
                                                                     'etc.).'}},
                              'Apache OpenOffice': {   'id': 'Apache.OpenOffice',
                                                       'url': 'https://www.openoffice.org/',
                                                       'note': {   'el': 'Κλασική '
                                                                         'ανοιχτού '
                                                                         'κώδικα '
                                                                         'σουίτα '
                                                                         'εφαρμογών '
                                                                         'γραφείου.',
                                                                   'en': 'Classic '
                                                                         'open-source '
                                                                         'office '
                                                                         'suite.'}},
                              'LibreOffice': {   'id': 'TheDocumentFoundation.LibreOffice',
                                                 'url': 'https://www.libreoffice.org/',
                                                 'note': {   'el': 'Η πιο '
                                                                   'ισχυρή '
                                                                   'δωρεάν και '
                                                                   'ανοιχτού '
                                                                   'κώδικα '
                                                                   'σουίτα '
                                                                   'γραφείου.',
                                                             'en': 'The most '
                                                                   'powerful '
                                                                   'free and '
                                                                   'open-source '
                                                                   'office '
                                                                   'suite.'}},
                              'ONLYOFFICE': {   'id': 'ONLYOFFICE.DesktopEditors',
                                                'url': 'https://www.onlyoffice.com/',
                                                'note': {   'el': 'Ευρωπαϊκή '
                                                                  'σουίτα '
                                                                  'γραφείου με '
                                                                  'υψηλή '
                                                                  'συμβατότητα '
                                                                  'με αρχεία '
                                                                  'MS Office.',
                                                            'en': 'European '
                                                                  'office '
                                                                  'suite with '
                                                                  'high '
                                                                  'compatibility '
                                                                  'with MS '
                                                                  'Office '
                                                                  'files.'}}},
    'Communication': {   'Discord': {   'id': 'Discord.Discord',
                                        'url': 'https://discord.com/',
                                        'note': {   'el': 'Πλατφόρμα '
                                                          'επικοινωνίας για '
                                                          'κοινότητες και '
                                                          'gamers.',
                                                    'en': 'Communication '
                                                          'platform for '
                                                          'communities and '
                                                          'gamers.'}},
                         'WhatsApp': {   'id': 'WhatsApp.WhatsApp',
                                         'url': 'https://www.whatsapp.com/',
                                         'note': {   'el': 'Δημοφιλής εφαρμογή '
                                                           'για μηνύματα και '
                                                           'κλήσεις.',
                                                     'en': 'Popular messaging '
                                                           'and calling app.'}},
                         'Telegram': {   'id': 'Telegram.TelegramDesktop',
                                         'url': 'https://telegram.org/',
                                         'note': {   'el': 'Γρήγορη και '
                                                           'ασφαλής εφαρμογή '
                                                           'μηνυμάτων, '
                                                           'ευρωπαϊκής '
                                                           'προέλευσης.',
                                                     'en': 'Fast and secure '
                                                           'messaging app, of '
                                                           'European origin.'}},
                         'Element': {   'id': 'Element.Element',
                                        'url': 'https://element.io/',
                                        'note': {   'el': 'Ανοιχτού κώδικα '
                                                          'εφαρμογή '
                                                          'επικοινωνίας '
                                                          'βασισμένη στο '
                                                          'πρωτόκολλο Matrix.',
                                                    'en': 'Open-source '
                                                          'communication app '
                                                          'based on the Matrix '
                                                          'protocol.'}},
                         'Zoom': {   'id': 'Zoom.Zoom',
                                     'url': 'https://zoom.us/',
                                     'note': {   'el': 'Πλατφόρμα για '
                                                       'βιντεοκλήσεις και '
                                                       'τηλεδιασκέψεις.',
                                                 'en': 'Platform for video '
                                                       'calls and video '
                                                       'conferencing.'}},
                         'Webex': {   'id': 'Cisco.Webex',
                                      'url': 'https://www.webex.com/',
                                      'note': {   'el': 'Επαγγελματικό '
                                                        'εργαλείο για '
                                                        'συναντήσεις και '
                                                        'συνεργασία.',
                                                  'en': 'Professional tool for '
                                                        'meetings and '
                                                        'collaboration.'}},
                         'Slack': {   'id': 'SlackTechnologies.Slack',
                                      'url': 'https://slack.com/',
                                      'note': {   'el': 'Η standard εφαρμογή '
                                                        'επικοινωνίας για '
                                                        'ομάδες εργασίας.',
                                                  'en': 'The standard '
                                                        'communication app for '
                                                        'workgroups.'}},
                         'Viber': {   'id': 'Rakuten.Viber',
                                      'url': 'https://www.viber.com/',
                                      'note': {   'el': 'Δημοφιλής εφαρμογή '
                                                        'για δωρεάν μηνύματα '
                                                        'και κλήσεις '
                                                        'παγκοσμίως.',
                                                  'en': 'Popular app for free '
                                                        'messaging and calls '
                                                        'worldwide.'}}},
    'Media & Entertainment': {   'VLC media player': {   'id': 'VideoLAN.VLC',
                                                         'url': 'https://www.videolan.org/',
                                                         'note': {   'el': 'Universal '
                                                                           'player '
                                                                           'για '
                                                                           'κάθε '
                                                                           'είδους '
                                                                           'αρχείο '
                                                                           'βίντεο '
                                                                           'και '
                                                                           'ήχου.',
                                                                     'en': 'Universal '
                                                                           'player '
                                                                           'for '
                                                                           'all '
                                                                           'types '
                                                                           'of '
                                                                           'video '
                                                                           'and '
                                                                           'audio '
                                                                           'files.'}},
                                 'Spotify': {   'id': 'Spotify.Spotify',
                                                'url': 'https://www.spotify.com/',
                                                'note': {   'el': 'Η κορυφαία '
                                                                  'υπηρεσία '
                                                                  'streaming '
                                                                  'μουσικής.',
                                                            'en': 'The leading '
                                                                  'music '
                                                                  'streaming '
                                                                  'service.'}},
                                 'K-Lite Codec Pack': {   'id': 'CodecGuide.K-LiteCodecPack.Full',
                                                          'url': 'https://codecguide.com/',
                                                          'note': {   'el': 'Συλλογή '
                                                                            'από '
                                                                            'codecs '
                                                                            'για '
                                                                            'αναπαραγωγή '
                                                                            'οποιασδήποτε '
                                                                            'ταινίας.',
                                                                      'en': 'Collection '
                                                                            'of '
                                                                            'codecs '
                                                                            'for '
                                                                            'playing '
                                                                            'any '
                                                                            'video.'}},
                                 'Steam': {   'id': 'Valve.Steam',
                                              'url': 'https://store.steampowered.com/',
                                              'note': {   'el': 'Η μεγαλύτερη '
                                                                'πλατφόρμα '
                                                                'διανομής '
                                                                'παιχνιδιών.',
                                                          'en': 'The largest '
                                                                'game '
                                                                'distribution '
                                                                'platform.'}}},
    'System & Cloud': {   '7-Zip': {   'id': '7zip.7zip',
                                       'url': 'https://www.7-zip.org/',
                                       'note': {   'el': 'Κορυφαίο εργαλείο '
                                                         'για συμπίεση και '
                                                         'αποσυμπίεση αρχείων.',
                                                   'en': 'Top tool for file '
                                                         'compression and '
                                                         'extraction.'}},
                          'pCloud': {   'id': 'pCloudAG.pCloudDrive',
                                        'url': 'https://www.pcloud.com/',
                                        'note': {   'el': 'Ασφαλής ευρωπαϊκή '
                                                          'υπηρεσία cloud '
                                                          'storage (Ελβετία).',
                                                    'en': 'Secure European '
                                                          'cloud storage '
                                                          'service '
                                                          '(Switzerland).'}},
                          'Proton Drive': {   'id': 'Proton.ProtonDrive',
                                              'url': 'https://proton.me/drive',
                                              'note': {   'el': 'Πλήρως '
                                                                'κρυπτογραφημένο '
                                                                'cloud storage '
                                                                'από την '
                                                                'Proton '
                                                                '(Ελβετία).',
                                                          'en': 'Fully '
                                                                'encrypted '
                                                                'cloud storage '
                                                                'from Proton '
                                                                '(Switzerland).'}},
                          'Nextcloud Desktop': {   'id': 'Nextcloud.NextcloudDesktop',
                                                   'url': 'https://nextcloud.com/',
                                                   'note': {   'el': 'Ανοιχτού '
                                                                     'κώδικα '
                                                                     'πλατφόρμα '
                                                                     'για '
                                                                     'προσωπικό '
                                                                     'cloud '
                                                                     'και '
                                                                     'συγχρονισμό.',
                                                               'en': 'Open-source '
                                                                     'platform '
                                                                     'for '
                                                                     'personal '
                                                                     'cloud '
                                                                     'and '
                                                                     'sync.'}},
                          'Google Earth Pro': {   'id': 'Google.EarthPro',
                                                  'url': 'https://www.google.com/earth/',
                                                  'note': {   'el': 'Εξερευνήστε '
                                                                    'τον κόσμο '
                                                                    'με '
                                                                    'τρισδιάστατες '
                                                                    'δορυφορικές '
                                                                    'εικόνες.',
                                                              'en': 'Explore '
                                                                    'the world '
                                                                    'with 3D '
                                                                    'satellite '
                                                                    'imagery.'}},
                          'Everything': {   'id': 'voidtools.Everything',
                                            'url': 'https://www.voidtools.com/',
                                            'note': {   'el': 'Άμεση αναζήτηση '
                                                              'αρχείων στο '
                                                              'σύστημα.',
                                                        'en': 'Instant file '
                                                              'search on the '
                                                              'system.'}},
                          'Sysinternals Suite': {   'id': 'Microsoft.SysinternalsSuite',
                                                    'url': 'https://learn.microsoft.com/en-us/sysinternals/',
                                                    'type': 'winget',
                                                    'note': {   'el': 'Η '
                                                                      'συλλογή '
                                                                      'εργαλείων '
                                                                      'της '
                                                                      'Microsoft '
                                                                      'για '
                                                                      'διαχείριση '
                                                                      'και '
                                                                      'debugging.',
                                                                'en': 'Microsoft '
                                                                      'utility '
                                                                      'collection '
                                                                      'for '
                                                                      'management '
                                                                      'and '
                                                                      'debugging.'}},
                          'CrystalDiskInfo': {   'id': 'CrystalDewWorld.CrystalDiskInfo',
                                                 'url': 'https://crystalmark.info/en/software/crystaldiskinfo/',
                                                 'type': 'winget',
                                                 'note': {   'el': 'Έλεγχος '
                                                                   'υγείας και '
                                                                   'θερμοκρασίας '
                                                                   'των '
                                                                   'δίσκων.',
                                                             'en': 'Disk '
                                                                   'health and '
                                                                   'temperature '
                                                                   'monitoring.'}},
                          'CPU-Z': {   'id': 'CPUID.CPU-Z',
                                       'url': 'https://www.cpuid.com/softwares/cpu-z.html',
                                       'type': 'winget',
                                       'note': {   'el': 'Λεπτομερείς '
                                                         'πληροφορίες για τον '
                                                         'επεξεργαστή και τη '
                                                         'μνήμη.',
                                                   'en': 'Detailed information '
                                                         'about CPU and '
                                                         'memory.'}},
                          'GPU-Z': {   'id': 'TechPowerUp.GPU-Z',
                                       'url': 'https://www.techpowerup.com/gpuz/',
                                       'type': 'winget',
                                       'note': {   'el': 'Λεπτομερείς '
                                                         'πληροφορίες για την '
                                                         'κάρτα γραφικών.',
                                                   'en': 'Detailed information '
                                                         'about the graphics '
                                                         'card.'}}},
    'Privacy & Security': {   'ProtonVPN': {   'id': 'Proton.ProtonVPN',
                                               'url': 'https://protonvpn.com/',
                                               'note': {   'el': 'Ασφαλές και '
                                                                 'γρήγορο VPN '
                                                                 'από την '
                                                                 'Proton.',
                                                           'en': 'Secure and '
                                                                 'fast VPN by '
                                                                 'Proton.'}},
                              'Proton Mail': {   'id': 'Proton.ProtonMail',
                                                 'url': 'https://proton.me/mail',
                                                 'note': {   'el': 'Η κορυφαία '
                                                                   'υπηρεσία '
                                                                   'κρυπτογραφημένου '
                                                                   'email '
                                                                   'παγκοσμίως.',
                                                             'en': 'The '
                                                                   'leading '
                                                                   'encrypted '
                                                                   'email '
                                                                   'service '
                                                                   'worldwide.'}}},
    'IDEs & Editors': {   'VS Code': {   'id': 'Microsoft.VisualStudioCode',
                                         'url': 'https://code.visualstudio.com/',
                                         'note': {   'el': 'Ο πιο δημοφιλής '
                                                           'open-source editor '
                                                           'από την Microsoft.',
                                                     'en': 'The most popular '
                                                           'open-source editor '
                                                           'from Microsoft.'}},
                          'VS Code Insiders': {   'id': 'Microsoft.VisualStudioCode.Insiders',
                                                  'url': 'https://code.visualstudio.com/insiders/',
                                                  'note': {   'el': 'Η έκδοση '
                                                                    'προεπισκόπησης '
                                                                    'του VS '
                                                                    'Code με '
                                                                    'νέες '
                                                                    'δυνατότητες.',
                                                              'en': 'Preview '
                                                                    'version '
                                                                    'of VS '
                                                                    'Code with '
                                                                    'new '
                                                                    'features.'}},
                          'PyCharm Community': {   'id': 'JetBrains.PyCharm.Community',
                                                   'url': 'https://www.jetbrains.com/pycharm/',
                                                   'note': {   'el': 'Πανίσχυρο '
                                                                     'IDE για '
                                                                     'Python '
                                                                     'ανάπτυξη.',
                                                               'en': 'Powerful '
                                                                     'IDE for '
                                                                     'Python '
                                                                     'development.'}},
                          'Android Studio': {   'id': 'Google.AndroidStudio',
                                                'url': 'https://developer.android.com/studio',
                                                'note': {   'el': 'Το επίσημο '
                                                                  'IDE για '
                                                                  'ανάπτυξη '
                                                                  'εφαρμογών '
                                                                  'Android.',
                                                            'en': 'The '
                                                                  'official '
                                                                  'IDE for '
                                                                  'Android app '
                                                                  'development.'}},
                          'Arduino IDE': {   'id': 'Arduino.IDE.2',
                                             'url': 'https://www.arduino.cc/en/software',
                                             'note': {   'el': 'Περιβάλλον '
                                                               'προγραμματισμού '
                                                               'για Arduino '
                                                               'και hardware.',
                                                         'en': 'Programming '
                                                               'environment '
                                                               'for Arduino '
                                                               'and '
                                                               'hardware.'}},
                          'Notepad++': {   'id': 'Notepad++.Notepad++',
                                           'url': 'https://notepad-plus-plus.org/',
                                           'note': {   'el': 'Ελαφρύς και '
                                                             'ταχύτατος text '
                                                             'editor.',
                                                       'en': 'Lightweight and '
                                                             'fast text '
                                                             'editor.'}},
                          'Dev-C++': {   'id': 'Embarcadero.Dev-CPP',
                                         'url': 'https://sourceforge.net/projects/orwelldevcpp/',
                                         'note': {   'el': 'Κλασικό IDE για '
                                                           'C/C++ (TDM-GCC).',
                                                     'en': 'Classic IDE for '
                                                           'C/C++ '
                                                           '(TDM-GCC).'}}},
    'Version Control': {   'Git': {   'id': 'Git.Git',
                                      'url': 'https://git-scm.com/',
                                      'note': {   'el': 'Το standard σύστημα '
                                                        'ελέγχου εκδόσεων.',
                                                  'en': 'The standard version '
                                                        'control system.'}},
                           'GitHub Desktop': {   'id': 'GitHub.GitHubDesktop',
                                                 'url': 'https://desktop.github.com/',
                                                 'note': {   'el': 'Γραφικό '
                                                                   'περιβάλλον '
                                                                   'για την '
                                                                   'διαχείριση '
                                                                   'Git repos.',
                                                             'en': 'Graphical '
                                                                   'user '
                                                                   'interface '
                                                                   'for '
                                                                   'managing '
                                                                   'Git '
                                                                   'repositories.'}},
                           'GitHub CLI (gh)': {   'id': 'GitHub.cli',
                                                  'url': 'https://cli.github.com/',
                                                  'note': {   'el': 'Εργαλείο '
                                                                    'γραμμής '
                                                                    'εντολών '
                                                                    'για το '
                                                                    'GitHub.',
                                                              'en': 'Command '
                                                                    'line tool '
                                                                    'for '
                                                                    'GitHub.'}},
                           'lazygit': {   'id': 'JesseDuffield.lazygit',
                                          'url': 'https://github.com/jesseduffield/lazygit',
                                          'note': {   'el': 'Τερματικό '
                                                            'περιβάλλον (TUI) '
                                                            'για Git.',
                                                      'en': 'Terminal user '
                                                            'interface (TUI) '
                                                            'for Git.'}},
                           'Git LFS': {   'id': 'GitHub.GitLFS',
                                          'url': 'https://git-lfs.github.com/',
                                          'note': {   'el': 'Διαχείριση '
                                                            'μεγάλων αρχείων '
                                                            'στο Git.',
                                                      'en': 'Large file '
                                                            'management in '
                                                            'Git.'}}},
    'Runtimes & Languages': {   'Node.js (LTS)': {   'id': 'OpenJS.NodeJS.LTS',
                                                     'url': 'https://nodejs.org/',
                                                     'note': {   'el': 'JavaScript '
                                                                       'runtime '
                                                                       'για '
                                                                       'server-side '
                                                                       'ανάπτυξη.',
                                                                 'en': 'JavaScript '
                                                                       'runtime '
                                                                       'for '
                                                                       'server-side '
                                                                       'development.'}},
                                'Python 3.14': {   'id': 'Python.Python.3.14',
                                                   'url': 'https://www.python.org/',
                                                   'note': {   'el': 'Η '
                                                                     'τελευταία '
                                                                     'έκδοση '
                                                                     'της '
                                                                     'γλώσσας '
                                                                     'Python.',
                                                               'en': 'The '
                                                                     'latest '
                                                                     'version '
                                                                     'of the '
                                                                     'Python '
                                                                     'language.'}},
                                'Go': {   'id': 'Google.Go',
                                          'url': 'https://go.dev/',
                                          'note': {   'el': 'Η γλώσσα '
                                                            'προγραμματισμού '
                                                            'της Google.',
                                                      'en': "Google's "
                                                            'programming '
                                                            'language.'}},
                                'TDM-GCC': {   'id': 'jmeubank.tdm-gcc',
                                               'url': 'https://jmeubank.github.io/tdm-gcc/',
                                               'note': {   'el': 'Compiler '
                                                                 'suite για '
                                                                 'C/C++ στα '
                                                                 'Windows.',
                                                           'en': 'Compiler '
                                                                 'suite for '
                                                                 'C/C++ on '
                                                                 'Windows.'}},
                                'MSYS2': {   'id': 'MSYS2.MSYS2',
                                             'url': 'https://www.msys2.org/',
                                             'note': {   'el': 'Περιβάλλον '
                                                               'Unix-like για '
                                                               'Windows '
                                                               'ανάπτυξη.',
                                                         'en': 'Unix-like '
                                                               'environment '
                                                               'for Windows '
                                                               'development.'}},
                                'Rust (rustup)': {   'id': 'Rustlang.Rustup',
                                                     'url': 'https://rustup.rs/',
                                                     'note': {   'el': 'Installer '
                                                                       'για '
                                                                       'την '
                                                                       'γλώσσα '
                                                                       'Rust.',
                                                                 'en': 'Installer '
                                                                       'for '
                                                                       'the '
                                                                       'Rust '
                                                                       'language.'}},
                                'Zig': {   'id': 'zig.zig',
                                           'url': 'https://ziglang.org/',
                                           'note': {   'el': 'Σύγχρονη και '
                                                             'ασφαλής γλώσσα '
                                                             'επιπέδου '
                                                             'συστήματος.',
                                                       'en': 'Modern and safe '
                                                             'systems '
                                                             'language.'}},
                                'Bun': {   'id': 'Oven-sh.Bun',
                                           'url': 'https://bun.sh/',
                                           'note': {   'el': 'Ταχύτατο '
                                                             'JavaScript '
                                                             'runtime & '
                                                             'package manager.',
                                                       'en': 'Extremely fast '
                                                             'JavaScript '
                                                             'runtime & '
                                                             'package '
                                                             'manager.'}},
                                'Deno': {   'id': 'DenoLand.Deno',
                                            'url': 'https://deno.land/',
                                            'note': {   'el': 'Ασφαλές runtime '
                                                              'για JavaScript '
                                                              'και TypeScript.',
                                                        'en': 'Secure runtime '
                                                              'for JavaScript '
                                                              'and '
                                                              'TypeScript.'}},
                                'Java 21 (Temurin)': {   'id': 'EclipseAdoptium.Temurin.21.JDK',
                                                         'url': 'https://adoptium.net/',
                                                         'note': {   'el': 'Open '
                                                                           'source '
                                                                           'διανομή '
                                                                           'της '
                                                                           'Java '
                                                                           '(JDK).',
                                                                     'en': 'Open '
                                                                           'source '
                                                                           'distribution '
                                                                           'of '
                                                                           'Java '
                                                                           '(JDK).'}},
                                'pyenv-win': {   'id': 'pyenv.pyenv',
                                                 'url': 'https://github.com/pyenv-win/pyenv-win',
                                                 'type': 'winget',
                                                 'note': {   'el': 'Διαχείριση '
                                                                   'πολλαπλών '
                                                                   'εκδόσεων '
                                                                   'Python στα '
                                                                   'Windows.',
                                                             'en': 'Manage '
                                                                   'multiple '
                                                                   'Python '
                                                                   'versions '
                                                                   'on '
                                                                   'Windows.'}},
                                'Miniconda3': {   'id': 'Anaconda.Miniconda3',
                                                  'url': 'https://docs.conda.io/en/latest/miniconda.html',
                                                  'type': 'winget',
                                                  'note': {   'el': 'Διαχειριστής '
                                                                    'περιβαλλόντων '
                                                                    'Python '
                                                                    'για AI '
                                                                    'και Data '
                                                                    'Science.',
                                                              'en': 'Python '
                                                                    'environment '
                                                                    'manager '
                                                                    'for AI '
                                                                    'and Data '
                                                                    'Science.'}},
                                'Java 17 (Temurin)': {   'id': 'EclipseAdoptium.Temurin.17.JDK',
                                                         'url': 'https://adoptium.net/',
                                                         'type': 'winget',
                                                         'note': {   'el': 'Η '
                                                                           'έκδοση '
                                                                           'LTS '
                                                                           '17 '
                                                                           'της '
                                                                           'Java '
                                                                           '(JDK).',
                                                                     'en': 'Java '
                                                                           'JDK '
                                                                           'LTS '
                                                                           'version '
                                                                           '17.'}}},
    'Package Managers': {   'Chocolatey': {   'id': 'Chocolatey.Chocolatey',
                                              'url': 'https://chocolatey.org/',
                                              'note': {   'el': 'Package '
                                                                'manager για '
                                                                'Windows '
                                                                'παρόμοιο με '
                                                                'το apt.',
                                                          'en': 'Package '
                                                                'manager for '
                                                                'Windows '
                                                                'similar to '
                                                                'apt.'}},
                            'uv (Fast Python)': {   'id': 'astral-sh.uv',
                                                    'url': 'https://github.com/astral-sh/uv',
                                                    'note': {   'el': 'Ταχύτατος '
                                                                      'Python '
                                                                      'package '
                                                                      '& '
                                                                      'project '
                                                                      'manager.',
                                                                'en': 'Extremely '
                                                                      'fast '
                                                                      'Python '
                                                                      'package '
                                                                      '& '
                                                                      'project '
                                                                      'manager.'}},
                            'pnpm': {   'id': 'pnpm.pnpm',
                                        'url': 'https://pnpm.io/',
                                        'note': {   'el': 'Αποδοτικός Node '
                                                          'package manager με '
                                                          'symlinks.',
                                                    'en': 'Efficient Node '
                                                          'package manager '
                                                          'using symlinks.'}},
                            'Poetry': {   'id': 'poetry',
                                          'url': 'https://python-poetry.org/',
                                          'type': 'powershell',
                                          'install_command': 'pipx install '
                                                             'poetry',
                                          'note': {   'el': 'Σύγχρονος python '
                                                            'package manager '
                                                            'και dependency '
                                                            'resolver.',
                                                      'en': 'Modern Python '
                                                            'package manager '
                                                            'and dependency '
                                                            'resolver.'}}},
    'Database Tools': {   'DB Browser (SQLite)': {   'id': 'DBBrowserForSQLite.DBBrowserForSQLite',
                                                     'url': 'https://sqlitebrowser.org/',
                                                     'note': {   'el': 'Γραφικό '
                                                                       'περιβάλλον '
                                                                       'για '
                                                                       'βάσεις '
                                                                       'δεδομένων '
                                                                       'SQLite.',
                                                                 'en': 'Graphical '
                                                                       'interface '
                                                                       'for '
                                                                       'SQLite '
                                                                       'databases.'}},
                          'DBeaver Community': {   'id': 'dbeaver.dbeaver',
                                                   'url': 'https://dbeaver.io/',
                                                   'note': {   'el': 'Universal '
                                                                     'database '
                                                                     'manager '
                                                                     'για όλες '
                                                                     'τις '
                                                                     'βάσεις.',
                                                               'en': 'Universal '
                                                                     'database '
                                                                     'manager '
                                                                     'for all '
                                                                     'databases.'}}},
    'Virtualization': {   'Docker Desktop': {   'id': 'Docker.DockerDesktop',
                                                'url': 'https://www.docker.com/',
                                                'note': {   'el': 'Διαχείριση '
                                                                  'containers '
                                                                  'για '
                                                                  'ανάπτυξη '
                                                                  'εφαρμογών.',
                                                            'en': 'Container '
                                                                  'management '
                                                                  'for '
                                                                  'application '
                                                                  'development.'},
                                                'requirements': {   'min_ram_gb': 8,
                                                                    'min_disk_gb': 20}},
                          'VMware Player': {   'id': 'VMware.WorkstationPlayer',
                                               'url': 'https://www.vmware.com/',
                                               'note': {   'el': 'Δωρεάν '
                                                                 'virtualization '
                                                                 'για εκτέλεση '
                                                                 'εικονικών '
                                                                 'μηχανών.',
                                                           'en': 'Free '
                                                                 'virtualization '
                                                                 'for running '
                                                                 'virtual '
                                                                 'machines.'}},
                          'WSL': {   'id': 'Microsoft.WSL',
                                     'url': 'https://learn.microsoft.com/en-us/windows/wsl/',
                                     'note': {   'el': 'Υποσύστημα Linux μέσα '
                                                       'στα Windows.',
                                                 'en': 'Linux subsystem inside '
                                                       'Windows.'}},
                          'Ubuntu (WSL)': {   'id': 'Canonical.Ubuntu',
                                              'url': 'https://ubuntu.com/wsl',
                                              'type': 'winget',
                                              'note': {   'el': 'Η επίσημη '
                                                                'διανομή '
                                                                'Ubuntu Linux '
                                                                'για το WSL.',
                                                          'en': 'The official '
                                                                'Ubuntu Linux '
                                                                'distribution '
                                                                'for WSL.'}},
                          'LxRunOffline': {   'id': 'DmitrySokolyuk.LxRunOffline',
                                              'url': 'https://github.com/DmitrySokolyuk/LxRunOffline',
                                              'type': 'winget',
                                              'note': {   'el': 'Ένας '
                                                                'πανίσχυρος '
                                                                'WSL manager '
                                                                'για backups '
                                                                'και μεταφορές '
                                                                'διανομών.',
                                                          'en': 'A powerful '
                                                                'WSL manager '
                                                                'for backups '
                                                                'and distro '
                                                                'migrations.'}}},
    'Hardware & AI': {   'Raspberry Pi Imager': {   'id': 'RaspberryPi.RaspberryPiImager',
                                                    'url': 'https://www.raspberrypi.com/software/',
                                                    'note': {   'el': 'Εργαλείο '
                                                                      'εγγραφής '
                                                                      'OS σε '
                                                                      'SD '
                                                                      'κάρτες '
                                                                      'για '
                                                                      'Raspberry '
                                                                      'Pi.',
                                                                'en': 'OS '
                                                                      'writing '
                                                                      'tool to '
                                                                      'SD '
                                                                      'cards '
                                                                      'for '
                                                                      'Raspberry '
                                                                      'Pi.'}},
                         'Logisim Evolution': {   'id': 'Logisim-Evolution.Logisim-Evolution',
                                                  'url': 'https://github.com/logisim-evolution/logisim-evolution',
                                                  'note': {   'el': 'Προσομοιωτής '
                                                                    'ψηφιακών '
                                                                    'κυκλωμάτων.',
                                                              'en': 'Digital '
                                                                    'circuit '
                                                                    'simulator.'}},
                         'LM Studio': {   'id': 'LMStudio.LMStudio',
                                          'url': 'https://lmstudio.ai/',
                                          'note': {   'el': 'Τοπική εκτέλεση '
                                                            'μεγάλων γλωσσικών '
                                                            'μοντέλων (LLMs).',
                                                      'en': 'Run LLMs '
                                                            'locally.'},
                                          'requirements': {   'min_ram_gb': 8,
                                                              'requires_gpu': True}},
                         'Ollama': {   'id': 'Ollama.Ollama',
                                       'url': 'https://ollama.com/',
                                       'type': 'winget',
                                       'requirements': {   'min_ram_gb': 8,
                                                           'min_disk_gb': 10,
                                                           'requires_gpu': True},
                                       'note': {   'el': 'Τοπική εκτέλεση '
                                                         'μεγάλων γλωσσικών '
                                                         'μοντέλων (LLMs).',
                                                   'en': 'Run LLMs locally.'}},
                         'Open WebUI': {   'id': 'open-webui',
                                           'url': 'https://github.com/open-webui/open-webui',
                                           'type': 'powershell',
                                           'install_command': 'pip install '
                                                              'open-webui',
                                           'requirements': {'min_ram_gb': 8},
                                           'note': {   'el': 'ChatGPT-like Web '
                                                             'UI για το '
                                                             'Ollama.',
                                                       'en': 'ChatGPT-like Web '
                                                             'UI for Ollama.'}},
                         'Hugging Face CLI': {   'id': 'huggingface-cli',
                                                 'url': 'https://huggingface.co/docs/huggingface_hub/guides/cli',
                                                 'type': 'powershell',
                                                 'install_command': 'pip '
                                                                    'install '
                                                                    'huggingface_hub[cli]',
                                                 'note': {   'el': 'Εργαλείο '
                                                                   'γραμμής '
                                                                   'εντολών '
                                                                   'για λήψη '
                                                                   'μοντέλων '
                                                                   'και '
                                                                   'datasets.',
                                                             'en': 'Command '
                                                                   'line tool '
                                                                   'for '
                                                                   'downloading '
                                                                   'models and '
                                                                   'datasets.'}}},
    'System & Shell': {   'Windows Terminal': {   'id': 'Microsoft.WindowsTerminal',
                                                  'url': 'https://aka.ms/terminal',
                                                  'note': {   'el': 'Σύγχρονο '
                                                                    'τερματικό '
                                                                    'για '
                                                                    'command '
                                                                    'line '
                                                                    'εργαλεία.',
                                                              'en': 'Modern '
                                                                    'terminal '
                                                                    'for '
                                                                    'command '
                                                                    'line '
                                                                    'tools.'}},
                          'Oh My Posh': {   'id': 'JanDeDobbeleer.OhMyPosh',
                                            'url': 'https://ohmyposh.dev/',
                                            'note': {   'el': 'Engine για '
                                                              'πανέμορφα '
                                                              'prompt στα '
                                                              'shells.',
                                                        'en': 'Engine for '
                                                              'beautiful shell '
                                                              'prompts.'}},
                          'zoxide': {   'id': 'ajeetdsouza.zoxide',
                                        'url': 'https://github.com/ajeetdsouza/zoxide',
                                        'note': {   'el': 'Έξυπνη εντολή cd '
                                                          'που μαθαίνει τις '
                                                          'συνήθειές σας.',
                                                    'en': 'Smart cd command '
                                                          'that learns your '
                                                          'habits.'}},
                          'PowerShell 7': {   'id': 'Microsoft.PowerShell',
                                              'url': 'https://github.com/PowerShell/PowerShell',
                                              'note': {   'el': 'Η τελευταία '
                                                                'έκδοση του '
                                                                'PowerShell.',
                                                          'en': 'The latest '
                                                                'version of '
                                                                'PowerShell.'}},
                          'PuTTY': {   'id': 'PuTTY.PuTTY',
                                       'url': 'https://www.putty.org/',
                                       'note': {   'el': 'SSH και Telnet '
                                                         'client για Windows.',
                                                   'en': 'SSH and Telnet '
                                                         'client for '
                                                         'Windows.'}},
                          'fastfetch': {   'id': 'fastfetch-cli.fastfetch',
                                           'url': 'https://github.com/fastfetch-cli/fastfetch',
                                           'note': {   'el': 'Εργαλείο '
                                                             'πληροφοριών '
                                                             'συστήματος.',
                                                       'en': 'System '
                                                             'information '
                                                             'tool.'}},
                          'FileZilla': {   'id': 'FileZilla.FileZilla',
                                           'url': 'https://filezilla-project.org/',
                                           'note': {   'el': 'Κλασικός '
                                                             'FTP/SFTP client.',
                                                       'en': 'Classic FTP/SFTP '
                                                             'client.'}},
                          'Warp Terminal': {   'id': 'Warp.Warp',
                                               'url': 'https://www.warp.dev/',
                                               'note': {   'el': 'Σύγχρονο '
                                                                 'AI-powered '
                                                                 'τερματικό.',
                                                           'en': 'Modern '
                                                                 'AI-powered '
                                                                 'terminal.'}},
                          'Starship Prompt': {   'id': 'Starship.Starship',
                                                 'url': 'https://starship.rs/',
                                                 'note': {   'el': 'Customizable '
                                                                   'και '
                                                                   'γρήγορο '
                                                                   'shell '
                                                                   'prompt.',
                                                             'en': 'Customizable '
                                                                   'and fast '
                                                                   'shell '
                                                                   'prompt.'}},
                          'bat': {   'id': 'sharkdp.bat',
                                     'url': 'https://github.com/sharkdp/bat',
                                     'note': {   'el': 'Βελτιωμένη έκδοση της '
                                                       'εντολής cat με syntax '
                                                       'highlighting.',
                                                 'en': 'Improved version of '
                                                       'the cat command with '
                                                       'syntax highlighting.'}},
                          'ripgrep': {   'id': 'BurntSushi.ripgrep.MSVC',
                                         'url': 'https://github.com/BurntSushi/ripgrep',
                                         'note': {   'el': 'Ταχύτατη αναζήτηση '
                                                           'κειμένου σε '
                                                           'αρχεία.',
                                                     'en': 'Blazing fast text '
                                                           'search within '
                                                           'files.'}},
                          'fd': {   'id': 'sharkdp.fd',
                                    'url': 'https://github.com/sharkdp/fd',
                                    'note': {   'el': 'Γρήγορη και φιλική '
                                                      'εναλλακτική της εντολής '
                                                      'find.',
                                                'en': 'Fast and user-friendly '
                                                      'alternative to the find '
                                                      'command.'}},
                          'fzf': {   'id': 'junegunn.fzf',
                                     'url': 'https://github.com/junegunn/fzf',
                                     'note': {   'el': 'Fuzzy finder για την '
                                                       'γραμμή εντολών.',
                                                 'en': 'Fuzzy finder for the '
                                                       'command line.'}},
                          'tldr': {   'id': 'tldr-pages.tlrc',
                                      'url': 'https://tldr.sh/',
                                      'note': {   'el': 'Συνοπτικά help pages '
                                                        'για εντολές '
                                                        'τερματικού.',
                                                  'en': 'Concise help pages '
                                                        'for terminal '
                                                        'commands.'}}},
    'AI Coding Assistants': {   'Claude Code (CLI)': {   'id': 'Anthropic.ClaudeCode',
                                                         'url': 'https://claude.com/claude-code',
                                                         'note': {   'el': 'Agentic '
                                                                           'τερματικό '
                                                                           'για '
                                                                           'AI-assisted '
                                                                           'προγραμματισμό.',
                                                                     'en': 'Agentic '
                                                                           'terminal '
                                                                           'for '
                                                                           'AI-assisted '
                                                                           'programming.'}},
                                'Cursor IDE': {   'id': 'Anysphere.Cursor',
                                                  'url': 'https://cursor.sh/',
                                                  'note': {   'el': 'AI-first '
                                                                    'editor, '
                                                                    'βασισμένος '
                                                                    'στον VS '
                                                                    'Code.',
                                                              'en': 'AI-first '
                                                                    'editor '
                                                                    'based on '
                                                                    'VS '
                                                                    'Code.'}},
                                'Windsurf IDE': {   'id': 'Codeium.Windsurf',
                                                    'url': 'https://codeium.com/windsurf',
                                                    'note': {   'el': 'Agentic '
                                                                      'IDE από '
                                                                      'την '
                                                                      'ομάδα '
                                                                      'του '
                                                                      'Codeium.',
                                                                'en': 'Agentic '
                                                                      'IDE by '
                                                                      'the '
                                                                      'Codeium '
                                                                      'team.'}},
                                'OpenCode': {   'id': 'SST.opencode',
                                                'url': 'https://opencode.ai/',
                                                'note': {   'el': 'AI coding '
                                                                  'agent για '
                                                                  'το '
                                                                  'τερματικό.',
                                                            'en': 'AI coding '
                                                                  'agent for '
                                                                  'the '
                                                                  'terminal.'}},
                                'Gemini CLI': {   'id': 'npm install -g '
                                                        '@google/gemini-cli',
                                                  'url': 'https://github.com/google/gemini-cli',
                                                  'note': {   'el': 'CLI για '
                                                                    'το '
                                                                    'μοντέλο '
                                                                    'Gemini '
                                                                    'της '
                                                                    'Google.',
                                                              'en': 'CLI for '
                                                                    "Google's "
                                                                    'Gemini '
                                                                    'model.'}},
                                'GitHub Copilot': {   'id': 'gh extension '
                                                            'install '
                                                            'github/gh-copilot',
                                                      'url': 'https://github.com/github/copilot-cli',
                                                      'note': {   'el': 'Extension '
                                                                        'για '
                                                                        'το '
                                                                        'GitHub '
                                                                        'CLI.',
                                                                  'en': 'Extension '
                                                                        'for '
                                                                        'GitHub '
                                                                        'CLI.'}},
                                'Antigravity': {   'id': 'Google.Antigravity',
                                                   'url': 'https://antigravity.google/download',
                                                   'note': {   'el': 'Η '
                                                                     'agent-first '
                                                                     'πλατφόρμα '
                                                                     'ανάπτυξης '
                                                                     'της '
                                                                     'Google '
                                                                     'για AI '
                                                                     'coding.',
                                                               'en': "Google's "
                                                                     'agent-first '
                                                                     'development '
                                                                     'platform '
                                                                     'for AI '
                                                                     'coding.'}}},
    'Productivity': {   'PowerToys': {   'id': 'Microsoft.PowerToys',
                                         'url': 'https://aka.ms/powertoys',
                                         'note': {   'el': 'Χρήσιμα utilities '
                                                           'για Windows power '
                                                           'users.',
                                                     'en': 'Useful utilities '
                                                           'for Windows power '
                                                           'users.'}},
                        'Fira Code Font': {   'id': 'SoftwareDesign.FiraCode',
                                              'url': 'https://github.com/tonsky/FiraCode',
                                              'note': {   'el': 'Γραμματοσειρά '
                                                                'με '
                                                                'προγραμματιστικά '
                                                                'ligatures.',
                                                          'en': 'Font with '
                                                                'programming '
                                                                'ligatures.'}},
                        'Notion': {   'id': 'Notion.Notion',
                                      'url': 'https://www.notion.so/',
                                      'note': {   'el': 'Πλατφόρμα οργάνωσης '
                                                        'σημειώσεων και tasks.',
                                                  'en': 'Platform for '
                                                        'organizing notes and '
                                                        'tasks.'}},
                        'Obsidian': {   'id': 'Obsidian.Obsidian',
                                        'url': 'https://obsidian.md/',
                                        'note': {   'el': 'Εργαλείο '
                                                          'διαχείρισης γνώσης '
                                                          'με Markdown.',
                                                    'en': 'Knowledge '
                                                          'management tool '
                                                          'using Markdown.'}},
                        'Flameshot': {   'id': 'Flameshot.Flameshot',
                                         'url': 'https://flameshot.org/',
                                         'note': {   'el': 'Ευέλικτο εργαλείο '
                                                           'για screenshots.',
                                                     'en': 'Flexible tool for '
                                                           'screenshots.'}},
                        'Greenshot': {   'id': 'Greenshot.Greenshot',
                                         'url': 'https://getgreenshot.org/',
                                         'note': {   'el': 'Ελαφρύ και ισχυρό '
                                                           'εργαλείο για λήψη '
                                                           'και επεξεργασία '
                                                           'screenshots.',
                                                     'en': 'Lightweight and '
                                                           'powerful tool for '
                                                           'capturing and '
                                                           'editing '
                                                           'screenshots.'}}},
    'Remote': {   'AnyDesk': {   'id': 'AnyDeskSoftwareGmbH.AnyDesk',
                                 'url': 'https://anydesk.com/',
                                 'note': {   'el': 'Εφαρμογή απομακρυσμένης '
                                                   'επιφάνειας εργασίας.',
                                             'en': 'Remote desktop '
                                                   'application.'}},
                  'RealVNC Viewer': {   'id': 'RealVNC.VNCViewer',
                                        'url': 'https://www.realvnc.com/',
                                        'note': {   'el': 'Viewer για '
                                                          'συνδέσεις VNC.',
                                                    'en': 'Viewer for VNC '
                                                          'connections.'}},
                  'RustDesk': {   'id': 'RustDesk.RustDesk',
                                  'url': 'https://rustdesk.com/',
                                  'note': {   'el': 'Open source εναλλακτική '
                                                    'του AnyDesk/TeamViewer.',
                                              'en': 'Open source alternative '
                                                    'to AnyDesk/TeamViewer.'}},
                  'TeamViewer': {   'id': 'TeamViewer.TeamViewer',
                                    'url': 'https://www.teamviewer.com/',
                                    'note': {   'el': 'Επαγγελματική '
                                                      'απομακρυσμένη πρόσβαση '
                                                      'και υποστήριξη.',
                                                'en': 'Professional remote '
                                                      'access and support.'}}},
    'Design & Media': {   'Figma': {   'id': 'Figma.Figma',
                                       'url': 'https://www.figma.com/',
                                       'note': {   'el': 'Εργαλείο design για '
                                                         'UI/UX επαγγελματίες.',
                                                   'en': 'Design tool for '
                                                         'UI/UX '
                                                         'professionals.'}},
                          'DaVinci Resolve': {   'id': 'BlackmagicDesign.DaVinciResolve',
                                                 'url': 'https://www.blackmagicdesign.com/',
                                                 'note': {   'el': 'Κορυφαίο '
                                                                   'πρόγραμμα '
                                                                   'video '
                                                                   'editing & '
                                                                   'color '
                                                                   'grading.',
                                                             'en': 'Industry-leading '
                                                                   'video '
                                                                   'editing & '
                                                                   'color '
                                                                   'grading '
                                                                   'program.'}},
                          'OBS Studio': {   'id': 'OBSProject.OBSStudio',
                                            'url': 'https://obsproject.com/',
                                            'note': {   'el': 'Λογισμικό για '
                                                              'live streaming '
                                                              'και εγγραφή '
                                                              'οθόνης.',
                                                        'en': 'Software for '
                                                              'live streaming '
                                                              'and screen '
                                                              'recording.'}},
                          'Adobe Cloud': {   'id': 'Adobe.CreativeCloud',
                                             'url': 'https://www.adobe.com/',
                                             'note': {   'el': 'Πρόσβαση στις '
                                                               'εφαρμογές της '
                                                               'Adobe '
                                                               '(Photoshop, '
                                                               'κλπ).',
                                                         'en': 'Access to '
                                                               'Adobe '
                                                               'applications '
                                                               '(Photoshop, '
                                                               'etc.).'}}},
    'C & Systems Dev': {   'CMake': {   'id': 'Kitware.CMake',
                                        'url': 'https://cmake.org/',
                                        'note': {   'el': 'Standard εργαλείο '
                                                          'build automation '
                                                          'για C/C++.',
                                                    'en': 'Standard build '
                                                          'automation tool for '
                                                          'C/C++.'}},
                           'Ninja': {   'id': 'ninja-build.ninja',
                                        'url': 'https://ninja-build.org/',
                                        'note': {   'el': 'Ταχύτατο build '
                                                          'system με έμφαση '
                                                          'στην ταχύτητα.',
                                                    'en': 'Blazing fast build '
                                                          'system focusing on '
                                                          'speed.'}},
                           'LLVM / Clang': {   'id': 'LLVM.LLVM',
                                               'url': 'https://llvm.org/',
                                               'note': {   'el': 'Σύγχρονο '
                                                                 'compiler '
                                                                 'infrastructure.',
                                                           'en': 'Modern '
                                                                 'compiler '
                                                                 'infrastructure.'}},
                           'Make (GnuWin32)': {   'id': 'GnuWin32.Make',
                                                  'url': 'http://gnuwin32.sourceforge.net/',
                                                  'note': {   'el': 'Το '
                                                                    'κλασικό '
                                                                    'εργαλείο '
                                                                    'Make για '
                                                                    'Windows.',
                                                              'en': 'The '
                                                                    'classic '
                                                                    'Make tool '
                                                                    'for '
                                                                    'Windows.'}}},
    'API & Testing': {   'Postman': {   'id': 'Postman.Postman',
                                        'url': 'https://www.postman.com/',
                                        'note': {   'el': 'Η κορυφαία '
                                                          'πλατφόρμα για '
                                                          'ανάπτυξη και δοκιμή '
                                                          'APIs.',
                                                    'en': 'The leading '
                                                          'platform for API '
                                                          'development and '
                                                          'testing.'}},
                         'Bruno': {   'id': 'Bruno.Bruno',
                                      'url': 'https://www.usebruno.com/',
                                      'note': {   'el': 'Open-source, '
                                                        'local-first API '
                                                        'client (ελαφρύς).',
                                                  'en': 'Open-source, '
                                                        'local-first API '
                                                        'client '
                                                        '(lightweight).'}},
                         'Insomnia': {   'id': 'Insomnia.Insomnia',
                                         'url': 'https://insomnia.rest/',
                                         'note': {   'el': 'Σχεδιασμός και '
                                                           'δοκιμή REST, '
                                                           'GraphQL, gRPC '
                                                           'APIs.',
                                                     'en': 'Design and test '
                                                           'REST, GraphQL, '
                                                           'gRPC APIs.'}}},
    'Security & Networking': {   'Wireshark': {   'id': 'WiresharkFoundation.Wireshark',
                                                  'url': 'https://www.wireshark.org/',
                                                  'note': {   'el': 'Αναλυτής '
                                                                    'πακέτων '
                                                                    'δικτύου '
                                                                    '(packet '
                                                                    'sniffer).',
                                                              'en': 'Network '
                                                                    'packet '
                                                                    'analyzer '
                                                                    '(packet '
                                                                    'sniffer).'}},
                                 'Nmap': {   'id': 'Insecure.Nmap',
                                             'url': 'https://nmap.org/',
                                             'note': {   'el': 'Εργαλείο '
                                                               'ανακάλυψης '
                                                               'δικτύου και '
                                                               'ελέγχου '
                                                               'ασφαλείας.',
                                                         'en': 'Network '
                                                               'discovery and '
                                                               'security '
                                                               'auditing '
                                                               'tool.'}},
                                 'Burp Suite Community': {   'id': 'manual',
                                                             'url': 'https://portswigger.net/burp/communitydownload',
                                                             'note': {   'el': 'Manual '
                                                                               'λήψη: '
                                                                               'Εργαλείο '
                                                                               'ελέγχου '
                                                                               'ασφαλείας '
                                                                               'web '
                                                                               'εφαρμογών.',
                                                                         'en': 'Manual '
                                                                               'download: '
                                                                               'Web '
                                                                               'application '
                                                                               'security '
                                                                               'testing '
                                                                               'tool.'}}},
    'Cloud & DevOps': {   'Kubectl': {   'id': 'Kubernetes.kubectl',
                                         'url': 'https://kubernetes.io/docs/tasks/tools/',
                                         'note': {   'el': 'CLI για την '
                                                           'διαχείριση '
                                                           'clusters '
                                                           'Kubernetes.',
                                                     'en': 'CLI for managing '
                                                           'Kubernetes '
                                                           'clusters.'}},
                          'Terraform': {   'id': 'Hashicorp.Terraform',
                                           'url': 'https://www.terraform.io/',
                                           'note': {   'el': 'Infrastructure '
                                                             'as Code (IaC) '
                                                             'από την '
                                                             'HashiCorp.',
                                                       'en': 'Infrastructure '
                                                             'as Code (IaC) by '
                                                             'HashiCorp.'}},
                          'Azure CLI': {   'id': 'Microsoft.AzureCLI',
                                           'url': 'https://docs.microsoft.com/en-us/cli/azure/install-azure-cli',
                                           'note': {   'el': 'Εργαλείο γραμμής '
                                                             'εντολών για το '
                                                             'Microsoft Azure.',
                                                       'en': 'Command line '
                                                             'tool for '
                                                             'Microsoft '
                                                             'Azure.'}},
                          'Minikube': {   'id': 'Kubernetes.minikube',
                                          'url': 'https://minikube.sigs.k8s.io/',
                                          'type': 'winget',
                                          'requirements': {   'min_ram_gb': 6,
                                                              'min_disk_gb': 20},
                                          'note': {   'el': 'Τοπικό Kubernetes '
                                                            'cluster για '
                                                            'δοκιμές.',
                                                      'en': 'Local Kubernetes '
                                                            'cluster for '
                                                            'testing.'}},
                          'Helm CLI': {   'id': 'Helm.Helm',
                                          'url': 'https://helm.sh/',
                                          'type': 'winget',
                                          'note': {   'el': 'Ο package manager '
                                                            'για το '
                                                            'Kubernetes.',
                                                      'en': 'The package '
                                                            'manager for '
                                                            'Kubernetes.'}},
                          'AWS CLI': {   'id': 'Amazon.AWSCLI',
                                         'url': 'https://aws.amazon.com/cli/',
                                         'type': 'winget',
                                         'note': {   'el': 'Εργαλείο γραμμής '
                                                           'εντολών για το '
                                                           'Amazon Web '
                                                           'Services.',
                                                     'en': 'Command line tool '
                                                           'for Amazon Web '
                                                           'Services.'}}}}





STACKS = {
    "Fresh Windows Kit": [
        "Google Chrome",
        "7-Zip",
        "VLC media player",
        "Discord",
        "Spotify",
        "Microsoft 365",
        "WhatsApp",
        "Viber",
    ],
    "React / Web": [
        "Node.js (LTS)",
        "pnpm",
        "VS Code",
        "Git",
        "GitHub CLI (gh)",
        "Figma",
        "Windows Terminal",
    ],
    "Python / AI": [
        "Python 3.14",
        "uv (Fast Python)",
        "PyCharm Community",
        "Docker Desktop",
        "LM Studio",
    ],
    "Data Analysis": [
        "Python 3.14",
        "uv (Fast Python)",
        "DBeaver Community",
        "Git",
    ],
    "C / Systems": [
        "Git",
        "CMake",
        "Ninja",
        "LLVM / Clang",
        "Dev-C++",
        "MSYS2",
        "WSL",
        "Windows Terminal",
    ],
    "Core Utils": [
        "Git",
        "Windows Terminal",
        "Oh My Posh",
        "zoxide",
        "PowerToys",
        "Fira Code Font",
        "Everything",
    ],
    "AI Coding": [
        "Claude Code (CLI)",
        "Cursor IDE",
        "OpenCode",
        "Antigravity",
        "Git",
        "GitHub CLI (gh)",
        "Windows Terminal",
        "Python 3.14",
        "uv (Fast Python)",
    ],
    "Full Stack Web": [
        "Node.js (LTS)",
        "Bun",
        "pnpm",
        "VS Code",
        "Git",
        "GitHub CLI (gh)",
        "Docker Desktop",
        "Bruno",
        "Figma",
        "Windows Terminal",
    ],
    "DevOps / Cloud": [
        "Docker Desktop",
        "Kubectl",
        "Terraform",
        "Azure CLI",
        "Git",
        "Windows Terminal",
        "WSL",
    ],
}

SUPER_CATEGORIES = {
    "Dev & Languages": [
        "IDEs & Editors",
        "Runtimes & Languages",
        "Package Managers",
        "Version Control",
        "Hardware & AI",
        "AI Coding Assistants",
        "C & Systems Dev"
    ],
    "Web & Data": [
        "Browsers",
        "API & Testing",
        "Database Tools"
    ],
    "System & Shell": [
        "System & Cloud",
        "System & Shell",
        "Virtualization",
        "Cloud & DevOps",
        "Privacy & Security",
        "Security & Networking"
    ],
    "Productivity & Design": [
        "Productivity",
        "Design & Media",
        "Office & Documents",
        "Remote"
    ],
    "Media & Games": [
        "Media & Entertainment",
        "Communication"
    ]
}

BACKUP_PATHS: Dict[str, str] = {
    "VS Code Settings": os.path.join(os.environ.get("APPDATA", ""), "Code", "User"),
    "Gemini CLI / Antigravity Rules": os.path.join(os.path.expanduser("~"), ".gemini"),
    "Antigravity Settings": os.path.join(os.environ.get("APPDATA", ""), "Antigravity"),
    "Cursor Settings": os.path.join(os.environ.get("APPDATA", ""), "Cursor", "User"),
    "Windsurf Settings": os.path.join(
        os.environ.get("APPDATA", ""), "Windsurf", "User"
    ),
    "Warp Config": os.path.join(os.path.expanduser("~"), ".warp"),
}

BACKUP_EXCLUDE_DIRS = {
    "Cache",
    "cache",
    "node_modules",
    ".git",
    "Cache_Data",
    "chat-plans",
}

ANTIGRAVITY_EXTENSIONS_PATH = os.path.join(
    os.environ.get("APPDATA", ""), "Antigravity", "CachedExtensionVSIXs"
)


class TranslationManager:
    """
    Translation Manager - Central localization management
    ===================================================
    Supports runtime language switching (EN/EL)
    and easy string lookups.
    """

    _current_lang = "el"  # Default to Greek since the app originally was focused on Greek

    _strings = {
        "el": {
            "menu_header": "ΜΕΝΟΥ ΠΛΟΗΓΗΣΗΣ",
            "nav_install": "Εγκατάσταση Εργαλείων",
            "nav_stacks": "Πακέτα Stacks",
            "nav_backup_restore": "Backup & Επαναφορά",
            "filter_all": "Όλα",
            "filter_selected": "Επιλεγμένα",
            "filter_installed": "Εγκατεστημένα",
            "filter_pending": "Εκκρεμή",
            "app_title": "DevTools Installer v2.1",
            "Dark Mode": "Σκοτεινή Λειτουργία",
            "categories": "ΚΑΤΗΓΟΡΙΕΣ",
            "stacks": "ΠΑΚΕΤΑ (STACKS)",
            "backup": "Backup",
            "restore": "Επαναφορά",
            "status_ready": "Status: Έτοιμο",
            "status_completed": "Status: Ολοκληρώθηκε",
            "status_prefix": "Status: ",
            "search_placeholder": "Αναζήτηση...",
            "tool_management": "Διαχείριση Εργαλείων",
            "show_console": "Εμφάνιση Κονσόλας",
            "hide_console": "Απόκρυψη Κονσόλας",
            "select_all": "Επιλογή Όλων",
            "deselect_all": "Αποεπιλογή Όλων",
            "install_selected": "Εγκατάσταση Επιλεγμένων",
            "select_at_least_one": "[ΠΡΟΣΟΧΗ] Παρακαλώ επιλέξτε τουλάχιστον μία εφαρμογή.",
            "starting_install": "Έναρξη εγκατάστασης {count} εφαρμογών...",
            "install_starting_tool": "Έναρξη εγκατάστασης: {name}...",
            "install_completed": "Ολοκληρώθηκε: {name}",
            "install_error_code": "Σφάλμα (Κωδικός {code}): {name}",
            "install_error_exception": "Σφάλμα κατά την εγκατάσταση του {name}: {error}",
            "install_all_completed": "Όλες οι εγκαταστάσεις ολοκληρώθηκαν!",
            "backup_select_title": "Επιλογή Στοιχείων Backup",
            "backup_select_label": "Επιλέξτε στοιχεία για backup:",
            "backup_select_btn": "Backup Επιλεγμένων",
            "cancel": "Ακύρωση",
            "not_found": "(δεν βρέθηκε)",
            "backup_start": "Έναρξη Backup -> {target}",
            "backup_compressing": "  > Συμπίεση: {name}",
            "backup_compressing_antigravity": "  > Συμπίεση: Antigravity Extensions",
            "backup_success": "Το Backup ολοκληρώθηκε με επιτυχία!",
            "backup_error": "Σφάλμα στο Backup: {error}",
            "restore_select_title": "Επιλέξτε Backup ZIP",
            "restore_start": "Έναρξη Επαναφοράς από: {path}",
            "restore_extracting": "  > Εξαγωγή: {name}",
            "restore_extensions": "  > Επαναφορά επεκτάσεων VS Code...",
            "restore_extension_installing": "    > Εγκατάσταση: {ext}",
            "restore_antigravity": "  > Επαναφορά επεκτάσεων Antigravity...",
            "restore_antigravity_success": "    > Επαναφέρθηκε: {name}",
            "restore_success": "Η Επαναφορά ολοκληρώθηκε!",
            "restore_error": "Σφάλμα κατά την Επαναφορά: {error}",
            "export_no_selection": "Δεν έχουν επιλεγεί εργαλεία για εξαγωγή.",
            "export_title": "Εξαγωγή Επιλογής",
            "export_success": "Η εξαγωγή ολοκληρώθηκε: {path}",
            "export_error": "Σφάλμα εξαγωγής: {error}",
            "import_title": "Εισαγωγή Επιλογής",
            "import_success": "Εισήχθησαν {count} εργαλεία.",
            "import_error": "Σφάλμα εισαγωγής: {error}",
            "checking_installed": "Έλεγχος εγκατεστημένων εργαλείων...",
            "check_complete": "Ο έλεγχος ολοκληρώθηκε.",
            # Categories
            "Browsers": "Περιηγητές (Browsers)",
            "Office & Documents": "Γράφειο & Έγγραφα",
            "Communication": "Επικοινωνία",
            "Media & Entertainment": "Πολυμέσα & Ψυχαγωγία",
            "System & Cloud": "Σύστημα & Cloud",
            "Privacy & Security": "Ιδιωτικότητα & Ασφάλεια",
            "IDEs & Editors": "IDEs & Editors",
            "Version Control": "Έλεγχος Εκδόσεων (Git)",
            "Runtimes & Languages": "Runtimes & Γλώσσες",
            "Package Managers": "Package Managers",
            "Database Tools": "Εργαλεία Βάσεων Δεδομένων",
            "Virtualization": "Virtualization & Containers",
            "Hardware & AI": "Hardware & AI",
            "System & Shell": "Σύστημα & Shell",
            "AI Coding Assistants": "AI Coding Assistants",
            "Productivity": "Παραγωγικότητα",
            "Remote": "Απομακρυσμένη Πρόσβαση",
            "Design & Media": "Σχεδιασμός & Media",
            "C & Systems Dev": "C & Systems Dev",
            "API & Testing": "API & Testing",
            "Security & Networking": "Ασφάλεια & Δίκτυα",
            "Cloud & DevOps": "Cloud & DevOps",
            "nav_skills": "AI Agent Skills",
            "warning_requirements_title": "Προειδοποίηση Απαιτήσεων",
            "warning_requirements_msg": "Το σύστημά σας δεν πληροί τις ελάχιστες απαιτήσεις για το εργαλείο {name}.\n\nΑπαιτήσεις:\n{reasons}\n\nΕίστε σίγουροι ότι θέλετε να το επιλέξετε;",
            "skills_title": "Διαχείριση AI Skills & Prompts",
            "skills_repo_label": "GitHub Repository URL:",
            "skills_btn_download": "Λήψη / Συγχρονισμός",
            "skills_destination": "Προορισμός Εξαγωγής (Project):",
            "skills_btn_export": "Εξαγωγή στο Project",
            "skills_global_path": "Global Φάκελος: {path}",
            "skills_status_prefix": "Κατάσταση: {status}",
            "diag_title": "AI Διάγνωση Σφάλματος",
            "diag_btn_search": "Αναζήτηση Λύσης στο Web",
            "diag_btn_ollama": "Ανάλυση με Τοπικό AI (Ollama)",
            "diag_exec_fix": "Εκτέλεση Διόρθωσης",
            "diag_expl_label": "Εξήγηση Σφάλματος:",
            "diag_cmd_label": "Προτεινόμενη Εντολή:"
        },
        "en": {
            "menu_header": "NAVIGATION MENU",
            "nav_install": "Install Tools",
            "nav_stacks": "System Stacks",
            "nav_backup_restore": "Backup & Restore",
            "filter_all": "All",
            "filter_selected": "Selected",
            "filter_installed": "Installed",
            "filter_pending": "Pending",
            "app_title": "DevTools Installer v2.1",
            "Dark Mode": "Dark Mode",
            "categories": "CATEGORIES",
            "stacks": "STACKS",
            "backup": "Backup",
            "restore": "Restore",
            "status_ready": "Status: Ready",
            "status_completed": "Status: Completed",
            "status_prefix": "Status: ",
            "search_placeholder": "Search tools...",
            "tool_management": "Tool Management",
            "show_console": "Show Console",
            "hide_console": "Hide Console",
            "select_all": "Select All",
            "deselect_all": "Deselect All",
            "install_selected": "Install Selected",
            "select_at_least_one": "[WARNING] Please select at least one application.",
            "starting_install": "Starting installation of {count} applications...",
            "install_starting_tool": "Starting installation: {name}...",
            "install_completed": "Completed: {name}",
            "install_error_code": "Error (Code {code}): {name}",
            "install_error_exception": "Error installing {name}: {error}",
            "install_all_completed": "All installations completed!",
            "backup_select_title": "Select Backup Items",
            "backup_select_label": "Select items to backup:",
            "backup_select_btn": "Backup Selected",
            "cancel": "Cancel",
            "not_found": "(not found)",
            "backup_start": "Starting Backup -> {target}",
            "backup_compressing": "  > Compressing: {name}",
            "backup_compressing_antigravity": "  > Compressing: Antigravity Extensions",
            "backup_success": "Backup completed successfully!",
            "backup_error": "Backup Error: {error}",
            "restore_select_title": "Select Backup ZIP",
            "restore_start": "Starting Restore from: {path}",
            "restore_extracting": "  > Extracting: {name}",
            "restore_extensions": "  > Restoring VS Code extensions...",
            "restore_extension_installing": "    > Installing: {ext}",
            "restore_antigravity": "  > Restoring Antigravity extensions...",
            "restore_antigravity_success": "    > Restored: {name}",
            "restore_success": "Restore completed!",
            "restore_error": "Error during Restore: {error}",
            "export_no_selection": "No tools selected for export.",
            "export_title": "Export Selection",
            "export_success": "Export successful: {path}",
            "export_error": "Export error: {error}",
            "import_title": "Import Selection",
            "import_success": "Imported {count} tools.",
            "import_error": "Import error: {error}",
            "checking_installed": "Checking installed tools...",
            "check_complete": "Check complete.",
            # Categories
            "Browsers": "Browsers",
            "Office & Documents": "Office & Documents",
            "Communication": "Communication",
            "Media & Entertainment": "Media & Entertainment",
            "System & Cloud": "System & Cloud",
            "Privacy & Security": "Privacy & Security",
            "IDEs & Editors": "IDEs & Editors",
            "Version Control": "Version Control",
            "Runtimes & Languages": "Runtimes & Languages",
            "Package Managers": "Package Managers",
            "Database Tools": "Database Tools",
            "Virtualization": "Virtualization",
            "Hardware & AI": "Hardware & AI",
            "System & Shell": "System & Shell",
            "AI Coding Assistants": "AI Coding Assistants",
            "Productivity": "Productivity",
            "Remote": "Remote",
            "Design & Media": "Design & Media",
            "C & Systems Dev": "C & Systems Dev",
            "API & Testing": "API & Testing",
            "Security & Networking": "Security & Networking",
            "Cloud & DevOps": "Cloud & DevOps",
            "nav_skills": "AI Agent Skills",
            "warning_requirements_title": "Requirements Warning",
            "warning_requirements_msg": "Your system does not meet the minimum requirements for {name}.\n\nRequirements:\n{reasons}\n\nAre you sure you want to select it?",
            "skills_title": "AI Agent Skills & Prompts",
            "skills_repo_label": "GitHub Repository URL:",
            "skills_btn_download": "Download / Sync",
            "skills_destination": "Export Destination (Project):",
            "skills_btn_export": "Export to Project",
            "skills_global_path": "Global Directory: {path}",
            "skills_status_prefix": "Status: {status}",
            "diag_title": "AI Error Diagnosis",
            "diag_btn_search": "Search Solution on Web",
            "diag_btn_ollama": "Analyze with Local AI (Ollama)",
            "diag_exec_fix": "Execute Fix",
            "diag_expl_label": "Error Explanation:",
            "diag_cmd_label": "Proposed Command:"
        }
    }

    @classmethod
    def set_language(cls, lang: str):
        if lang in cls._strings:
            cls._current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def translate(cls, key: str, **kwargs) -> str:
        text = cls._strings[cls._current_lang].get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text


def _(key: str, **kwargs) -> str:
    return TranslationManager.translate(key, **kwargs)


# Κλάση LanguageSwitcher για εναλλαγή γλώσσας (EN / ΕΛ) στο sidebar
class LanguageSwitcher(tk.Frame):
    def __init__(self, parent, on_change, **kwargs):
        # Αρχικοποίηση του frame με το χρώμα φόντου του sidebar.
        bg_color = kwargs.pop("bg", COLORS["sidebar_bg"])
        super().__init__(parent, bg = bg_color, **kwargs)
        self.on_change = on_change

        # Container με λεπτό περίγραμμα (border) για τα δύο κουμπιά.
        self.container = tk.Frame(self, bg = COLORS["border"], padx = 1, pady = 1)
        self.container.pack(pady = 5, fill = "x", expand = True)

        # Ρύθμιση ισομερούς κατανομής στηλών.
        self.container.columnconfigure(0, weight = 1)
        self.container.columnconfigure(1, weight = 1)

        # Κουμπί για Αγγλικά (EN).
        self.en_btn = tk.Label(
            self.container,
            text = "EN",
            font = ("Segoe UI", 9, "bold"),
            pady = 6,
            cursor = "hand2"
        )
        self.en_btn.grid(row = 0, column = 0, sticky = "ew")

        # Κουμπί για Ελληνικά (ΕΛ).
        self.el_btn = tk.Label(
            self.container,
            text = "ΕΛ",
            font = ("Segoe UI", 9, "bold"),
            pady = 6,
            cursor = "hand2"
        )
        self.el_btn.grid(row = 0, column = 1, sticky = "ew")

        # Σύνδεση click events για την επιλογή γλώσσας.
        self.en_btn.bind("<Button-1>", lambda e: self.select("en"))
        self.el_btn.bind("<Button-1>", lambda e: self.select("el"))

        # Ενημέρωση της τρέχουσας επιλογής.
        self.update_selection()

    def select(self, lang):
        # Αλλαγή γλώσσας αν επιλεγεί διαφορετική από την τρέχουσα.
        if lang != TranslationManager.get_language():
            TranslationManager.set_language(lang)
            self.update_selection()
            self.on_change()  # Κλήση callback για ανανέωση του UI

    def update_selection(self):
        # Ενημέρωση των χρωμάτων ανάλογα με την επιλεγμένη γλώσσα.
        lang = TranslationManager.get_language()
        if lang == "en":
            self.en_btn.config(bg = COLORS["accent"], fg = "white")
            self.el_btn.config(bg = COLORS["card_bg"], fg = COLORS["text"])
        else:
            self.el_btn.config(bg = COLORS["accent"], fg = "white")
            self.en_btn.config(bg = COLORS["card_bg"], fg = COLORS["text"])


class ThemeManager:
    """
    Theme Manager - Central color management
    ========================================
    Supports theme switching (light/dark)
    and easy color modification.
    """

    _themes = {
        "dark": {
            "bg": "#0a0a0a",
            "card_bg": "#161616",
            "card_hover": "#1e1e1e",
            "accent": "#007acc",
            "accent_hover": "#0098ff",
            "text": "#e0e0e0",
            "text_dim": "#888888",
            "border": "#333333",
            "sidebar_bg": "#121212",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
        },
        "light": {
            "bg": "#f5f5f5",
            "card_bg": "#ffffff",
            "card_hover": "#e8e8e8",
            "accent": "#0078d4",
            "accent_hover": "#106ebe",
            "text": "#1a1a1a",
            "text_dim": "#666666",
            "border": "#d0d0d0",
            "sidebar_bg": "#f0f0f0",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
        },
    }

    _current_theme = "dark"

    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Returns the colors of the current theme."""
        return cls._themes[cls._current_theme].copy()

    @classmethod
    def set_theme(cls, theme_name: str):
        """Sets the current theme."""
        if theme_name in cls._themes:
            cls._current_theme = theme_name

    @classmethod
    def get_current_theme(cls) -> str:
        """Returns the name of the current theme."""
        return cls._current_theme


COLORS = ThemeManager.get_colors()

FONTS = {
    "title": ("Segoe UI Semibold", 18),
    "header": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 9),
    "mono": ("Cascadia Code", 8),
    "small": ("Segoe UI", 7),
    "button": ("Segoe UI", 9, "bold"),
}


class GradientButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        width=200,
        height=36,
        gradient=("#007acc", "#5b4cf5"),
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=COLORS["sidebar_bg"],
            **kwargs,
        )
        self.command = command
        self.text = text
        self.gradient = gradient
        self.hovered = False
        self.enabled = True

        self._draw_button()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._draw_button())

    def _draw_button(self):
        self.delete("all")
        color = self.gradient[0] if self.enabled else "#444444"
        self._rounded_rect(
            2, 2, self.winfo_width() - 2, self.winfo_height() - 2, 8, fill=color
        )
        self.create_text(
            self.winfo_width() // 2,
            self.winfo_height() // 2,
            text=self.text,
            fill="white",
            font=FONTS["button"],
        )

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draws a rounded rectangle using arcs and rectangles."""
        fill = kwargs.pop("fill", None)
        outline = kwargs.pop("outline", "")

        try:
            # Arcs for corners
            self.create_arc(
                x1,
                y1,
                x1 + 2 * radius,
                y1 + 2 * radius,
                start=90,
                extent=90,
                fill=fill,
                outline=outline,
                **kwargs,
            )
            self.create_arc(
                x2 - 2 * radius,
                y1,
                x2,
                y1 + 2 * radius,
                start=0,
                extent=90,
                fill=fill,
                outline=outline,
                **kwargs,
            )
            self.create_arc(
                x1,
                y2 - 2 * radius,
                x1 + 2 * radius,
                y2,
                start=180,
                extent=90,
                fill=fill,
                outline=outline,
                **kwargs,
            )
            self.create_arc(
                x2 - 2 * radius,
                y2 - 2 * radius,
                x2,
                y2,
                start=270,
                extent=90,
                fill=fill,
                outline=outline,
                **kwargs,
            )
        except Exception:
            # Fallback to plain rectangle if arcs fail (e.g. radius too large)
            self.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, **kwargs)
            return

        # Rectangles for the middle
        self.create_rectangle(
            x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline, **kwargs
        )
        self.create_rectangle(
            x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline, **kwargs
        )

    def _on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self._draw_button()

    def _on_leave(self, event):
        self.hovered = False
        self._draw_button()

    def _on_click(self, event):
        if self.enabled:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw_button()


class ToggleSwitch(tk.Frame):
    def __init__(self, parent, command=None, **kwargs):
        bg_color = kwargs.pop("bg", COLORS["card_bg"])
        super().__init__(parent, bg = bg_color, **kwargs)
        self.command = command
        self.var = tk.BooleanVar(value=False)

        self.canvas = tk.Canvas(
            self, width = 44, height = 24, highlightthickness = 0, bg = bg_color
        )
        self.canvas.pack(pady=2)

        self._draw()
        self.canvas.bind("<Button-1>", self._toggle)
        self.canvas.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 44
        h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 24

        # Center the toggle in the canvas
        r = min(w, h) - 4
        bg = COLORS["accent"] if self.var.get() else COLORS["border"]

        # Draw track
        self._rounded_rect(2, 4, w - 2, h - 4, 8, fill=bg, outline="")

        # Draw knob
        knob_pos = w - h + 2 if self.var.get() else 2
        self.canvas.create_oval(
            knob_pos, 2, knob_pos + h - 4, h - 2, fill="white", outline=""
        )

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        self.canvas.create_arc(
            x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, **kwargs
        )
        self.canvas.create_arc(
            x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, **kwargs
        )
        self.canvas.create_arc(
            x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, **kwargs
        )
        self.canvas.create_arc(
            x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, **kwargs
        )
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)

    def _toggle(self, event=None):
        self.var.set(not self.var.get())
        self._draw()
        if self.command:
            self.command()

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)
        self._draw()


class CategoryButton(tk.Frame):
    """Modern sidebar button with active state indicator."""

    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, bg = COLORS["sidebar_bg"], **kwargs)
        self.command = command
        self.text = text
        self.active = False
        self._hovered = False

        # Canvas για σχεδίαση του κουμπιού με στρογγυλεμένη αίσθηση και δείκτη.
        self.canvas = tk.Canvas(
            self, height = 44, highlightthickness = 0, bg = COLORS["sidebar_bg"], cursor = "hand2"
        )
        self.canvas.pack(fill = "x")

        # Σύνδεση των συμβάντων (hover, click, configure).
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        # Καθορισμός χρωμάτων βάσει της κατάστασης (active / hover).
        bg = COLORS["card_hover"] if (self.active or self._hovered) else COLORS["sidebar_bg"]
        self.canvas.config(bg = bg)
        self.config(bg = bg)

        indicator_color = COLORS["accent"] if self.active else bg
        text_color = "white" if (self.active or self._hovered) else COLORS["text_dim"]
        text_font = ("Segoe UI Semibold", 10) if self.active else ("Segoe UI", 10)

        # Σχεδίαση δείκτη (indicator) στα αριστερά.
        self.canvas.create_rectangle(
            0, 4, 4, h - 4, fill = indicator_color, outline = ""
        )

        # Σχεδίαση κειμένου.
        self.canvas.create_text(
            30, h // 2, text = self.text, fill = text_color, anchor = "w", font = text_font
        )

    def _on_enter(self, e):
        self._hovered = True
        self._draw()

    def _on_leave(self, e):
        self._hovered = False
        self._draw()

    def _on_click(self, e):
        self.command()

    def set_active(self, active):
        self.active = active
        self._draw()


class RoundedEntry(tk.Frame):
    def __init__(self, parent, placeholder="", width=250, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        self.placeholder = placeholder

        self.canvas = tk.Canvas(
            self, width=width, height=36, highlightthickness=0, bg=COLORS["card_bg"]
        )
        self.canvas.pack(fill="x", expand=True)

        self.entry = tk.Entry(
            self.canvas,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=0,
        )

        self.canvas.bind("<Configure>", self._draw)

        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS["text_dim"])
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)

    def _draw(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        self._rounded_rect(
            1, 1, w - 2, h - 2, 8, fill=COLORS["card_bg"], outline=COLORS["border"]
        )

        self.entry.place(x=12, y=h // 2, anchor="w", width=w - 24)

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        try:
            self.canvas.create_arc(
                x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, **kwargs
            )
            self.canvas.create_arc(
                x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, **kwargs
            )
            self.canvas.create_arc(
                x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, **kwargs
            )
            self.canvas.create_arc(
                x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, **kwargs
            )
        except Exception:
            self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)

    def _on_focus_in(self, e):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text"])

    def _on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=COLORS["text_dim"])

    def get(self):
        val = self.entry.get()
        return "" if val == self.placeholder else val

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def update_placeholder(self, new_placeholder):
        old_placeholder = self.placeholder
        self.placeholder = new_placeholder
        if self.entry.get() == old_placeholder or not self.entry.get():
            self.entry.delete(0, "end")
            self.entry.insert(0, new_placeholder)
            self.entry.config(fg=COLORS["text_dim"])


class StyledButton(tk.Canvas):
    def __init__(
        self, parent, text, command, primary=True, width=140, height=32, **kwargs
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=COLORS["sidebar_bg"],
            **kwargs,
        )
        self.command = command
        self.text = text
        self.primary = primary
        self.hovered = False
        self.enabled = True

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()

        bg_color = COLORS["accent"] if self.primary else COLORS["border"]
        if self.hovered and self.enabled:
            bg_color = COLORS["accent_hover"] if self.primary else "#444444"

        if not self.enabled:
            bg_color = "#333333" if self.primary else "#222222"

        self.rounded_rect(2, 2, w - 2, h - 2, radius=6, fill=bg_color, tags="bg")
        self.create_text(
            w // 2,
            h // 2,
            text=self.text,
            fill="white" if self.enabled else "#888888",
            font=FONTS["button"],
            tags="text",
        )

    def rounded_rect(self, x1, y1, x2, y2, radius, fill, **kwargs):
        self.create_arc(
            x1,
            y1,
            x1 + 2 * radius,
            y1 + 2 * radius,
            start=90,
            extent=90,
            fill=fill,
            outline="",
            **kwargs,
        )
        self.create_arc(
            x2 - 2 * radius,
            y1,
            x2,
            y1 + 2 * radius,
            start=0,
            extent=90,
            fill=fill,
            outline="",
            **kwargs,
        )
        self.create_arc(
            x1,
            y2 - 2 * radius,
            x1 + 2 * radius,
            y2,
            start=180,
            extent=90,
            fill=fill,
            outline="",
            **kwargs,
        )
        self.create_arc(
            x2 - 2 * radius,
            y2 - 2 * radius,
            x2,
            y2,
            start=270,
            extent=90,
            fill=fill,
            outline="",
            **kwargs,
        )
        self.create_rectangle(
            x1 + radius, y1, x2 - radius, y2, fill=fill, outline="", **kwargs
        )
        self.create_rectangle(
            x1, y1 + radius, x2, y2 - radius, fill=fill, outline="", **kwargs
        )

    def _on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self._draw()

    def _on_leave(self, event):
        if self.enabled:
            self.hovered = False
            self._draw()

    def _on_click(self, event):
        if self.enabled:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw()


class ScrollableFrame(tk.Frame):
    """
    A reusable scrollable container.
    =================================
    Uses a Canvas to allow scrolling of
    a Frame containing widgets.
    """

    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", COLORS["bg"])
        width = kwargs.pop("width", None)
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, width=width)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg, width=width)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel support - localized to this widget
        self.canvas.bind(
            "<Enter>",
            lambda _: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel),
        )
        self.canvas.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

    def _on_canvas_configure(self, event):
        # Update the width of the inner frame to match the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Simplified: if we're here, the listener is active only for this widget
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0" if ThemeManager.get_current_theme() != "dark" else "#2c2c2c",
                         foreground="#000000" if ThemeManager.get_current_theme() != "dark" else "#ffffff",
                         relief="solid", borderwidth=1,
                         font=("Segoe UI", 9, "normal"))
        label.pack(ipadx=5, ipady=3)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class ToolCard(tk.Frame):
    def __init__(self, parent, name, details, on_toggle, on_link, on_retry=None, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], relief="flat", bd=0, **kwargs)
        self.name = name
        self.details = details
        self.on_toggle = on_toggle
        self.on_link = on_link
        self.on_retry = on_retry
        self._hovered = False
        self._selected = False
        self._status = "PENDING"
        self.visible = True
        self.warn_label = None
        self.missing_reasons = []

        self.config(highlightbackground=COLORS["border"], highlightthickness=1, bd=0)

        # Using grid for internal layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Top Section: Name and Icons
        self.header_frame = tk.Frame(self, bg=COLORS["card_bg"])
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.columnconfigure(0, weight=1)

        self.name_label = tk.Label(
            self.header_frame,
            text=name,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            anchor="w",
        )
        self.name_label.grid(row=0, column=0, sticky="w")

        self.link_btn = tk.Button(
            self.header_frame,
            text="↗",
            command=lambda: self.on_link(self.details["url"]),
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            relief="flat",
            font=("Segoe UI", 11),
            cursor="hand2",
            bd=0,
            padx=4,
        )
        self.link_btn.grid(row=0, column=2, sticky="e")

        # Middle Section: ID and Note
        self.id_label = tk.Label(
            self,
            text=f"ID: {details['id']}",
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["small"],
            anchor="w",
        )
        self.id_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 2))

        if details.get("note"):
            note_val = details["note"].get(TranslationManager.get_language(), "") if isinstance(details["note"], dict) else details["note"]
            self.note_label = tk.Label(
                self,
                text=note_val,
                bg=COLORS["card_bg"],
                fg=COLORS["text_dim"],
                font=FONTS["small"],
                anchor="w",
                justify="left",
                wraplength=260,
            )
            self.note_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 15))
        else:
            tk.Frame(self, bg=COLORS["card_bg"], height=10).grid(row=2, column=0)

        # Bottom Section: Toggle and Status
        self.actions_frame = tk.Frame(self, bg=COLORS["card_bg"])
        self.actions_frame.grid(row=3, column=0, sticky="sew", padx=10, pady=(0, 10))
        self.actions_frame.columnconfigure(1, weight=1)

        self.toggle = ToggleSwitch(self.actions_frame, command=self._on_check)
        self.toggle.grid(row=0, column=0, sticky="w")

        # Retry button (initially forgotten)
        self.retry_btn = tk.Button(
            self.actions_frame,
            text="Retry",
            command=self._on_retry_click,
            bg=COLORS["border"],
            fg=COLORS["text"],
            activebackground=COLORS["card_hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            font=FONTS["small"],
            cursor="hand2",
            padx=6,
            pady=2
        )

        self.status_dot = tk.Label(
            self.actions_frame,
            text=TOOL_STATUS["PENDING"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        )
        self.status_dot.grid(row=0, column=2, sticky="e")

        # Events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            if child != self.retry_btn:
                child.bind("<Enter>", self._on_enter)
                child.bind("<Leave>", self._on_leave)

    def _on_retry_click(self):
        if self.on_retry:
            self.on_retry(self)

    def set_status(self, status: str):
        self._status = status
        if status in TOOL_STATUS:
            self.status_dot.config(text=TOOL_STATUS[status])
        
        if status == "ERROR" and self.on_retry:
            self.retry_btn.grid(row=0, column=1, sticky="e", padx=(0, 5))
        else:
            self.retry_btn.grid_forget()

    def get_status(self) -> str:
        return self._status

    def show_warning(self, reasons: List[str]):
        self.missing_reasons = reasons
        if not self.warn_label:
            self.warn_label = tk.Label(
                self.header_frame,
                text="⚠️",
                bg=self.cget("bg"),
                fg="orange",
                font=("Segoe UI", 12),
                cursor="hand2"
            )
            self.warn_label.grid(row=0, column=1, sticky="e", padx=(0, 5))
            
            reasons_str = "\n".join(reasons)
            Tooltip(self.warn_label, f"{_('warning_requirements_title')}:\n{reasons_str}")

    def _on_check(self):
        checked = self.toggle.get()
        if checked and self.missing_reasons:
            from tkinter import messagebox
            reasons_str = "\n".join([f"- {r}" for r in self.missing_reasons])
            msg = _("warning_requirements_msg", name=self.name, reasons=reasons_str)
            title = _("warning_requirements_title")
            ans = messagebox.askyesno(title, msg, parent=self)
            if not ans:
                self.toggle.set(False)
                self._selected = False
                self._update_style()
                return
        
        self._selected = checked
        self.on_toggle(self)

    def _on_enter(self, event):
        self._hovered = True
        self._update_style()

    def _on_leave(self, event):
        self._hovered = False
        self._update_style()

    def _update_style(self):
        bg = (
            COLORS["card_hover"]
            if (self._hovered or self._selected)
            else COLORS["card_bg"]
        )
        border = (
            COLORS["accent"] if (self._hovered or self._selected) else COLORS["border"]
        )

        self.config(bg=bg, highlightbackground=border)

        # Streamlined update: only target widgets that definitely need it
        self.header_frame.config(bg=bg)
        self.name_label.config(bg=bg)
        self.link_btn.config(bg=bg)
        if self.warn_label:
            self.warn_label.config(bg=bg)
        self.id_label.config(bg=bg)
        if hasattr(self, "note_label"):
            self.note_label.config(bg=bg)
        self.actions_frame.config(bg=bg)
        self.status_dot.config(bg=bg)
        self.toggle.config(bg=bg)
        if hasattr(self.toggle, "canvas"):
            self.toggle.canvas.config(bg=bg)

    def is_checked(self) -> bool:
        return self.toggle.get()

    def set_checked(self, checked: bool):
        self.toggle.set(checked)
        self._selected = checked
        self._update_style()

    def set_visible(self, visible: bool):
        self.visible = visible
        if not visible:
            self.grid_forget()

    def update_language(self):
        if hasattr(self, "note_label") and self.details.get("note"):
            # Ανάκτηση της σωστής μετάφρασης για τη σημείωση
            note_val = self.details["note"].get(TranslationManager.get_language(), "") if isinstance(self.details["note"], dict) else self.details["note"]
            self.note_label.config(text=note_val)


class StackCard(tk.Frame):
    def __init__(self, parent, stack_name, tools_list, on_apply, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], relief="flat", bd=0, **kwargs)
        self.stack_name = stack_name
        self.tools_list = tools_list
        self.on_apply = on_apply
        self.hovered = False

        self.config(highlightbackground=COLORS["border"], highlightthickness=1, bd=0)

        # Name label
        self.title_label = tk.Label(
            self,
            text=stack_name,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["header"],
            anchor="w"
        )
        self.title_label.pack(anchor="w", padx=15, pady=(15, 5))

        # Tools description list
        tools_text = ", ".join(tools_list)
        self.desc_label = tk.Label(
            self,
            text=tools_text,
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["body"],
            anchor="w",
            justify="left",
            wraplength=260
        )
        self.desc_label.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Apply button
        self.apply_btn = StyledButton(
            self,
            text=_("apply_stack"),
            command=lambda: self.on_apply(self.stack_name),
            primary=True,
            width=140,
            height=30
        )
        self.apply_btn.pack(anchor="sw", padx=15, pady=(0, 15))

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            if not isinstance(child, StyledButton):
                child.bind("<Enter>", self._on_enter)
                child.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self.hovered = True
        self._update_style()

    def _on_leave(self, event):
        self.hovered = False
        self._update_style()

    def _update_style(self):
        bg = COLORS["card_hover"] if self.hovered else COLORS["card_bg"]
        border = COLORS["accent"] if self.hovered else COLORS["border"]
        self.config(bg=bg, highlightbackground=border)
        self.title_label.config(bg=bg)
        self.desc_label.config(bg=bg)
        self.apply_btn.config(bg=bg)

    def update_colors(self):
        self.config(bg=COLORS["card_bg"], highlightbackground=COLORS["border"])
        self.title_label.config(bg=COLORS["card_bg"], fg=COLORS["text"])
        self.desc_label.config(bg=COLORS["card_bg"], fg=COLORS["text_dim"])
        self.apply_btn.config(bg=COLORS["card_bg"])
        self.apply_btn._draw()

    def update_language(self):
        self.apply_btn.text = _("apply_stack")
        self.apply_btn._draw()


class StacksPanel(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.app = app_instance
        self.cards = []

        # Title Header
        self.header_label = tk.Label(
            self,
            text=_("stacks"),
            bg=COLORS["bg"],
            fg="white" if ThemeManager.get_current_theme() == "dark" else "black",
            font=FONTS["title"]
        )
        self.header_label.pack(anchor="w", padx=25, pady=(30, 20))

        # Scrollable container for stacks
        self.scroll_area = ScrollableFrame(self)
        self.scroll_area.pack(fill="both", expand=True)
        self.grid_frame = self.scroll_area.scrollable_frame

        self.scroll_area.canvas.bind("<Configure>", self._on_resize)

        self._build_grid()

    def _build_grid(self):
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        for stack_name, tools in STACKS.items():
            card = StackCard(
                self.grid_frame,
                stack_name=stack_name,
                tools_list=tools,
                on_apply=self.app.apply_stack
            )
            self.cards.append(card)

        self._reposition_cards()

    def _on_resize(self, event):
        self._reposition_cards(event.width)

    def _reposition_cards(self, width=None):
        if width is None:
            width = self.scroll_area.canvas.winfo_width()

        card_width = 300
        columns = max(1, int(width // card_width))
        if columns < 1:
            columns = 1

        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns
            card.grid(row=row, column=col, sticky="nsew", padx=15, pady=15)

        for col in range(columns):
            self.grid_frame.columnconfigure(col, weight=1)

    def update_theme(self):
        self.config(bg=COLORS["bg"])
        self.header_label.config(bg=COLORS["bg"], fg="white" if ThemeManager.get_current_theme() == "dark" else "black")
        self.scroll_area.config(bg=COLORS["bg"])
        self.scroll_area.canvas.config(bg=COLORS["bg"])
        self.scroll_area.scrollable_frame.config(bg=COLORS["bg"])
        for card in self.cards:
            card.update_colors()

    def update_language(self):
        self.header_label.config(text=_("stacks"))
        for card in self.cards:
            card.update_language()


class BackupRestorePanel(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.app = app_instance

        # Header Title
        self.header_label = tk.Label(
            self,
            text=_("backup_restore_title"),
            bg=COLORS["bg"],
            fg="white" if ThemeManager.get_current_theme() == "dark" else "black",
            font=FONTS["title"]
        )
        self.header_label.pack(anchor="w", padx=25, pady=(30, 20))

        # Outer container for centering cards
        self.cards_container = tk.Frame(self, bg=COLORS["bg"])
        self.cards_container.pack(fill="both", expand=True, padx=25, pady=10)
        self.cards_container.columnconfigure(0, weight=1)
        self.cards_container.columnconfigure(1, weight=1)

        # Backup Card Frame
        self.backup_card = tk.Frame(self.cards_container, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        self.backup_card.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.backup_title = tk.Label(
            self.backup_card,
            text=_("backup"),
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["header"]
        )
        self.backup_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.backup_desc = tk.Label(
            self.backup_card,
            text=_("backup_desc"),
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["body"],
            justify="left",
            wraplength=350
        )
        self.backup_desc.pack(anchor="w", padx=20, pady=(0, 20))

        self.backup_btn = StyledButton(
            self.backup_card,
            text=_("backup"),
            command=self.app.start_backup,
            primary=True,
            width=160,
            height=36
        )
        self.backup_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # Restore Card Frame
        self.restore_card = tk.Frame(self.cards_container, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        self.restore_card.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.restore_title = tk.Label(
            self.restore_card,
            text=_("restore"),
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["header"]
        )
        self.restore_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.restore_desc = tk.Label(
            self.restore_card,
            text=_("restore_desc"),
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["body"],
            justify="left",
            wraplength=350
        )
        self.restore_desc.pack(anchor="w", padx=20, pady=(0, 20))

        self.restore_btn = StyledButton(
            self.restore_card,
            text=_("restore"),
            command=self.app.start_restore,
            primary=False,
            width=160,
            height=36
        )
        self.restore_btn.pack(anchor="w", padx=20, pady=(0, 20))

    def update_theme(self):
        self.config(bg=COLORS["bg"])
        self.header_label.config(bg=COLORS["bg"], fg="white" if ThemeManager.get_current_theme() == "dark" else "black")
        self.cards_container.config(bg=COLORS["bg"])
        
        self.backup_card.config(bg=COLORS["card_bg"], highlightbackground=COLORS["border"])
        self.backup_title.config(bg=COLORS["card_bg"], fg=COLORS["text"])
        self.backup_desc.config(bg=COLORS["card_bg"], fg=COLORS["text_dim"])
        self.backup_btn.config(bg=COLORS["card_bg"])
        self.backup_btn._draw()

        self.restore_card.config(bg=COLORS["card_bg"], highlightbackground=COLORS["border"])
        self.restore_title.config(bg=COLORS["card_bg"], fg=COLORS["text"])
        self.restore_desc.config(bg=COLORS["card_bg"], fg=COLORS["text_dim"])
        self.restore_btn.config(bg=COLORS["card_bg"])
        self.restore_btn._draw()

    def update_language(self):
        self.header_label.config(text=_("backup_restore_title"))
        self.backup_title.config(text=_("backup"))
        self.backup_desc.config(text=_("backup_desc"))
        self.backup_btn.text = _("backup")
        self.backup_btn._draw()

        self.restore_title.config(text=_("restore"))
        self.restore_desc.config(text=_("restore_desc"))
        self.restore_btn.text = _("restore")
        self.restore_btn._draw()


class SkillsPanel(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.app = app_instance
        self.selected_file_path = ""

        # Header Title
        self.header_label = tk.Label(
            self,
            text=_("skills_title"),
            bg=COLORS["bg"],
            fg="white" if ThemeManager.get_current_theme() == "dark" else "black",
            font=FONTS["title"]
        )
        self.header_label.pack(anchor="w", padx=25, pady=(30, 20))

        # Main Layout Frame
        self.main_container = tk.Frame(self, bg=COLORS["bg"])
        self.main_container.pack(fill="both", expand=True, padx=25, pady=10)
        self.main_container.columnconfigure(0, weight=1, minsize=400)
        self.main_container.columnconfigure(1, weight=1, minsize=400)
        self.main_container.rowconfigure(0, weight=1)

        # Left Column: Downloader Card
        self.left_card = tk.Frame(self.main_container, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.left_card.columnconfigure(0, weight=1)

        tk.Label(self.left_card, text=_("skills_repo_label"), bg=COLORS["card_bg"], fg=COLORS["text"], font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 10))

        # Curated repo dropdown
        self.curated_repo_var = tk.StringVar()
        curated_repos = [repo["url"] for repo in SkillsManager.DEFAULT_REPOS]
        self.repo_dropdown = ttk.Combobox(self.left_card, textvariable=self.curated_repo_var, values=curated_repos, width=45, style="TCombobox")
        self.repo_dropdown.pack(anchor="w", padx=20, pady=(0, 10))
        if curated_repos:
            self.repo_dropdown.set(curated_repos[0])

        # Status & Path Labels
        self.global_path_label = tk.Label(self.left_card, text=_("skills_global_path", path=SkillsManager.get_global_dir()), bg=COLORS["card_bg"], fg=COLORS["text_dim"], font=FONTS["small"])
        self.global_path_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.status_var = tk.StringVar(value=_("skills_status_prefix", status=_("status_ready")))
        self.status_lbl = tk.Label(self.left_card, textvariable=self.status_var, bg=COLORS["card_bg"], fg=COLORS["accent"], font=FONTS["body"])
        self.status_lbl.pack(anchor="w", padx=20, pady=(0, 20))

        self.download_btn = StyledButton(
            self.left_card,
            text=_("skills_btn_download"),
            command=self.start_download,
            primary=True,
            width=180,
            height=36
        )
        self.download_btn.pack(anchor="w", padx=20, pady=(0, 20))

        # Right Column: Local Repos & Export Card
        self.right_card = tk.Frame(self.main_container, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_card.columnconfigure(0, weight=1)

        tk.Label(self.right_card, text=_("skills_destination"), bg=COLORS["card_bg"], fg=COLORS["text"], font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 10))

        # Destination input & Browse Button
        self.dest_frame = tk.Frame(self.right_card, bg=COLORS["card_bg"])
        self.dest_frame.pack(fill="x", padx=20, pady=(0, 15))
        self.dest_frame.columnconfigure(0, weight=1)

        self.dest_var = tk.StringVar()
        self.dest_entry = tk.Entry(self.dest_frame, textvariable=self.dest_var, bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["body"], relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        self.dest_entry.grid(row=0, column=0, sticky="ew", ipady=4)

        self.browse_btn = StyledButton(
            self.dest_frame,
            text="...",
            command=self.browse_dest,
            width=40,
            height=28
        )
        self.browse_btn.grid(row=0, column=1, padx=(10, 0), sticky="e")

        # Local Skills tree / file list
        tk.Label(self.right_card, text="Τοπικά Αρχεία Prompts/Rules:", bg=COLORS["card_bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w", padx=20, pady=(0, 5))

        self.files_listbox = tk.Listbox(
            self.right_card,
            bg=COLORS["bg"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="white",
            relief="flat",
            font=FONTS["small"],
            height=6,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        self.files_listbox.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.files_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        self.export_btn = StyledButton(
            self.right_card,
            text=_("skills_btn_export"),
            command=self.export_skill,
            primary=True,
            width=180,
            height=36
        )
        self.export_btn.pack(anchor="w", padx=20, pady=(0, 20))

        self.refresh_local_files()

    def start_download(self):
        url = self.curated_repo_var.get().strip()
        if not url:
            return
        
        self.status_var.set(_("skills_status_prefix", status="Downloading..."))
        
        def run():
            repo_name = url.split("/")[-1].replace(".git", "")
            success, msg = SkillsManager.download_repo(url, repo_name)
            def done():
                self.status_var.set(_("skills_status_prefix", status=msg))
                self.refresh_local_files()
            self.after(0, done)
            
        threading.Thread(target=run, daemon=True).start()

    def browse_dest(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Επιλογή φακέλου Project")
        if path:
            self.dest_var.set(path)

    def refresh_local_files(self):
        self.files_listbox.delete(0, tk.END)
        self.local_files_map = {}
        
        local_repos = SkillsManager.list_local_skills()
        for repo in local_repos:
            repo_path = repo["full_path"]
            repo_folder = repo["folder_name"]
            
            for root, dirs, files in os.walk(repo_path):
                if ".git" in root:
                    continue
                for f in files:
                    if f.endswith("rules") or f.endswith(".cursorrules") or f.endswith(".windsurfrules") or f.endswith(".md") or "prompt" in f.lower():
                        rel_path = os.path.relpath(os.path.join(root, f), SkillsManager.get_global_dir())
                        display_name = f"{repo_folder} -> {os.path.basename(f)}"
                        self.files_listbox.insert(tk.END, display_name)
                        self.local_files_map[display_name] = os.path.join(root, f)

    def on_file_select(self, event):
        selection = self.files_listbox.curselection()
        if selection:
            display_name = self.files_listbox.get(selection[0])
            self.selected_file_path = self.local_files_map.get(display_name, "")

    def export_skill(self):
        if not self.selected_file_path:
            from tkinter import messagebox
            messagebox.showwarning("Προειδοποίηση", "Παρακαλώ επιλέξτε ένα αρχείο από τη λίστα.")
            return
            
        dest = self.dest_var.get().strip()
        if not dest or not os.path.exists(dest):
            from tkinter import messagebox
            messagebox.showwarning("Προειδοποίηση", "Παρακαλώ επιλέξτε έναν έγκυρο φάκελο project.")
            return
            
        file_name = os.path.basename(self.selected_file_path)
        if "cursorrules" in file_name.lower():
            file_name = ".cursorrules"
        elif "windsurfrules" in file_name.lower():
            file_name = ".windsurfrules"
            
        success, msg = SkillsManager.export_skill_to_project(self.selected_file_path, dest, file_name)
        from tkinter import messagebox
        if success:
            messagebox.showinfo("Επιτυχία", msg)
        else:
            messagebox.showerror("Σφάλμα", msg)

    def update_theme(self):
        self.config(bg=COLORS["bg"])
        self.header_label.config(bg=COLORS["bg"], fg="white" if ThemeManager.get_current_theme() == "dark" else "black")
        self.left_card.config(bg=COLORS["card_bg"], highlightbackground=COLORS["border"])
        self.right_card.config(bg=COLORS["card_bg"], highlightbackground=COLORS["border"])
        self.global_path_label.config(bg=COLORS["card_bg"], fg=COLORS["text_dim"])
        self.status_lbl.config(bg=COLORS["card_bg"])
        self.dest_frame.config(bg=COLORS["card_bg"])
        self.dest_entry.config(bg=COLORS["bg"], fg=COLORS["text"], highlightbackground=COLORS["border"])
        self.files_listbox.config(bg=COLORS["bg"], fg=COLORS["text"], highlightbackground=COLORS["border"])
        self.download_btn.config(bg=COLORS["card_bg"])
        self.download_btn._draw()
        self.browse_btn.config(bg=COLORS["card_bg"])
        self.browse_btn._draw()
        self.export_btn.config(bg=COLORS["card_bg"])
        self.export_btn._draw()

    def update_language(self):
        self.header_label.config(text=_("skills_title"))
        self.global_path_label.config(text=_("skills_global_path", path=SkillsManager.get_global_dir()))
        self.status_var.set(_("skills_status_prefix", status=_("status_ready")))
        self.download_btn.text = _("skills_btn_download")
        self.download_btn._draw()
        self.export_btn.text = _("skills_btn_export")
        self.export_btn._draw()


class ModernInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(_("app_title"))
        self.geometry("1400x850")
        self.minsize(1000, 700)
        self.configure(bg=COLORS["bg"])

        self.cards: List[ToolCard] = []
        self.install_queue: queue.Queue = queue.Queue()
        self.is_installing = False
        self._search_after_id: Optional[str] = None
        self._resize_after_id: Optional[str] = None

        self.system_specs = {
            "ram_gb": 0.0,
            "free_disk_gb": 0.0,
            "has_gpu": False,
            "gpu_name": ""
        }
        self._detect_system_specs()

        self._setup_styles()
        self._init_ui()
        self._process_queue()
        self.after(500, self.check_installed_tools)

    def _detect_system_specs(self):
        def detect():
            specs = SystemSpecChecker.get_system_specs()
            # Έλεγχος αν το παράθυρο της εφαρμογής είναι ακόμα ενεργό και δεν έχει κλείσει (π.χ. κατά τα unit tests).
            # Αυτό αποτρέπει σφάλματα τύπου 'main thread is not in main loop' όταν καλείται η self.after().
            try:
                if self.winfo_exists():
                    self.system_specs.update(specs)
                    self.after(100, self._refresh_requirements_on_cards)
            except (tk.TclError, RuntimeError, Exception):
                pass
        threading.Thread(target=detect, daemon=True).start()

    def _refresh_requirements_on_cards(self):
        for card in self.cards:
            requirements = card.details.get("requirements")
            if requirements:
                is_ok, reasons = SystemSpecChecker.check_requirements(requirements, self.system_specs)
                if not is_ok:
                    card.show_warning(reasons)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=COLORS["border"],
            troughcolor=COLORS["bg"],
        )
        style.map("Vertical.TScrollbar", background=[("active", COLORS["accent"])])

        style.configure(
            "TCombobox",
            fieldbackground=COLORS["card_bg"],
            background=COLORS["border"],
            foreground=COLORS["text"],
            darkrow=0,
            arrowcolor=COLORS["text"]
        )

        style.configure(
            "TNotebook", background=COLORS["bg"], borderwidth=0, tabposition="n"
        )
        style.configure(
            "TNotebook.Tab",
            background=COLORS["card_bg"],
            foreground=COLORS["text"],
            padding=(15, 8),
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", COLORS["accent"]),
                ("active", COLORS["card_hover"]),
            ],
            foreground=[("selected", "white"), ("active", COLORS["text"])],
        )

    def _build_category_grid(self, parent: tk.Frame, category: str):
        tools = TOOLS_REGISTRY[category]

        scroll_area = ScrollableFrame(parent)
        scroll_area.pack(fill="both", expand=True)

        scrollable_frame = scroll_area.scrollable_frame

        def _on_resize(event):
            if self._resize_after_id:
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(
                200, lambda: _reposition_cards(event.width)
            )

        scroll_area.canvas.bind("<Configure>", _on_resize, add="+")
        self.bind("<<SearchUpdate>>", lambda e: _reposition_cards(), add="+")

        def _reposition_cards(width=None):
            if width is None:
                width = (
                    scroll_area.canvas.winfo_width()
                    / self.tk.call("tk", "scaling")
                    * 72
                    / 96
                )

            card_width = 280
            columns = max(1, int(width // card_width))

            visible_children = [
                c
                for c in scrollable_frame.winfo_children()
                if getattr(c, "visible", True)
            ]

            for i, child in enumerate(visible_children):
                row = i // columns
                col = i % columns
                child.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

            for child in scrollable_frame.winfo_children():
                if child not in visible_children:
                    child.grid_forget()

            for col in range(columns):
                scrollable_frame.columnconfigure(col, weight=1)

        for name in tools.keys():
            card = ToolCard(
                scrollable_frame,
                name,
                tools[name],
                on_toggle=self._on_card_toggle,
                on_link=lambda url: webbrowser.open(url),
                on_retry=lambda c: self.retry_tool(c.name, c.details["id"]),
            )
            self.cards.append(card)

        self.after(200, _reposition_cards)

    def _init_ui(self):
        self.columnconfigure(0, weight=0, minsize=240)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar_area = ScrollableFrame(self, bg=COLORS["sidebar_bg"], width=240)
        self.sidebar_area.grid(row=0, column=0, sticky="nsew")
        self.sidebar_area.pack_propagate(False)
        self.sidebar = self.sidebar_area.scrollable_frame

        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")

        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=0)
        self.content.rowconfigure(2, weight=0)

        self._build_sidebar(self.sidebar)

        self.install_panel = tk.Frame(self.content, bg=COLORS["bg"])
        self._build_install_panel(self.install_panel)

        self.stacks_panel = StacksPanel(self.content, self)
        self.backup_restore_panel = BackupRestorePanel(self.content, self)
        self.skills_panel = SkillsPanel(self.content, self)

        self.console_expanded = False
        self.console_container = tk.Frame(self.content, bg=COLORS["bg"])
        self.console_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(10, 0))
        self.console_container.columnconfigure(0, weight=1)

        self.console_toggle = tk.Button(
            self.console_container,
            text=_("show_console"),
            command=self._toggle_console,
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=COLORS["bg"],
            activeforeground=COLORS["accent_hover"],
        )
        self.console_toggle.grid(row=0, column=0, sticky="w")

        self.log_frame = tk.Frame(self.content, bg=COLORS["bg"])
        self.log_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 20))
        self.log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            self.log_frame,
            height=0,
            bg="#0d0d0d" if ThemeManager.get_current_theme() == "dark" else "#ffffff",
            fg="#00ff00" if ThemeManager.get_current_theme() == "dark" else "#000000",
            font=FONTS["mono"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.log_text.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ttk.Progressbar(
            self.log_frame,
            mode="determinate",
            length=400,
            style="Custom.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.show_panel("install")

    def show_panel(self, name: str):
        self.install_panel.grid_forget()
        self.stacks_panel.grid_forget()
        self.backup_restore_panel.grid_forget()
        self.skills_panel.grid_forget()

        for k, btn in self.nav_buttons.items():
            btn.set_active(k == name)

        if name == "install":
            self.install_panel.grid(row=0, column=0, sticky="nsew")
        elif name == "stacks":
            self.stacks_panel.grid(row=0, column=0, sticky="nsew")
            self.stacks_panel._reposition_cards()
        elif name == "backup_restore":
            self.backup_restore_panel.grid(row=0, column=0, sticky="nsew")
        elif name == "skills":
            self.skills_panel.grid(row=0, column=0, sticky="nsew")

    def _build_sidebar(self, sidebar: tk.Frame):
        sidebar.columnconfigure(0, weight = 1)
        sidebar.rowconfigure(10, weight = 1)

        # Frame υποδοχής λογοτύπου (logo).
        self.logo_frame = tk.Frame(sidebar, bg = COLORS["sidebar_bg"])
        self.logo_frame.grid(row = 0, column = 0, sticky = "ew", padx = 25, pady = (40, 5))

        # Σχεδίαση "Dev" σε λευκό χρώμα.
        self.logo_dev = tk.Label(
            self.logo_frame,
            text = "Dev",
            bg = COLORS["sidebar_bg"],
            fg = "white",
            font = ("Segoe UI Semibold", 20),
        )
        self.logo_dev.pack(side = "left")

        # Σχεδίαση "Tools" σε χρώμα έμφασης (accent).
        self.logo_tools = tk.Label(
            self.logo_frame,
            text = "Tools",
            bg = COLORS["sidebar_bg"],
            fg = COLORS["accent"],
            font = ("Segoe UI Semibold", 20),
        )
        self.logo_tools.pack(side = "left")

        # Υπότιτλος λογοτύπου.
        self.sidebar_subtitle = tk.Label(
            sidebar,
            text = "INSTALLER & SUITE",
            bg = COLORS["sidebar_bg"],
            fg = COLORS["text_dim"],
            font = ("Segoe UI", 7, "bold"),
        )
        self.sidebar_subtitle.grid(row = 1, column = 0, sticky = "w", padx = 25, pady = (0, 15))

        # Διαχωριστική γραμμή.
        self.sidebar_divider1 = tk.Frame(sidebar, bg = COLORS["border"], height = 1)
        self.sidebar_divider1.grid(row = 2, column = 0, sticky = "ew", padx = 25, pady = (0, 20))

        # Επικεφαλίδα μενού.
        self.menu_header = tk.Label(
            sidebar,
            text = _("menu_header"),
            bg = COLORS["sidebar_bg"],
            fg = COLORS["text_dim"],
            font = ("Segoe UI", 8, "bold"),
        )
        self.menu_header.grid(row = 3, column = 0, sticky = "w", padx = 25, pady = (0, 10))

        self.nav_buttons = {}
        nav_items = [
            ("install", _("nav_install")),
            ("stacks", _("nav_stacks")),
            ("backup_restore", _("nav_backup_restore")),
            ("skills", _("nav_skills"))
        ]
        
        for i, (key, label) in enumerate(nav_items):
            btn = CategoryButton(
                sidebar,
                text = label,
                command = lambda k = key: self.show_panel(k)
            )
            # Προσθήκη padding γύρω από τα κουμπιά για πιο καθαρό UI.
            btn.grid(row = 4 + i, column = 0, sticky = "ew", padx = 15, pady = 4)
            self.nav_buttons[key] = btn

        # Spacer για να σπρώξει τα στοιχεία στο κάτω μέρος.
        self.sidebar_spacer = tk.Frame(sidebar, bg = COLORS["sidebar_bg"])
        self.sidebar_spacer.grid(row = 10, column = 0, sticky = "nsew")

        self.bottom_frame = tk.Frame(sidebar, bg = COLORS["sidebar_bg"])
        self.bottom_frame.grid(row = 11, column = 0, sticky = "ew", padx = 20, pady = (20, 5))
        self.bottom_frame.columnconfigure(0, weight = 1)

        self.theme_frame = tk.Frame(self.bottom_frame, bg = COLORS["sidebar_bg"])
        self.theme_frame.pack(fill = "x", pady = 5)
        
        self.theme_label = tk.Label(
            self.theme_frame,
            text = _("Dark Mode"),
            bg = COLORS["sidebar_bg"],
            fg = COLORS["text"],
            font = FONTS["body"]
        )
        self.theme_label.pack(side = "left")
        
        self.theme_toggle = ToggleSwitch(self.theme_frame, command = self._toggle_theme, bg = COLORS["sidebar_bg"])
        self.theme_toggle.set(ThemeManager.get_current_theme() == "dark")
        self.theme_toggle.pack(side = "right")

        self.lang_switcher = LanguageSwitcher(self.bottom_frame, on_change = self.update_ui_languages)
        self.lang_switcher.pack(fill = "x", pady = 5)

        self.status_label = tk.Label(
            sidebar,
            text = _("status_ready"),
            bg = COLORS["sidebar_bg"],
            fg = COLORS["text_dim"],
            font = FONTS["small"],
            wraplength = 200,
        )
        self.status_label.grid(row = 12, column = 0, sticky = "sw", padx = 25, pady = 15)

    def _build_install_panel(self, panel: tk.Frame):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=0)
        panel.rowconfigure(2, weight=0)
        panel.rowconfigure(3, weight=1)
        panel.rowconfigure(4, weight=0)

        self.install_header = tk.Frame(panel, bg=COLORS["bg"])
        self.install_header.grid(row=0, column=0, sticky="ew", padx=25, pady=(30, 10))
        self.install_header.columnconfigure(0, weight=1)

        self.tool_mgmt_header = tk.Label(
            self.install_header,
            text=_("tool_management"),
            bg=COLORS["bg"],
            fg="white" if ThemeManager.get_current_theme() == "dark" else "black",
            font=FONTS["title"],
        )
        self.tool_mgmt_header.grid(row=0, column=0, sticky="w")

        self.search_container = tk.Frame(self.install_header, bg=COLORS["bg"])
        self.search_container.grid(row=0, column=1, sticky="e")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self.search_entry = RoundedEntry(
            self.search_container, placeholder=_("search_placeholder"), width=200
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.entry.config(textvariable=self.search_var)

        self.filter_var = tk.StringVar(value=_("filter_all"))
        self.filter_dropdown = ttk.Combobox(
            self.search_container,
            textvariable=self.filter_var,
            values=[_("filter_all"), _("filter_selected"), _("filter_installed"), _("filter_pending")],
            state="readonly",
            width=14,
            style="TCombobox"
        )
        self.filter_dropdown.pack(side="left")
        self.filter_dropdown.bind("<<ComboboxSelected>>", self._on_search)

        self.super_tabs_frame = tk.Frame(panel, bg=COLORS["bg"])
        self.super_tabs_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=5)

        self.super_tab_buttons = {}
        for idx, super_cat in enumerate(SUPER_CATEGORIES.keys()):
            btn = StyledButton(
                self.super_tabs_frame,
                text=super_cat,
                command=lambda sc=super_cat: self.show_super_category(sc),
                primary=False,
                width=160,
                height=30
            )
            btn.pack(side="left", padx=5)
            self.super_tab_buttons[super_cat] = btn

        self.sub_tabs_frame = tk.Frame(panel, bg=COLORS["bg"])
        self.sub_tabs_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=5)
        self.sub_tab_buttons = []

        self.category_notebook = tk.Frame(panel, bg=COLORS["bg"])
        self.category_notebook.grid(row=3, column=0, sticky="nsew", padx=15, pady=5)
        self.category_notebook.columnconfigure(0, weight=1)
        self.category_notebook.rowconfigure(0, weight=1)

        self.category_frames = {}
        self.category_visible = {}

        for category in TOOLS_REGISTRY.keys():
            frame = tk.Frame(self.category_notebook, bg=COLORS["bg"])
            self.category_frames[category] = frame
            self._build_category_grid(frame, category)
            self.category_visible[category] = False

        self.current_category = None
        self.current_super_category = None

        self.footer_frame = tk.Frame(panel, bg=COLORS["bg"])
        self.footer_frame.grid(row=4, column=0, sticky="ew", padx=25, pady=(15, 20))
        self.footer_frame.columnconfigure(1, weight=1)

        self.select_all_btn = StyledButton(
            self.footer_frame,
            _("select_all"),
            command=self.select_all,
            width=140,
            primary=False,
        )
        self.select_all_btn.grid(row=0, column=0, padx=(0, 10))

        self.deselect_all_btn = StyledButton(
            self.footer_frame,
            _("deselect_all"),
            command=self.deselect_all,
            width=140,
            primary=False,
        )
        self.deselect_all_btn.grid(row=0, column=1, sticky="w")

        self.install_btn = GradientButton(
            self.footer_frame,
            _("install_selected"),
            command=self.start_installation,
            width=240,
            height=40,
        )
        self.install_btn.grid(row=0, column=2, sticky="e")

        self.show_super_category(list(SUPER_CATEGORIES.keys())[0])

    def show_super_category(self, super_cat: str):
        if self.current_super_category == super_cat:
            return

        self.current_super_category = super_cat

        for sc, btn in self.super_tab_buttons.items():
            btn.primary = (sc == super_cat)
            btn._draw()

        for btn in self.sub_tab_buttons:
            btn.destroy()
        self.sub_tab_buttons.clear()

        sub_cats = SUPER_CATEGORIES[super_cat]
        for sub_cat in sub_cats:
            btn = StyledButton(
                self.sub_tabs_frame,
                text=_(sub_cat),
                command=lambda sc=sub_cat: self.show_category(sc),
                primary=False,
                width=140,
                height=26
            )
            btn.pack(side="left", padx=3)
            self.sub_tab_buttons.append(btn)

        if sub_cats:
            self.show_category(sub_cats[0])

    def show_category(self, category: str):
        if self.current_category == category:
            return

        sub_cats = SUPER_CATEGORIES[self.current_super_category]
        category_index = sub_cats.index(category) if category in sub_cats else -1
        
        for idx, btn in enumerate(self.sub_tab_buttons):
            btn.primary = (idx == category_index)
            btn._draw()

        for cat, frame in self.category_frames.items():
            if cat == category:
                frame.grid(row=0, column=0, sticky="nsew")
                self.category_visible[cat] = True
            else:
                frame.grid_forget()
                self.category_visible[cat] = False

        self.current_category = category

    def _toggle_console(self):
        self.console_expanded = not self.console_expanded
        if self.console_expanded:
            self.log_text.config(height=8)
            self.console_toggle.config(text=_("hide_console"))
        else:
            self.log_text.config(height=0)
            self.console_toggle.config(text=_("show_console"))
        self.update_idletasks()

    def update_ui_languages(self):
        self.title(_("app_title"))
        self.menu_header.config(text=_("menu_header"))

        nav_items = [
            ("install", _("nav_install")),
            ("stacks", _("nav_stacks")),
            ("backup_restore", _("nav_backup_restore"))
        ]
        for key, label in nav_items:
            if key in self.nav_buttons:
                self.nav_buttons[key].text = label
                self.nav_buttons[key]._draw()

        self.theme_label.config(text=_("Dark Mode"))

        curr_status = self.status_label.cget("text")
        if curr_status.startswith("Status: ") or curr_status.startswith("Κατάσταση: "):
            if "Ready" in curr_status or "Έτοιμο" in curr_status:
                self.status_label.config(text=_("status_ready"))
            elif "Completed" in curr_status or "Ολοκληρώθηκε" in curr_status:
                self.status_label.config(text=_("status_completed"))
            else:
                clean_status = curr_status.split(": ", 1)[-1]
                self.status_label.config(text=f"{_('status_prefix')}{clean_status}")
        else:
            if curr_status == "Ready" or curr_status == "Έτοιμο":
                self.status_label.config(text=_("status_ready"))
            elif curr_status == "Completed" or curr_status == "Ολοκληρώθηκε":
                self.status_label.config(text=_("status_completed"))

        self.tool_mgmt_header.config(text=_("tool_management"))
        self.search_entry.update_placeholder(_("search_placeholder"))
        
        self.filter_dropdown.config(
            values=[_("filter_all"), _("filter_selected"), _("filter_installed"), _("filter_pending")]
        )
        self.filter_var.set(_("filter_all"))

        if self.console_expanded:
            self.console_toggle.config(text=_("hide_console"))
        else:
            self.console_toggle.config(text=_("show_console"))

        self.select_all_btn.text = _("select_all")
        self.select_all_btn._draw()
        self.deselect_all_btn.text = _("deselect_all")
        self.deselect_all_btn._draw()
        self.install_btn.text = _("install_selected")
        self.install_btn._draw_button()

        if self.current_super_category:
            sub_cats = SUPER_CATEGORIES[self.current_super_category]
            for idx, btn in enumerate(self.sub_tab_buttons):
                if idx < len(sub_cats):
                    btn.text = _(sub_cats[idx])
                    btn._draw()

        for card in self.cards:
            card.update_language()

        self.stacks_panel.update_language()
        self.backup_restore_panel.update_language()
        self.skills_panel.update_language()

    def _toggle_theme(self):
        current = ThemeManager.get_current_theme()
        new_theme = "light" if current == "dark" else "dark"
        ThemeManager.set_theme(new_theme)
        
        global COLORS
        COLORS = ThemeManager.get_colors()
        
        self.update_theme_colors()

    def update_theme_colors(self):
        self.configure(bg=COLORS["bg"])
        self._setup_styles()

        self.sidebar_area.config(bg=COLORS["sidebar_bg"])
        self.sidebar_area.canvas.config(bg=COLORS["sidebar_bg"])
        self.sidebar_area.scrollable_frame.config(bg=COLORS["sidebar_bg"])
        
        self.logo_frame.config(bg=COLORS["sidebar_bg"])
        self.logo_dev.config(bg=COLORS["sidebar_bg"])
        self.logo_tools.config(bg=COLORS["sidebar_bg"], fg=COLORS["accent"])
        self.sidebar_subtitle.config(bg=COLORS["sidebar_bg"], fg=COLORS["text_dim"])
        self.sidebar_divider1.config(bg=COLORS["border"])
        self.menu_header.config(bg=COLORS["sidebar_bg"], fg=COLORS["text_dim"])
        self.sidebar_spacer.config(bg=COLORS["sidebar_bg"])
        
        for btn in self.nav_buttons.values():
            btn.canvas.config(bg=COLORS["sidebar_bg"])
            btn.config(bg=COLORS["sidebar_bg"])
            btn._draw()
            
        self.bottom_frame.config(bg=COLORS["sidebar_bg"])
        self.theme_frame.config(bg=COLORS["sidebar_bg"])
        self.theme_label.config(bg=COLORS["sidebar_bg"], fg=COLORS["text"])
        self.theme_toggle.config(bg=COLORS["sidebar_bg"])
        if hasattr(self.theme_toggle, "canvas"):
            self.theme_toggle.canvas.config(bg=COLORS["sidebar_bg"])
        self.theme_toggle._draw()
        
        self.lang_switcher.config(bg=COLORS["sidebar_bg"])
        self.lang_switcher.container.config(bg=COLORS["border"])
        self.lang_switcher.update_selection()
        
        self.status_label.config(bg=COLORS["sidebar_bg"], fg=COLORS["text_dim"])
        
        self.install_panel.config(bg=COLORS["bg"])
        self.install_header.config(bg=COLORS["bg"])
        self.tool_mgmt_header.config(bg=COLORS["bg"], fg="white" if ThemeManager.get_current_theme() == "dark" else "black")
        
        self.search_container.config(bg=COLORS["bg"])
        self.search_entry.config(bg=COLORS["card_bg"])
        self.search_entry.canvas.config(bg=COLORS["card_bg"])
        self.search_entry.entry.config(bg=COLORS["card_bg"], fg=COLORS["text"], insertbackground=COLORS["text"])
        self.search_entry._draw()
        
        self.super_tabs_frame.config(bg=COLORS["bg"])
        for btn in self.super_tab_buttons.values():
            btn.config(bg=COLORS["bg"])
            btn._draw()
            
        self.sub_tabs_frame.config(bg=COLORS["bg"])
        for btn in self.sub_tab_buttons:
            btn.config(bg=COLORS["bg"])
            btn._draw()

        self.category_notebook.config(bg=COLORS["bg"])
        for frame in self.category_frames.values():
            frame.config(bg=COLORS["bg"])
            for child in frame.winfo_children():
                if isinstance(child, ScrollableFrame):
                    child.config(bg=COLORS["bg"])
                    child.canvas.config(bg=COLORS["bg"])
                    child.scrollable_frame.config(bg=COLORS["bg"])
                    
        for card in self.cards:
            card.config(bg=COLORS["card_bg"])
            card._update_style()
            
        self.console_container.config(bg=COLORS["bg"])
        self.console_toggle.config(bg=COLORS["bg"], activebackground=COLORS["bg"])
        
        self.log_frame.config(bg=COLORS["bg"])
        self.log_text.config(
            bg="#0d0d0d" if ThemeManager.get_current_theme() == "dark" else "#ffffff",
            fg="#00ff00" if ThemeManager.get_current_theme() == "dark" else "#000000",
            highlightbackground=COLORS["border"]
        )
        
        self.footer_frame.config(bg=COLORS["bg"])
        self.select_all_btn.config(bg=COLORS["bg"])
        self.select_all_btn._draw()
        self.deselect_all_btn.config(bg=COLORS["bg"])
        self.deselect_all_btn._draw()
        
        self.install_btn.config(bg=COLORS["bg"])
        self.install_btn._draw_button()

        self.stacks_panel.update_theme()
        self.backup_restore_panel.update_theme()
        self.skills_panel.update_theme()

    def _on_card_toggle(self, card: ToolCard):
        pass

    def _on_search(self, *args):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._execute_search)

    def _execute_search(self):
        try:
            query = self.search_entry.get().lower()
        except:
            query = ""

        filter_val = self.filter_var.get()
        all_text = _("filter_all")
        sel_text = _("filter_selected")
        inst_text = _("filter_installed")
        pend_text = _("filter_pending")

        for card in self.cards:
            match_search = query in card.name.lower() or query in card.details["id"].lower()
            
            match_filter = True
            if filter_val == sel_text:
                match_filter = card.is_checked()
            elif filter_val == inst_text:
                match_filter = card.get_status() == "INSTALLED"
            elif filter_val == pend_text:
                match_filter = card.get_status() == "PENDING"
                
            card.set_visible(match_search and match_filter)

        self.event_generate("<<SearchUpdate>>")

    def _process_queue(self):
        try:
            while True:
                msg = self.install_queue.get_nowait()
                self._handle_queue_message(msg)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def _handle_queue_message(self, msg: Dict):
        msg_type = msg.get("type")

        if msg_type == "log":
            self._append_log(msg["text"], msg.get("tag", "info"))
        elif msg_type == "progress":
            pass
        elif msg_type == "finished":
            self._on_install_finished()
        elif msg_type == "status":
            self.status_label.config(text=msg["text"])

    def _append_log(self, text: str, tag: str = "info"):
        self.log_text.insert("end", text + "\n", tag)
        self.log_text.see("end")

    def select_all(self):
        for card in self.cards:
            if card.master.master.master == self.category_frames[self.current_category]:
                card.set_checked(True)

    def deselect_all(self):
        for card in self.cards:
            if card.master.master.master == self.category_frames[self.current_category]:
                card.set_checked(False)

    def apply_stack(self, stack_name: str):
        self.deselect_all()
        active_tools = STACKS.get(stack_name, [])
        for card in self.cards:
            if card.name in active_tools:
                card.set_checked(True)
        self.status_label.config(text=f"Selected Stack: {stack_name}")
        self.show_panel("install")

    def start_installation(self):
        selected = [(c.name, c.details["id"]) for c in self.cards if c.is_checked()]

        if not selected:
            self._append_log(_("select_at_least_one"), "warning")
            return

        self.is_installing = True
        self._set_ui_enabled(False)
        self.log_text.delete("1.0", "end")

        self._append_log(
            _("starting_install", count=len(selected)), "info"
        )
        if not self.console_expanded:
            self._toggle_console()

        thread = threading.Thread(
            target=self._run_installation, args=(selected,), daemon=True
        )
        thread.start()

    def retry_tool(self, name: str, winget_id: str):
        # Ξεκινάει την εγκατάσταση ενός συγκεκριμένου εργαλείου.
        # Θέτει την κατάσταση εγκατάστασης σε True.
        self.is_installing = True

        # Απενεργοποιεί τα στοιχεία ελέγχου του UI.
        self._set_ui_enabled(False)

        # Καθαρίζει το πλαίσιο καταγραφής (console log).
        self.log_text.delete("1.0", "end")

        # Καταγράφει την έναρξη εγκατάστασης για ένα εργαλείο.
        self._append_log(
            _("starting_install", count = 1), "info"
        )

        # Επεκτείνει την κονσόλα αν είναι κλειστή.
        if not self.console_expanded:
            self._toggle_console()

        # Ορίζει τη λίστα εργαλείων με το συγκεκριμένο εργαλείο.
        selected_tool = [(name, winget_id)]

        # Δημιουργεί και ξεκινάει το νήμα της εγκατάστασης.
        thread = threading.Thread(
            target = self._run_installation, args = (selected_tool,), daemon = True
        )
        thread.start()

    def _run_installation(self, tools: List[Tuple[str, str]]):
        total = len(tools)

        for i, (name, winget_id) in enumerate(tools):
            card = next((c for c in self.cards if c.name == name), None)
            if card:
                card.set_status("RUNNING")

            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("install_starting_tool", name=name),
                    "tag": "info",
                }
            )

            self.after(0, lambda: self.update_progress(i, total))

            # Εύρεση του τρόπου εγκατάστασης από το TOOLS_REGISTRY
            tool_details = None
            for category, category_tools in TOOLS_REGISTRY.items():
                if name in category_tools:
                    tool_details = category_tools[name]
                    break

            install_type = "winget"
            install_cmd = ""
            if tool_details:
                install_type = tool_details.get("type", "winget")
                install_cmd = tool_details.get("install_command", "")

            if install_type == "powershell" and install_cmd:
                cmd = install_cmd
            elif install_type == "npm":
                cmd = f"npm install -g {winget_id}"
            elif install_type == "gh_extension":
                cmd = f"gh extension install {winget_id}"
            elif name == "WSL":
                cmd = "wsl --install"
            else:
                cmd = f"winget install --id {winget_id} --silent --accept-package-agreements --accept-source-agreements"

            error_lines = []
            try:
                process = subprocess.Popen(
                    ["powershell.exe", "-Command", cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                if process.stdout:
                    for line in process.stdout:
                        if line.strip():
                            self.install_queue.put(
                                {
                                    "type": "log",
                                    "text": f"  > {line.strip()}",
                                    "tag": "info",
                                }
                            )
                            error_lines.append(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": _("install_completed", name=name),
                            "tag": "success",
                        }
                    )
                    if card:
                        card.set_status("INSTALLED")
                else:
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": _("install_error_code", code=process.returncode, name=name),
                            "tag": "warning",
                        }
                    )
                    if card:
                        card.set_status("ERROR")
                    
                    # Άνοιγμα του AI Diagnostic Dialog
                    error_log_str = "\n".join(error_lines) if error_lines else f"PowerShell returned non-zero exit code: {process.returncode}"
                    self.after(0, lambda n=name, l=error_log_str: self.show_ai_diagnostic_dialog(n, l))

            except Exception as e:
                self.install_queue.put(
                    {
                        "type": "log",
                        "text": _("install_error_exception", name=name, error=str(e)),
                        "tag": "error",
                    }
                )
                self.after(0, lambda n=name, err=str(e): self.show_ai_diagnostic_dialog(n, f"Exception: {err}"))

        self.install_queue.put(
            {
                "type": "log",
                "text": _("install_all_completed"),
                "tag": "success",
            }
        )
        self.install_queue.put({"type": "finished"})

    def show_ai_diagnostic_dialog(self, name: str, error_log: str):
        dialog = AIDiagnosticDialog(self, name, error_log)


    def _on_install_finished(self):
        self.is_installing = False
        self._set_ui_enabled(True)
        self.progress_bar["value"] = 0
        self.status_label.config(text=_("status_completed"))

    def _set_ui_enabled(self, enabled: bool):
        self.install_btn.set_enabled(enabled)

    def start_backup(self):
        dialog = BackupSelectionDialog(self, BACKUP_PATHS)
        self.wait_window(dialog)

        selected_items = dialog.get_selected()
        if selected_items:
            from tkinter import filedialog

            default_name = (
                f"DevTools_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            )
            target_path = filedialog.asksaveasfilename(
                title=_("backup_select_title"),
                defaultextension=".zip",
                filetypes=[("Zip Files", "*.zip")],
                initialfile=default_name,
                initialdir=os.path.join(os.path.expanduser("~"), "Documents"),
            )

            if target_path:
                if not self.console_expanded:
                    self._toggle_console()
                threading.Thread(
                    target=self._run_backup,
                    args=(selected_items, target_path),
                    daemon=True,
                ).start()

    def _run_backup(self, selected_items: List[str], target_zip: str):
        try:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("backup_start", target=target_zip),
                    "tag": "info",
                }
            )

            with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                temp_dir = os.path.dirname(target_zip) or os.path.expanduser("~")
                ext_file = os.path.join(temp_dir, "vscode_extensions.txt")
                subprocess.run(
                    [
                        "powershell.exe",
                        "-Command",
                        f"code --list-extensions > '{ext_file}'",
                    ],
                    capture_output=True,
                )

                if os.path.exists(ext_file):
                    zipf.write(ext_file, "vscode_extensions.txt")
                    os.remove(ext_file)

                if os.path.exists(ANTIGRAVITY_EXTENSIONS_PATH):
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": _("backup_compressing_antigravity"),
                            "tag": "info",
                        }
                    )
                    for root, _, files in os.walk(ANTIGRAVITY_EXTENSIONS_PATH):
                        for file in files:
                            if file.endswith(".vsix"):
                                full_path = os.path.join(root, file)
                                zipf.write(
                                    full_path,
                                    os.path.join(
                                        "Antigravity_Extensions",
                                        os.path.relpath(
                                            full_path, ANTIGRAVITY_EXTENSIONS_PATH
                                        ),
                                    ),
                                )

                for name in selected_items:
                    path = BACKUP_PATHS.get(name)
                    if path and os.path.exists(path):
                        self.install_queue.put(
                            {
                                    "type": "log",
                                    "text": _("backup_compressing", name=name),
                                    "tag": "info",
                            }
                        )
                        for root, _, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                rel_path = os.path.relpath(full_path, path)
                                if any(
                                    excl in rel_path.split(os.sep)
                                    for excl in BACKUP_EXCLUDE_DIRS
                                ):
                                    continue
                                try:
                                    zipf.write(
                                        full_path,
                                        os.path.join(name, rel_path),
                                    )
                                except PermissionError:
                                    continue

            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("backup_success"),
                    "tag": "success",
                }
            )

        except Exception as e:
            self.install_queue.put(
                {"type": "log", "text": _("backup_error", error=str(e)), "tag": "error"}
            )

    def start_restore(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title=_("restore_select_title"), filetypes=[("Zip Files", "*.zip")]
        )

        if path:
            if not self.console_expanded:
                self._toggle_console()
            threading.Thread(
                target=self._run_restore, args=(path,), daemon=True
            ).start()

    def _run_restore(self, zip_path: str):
        try:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("restore_start", path=zip_path),
                    "tag": "info",
                }
            )

            with zipfile.ZipFile(zip_path, "r") as zipf:
                for name, dest in BACKUP_PATHS.items():
                    prefix = f"{name}/"
                    members = [m for m in zipf.namelist() if m.startswith(prefix)]

                    if members:
                        self.install_queue.put(
                            {
                                "type": "log",
                                "text": _("restore_extracting", name=name),
                                "tag": "info",
                            }
                        )

                        os.makedirs(dest, exist_ok=True)

                        for m in members:
                            rel = os.path.relpath(m, prefix)
                            target = os.path.join(dest, rel)

                            if m.endswith("/"):
                                os.makedirs(target, exist_ok=True)
                            else:
                                os.makedirs(os.path.dirname(target), exist_ok=True)
                                with zipf.open(m) as s, open(target, "wb") as t:
                                    shutil.copyfileobj(s, t)

                if "vscode_extensions.txt" in zipf.namelist():
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": _("restore_extensions"),
                            "tag": "info",
                        }
                    )
                    with zipf.open("vscode_extensions.txt") as f:
                        extensions = f.read().decode("utf-8").strip().split("\n")

                    for ext in extensions:
                        ext = ext.strip()
                        if ext:
                            self.install_queue.put(
                                {
                                    "type": "log",
                                    "text": _("restore_extension_installing", ext=ext),
                                    "tag": "info",
                                }
                            )
                            subprocess.run(
                                [
                                    "powershell.exe",
                                    "-Command",
                                    f"code --install-extension {ext} --force",
                                ],
                                capture_output=True,
                            )

                if "Antigravity_Extensions/" in zipf.namelist():
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": _("restore_antigravity"),
                            "tag": "info",
                        }
                    )
                    os.makedirs(ANTIGRAVITY_EXTENSIONS_PATH, exist_ok=True)
                    for name in zipf.namelist():
                        if name.startswith(
                            "Antigravity_Extensions/"
                        ) and not name.endswith("/"):
                            target = os.path.join(
                                ANTIGRAVITY_EXTENSIONS_PATH,
                                os.path.relpath(name, "Antigravity_Extensions"),
                            )
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            with zipf.open(name) as s, open(target, "wb") as t:
                                shutil.copyfileobj(s, t)
                            ext_name = os.path.basename(target)
                            self.install_queue.put(
                                {
                                    "type": "log",
                                    "text": _("restore_antigravity_success", name=ext_name),
                                    "tag": "info",
                                }
                            )

            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("restore_success"),
                    "tag": "success",
                }
            )

        except Exception as e:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": _("restore_error", error=str(e)),
                    "tag": "error",
                }
            )

    def export_selection(self):
        from tkinter import filedialog
        import json

        selected = [c.name for c in self.cards if c.is_checked()]
        if not selected:
            self._append_log(_("export_no_selection"), "warning")
            return

        path = filedialog.asksaveasfilename(
            title=_("export_title"),
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="devtools_selection.json",
        )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"selected_tools": selected}, f, ensure_ascii=False, indent=2
                    )
                self._append_log(_("export_success", path=path), "success")
            except Exception as e:
                self._append_log(_("export_error", error=str(e)), "error")

    def import_selection(self):
        from tkinter import filedialog
        import json

        path = filedialog.askopenfilename(
            title=_("import_title"),
            filetypes=[("JSON Files", "*.json")],
        )

        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    selected = data.get("selected_tools", [])

                self.deselect_all()
                for card in self.cards:
                    if card.name in selected:
                        card.set_checked(True)

                self._append_log(_("import_success", count=len(selected)), "success")
            except Exception as e:
                self._append_log(_("import_error", error=str(e)), "error")

    def check_installed_tools(self):
        self._append_log(_("checking_installed"), "info")

        def check():
            for card in self.cards:
                tool_id = card.details["id"]
                is_installed = self._is_tool_installed(tool_id)
                if is_installed:
                    card.set_status("INSTALLED")
                else:
                    card.set_status("PENDING")

            self.install_queue.put(
                {"type": "log", "text": _("check_complete"), "tag": "success"}
            )

        threading.Thread(target=check, daemon=True).start()

    def _is_tool_installed(self, tool_id: str) -> bool:
        try:
            result = subprocess.run(
                ["winget", "list", "--id", tool_id, "--exact"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return tool_id in result.stdout
        except Exception:
            return False

    def update_progress(self, current: int, total: int):
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar["value"] = percentage
            self.update_idletasks()

class AIDiagnosticDialog(tk.Toplevel):
    def __init__(self, parent, tool_name: str, error_log: str):
        super().__init__(parent)
        self.title(_("diag_title"))
        self.geometry("700x600")
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.grab_set()

        self.tool_name = tool_name
        self.error_log = error_log
        self.proposed_cmd = ""

        self._build_ui()
        self.geometry(f"+{parent.winfo_x() + 100}+{parent.winfo_y() + 100}")

    def _build_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            main_frame,
            text=f"{_('diag_title')}: {self.tool_name}",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=FONTS["header"],
        ).pack(anchor="w", pady=(0, 10))

        # Log frame
        tk.Label(main_frame, text="Log Σφάλματος:", bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w")
        log_text = tk.Text(main_frame, height=5, bg="#0d0d0d", fg="#ff3333", font=FONTS["mono"], relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        log_text.pack(fill="x", pady=(0, 15))
        log_text.insert("1.0", self.error_log)
        log_text.config(state="disabled")

        # Action Buttons frame
        btn_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", pady=(0, 15))

        self.search_btn = StyledButton(
            btn_frame,
            text=_("diag_btn_search"),
            command=self.run_web_search,
            primary=True,
            width=200,
        )
        self.search_btn.pack(side="left", padx=(0, 10))

        self.ollama_btn = StyledButton(
            btn_frame,
            text=_("diag_btn_ollama"),
            command=self.run_ollama_diag,
            primary=False,
            width=220,
        )
        self.ollama_btn.pack(side="left")

        # Results area
        tk.Label(main_frame, text=_("diag_expl_label"), bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"]).pack(anchor="w")
        
        self.result_text = tk.Text(
            main_frame,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            wrap="word",
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        self.result_text.pack(fill="both", expand=True, pady=(0, 15))
        
        # Proposed fix CLI area
        self.fix_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        self.fix_frame.pack(fill="x", pady=(0, 10))
        
        self.cmd_lbl = tk.Label(self.fix_frame, text=_("diag_cmd_label"), bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["small"])
        self.cmd_var = tk.StringVar()
        self.cmd_entry = tk.Entry(self.fix_frame, textvariable=self.cmd_var, bg=COLORS["card_bg"], fg=COLORS["accent"], font=FONTS["mono"], state="readonly", relief="flat", highlightbackground=COLORS["border"], highlightthickness=1)
        
        self.run_fix_btn = StyledButton(
            self.fix_frame,
            text=_("diag_exec_fix"),
            command=self.execute_proposed_command,
            primary=True,
            width=180,
        )

        # Bottom Close Button
        close_btn = StyledButton(
            main_frame,
            text=_("cancel"),
            command=self.destroy,
            width=100,
        )
        close_btn.pack(side="right")

    def run_web_search(self):
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "Αναζήτηση στο διαδίκτυο σε εξέλιξη...")
        self.update_idletasks()
        
        query = f"winget install {self.tool_name} error " + self.error_log.replace("\n", " ")[:100]
        
        def run():
            results = AIDiagnosticAgent.search_web(query)
            
            def done():
                self.result_text.delete("1.0", "end")
                if not results:
                    self.result_text.insert("1.0", "Δεν βρέθηκαν αποτελέσματα στο διαδίκτυο ή το API Rate Limit μπλόκαρε την αναζήτηση.")
                    return
                
                text_out = "Βρέθηκαν οι εξής πιθανές λύσεις:\n\n"
                for i, r in enumerate(results, 1):
                    text_out += f"{i}. {r['title']}\n   Σύνδεσμος: {r['link']}\n   Πληροφορίες: {r['snippet']}\n\n"
                self.result_text.insert("1.0", text_out)
                
            self.after(0, done)
            
        threading.Thread(target=run, daemon=True).start()

    def run_ollama_diag(self):
        if not AIDiagnosticAgent.is_ollama_running():
            from tkinter import messagebox
            messagebox.showwarning("Ollama Offline", "Το Ollama δεν εκτελείται τοπικά. Εκκινήστε το Ollama και δοκιμάστε ξανά.")
            return

        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "Το τοπικό AI αναλύει τα σφάλματα και τα αποτελέσματα αναζήτησης. Παρακαλώ περιμένετε...")
        self.update_idletasks()

        query = f"winget install {self.tool_name} error " + self.error_log.replace("\n", " ")[:100]
        
        def run():
            search_results = AIDiagnosticAgent.search_web(query)
            
            success, explanation, cmd = AIDiagnosticAgent.diagnose_with_ollama(
                self.tool_name, 
                self.error_log, 
                search_results
            )
            
            def done():
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", explanation)
                
                if success and cmd:
                    self.proposed_cmd = cmd
                    self.cmd_var.set(cmd)
                    
                    self.cmd_lbl.pack(anchor="w")
                    self.cmd_entry.pack(fill="x", pady=(0, 10), ipady=4)
                    self.run_fix_btn.pack(side="left")
                else:
                    self.cmd_lbl.pack_forget()
                    self.cmd_entry.pack_forget()
                    self.run_fix_btn.pack_forget()
                    
            self.after(0, done)
            
        threading.Thread(target=run, daemon=True).start()

    def execute_proposed_command(self):
        if not self.proposed_cmd:
            return
            
        def run():
            try:
                process = subprocess.Popen(
                    ["powershell.exe", "-Command", self.proposed_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                output, _ = process.communicate()
                
                def done():
                    from tkinter import messagebox
                    if process.returncode == 0:
                        messagebox.showinfo("Επιτυχία", "Η εντολή διόρθωσης εκτελέστηκε με επιτυχία!")
                    else:
                        messagebox.showerror("Σφάλμα", f"Η εντολή διόρθωσης απέτυχε με κωδικό {process.returncode}.\n\nΈξοδος:\n{output}")
                self.after(0, done)
            except Exception as e:
                def done_err():
                    from tkinter import messagebox
                    messagebox.showerror("Σφάλμα", f"Αποτυχία εκτέλεσης εντολής: {str(e)}")
                self.after(0, done_err)
                
        threading.Thread(target=run, daemon=True).start()


class BackupSelectionDialog(tk.Toplevel):
    def __init__(self, parent, backup_paths: Dict[str, str]):
        super().__init__(parent)
        # Χρήση μεταφρασμένου τίτλου για το παράθυρο διαλόγου
        self.title(_("backup_select_title"))
        self.geometry("400x400")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])

        self.transient(parent)
        self.grab_set()

        self.backup_paths = backup_paths
        self.selected_items: List[str] = []
        self.checkboxes: Dict[str, tk.BooleanVar] = {}

        self._build_ui()

        self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")

    def _build_ui(self):
        main_frame = tk.Frame(self, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Ετικέτα με μεταφρασμένο κείμενο προτροπής
        tk.Label(
            main_frame,
            text=_("backup_select_label"),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=FONTS["header"],
        ).pack(anchor="w", pady=(0, 15))

        scroll_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        scroll_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_frame, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=COLORS["bg"])

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        for name, path in self.backup_paths.items():
            frame = tk.Frame(content_frame, bg=COLORS["bg"])
            frame.pack(fill="x", pady=5)

            var = tk.BooleanVar(value=True)
            exists = os.path.exists(path)

            cb = tk.Checkbutton(
                frame,
                text=name,
                variable=var,
                bg=COLORS["bg"],
                fg=COLORS["text"] if exists else COLORS["text_dim"],
                selectcolor=COLORS["card_bg"],
                font=FONTS["body"],
                state="normal" if exists else "disabled",
            )
            cb.pack(side="left")

            if not exists:
                # Μετάφραση της ένδειξης μη εύρεσης στοιχείου
                tk.Label(
                    frame,
                    text=_("not_found"),
                    bg=COLORS["bg"],
                    fg=COLORS["text_dim"],
                    font=FONTS["small"],
                ).pack(side="left", padx=5)

            self.checkboxes[name] = var

        button_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        button_frame.pack(fill="x", pady=(15, 0))

        # Μεταφρασμένο κουμπί επιβεβαίωσης λήψης backup
        backup_all_btn = StyledButton(
            button_frame,
            _("backup_select_btn"),
            command=self._on_backup,
            primary=True,
            width=140,
        )
        backup_all_btn.pack(side="right")

        # Μεταφρασμένο κουμπί ακύρωσης
        cancel_btn = StyledButton(
            button_frame,
            _("cancel"),
            command=self.destroy,
            primary=False,
            width=100,
        )
        cancel_btn.pack(side="right", padx=(10, 0))

    def _on_backup(self):
        self.selected_items = [
            name for name, var in self.checkboxes.items() if var.get()
        ]
        self.destroy()

    def get_selected(self) -> List[str]:
        return self.selected_items


if __name__ == "__main__":
    app = ModernInstaller()
    app.mainloop()
