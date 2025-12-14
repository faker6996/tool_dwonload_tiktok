# Video Editor Assets

This folder contains application assets:

- `app_icon.png` - Application icon (PNG format)
- `app_icon.icns` - macOS icon format (optional)
- `app_icon.ico` - Windows icon format (optional)

## Creating Icons

### macOS (.icns)

```bash
# Install iconutil (comes with Xcode)
mkdir temp.iconset
sips -z 16 16 app_icon.png --out temp.iconset/icon_16x16.png
sips -z 32 32 app_icon.png --out temp.iconset/icon_16x16@2x.png
sips -z 32 32 app_icon.png --out temp.iconset/icon_32x32.png
sips -z 64 64 app_icon.png --out temp.iconset/icon_32x32@2x.png
sips -z 128 128 app_icon.png --out temp.iconset/icon_128x128.png
sips -z 256 256 app_icon.png --out temp.iconset/icon_128x128@2x.png
sips -z 256 256 app_icon.png --out temp.iconset/icon_256x256.png
sips -z 512 512 app_icon.png --out temp.iconset/icon_256x256@2x.png
sips -z 512 512 app_icon.png --out temp.iconset/icon_512x512.png
sips -z 1024 1024 app_icon.png --out temp.iconset/icon_512x512@2x.png
iconutil -c icns temp.iconset -o app_icon.icns
rm -rf temp.iconset
```

### Windows (.ico)

Use online converter or `imagemagick`:

```bash
convert app_icon.png -resize 256x256 app_icon.ico
```
