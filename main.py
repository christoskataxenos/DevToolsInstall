import os
import sys
import logging
from ui.app_window import AppWindow
from core.config import TranslationManager

def init_logging() -> None:
    """Configures centralized logging structure."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "devtools_install.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> None:
    """Main application launcher."""
    init_logging()
    logging.info("Starting DevTools Installer refactored application...")
    
    # Set default language preference to English as requested
    TranslationManager.set_language("en")

    try:
        app = AppWindow()
        # Add basic window closing handler
        app.protocol("WM_DELETE_WINDOW", lambda: on_close(app))
        app.mainloop()
    except Exception as e:
        logging.critical(f"Unhandled critical exception starting app: {str(e)}", exc_info=True)
        sys.exit(1)

def on_close(app: AppWindow) -> None:
    """Cleans resources and terminates app threads on exit."""
    logging.info("Closing application. Cleaning resources...")
    try:
        # Instantly hide window to provide instant visual feedback to user
        app.withdraw()
    except Exception:
        pass
    
    try:
        # Clean up any active installer subprocesses
        app.installer_service.cleanup()
    except Exception:
        pass

    try:
        app.quit()
        app.destroy()
    except Exception:
        pass
        
    sys.exit(0)

if __name__ == "__main__":
    main()
