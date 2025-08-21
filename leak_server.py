from flask import Flask, request, make_response
from datetime import datetime

app = Flask(__name__)
app.url_map.strict_slashes = False  # /leak.gif/ 허용

# 1x1 transparent GIF (hex → bytes)
PIXEL_GIF = bytes.fromhex(
    "47494638396101000100910000ffffff00000021f90401000001002c00000000010001"
    "000002024401003b"
)

def gif_response(status=200):
    resp = make_response(PIXEL_GIF, status)
    resp.headers.update({
        "Content-Type": "image/gif",
        "Content-Length": str(len(PIXEL_GIF)),
        "Cache-Control": "no-store",             # 캐시 방지
        "Access-Control-Allow-Origin": "*",      # 편의
        "X-Content-Type-Options": "nosniff",     # 타입 스니핑 방지
        "Referrer-Policy": "no-referrer",
    })
    return resp

@app.get("/health")
def health():
    return "ok", 200

# ✅ 어떤 변형으로 와도 전부 GIF로 응답 (GET/HEAD)
@app.route("/leak.gif", methods=["GET", "HEAD"])
@app.route("/leak.gif/<path:_rest>", methods=["GET", "HEAD"])
@app.route("/leak", methods=["GET", "HEAD"])
@app.route("/leak/<path:_rest>", methods=["GET", "HEAD"])
def leak(_rest=None):
    print(
        f"[LEAK {datetime.utcnow().isoformat()}Z] "
        f"method={request.method} path={request.path} args={dict(request.args)} "
        f"ua={request.headers.get('User-Agent','')}"
    )
    # HEAD면 바디 없이 헤더만, GET이면 1x1 GIF 바디 포함
    if request.method == "HEAD":
        return gif_response()
    return gif_response()

# 모든 에러 상황에서도 GIF로 응답하도록 처리
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_any_error(e):
    return gif_response(200)

if __name__ == "__main__":
    # ngrok http 8080 으로 노출
    app.run(host="0.0.0.0", port=8080)
