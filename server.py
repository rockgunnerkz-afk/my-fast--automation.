import asyncio
import websockets
import json
import urllib.request

# 🔑 SUPABASE CREDENTIALS (ဘရို၏ Key များ အစားထိုးရန်)
SUPABASE_URL = "verujcinfhcwuaydjqem"       # <--- မိမိ URL ထည့်ရန်
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlcnVqY2luZmhjd3VheWRqcWVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMjMyMTMsImV4cCI6MjA5NzY5OTIxM30.eVjnNsW61vSjjhP-ZO7MUZKOYWvwgx0b5ckvdP0wYi8"  # <--- မိမိ Anon Key ထည့်ရန်

# REST API Endpoint URL (Table နာမည်က users_nodes ဖြစ်ပါတယ်)
SUPABASE_API_URL = f"{SUPABASE_URL}/rest/v1/users_nodes"

POINT_TO_MMK_RATE = 0.5

def supabase_request(method, query_param="", payload=None):
    """Supabase သို့ Package မလိုဘဲ တိုက်ရိုက် Data လှမ်းပို့/တောင်းသည့် စမတ် Function"""
    url = f"{SUPABASE_API_URL}{query_param}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation" if method in ["POST", "PATCH"] else ""
    }
    
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"⚠️ Supabase API Error: {e}")
        return None

async def handle_node(websocket, path):
    # Flutter ဘက်က လှမ်းချိတ်တဲ့ Phone Number ကို လမ်းကြောင်းထဲကနေ ဆွဲထုတ်တာပါ
    phone_number = path.strip("/").split("/")[-1]
    print(f"📡 [Node Connected] {phone_number} ချိတ်ဆက်လာပါပြီ။")
    
    # ၁။ အကောင့်ရှိမရှိ REST API ဖြင့် စစ်ဆေးခြင်း
    user_data_list = supabase_request("GET", f"?phone_number=eq.{phone_number}")
    
    if not user_data_list:
        # အကောင့်မရှိပါက အသစ်ဆောက်ခြင်း (POST)
        new_user = {"phone_number": phone_number, "total_points": 0.0, "kpay_balance": 0.0}
        user_data_list = supabase_request("POST", "", new_user)
        print(f"🆕 [New Account] {phone_number} အတွက် စာရင်းဖွင့်ပြီး။")
        
    current_user = user_data_list[0] if user_data_list else {"total_points": 0.0}

    try:
        async for message in websocket:
            payload = json.loads(message)
            mb_shared = payload.get("mb_shared", 0)
            cpu_allocated = payload.get("cpu_usage_allocated", 0)
            
            # ပွိုင့်တွက်ချက်ခြင်း
            reward_points = (mb_shared * 10) + (cpu_allocated * 0.5)
            
            # လက်ရှိပွိုင့်အဟောင်းပေါ်မူတည်၍ အသစ်တွက်ချက်ခြင်း
            new_points = round(current_user["total_points"] + reward_points, 2)
            new_kpay_balance = round(new_points * POINT_TO_MMK_RATE, 2)
            
            # ဒေတာဘေ့စ်သို့ တိုက်ရိုက် လှမ်းစစ်/ပြင်ဆင်ခြင်း (PATCH)
            updated_data = supabase_request("PATCH", f"?phone_number=eq.{phone_number}", {
                "total_points": new_points,
                "kpay_balance": new_kpay_balance
            })
            
            if updated_data:
                current_user = updated_data[0]
            
            # Client (Flutter App) ဆီ Live ပြန်ပို့ခြင်း
            response = {"msg": "success", "current_points": new_points, "kpay_equivalent": new_kpay_balance}
            await websocket.send(json.dumps(response))
            print(f"📊 [Update] {phone_number} -> Total: {new_points} Pts ({new_kpay_balance} ကျပ်)")
            
    except websockets.exceptions.ConnectionClosed:
        print(f"❌ [Node Disconnected] {phone_number} လိုင်းပြတ်သွားပါပြီ။")

async def main():
    async with websockets.serve(handle_node, "0.0.0.0", 8000):
        print("🚀 Kyaw DePIN Smart REST Server (Port: 8000) ပွင့်ပါပြီ...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
