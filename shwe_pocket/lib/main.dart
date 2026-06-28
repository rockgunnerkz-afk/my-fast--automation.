import 'package:flutter/material.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Shwe Pocket Node Engine',
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
  final String serverUrl = "wss://redesigned-lamp-pj4v-8000.app.github.dev";
  final String phoneNumber = "09777777777";

  WebSocketChannel? _channel;
  bool _isMining = false;
  String _statusMessage = "စတင်ချိတ်ဆက်ရန် အသင့်ဖြစ်ပါပြီ";
  double _mbShared = 0.0;
  double _ramRewards = 0.0;

  void _toggleMining() {
    if (_isMining) {
      _channel?.sink.close();
      setState(() {
        _isMining = false;
        _statusMessage = "ချိတ်ဆက်မှုကို ရပ်တန့်လိုက်ပါပြီ";
      });
    } else {
      setState(() {
        _statusMessage = "ဆာဗာသို့ လှမ်း၍ ချိတ်ဆက်နေပါသည်...";
      });

      try {
        _channel = IOWebSocketChannel.connect(Uri.parse(serverUrl));
        _channel?.sink.add('CONNECT:$phoneNumber');

        _channel?.stream.listen(
          (message) {
            setState(() {
              _isMining = true;
              _statusMessage = "ဆာဗာနှင့် ချိတ်ဆက်မှု အောင်မြင်ပါပြီ ✅";
              
              if (message.toString().startsWith("DATA:")) {
                var parts = message.toString().split('|');
                _mbShared = double.tryParse(parts[0].split(':')[1]) ?? _mbShared;
                _ramRewards = double.tryParse(parts[1].split(':')[1]) ?? _ramRewards;
              }
            });
          },
          onError: (error) {
            setState(() {
              _isMining = false;
              _statusMessage = "Error: ချိတ်ဆက်မှု ပြတ်တောက်သွားပါသည် ❌";
            });
          },
          onDone: () {
            setState(() {
              _isMining = false;
              _statusMessage = "ဆာဗာမှ ချိတ်ဆက်မှု ပိတ်လိုက်ပါပြီ";
            });
          },
        );
      } catch (e) {
        setState(() {
          _isMining = false;
          _statusMessage = "ဆာဗာလင့်ခ် မှားယွင်းနေပါသည်";
        });
      }
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Shwe Pocket Node Engine...'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _isMining ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                border: Border.all(color: _isMining ? Colors.green : Colors.red, width: 2),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.circle, color: _isMining ? Colors.green : Colors.red, size: 24),
                      const SizedBox(width: 10),
                      Text(_isMining ? "NODE IS ACTIVE" : "NODE IS IDLE", style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(_statusMessage, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, color: Colors.grey)),
                ],
              ),
            ),
            const SizedBox(height: 40),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Column(
                  children: [
                    const Text("Pooled Data", style: TextStyle(fontSize: 16, color: Colors.grey)),
                    const SizedBox(height: 5),
                    Text("${_mbShared.toStringAsFixed(1)} MB", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.amber)),
                  ],
                ),
                Column(
                  children: [
                    const Text("RAM Rewards", style: TextStyle(fontSize: 16, color: Colors.grey)),
                    const SizedBox(height: 5),
                    Text("${_ramRewards.toStringAsFixed(1)} Pts", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.amber)),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 50),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isMining ? Colors.redAccent : const Color(0xFF00695C),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _toggleMining,
                child: Text(_isMining ? "STOP MINING" : "START MINING & EARN", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
