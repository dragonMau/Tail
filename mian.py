from PIL import Image
import numpy as np

LOCATION = "/storage/emulated/0/Download/"
file_name = "fubuki_sit.png"

quantize_b = 0
quantize_a = 0
sensetivity_ = 16  #0 - 255
gray_scale = False
scale_ = 1
checks = [
    0, 1, 0,
    1,     1,
    0, 1, 0,
]
play_ = [
    (255, 8),
    (0, 8)
]*0

img_ = Image.open(LOCATION+file_name)


#def get_dif(img_b):
#    diff = (arr_img - img_b)**2
#    #diff = np.sqrt(diff.sum(axis=2))
#    diff = diff.sum(axis=2)
#    return diff

def get_dif(img_a, img_b):
    a = np.average(img_a, axis=2)
    b = np.average(img_b, axis=2)
    return np.abs(a - b)

n = None
slices = [
    (slice(n, -2), slice(n, -2)),
    (slice(1, -1), slice(n, -2)),
    (slice(2,  n), slice(n, -2)),
    (slice(n, -2), slice(1, -1)),
    (slice(2,  n), slice(1, -1)),
    (slice(n, -2), slice(2,  n)),
    (slice(1, -1), slice(2,  n)),
    (slice(2,  n), slice(2,  n)),
]
del n

def get_brail(p: list[bool]):
    p[2] = (not any(p[::2])) and any(p)
    ch = int(0x28<<8|p[0]<<0|p[1]<<3|p[2]<<1|p[3]<<4|p[4]<<2|p[5]<<5|p[6]<<6|p[7]<<7)
    return ch.to_bytes(2, "little").decode("utf-16")
    
    


def gen_art(img: Image.Image, sensetivity:int=16, scale:float=1.0):
    img = img.resize((int(img.width*scale), int(img.height*scale)))
    if quantize_b:
        img = img.quantize(colors=quantize_b)
    if gray_scale:
        img = img.convert("L")
    if quantize_a:
        img = img.quantize(colors=quantize_a)
    img = img.convert("RGBA")
    
    arr_img = (np.array(img))
    diff_img = np.zeros(arr_img.shape[:-1], dtype=np.float128)
    
    arr_img_pad = np.pad(arr_img,((1,1),(1,1),(0,0)), mode="reflect")
    
    for s, ch in zip(slices, checks):
        if ch:
            diff_img += get_dif(arr_img, arr_img_pad[s])
            

    diff_img /= diff_img.max()
    diff_img *= 255
    
    s = sensetivity
    diff_img[diff_img < s] = 0
    diff_img[diff_img >= s] = 255
    
    diff_img = diff_img.astype(np.uint8)
    
    diff_img = np.pad(diff_img, 1)
    
    ct = play_
    
    for c, t in ct:
        m = np.array([diff_img[s] for s in slices]) == c
        mask = m.sum(axis=(0)) >=  t
        diff_img[1:-1, 1:-1][mask] = c
        
    result = diff_img[1:-1, 1:-1][:, ::-1]
    result = np.pad(result, (
        (0,4-result.shape[0]%4),
        (0,2-result.shape[1]%2)))
        
    codes = []
    for l in range(0, result.shape[1], 4):
        codes.append(np.array([
            result[l + 0, 0::2], result[l + 0, 1::2],
            result[l + 1, 0::2], result[l + 1, 1::2],
            result[l + 2, 0::2], result[l + 2, 1::2],
            result[l + 3, 0::2], result[l + 3, 1::2]
        ]) == 255)
    codes = np.rot90(np.array(codes), axes=(1,2))
    
    buffer = []
    for row in codes:
        for cell in row:
            buffer.append(get_brail(cell.astype(bool)))
        buffer.append('<br>')
    
    buffer = ''.join(buffer)
    style_td = ''.join((
        "vertical-align: middle;",
        "height: 95vh;",
        "width: 100vw;",
        "line-height:8.8px;",
        "letter-spacing:-1.2px;",
        "font-size:8px;",
        "text-align:center"
    ))
    style_menu = ''.join((
        "height: 5vh",
    ))
    style_a = ''.join((
        "font-size: 4vh;",
        "text-decoration: none;"
    ))
    
    return_ = '\n'.join((
         "<!DOCTYPE html>",
         "<html>",
         "    <head>",
         "        <meta charset=\"utf-8\">",
         "        <title>Braile Image</title>",
         "    </head>",
         "    <body>",
         "        <table>",
        f"           <tr><td style=\"{style_menu}\">",
        f"                <a style=\"{style_a}\" href=\"/\"><-</a>"
         "            </td></tr>"
        f"            <tr><td style=\"{style_td}\">",
        f"                {buffer}",
         "            </td></tr>",
         "        </table>",
         "    </body>",
         "</html>",
    ))
    
    return return_
       
#gen_art(img_, sensetivity_, scale_)

from aiohttp import web

async def generate_html(img, a, b):
  html_content = gen_art(img, a, b)  # Call your existing function
  return html_content

routes = web.RouteTableDef()

@routes.get('/')
async def home(_):
    style_home = '\n'.join((
        "body {",
        "    width: 400px;",
        "}",
    ))
    return_ = '\n'.join((
        "<!DOCTYPE html>",
        "<html>",
        "    <head>",
        "        <meta charset=\"UTF-8\">",
        "        <title>Braile Image</title>",
       f"        <style>{style_home}</style>",
        "    </head>",
        "    <body>",
        "        <h1>Enter Information</h1>",
        "        <form action=\"/result\" method=\"post\" enctype=\"multipart/form-data\">",
        "            <label for=\"sens\">Sensetivity:</label>",
        "            <input type=\"number\" id=\"sens\" name=\"sens\" required><br><br>",
        "            <label for=\"scale\">Scale:</label>",
        "            <input type=\"number\" id=\"scale\" name=\"scale\" required><br><br>",
        "            <label for=\"file_upload\">Image Upload:</label>",
        "            <input type=\"file\" id=\"file_upload\" name=\"file_upload\" required><br><br>",
        "            <button type=\"submit\">Send Data</button>",
        "        </form>",
        "</body>",
        "</html>"
    ))
    return web.Response(body=return_, content_type="text/html")

@routes.post('/result')
async def generate(request):
    data = await request.post()
    a = int(data["sens"]) % 256
    b = float(data["scale"])
    img = Image.open(data["file_upload"].file)
    return_ = await generate_html(img, a, b)
    return web.Response(body=return_, content_type="text/html")

app = web.Application()
app.add_routes(routes)
web.run_app(app)
