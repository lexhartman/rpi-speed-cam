# Mobile Access Guide

This guide explains how to easily access the Speed Cam Pi application from your mobile phone.

## 1. Accessing on the Local Network (Wi-Fi)

To access the application when your phone is connected to the same Wi-Fi network as the Raspberry Pi:

### Use the Hostname (mDNS)
If your Raspberry Pi's hostname is `raspberrypi` (default), try opening this address in your phone's browser:
- `http://raspberrypi.local`

### Use the IP Address
If the hostname doesn't work, find the IP address of your Raspberry Pi (e.g., `192.168.1.50`). Open it in your browser:
- `http://192.168.1.50`

(Note: If you changed the port in `docker-compose.yml`, append it like `:8000`.)

## 2. Add to Home Screen (App-like Experience)

You can "install" the web page on your phone's home screen. This removes the address bar and makes it feel like a native app.

### iPhone (iOS - Safari)
1. Open the page in Safari.
2. Tap the **Share** button (box with an arrow pointing up).
3. Scroll down and tap **Add to Home Screen**.
4. Give it a name (e.g., "Speed Cam") and tap **Add**.

### Android (Chrome)
1. Open the page in Chrome.
2. Tap the **Menu** icon (three dots in the top right).
3. Tap **Add to Home screen** or **Install App**.
4. Confirm by tapping **Add**.

## 3. Remote Access (Away from Home)

If you want to access the camera when you are not at home, **do not open ports on your router** unless you know exactly what you are doing (security risk).

### Recommended: Tailscale (Easiest & Safest)
Tailscale creates a secure private network between your devices.
1. Install Tailscale on your Raspberry Pi: `curl -fsSL https://tailscale.com/install.sh | sh`
2. Run `sudo tailscale up` and log in.
3. Install the Tailscale app on your phone and log in with the same account.
4. Use the "MagicDNS" name or the Tailscale IP address of your Pi to access it securely from anywhere (even on 4G/5G).

### Alternative: Cloudflare Tunnel
Another secure option without opening ports. It requires a domain name but is very robust.
