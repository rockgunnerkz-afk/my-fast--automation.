import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/io.dart';
import 'package:device_info_plus/device_info_plus.dart';

void main() {
  runApp(const ShwePocketClientApp());
}

class ShwePocketClientApp extends StatelessWidget {
  const ShwePocketClientApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      home: const MainNodeScreen(),
    );
  }
}

class MainNodeScreen extends StatefulWidget {
  const MainNodeScreen({super.key});

  @override
  State<MainNodeScreen> createState() => _MainNodeScreenState();
}

class _MainNodeScreenState extends State<MainNodeScreen> {
  // ⚙️ CONFIGURATION (Termux Port Forward သုံးထား၍ Localhost အတိုင်း ထားပါသည်)
  final String serverUrl = "ws://127.0.0.1:8000"; 
  final String phoneNumber = "09777777777"; 

  IOWebSocketChannel? _channel;
  bool _isMining = false;
  String _statusMessage = "စတင်ချိတ်ဆက်ရန် အသင့်ဖြစ်ပါပြီ";
  double _mbShared = 0.0;
  Timer? _depinTimer;

  // 🛡️ Get Unique Device ID
  Future<String> _getDeviceId() async {
    DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
    try {
      AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
      return androidInfo.id; 
    } catch (e) {
      return "DESKTOP_TEST_NODE_ID";
    }
  }

  // 🚀 Start Shwe Pocket Node
  void _startNode() async {
    String deviceId = await _getDeviceId();
    final connectionUrl = "$serverUrl/$deviceId/$phoneNumber";

    try {
      _channel = IOWebSocketChannel.connect(Uri.parse(connectionUrl));
      
      setState(() {
        _isMining = true;
        _statusMessage = "Shwe Pocket Network နှင့် ချိတ်ဆက်မှု အောင်မြင်သည် 📡";
      });

      _channel!.stream.listen((message) {
        final data = jsonDecode(message);
        
        if (data["type"] == "ai_wasm_task") {
          _executeWasmTask(data["task_id"], data["script_text"]);
        } else if (data["type"] == "error" && data["msg"] == "device_conflict") {
          _stopNode();
          setState(() {
            _statusMessage = "🚫 စက်တစ်ခုတည်းတွင် အကောင့်ခွဲသုံးခြင်းကို ငြင်းပယ်လိုက်သည်။";
          });
        }
      }, onDone: () => _stopNode(), onError: (err) => _stopNode());

      // 📡 DePIN Data Pool Timed Worker (10s interval)
      _depinTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
        if (_channel != null) {
          _mbShared += 0.2;
          _channel!.sink.add(jsonEncode({
            "type": "depin_data",
            "mb_shared": 0.2
          }));
          setState(() {});
        }
      });

    } catch (e) {
      _stopNode();
      setState(() {
        _statusMessage = "ဆာဗာချိတ်ဆက်မှု မအောင်မြင်ပါ ❌";
      });
    }
  }

  // ⚡ CPU WASM WORKER TASK
  void _executeWasmTask(int taskId, String scriptText) async {
    setState(() {
      _statusMessage = "⚡ AI Task $taskId ကို ဖုန်း CPU သုံး၍ တွက်ချက်နေပါသည်...";
    });

    print("🧠 Processing: $scriptText");
    await Future.delayed(const Duration(seconds: 3)); 

    if (_channel != null) {
      _channel!.sink.add(jsonEncode({
        "type": "wasm_task_complete",
        "task_id": taskId,
        "audio_data": "BASE64_GENERATED_AUDIO_MOCKDATA" 
      }));
    }

    setState(() {
      _statusMessage = "တွက်ချက်မှု ပြီးမြောက်။ နောက်ထပ် Task များကို စောင့်ဆိုင်းနေသည် 🔋";
    });
  }

  void _stopNode() {
    _channel?.sink.close();
    _depinTimer?.cancel();
    setState(() {
      _isMining = false;
      _statusMessage = "ချိတ်ဆက်မှုကို ရပ်တန့်လိုက်ပါပြီ";
    });
  }

  @override
  void dispose() {
    _stopNode();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Shwe Pocket Node Engine v1.0"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _isMining ? Colors.teal.withOpacity(0.15) : Colors.redAccent.withOpacity(0.15),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(color: _isMining ? Colors.teal : Colors.redAccent, width: 2),
              ),
              child: Column(
                children: [
                  Text(
                    _isMining ? "🟢 NODE IS ACTIVE" : "🔴 NODE IS IDLE", 
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 1.2),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _statusMessage, 
                    textAlign: TextAlign.center, 
                    style: const TextStyle(fontSize: 14, color: Colors.white70),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 40),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatTile("Pooled Data", "${_mbShared.toStringAsFixed(1)} MB"),
                _buildStatTile("RAM Rewards", "${(_mbShared * 5).toStringAsFixed(1)} Pts"),
              ],
            ),
            const SizedBox(height: 50),
            ElevatedButton(
              onPressed: _isMining ? _stopNode : _startNode,
              style: ElevatedButton.styleFrom(
                backgroundColor: _isMining ? Colors.redAccent : Colors.teal,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(
                _isMining ? "STOP NODE CONNECTOR" : "START MINING & EARN", 
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildStatTile(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 14)),
        const SizedBox(height: 6),
        Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.amber)),
      ],
    );
  }
}
