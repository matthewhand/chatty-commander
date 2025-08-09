import pystray
from PIL import Image, ImageDraw

def create_image(width, height, color1, color2):
    """Create a simple icon image."""
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)
    return image

def on_clicked(icon, item):
    """Handle menu item clicks."""
    if str(item) == "Exit":
        icon.stop()
    else:
        print(f"Clicked: {item}")

def run_gui():
    """Create and run the system tray icon."""
    print("Starting GUI mode: Creating system tray icon...")
    icon_image = create_image(64, 64, 'black', 'blue')
    
    menu = pystray.Menu(
        pystray.MenuItem('Show Status', on_clicked),
        pystray.MenuItem('Exit', on_clicked)
    )
    
    icon = pystray.Icon(
        'chatty_commander',
        icon_image,
        'Chatty Commander',
        menu
    )
    
    icon.run()
    print("GUI mode has been stopped.")

if __name__ == '__main__':
    # This allows running the GUI directly for testing.
    # Note: Requires a display server (e.g., X11 or Wayland on Linux).
    run_gui()
