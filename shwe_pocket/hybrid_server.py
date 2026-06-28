import os
import asyncio
import websockets
import json
import urllib.request
import time

# 🛡️ GitHub လုံခြုံရေးအတွက် `.env` ဖိုင်ထဲမှ API Keys များကို ဆွဲဖတ်ခြင်း
# Local တွင် Run မည်ဆိုပါက python-dotenv ကို သုံးနိုင်သည်၊ သို့မဟုတ် Environment ထဲ တိုက်ရိုက်ထည့်နိုင်သည်။
SUPABASE_URL = os.getenv("SUPABASE_URL", "verujcinfhcwuaydjqem")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZlcnVqY2luZmhjd3VheWRqcWVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMjMyMTMsImV4cCI6MjA5NzY5OTIxM30.eVjnNsW61vSjjhP-ZO7MUZKOYWvwgx0b5ckvdP0wYi8")
SUPABASE_API_URL = f"{SUPABASE_URL}/rest/v1/users_nodes"

# 🪙 SYSTEM & FINANCIAL CONFIGURATION
POINT_TO_MMK_RATE = 1.0        # 1 Point = 1 MMK
WITHDRAWAL_FEE_PERCENT = 0.08   # KPay / Network Fee ၈ ရာခိုင်နှုန်း

# 🏛️ HYBRID SESSION & POOL MANAGER (Data Buffer နှင့် CPU Task ခွဲဝေမှုစနစ်)
class ShwePocketHybridManager:
    def __init__(self):
        self.active_nodes = {}       # { "phone_number": { "ws": ws, "device_id": id, "status": "idle" } }
        self.data_pool_buffer = {}   # { "phone_number": accumulated_mb_pooled } (ဒေတာများ စုရောင်းရန်)
        self.points_buffer = {}      # { "phone_number": accumulated_points_in_ram }
        self.task_queue = asyncio.Queue() # AI Video တွက်ချက်မည့် စာသား Queue

    def register_node(self, phone_number, device_id, websocket):
        # 🛡️ Device Multi-Accounting Prevention (စက်တစ်လုံးတည်း အကောင့်ခွဲတူးခြင်း ကာကွယ်ရန်)
        for phone, node in list(self.active_nodes.items()):
            if node["device_id"] == device_id and phone != phone_number:
                print(f"🚫 [Security Code: 403] Device ID {device_id} က အကောင့်ခွဲရန် ကြိုးစားသဖြင့် ငြင်းပယ်လိုက်သည်။")
                return False
        
        self.active_nodes[phone_number] = {
            "device_id": device_id,
            "ws": websocket,
            "status": "idle"
        }
        if phone_number not in self.data_pool_buffer:
            self.data_pool_buffer[phone_number] = 0.0
        if phone_number not in self.points_buffer:
            self.points_buffer[phone_number] = 0.0
            
        print(f"📡 [Node Connect] {phone_number} တက်လာပါပြီ။ စုစုပေါင်း Live Nodes: {len(self.active_nodes)} လုံး")
        return True

    def unregister_node(self, phone_number):
        if phone_number in self.active_nodes:
            del self.active_nodes[phone_number]
            print(f"❌ [Node Disconnect] {phone_number} လိုင်းပြတ်သွားပါပြီ။ Live Nodes: {len(self.active_nodes)} လုံး")

hybrid_manager = ShwePocketHybridManager()

# 🌐 Supabase HTTP REST Helper (External Library မလိုဘဲ သုံးနိုင်ရန် urllib ဖြင့် ရေးထားသည်)
def supabase_request(method, query_param="", payload=None):
    if "YOUR_SUPABASE" in SUPABASE_URL:
        return None # Credentials မထည့်ရသေးပါက ကျော်သွားမည်
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
        print(f"⚠️ Supabase Error: {e}")
        return None

