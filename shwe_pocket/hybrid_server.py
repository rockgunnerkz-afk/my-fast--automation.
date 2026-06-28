import asyncio
import websockets
import json

# 🛠️ GitHub Codespace Header Fix Logic
async def process_request(path, request_headers):
    """
    Codespace Port Forwarding ကြောင့် Connection Header မှားယွင်းပြီး 
    invalid Connection header: keep-alive ဖြစ်လာတာကို Upgrade ပြန်ပြင်ပေးတဲ့ function
    """
    if "Connection" in request_headers:
        request_headers["Connection"] = "Upgrade"
    return None

# 🚀 WebSocket Client တက်လာရင် အလုပ်လုပ်မယ့် Handler
async def echo(websocket):
    print(f"📡 Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            # ဘရိုရဲ့ လက်ရှိ Logic တွေ (ဥပမာ- Mining process, data pooled) ကို ဒီနေရာမှာ ထည့်ပါ
            print(f"📩 Received: {message}")
            
            # စမ်းသပ်ဖို့အတွက် Client ဆီ Data ပြန်ပို့ပေးမယ့်ပုံစံ
            response = {
                "status": "ACTIVE",
                "pooled_data": 1.2,  # Example data
                "ram_rewards": 15.0  # Example points
            }
            await websocket.send(json.dumps(response))
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Client disconnected: {e}")
    except Exception as e:
        print(f"⚠️ Error inside session: {e}")

# 🌐 Server မောင်းနှင်မယ့် ပင်မ Function
async def main():
    print("■ Master Command (e.g., ဗျာန်ဆန်း) -> 🚀 Shwe Pocket Master Core Engine")
    print("Running on Port: 8000...")
    
    # 💡 အဓိကပြင်ဆင်ချက်: process_request handler ကို serve ထဲ ထည့်သွင်းလိုက်ခြင်း
    async with websockets.serve(echo, "0.0.0.0", 8000, process_request=process_request):
        await asyncio.Future()  # ဆာဗာကို အမြဲတမ်း ပွင့်နေစေရန် run ထားခြင်း

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by master command.")
