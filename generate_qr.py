import qrcode

url = "https://redlight-booth.onrender.com"

img = qrcode.make(url)

img.save("booth_qr.png")

print("QR code saved as booth_qr.png")