# 🔄 BULK DATA & POINTS SYNC (၅ မိနစ်တစ်ကြိမ် ပွိုင့်နှင့် စုထားသော Data စာရင်းပိတ်ခြင်း)
async def periodic_bulk_sync_worker():
    while True:
        await asyncio.sleep(300) # ၅ မိနစ် (၃00 စက္ကန့်) စောင့်မည်
        if not hybrid_manager.points_buffer:
            continue
            
        print("💾 [Bulk Sync] Memory ပေါ်မှ ပွိုင့်များနှင့် စုထားသော ဒေတာများကို DB သို့ ပို့နေပါသည်...")
        for phone, ram_points in list(hybrid_manager.points_buffer.items()):
            if ram_points > 0:
                user_data = supabase_request("GET", f"?phone_number=eq.{phone}")
                if user_data:
                    db_points = user_data[0].get("total_points", 0.0)
                    new_points = round(db_points + ram_points, 2)
                    new_balance = round(new_points * POINT_TO_MMK_RATE, 2)
                    
                    supabase_request("PATCH", f"?phone_number=eq.{phone}", {
                        "total_points": new_points,
                        "kpay_balance": new_balance
                    })
                    hybrid_manager.points_buffer[phone] = 0.0
        print("✅ [Sync Complete] စာရင်းပိတ်ခြင်း အောင်မြင်ပါသည်။ (ဒေတာများကို Buffer တွင် Poll လုပ်ထားဆဲဖြစ်သည်)")

# 🎬 AI VIDEO WORK DISTRIBUTER (ဖုန်း CPU များဆီသို့ Real-time အလုပ်ခွဲဝေပေးမည့် စနစ်)
async def ai_task_distributor_worker():
    while True:
        task = await hybrid_manager.task_queue.get()
        assigned = False
        while not assigned:
            # အားနေတဲ့ ဖုန်း CPU (Idle Node) ကို ရှာခြင်း
            for phone, node in hybrid_manager.active_nodes.items():
                if node["status"] == "idle":
                    node["status"] = "processing"
                    try:
                        # Wasm ဖြင့် တွက်ချက်ရန် ဖုန်းဆီသို့ JSON Payload လှမ်းထိုးခြင်း (Task Injection)
                        await node["ws"].send(json.dumps({
                            "type": "ai_wasm_task",
                            "task_id": task["task_id"],
                            "script_text": task["script_text"]
                        }))
                        print(f"⚡ [Task Injected] Task {task['task_id']} ကို {phone} ဆီသို့ ပေးလိုက်ပါပြီ။")
                        assigned = True
                        break
                    except Exception:
                        node["status"] = "idle"
            if not assigned:
                await asyncio.sleep(1) # အားမယ့်ဖုန်းမရှိသေးပါက ၁ စက္ကန့် စောင့်ပြီး ပြန်ရှာမည်
        hybrid_manager.task_queue.task_done()

# 📟 MASTER COMMAND TERMINAL (ကျန်စစ်သား ဟု ရိုက်ထည့်မည့် အပိုင်း)
async def master_terminal_input():
    loop = asyncio.get_event_loop()
    task_counter = 1
    while True:
        keyword = await loop.run_in_executor(None, input, "⌨️ Master Command (e.g., ကျန်စစ်သား) -> ")
        if keyword.strip() == "ကျန်စစ်သား":
            print("🤖 AI Script Generater က ဇာတ်ညွှန်းကို JSON အပိုင်းအစများအဖြစ် ခွဲထုတ်နေပါသည်...")
            scripts = [
                "ကျန်စစ်သားသည် ပုဂံခေတ်တွင် အလွန်ရဲရင့်သော စစ်သူကြီးတစ်ဦး ဖြစ်သည်။",
                "သူသည် အနော်ရထာမင်းကြီး၏ ယုံကြည်ရဆုံးသော လက်ရုံးလည်း ဖြစ်၏။",
                "နောင်တွင် ပုဂံထီးနန်းကို ဆက်ခံ၍ ပြည်သူတို့ကို အေးချမ်းစေခဲ့သည်။"
            ]
            for chunk in scripts:
                await hybrid_manager.task_queue.put({
                    "task_id": task_counter,
                    "script_text": chunk
                })
                task_counter += 1
            print(f"🚀 AI Tasks {len(scripts)} ခုကို CPU Pool Queue ထဲသို့ ထည့်သွင်းပြီးပါပြီ။")

