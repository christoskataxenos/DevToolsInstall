# DevTools Installer

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

A professional Windows desktop application built with Python and Tkinter for managing development environments. It automates the installation of essential developer tools, ensures consistency through curated "Stacks," and provides robust backup/restore capabilities for editor settings.

[Ελληνικά](#ελληνικά)

## Motivation

This project began as a personal solution to a recurring problem: after every format or new machine setup, reinstalling development tools manually — even with helpers like Ninite or Chris Titus Tool — was time‑consuming and repetitive. **DevTools Installer** was created to streamline this process, offering a fast, consistent, and customizable way to bootstrap a full development environment tailored to real‑world needs.

## Features

- **Automated Installation** — Uses `winget` for silent, reliable installation of 100+ developer tools and essential applications.
- **Environment Stacks** — Predefined bundles (Python/AI, React/Web, DevOps, etc.) for one‑click environment setup.
- **Settings Backup & Restore** — Save and restore settings for VS Code, Cursor, Windsurf, and other popular tools.
- **Modern UI/UX** — Responsive grid‑based interface with dark/light themes, custom widgets, and smooth scrolling.
- **European Focus** — Includes high‑quality European and open‑source alternatives (Vivaldi, Proton, pCloud, etc.) with emphasis on privacy.

## Screenshots

*Replace the image placeholders with your actual screenshots.*

| Main Dashboard | Stacks View | Backup/Restore |
| :---: | :---: | :---: |
| ![Dashboard](https://via.placeholder.com/300x200?text=Dashboard) | ![Stacks](https://via.placeholder.com/300x200?text=Stacks) | ![Backup](https://via.placeholder.com/300x200?text=Backup) |

## Why the Greek Language?

The interface includes Greek labels and descriptions to provide a localized, intuitive experience for Greek‑speaking developers. This design choice improves accessibility and usability for the local ecosystem while maintaining a professional, international‑ready structure.

## Installation

1. Ensure you have **Python 3.10+** installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/christoskataxenos/DevToolsInstall.git
   cd DevToolsInstall
   ```
3. Run the setup script:
   ```bash
   ./setup.bat
   ```
4. Launch the application:
   ```bash
   python DevToolsInstaller.py
   ```

## Roadmap

- [ ] Add customizable user-defined stacks
- [ ] Add plugin system for community extensions
- [ ] Add automatic detection of installed tools
- [ ] Add cloud sync for backups
- [ ] Add portable version (no Python required)
- [ ] Add full dark/light theme customization

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

# Ελληνικά

Μια επαγγελματική desktop εφαρμογή για Windows, κατασκευασμένη με Python και Tkinter, για τη διαχείριση προγραμματιστικών περιβαλλόντων. Αυτοματοποιεί την εγκατάσταση εργαλείων, εξασφαλίζει συνοχή μέσω "Stacks" και παρέχει δυνατότητες backup/restore για τις ρυθμίσεις των editors.

## Κίνητρο

Το εργαλείο ξεκίνησε ως προσωπική λύση: κάθε φορά που έκανα format σε laptop/PC, η διαδικασία επανεγκατάστασης όλων των εργαλείων — ακόμη και με Ninite ή Chris Titus Tool — ήταν χρονοβόρα και κουραστική. Έτσι δημιουργήθηκε το **DevTools Installer**, ένα εργαλείο κομμένο και ραμμένο στις πραγματικές ανάγκες ενός προγραμματιστή που θέλει γρήγορο, σταθερό και επαναλήψιμο setup.

## Χαρακτηριστικά

- **Αυτοματοποιημένη Εγκατάσταση** — Χρησιμοποιεί `winget` για αθόρυβη και αξιόπιστη εγκατάσταση 100+ εργαλείων.
- **Environment Stacks** — Προκαθορισμένα πακέτα (Python/AI, React/Web, DevOps κ.λπ.) για setup με ένα κλικ.
- **Backup & Επαναφορά Ρυθμίσεων** — Αποθήκευση και επαναφορά ρυθμίσεων για VS Code, Cursor, Windsurf κ.ά.
- **Σύγχρονο UI/UX** — Responsive διεπαφή με dark/light theme και custom widgets.
- **Έμφαση στην Ευρώπη** — Ευρωπαϊκές και open‑source εναλλακτικές με έμφαση στην ιδιωτικότητα.

## Εγκατάσταση

1. Βεβαιωθείτε ότι έχετε **Python 3.10+**.
2. Κάντε clone το repository:
   ```bash
   git clone https://github.com/christoskataxenos/DevToolsInstall.git
   cd DevToolsInstall
   ```
3. Εκτελέστε το setup:
   ```bash
   ./setup.bat
   ```
4. Εκκινήστε την εφαρμογή:
   ```bash
   python DevToolsInstaller.py
   ```