# 🌐 WEBSOCKET ROUTER INTERFACE
async def socket_handler(websocket, path):
    parts = path.strip("/").split("/")
    if len(parts) < 2:
        await websocket.close()
        return
        
    phone_number = parts[-1]
    device_id = parts[-2]

    if not hybrid_manager.register_node(phone_number, device_id, websocket):
        await websocket.send(json.dumps({"type": "error", "msg": "device_conflict"}))
        await websocket.close()
        return

    # Database ထဲတွင် အကောင့်ရှိမရှိစစ်ဆေးပြီး မရှိပါက Auto Create လုပ်ပေးခြင်း
    user_data = supabase_request("GET", f"?phone_number=eq.{phone_number}")
    if user_data is not None and not user_data:
        supabase_request("POST", "", {
            "phone_number": phone_number, "device_id": device_id,
            "total_points": 0.0, "kpay_balance": 0.0, "city_location": "Yangon"
        })

    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type")

            # 📡 Case A: DePIN Data ဝင်လာခြင်း (Poll လုပ်ပြီး ခေတ္တစုထားမည်)
            if msg_type == "depin_data":
                mb_shared = payload.get("mb_shared", 0.0)
                hybrid_manager.data_pool_buffer[phone_number] += mb_shared
                
                # Base Reward ပေးပြီး RAM buffer ထဲပေါင်းထည့်ခြင်း
                reward = mb_shared * 5.0 
                hybrid_manager.points_buffer[phone_number] += reward
                print(f"📊 [Data Pooled] {phone_number} က {mb_shared}MB ပို့။ စုစုပေါင်း Pool ပြည့်ရန် စောင့်ဆိုင်းနေဆဲဖြစ်သည်...")

            # ⚡ Case B: ဖုန်း CPU က Wasm တွက်ချက်ပြီး အသံဖိုင် ပြန်ပို့လာခြင်း
            elif msg_type == "wasm_task_complete":
                task_id = payload.get("task_id")
                hybrid_manager.points_buffer[phone_number] += 50.0 # တွက်ပေးသဖြင့် Bonus ပွိုင့်ပေးခြင်း
                
                if phone_number in hybrid_manager.active_nodes:
                    hybrid_manager.active_nodes[phone_number]["status"] = "idle" # ဖုန်းအားသွားပြီဟု ပြောင်းခြင်း
                print(f"🎉 [Wasm Complete] Task {task_id} ကို {phone_number} က တွက်ချက်ပြီး အသံဖိုင် ပြန်ပို့ပေးလိုက်ပါပြီ။")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # လိုင်းပြတ်သွားပါက ကာကွယ်ရေးအနေဖြင့် RAM ထဲက ပွိုင့်ကို DB ထဲ တန်းသိမ်းပေးခြင်း
        ram_points = hybrid_manager.points_buffer.get(phone_number, 0.0)
        if ram_points > 0:
            user_data = supabase_request("GET", f"?phone_number=eq.{phone_number}")
            if user_data:
                new_points = round(user_data[0].get("total_points", 0.0) + ram_points, 2)
                supabase_request("PATCH", f"?phone_number=eq.{phone_number}", {
                    "total_points": new_points, "kpay_balance": round(new_points * POINT_TO_MMK_RATE, 2)
                })
                hybrid_manager.points_buffer[phone_number] = 0.0
        hybrid_manager.unregister_node(phone_number)

async def main():
    asyncio.create_task(periodic_bulk_sync_worker())
    asyncio.create_task(ai_task_distributor_worker())
    asyncio.create_task(master_terminal_input())
    
    async with websockets.serve(socket_handler, "0.0.0.0", 8000):
        print("🚀 Shwe Pocket Master Core Engine Running on Port: 8000...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
